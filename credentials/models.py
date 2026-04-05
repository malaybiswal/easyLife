from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from cryptography.fernet import Fernet
import base64

class EncryptedCredential(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credentials', null=True)
    tag = models.CharField(max_length=255, db_index=True, blank=True, null=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    encrypted_password = models.TextField(blank=True, null=True)
    url = models.URLField(max_length=500, blank=True, null=True)
    additional_info = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tag} - {self.username}"

    @property
    def password(self):
        if not self.encrypted_password:
            return None
        f = Fernet(settings.ENCRYPTION_KEY.encode('utf-8'))
        try:
            decrypted = f.decrypt(self.encrypted_password.encode('utf-8'))
            return decrypted.decode('utf-8')
        except Exception:
            return "Decryption Error"

    @password.setter
    def password(self, raw_password):
        if raw_password:
            f = Fernet(settings.ENCRYPTION_KEY.encode('utf-8'))
            encrypted = f.encrypt(raw_password.encode('utf-8'))
            self.encrypted_password = encrypted.decode('utf-8')
        else:
            self.encrypted_password = None

class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses', null=True)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    tag = models.CharField(max_length=100, blank=True, null=True)
    raw_row = models.TextField(blank=True, null=True) # To track original row if needed for debugging

    def __str__(self):
        return f"{self.description} - {self.amount}"

class FileDetail(models.Model):
    tag = models.CharField(max_length=100)
    file_location = models.CharField(max_length=500)
    detailed_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tag} - {self.file_location}"
