import os
import io
import getpass
import msoffcrypto
import xml.etree.ElementTree as ET
import html
import decimal
import zipfile
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from credentials.models import EncryptedCredential, Expense

class Command(BaseCommand):
    help = 'Parse password protected excel spreadsheet using raw XML parsing for high compatibility'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Path to the excel file')
        parser.add_argument('--user', type=str, default='admin', help='Username to assign data to')

    def handle(self, *args, **options):
        excel_path = options['excel_file']
        target_username = options['user']
        from django.contrib.auth.models import User
        try:
            target_user = User.objects.get(username=target_username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User {target_username} not found!"))
            return
        
        if not os.path.exists(excel_path):
            self.stdout.write(self.style.ERROR(f"File {excel_path} not found"))
            return

        password = getpass.getpass("Enter Excel password: ")

        try:
            # Decrypt to memory stream
            decrypted = io.BytesIO()
            with open(excel_path, "rb") as f:
                file = msoffcrypto.OfficeFile(f)
                file.load_key(password=password)
                file.decrypt(decrypted)
            
            decrypted.seek(0)
            
            with zipfile.ZipFile(decrypted, 'r') as z:
                # 1. Load Shared Strings (Aggressive Regex Fallback)
                shared_strings = []
                try:
                    with z.open('xl/sharedStrings.xml') as f:
                        content = f.read().decode('utf-8')
                        shared_strings = [html.unescape(s) for s in re.findall(r'<t[^>]*>(.*?)</t>', content)]
                except Exception: pass
                self.stdout.write(self.style.SUCCESS(f"    - Loaded {len(shared_strings)} shared strings."))

                # 2. Map Sheet Names to rIds
                with z.open('xl/workbook.xml') as f:
                    content = f.read().decode('utf-8')
                    sheet_info = [] # (name, rId)
                    matches = re.findall(r'<sheet [^>]*name="([^"]+)"[^>]*r:id="([^"]+)"', content)
                    for name, rid in matches:
                        sheet_info.append((html.unescape(name), rid))
                
                self.stdout.write(self.style.SUCCESS(f"Found {len(sheet_info)} tabs."))

                # 3. Map rIds to paths
                with z.open('xl/_rels/workbook.xml.rels') as f:
                    rel_tree = ET.parse(f)
                rel_map = {}
                for rel in rel_tree.findall('{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'):
                    rel_map[rel.get('Id')] = rel.get('Target')

                # 4. Clear existing data FOR THIS USER ONLY and init logs
                self.stdout.write(self.style.WARNING(f"Clearing existing data for {target_username}..."))
                EncryptedCredential.objects.filter(user=target_user).delete()
                Expense.objects.filter(user=target_user).delete()
                with open("processed.txt", "w") as f_proc: f_proc.write(f"Processed for {target_username}:\n")
                with open("error.txt", "w") as f_err: f_err.write(f"Errors for {target_username}:\n")

                # 5. Search for Credentials for THIS USER
                error_count = 0
                processed_count = 0
                
                for target_name, target_rid in sheet_info:
                    if target_name.lower() != 'pwd_personal':
                        continue
                    
                    path = rel_map.get(target_rid)
                    if not path: continue
                    if not path.startswith('xl/'): path = 'xl/' + path
                    
                    self.stdout.write(self.style.SUCCESS(f"Reading {target_name} [ID: {target_rid}] from {path}"))
                    
                    try:
                        with z.open(path) as f:
                            raw_xml = f.read()
                            sheet_tree = ET.fromstring(raw_xml)
                        
                        rows_data = []
                        for row_node in sheet_tree.findall('.//{*}row'):
                            row_vals = []
                            for c in row_node.findall('{*}c'):
                                val = ""
                                v_node = c.find('{*}v')
                                if v_node is not None:
                                    val = v_node.text or ""
                                    if c.get('t') == 's' and val:
                                        try: val = shared_strings[int(val)]
                                        except: pass
                                else:
                                    is_node = c.find('{*}is')
                                    if is_node is not None:
                                        t_node = is_node.find('{*}t')
                                        if t_node is not None: val = t_node.text or ""
                                row_vals.append(val)
                            
                            if any(row_vals): 
                                rows_data.append(row_vals)
                                row_str = " | ".join([str(v) for v in row_vals]).lower()
                                if 'citi' in row_str or 'costco' in row_str:
                                    self.stdout.write(self.style.WARNING(f"      >>> TRACE ({target_name}): {row_str}"))

                        if rows_data:
                            self.stdout.write(f"    - Processing {len(rows_data)} rows for {target_username}...")
                            for i, cells in enumerate(rows_data):
                                try:
                                    clean_cells = [str(c).strip() for c in cells if str(c).strip()]
                                    if not clean_cells: continue
                                    
                                    # Header skip
                                    if len(clean_cells) < 4 and clean_cells[0].lower() in ['password', 'tag', 'passwords']:
                                        continue
                                    
                                    res = self.parse_row_credential(clean_cells)
                                    if res:
                                        obj = EncryptedCredential(
                                            user=target_user,
                                            tag=res.get('tag'), username=res.get('username'),
                                            url=res.get('url'), additional_info=res.get('info')
                                        )
                                        if res.get('password'): obj.password = res.get('password')
                                        obj.save()
                                        processed_count += 1
                                        with open("processed.txt", "a") as f_proc:
                                            f_proc.write(f"Row {i+1}: Saved {res.get('tag')}\n")
                                except Exception as e:
                                    error_count += 1
                                    with open("error.txt", "a") as f_err:
                                        f_err.write(f"Row {i+1} | Error: {str(e)}\n")
                    except Exception as e:
                        error_count += 1
                        with open("error.txt", "a") as f_err:
                            f_err.write(f"Critical Error in {path}: {str(e)}\n")
                
                self.stdout.write(self.style.SUCCESS(f"\nFinal Result: Stored {processed_count} credentials. Errors: {error_count}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Critical error: {str(e)}"))
            import traceback; traceback.print_exc()

    def parse_row_credential(self, cells):
        if not cells: return None
        res = {'tag': cells[0], 'username': None, 'password': None, 'url': None, 'info': []}
        remaining = cells[1:]

        for cell in remaining:
            if cell.startswith('http') or 'www.' in cell or '.gov' in cell or '.com' in cell:
                if not (cell.startswith('http') or '://' in cell) and '/' in cell:
                    pass
                else:
                    if not res['url']: res['url'] = cell; continue
            
            if '/' in cell and not (cell.startswith('http') or '://' in cell):
                parts = cell.split('/', 1)
                u_part, p_part = parts[0].strip(), parts[1].strip()
                if not res['username']: res['username'] = u_part
                else: res['info'].append(u_part)
                if not res['password']: res['password'] = p_part
                else: res['info'].append(p_part)
                continue
            
            if ' ' in cell and '@' not in cell and '.' not in cell:
                parts = cell.split(' ', 1)
                u_part, p_part = parts[0].strip(), parts[1].strip()
                if not res['username']: res['username'] = u_part
                else: res['info'].append(u_part)
                if not res['password']: res['password'] = p_part
                else: res['info'].append(p_part)
                continue

            if '@' in cell and '.' in cell:
                if not res['username']: res['username'] = cell; continue
            
            if not res['password'] and not res['username'] and len(cell) > 3:
                res['username'] = cell; continue
            
            if not res['password'] and res['username']:
                res['password'] = cell; continue

            res['info'].append(cell)

        res['info'] = " | ".join(res['info']) if res['info'] else None
        return res
