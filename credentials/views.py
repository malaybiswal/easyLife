from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from credentials.models import EncryptedCredential, Expense, FileDetail
import decimal
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout, logout as auth_logout
from django.http import JsonResponse
import json
import time

@login_required(login_url='login')
def verify_vault_access(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        password = data.get('password')
        if request.user.check_password(password):
            return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=403)

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')
    else:
        form = UserCreationForm()
    return render(request, 'credentials/register.html', {'form': form})

@login_required(login_url='login')
def credential_list(request):
    tag_search = request.GET.get('tag', '')
    context = {'tag_search': tag_search}
    # ONLY show items for this specific user
    items = EncryptedCredential.objects.filter(user=request.user)
    if tag_search: items = items.filter(tag__icontains=tag_search)
    context['items'] = items
    return render(request, 'credentials/list.html', context)

@login_required(login_url='login')
def edit_credential(request, pk):
    # Only allow editing if the record belongs to the current user
    item = get_object_or_404(EncryptedCredential, pk=pk, user=request.user)
    if request.method == 'POST':
        item.tag = request.POST.get('tag')
        item.username = request.POST.get('username')
        item.url = request.POST.get('url')
        item.additional_info = request.POST.get('additional_info')
        if request.POST.get('password'):
            item.password = request.POST.get('password')
        item.save()
        return redirect('/?tag=' + request.POST.get('tag', ''))
    return render(request, 'credentials/edit_credential.html', {'item': item})

from django.contrib.auth import logout

@login_required(login_url='login')
def delete_credential(request, pk):
    # Only allow deletion if the record belongs to the current user
    item = get_object_or_404(EncryptedCredential, pk=pk, user=request.user)
    if request.method == 'POST':
        confirm_text = request.POST.get('confirm_tag', '').strip()
        if confirm_text == item.tag.strip():
            item.delete()
            return redirect('/')
        else:
            return render(request, 'credentials/delete_confirm.html', {
                'item': item, 
                'error': f'The name you entered ("{confirm_text}") does not match the record name.'
            })
    return render(request, 'credentials/delete_confirm.html', {'item': item})

@login_required(login_url='login')
def create_credential(request):
    if request.method == 'POST':
        tag = request.POST.get('tag')
        username = request.POST.get('username')
        password = request.POST.get('password')
        url = request.POST.get('url')
        info = request.POST.get('additional_info')
        smart = request.POST.get('smart_entry', '').strip()

        if smart and not username and not password:
            parts = []
            if '/' in smart: parts = smart.split('/', 1)
            elif ' ' in smart: parts = smart.split(' ', 1)
            if len(parts) == 2:
                username = parts[0].strip()
                password = parts[1].strip()

        # Associate specifically with THIS user
        item = EncryptedCredential(
            user=request.user, tag=tag, username=username, url=url, additional_info=info
        )
        if password: item.password = password
        item.save()
        return redirect('/')
    return render(request, 'credentials/edit_credential.html', {'is_create': True})

def logout_view(request):
    logout(request)
    return redirect('login')
