from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from credentials.models import EncryptedCredential

class EasyLifeSecurityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='malay', password='password123')
        self.user2 = User.objects.create_user(username='other_user', password='password456')

    def test_encryption_on_save(self):
        """Verify that password is encrypted when saved."""
        cred = EncryptedCredential.objects.create(
            user=self.user1, tag='Test Bank', username='malay', password='super_secret_password'
        )
        # Check that the raw password is NEVER stored in the database
        self.assertNotEqual(cred.encrypted_password, 'super_secret_password')
        # Check that it decrypts correctly
        self.assertEqual(cred.password, 'super_secret_password')

    def test_user_data_isolation(self):
        """CRITICAL: Test that one user cannot see another user's data."""
        # Malay adds a credential
        EncryptedCredential.objects.create(
            user=self.user1, tag='Malay Personal', password='secret1'
        )
        # Other user adds a credential
        EncryptedCredential.objects.create(
            user=self.user2, tag='Other Personal', password='secret2'
        )

        # Log in as Malay
        self.client.login(username='malay', password='password123')
        response = self.client.get(reverse('credential_list'))
        
        # Malay should see his vault but NOT other_user's
        self.assertContains(response, 'Malay Personal')
        self.assertNotContains(response, 'Other Personal')

    def test_registration_flow(self):
        """Test that a new user can sign up."""
        response = self.client.post(reverse('register'), {
            'username': 'new_user',
            'password1': 'newpassword123',
            'password2': 'newpassword123'
        }, follow=True)
        # Should redirect to home after registration
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='new_user').exists())

    def test_smart_entry_parsing(self):
        """Test the logic that splits user/pass or user pass."""
        from credentials.management.commands.parse_credentials import Command
        cmd = Command()
        
        # Test slash separator
        res1 = cmd.parse_row_credential(['Citibank', 'malay/secret123'])
        self.assertEqual(res1['username'], 'malay')
        self.assertEqual(res1['password'], 'secret123')
        
    def test_safe_deletion_verification(self):
        """Test that a record is only deleted after correct text confirmation."""
        cred = EncryptedCredential.objects.create(
            user=self.user1, tag='Sensitive Bank', password='secretpassword'
        )
        
        # Log in as user
        self.client.login(username='malay', password='password123')
        
        # Attempt deletion with WRONG text
        self.client.post(reverse('delete_credential', args=[cred.pk]), {
            'confirm_tag': 'wrong_text'
        })
        self.assertTrue(EncryptedCredential.objects.filter(pk=cred.pk).exists())
        
        # Attempt deletion with CORRECT text
        self.client.post(reverse('delete_credential', args=[cred.pk]), {
            'confirm_tag': 'Sensitive Bank'
        })
        # Record should be GONE now
        self.assertFalse(EncryptedCredential.objects.filter(pk=cred.pk).exists())
