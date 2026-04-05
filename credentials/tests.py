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
    def test_edit_credential_functionality(self):
        """Test that a record can be updated securely."""
        cred = EncryptedCredential.objects.create(
            user=self.user1, tag='Initial Name', username='initial_user', password='old_password'
        )
        
        # Log in as user
        self.client.login(username='malay', password='password123')
        
        # Post UPDATED data
        self.client.post(reverse('edit_credential', args=[cred.pk]), {
            'tag': 'Updated Name',
            'username': 'updated_user',
            'password': 'new_password_123',
            'url': 'https://google.com',
            'additional_info': 'Edited info'
        })
        
        # Refresh from DB
        cred.refresh_from_db()
        self.assertEqual(cred.tag, 'Updated Name')
        self.assertEqual(cred.username, 'updated_user')
    def test_create_credential_via_view(self):
        """Test creating a record through the actual web form."""
        self.client.login(username='malay', password='password123')
        
        # Post data to the create view
        self.client.post(reverse('create_credential'), {
            'tag': 'Web Added Account',
            'username': 'web_user',
            'password': 'web_password_123',
            'url': 'https://github.com',
            'additional_info': 'Added via test'
        })
        
    def test_unauthenticated_access_blocked(self):
        """Ensure that guests are redirected to login."""
        self.client.logout()
        response = self.client.get(reverse('credential_list'))
        self.assertRedirects(response, '/login/?next=/')

    def test_unauthorized_edit_blocked(self):
        """CRITICAL: User A cannot edit User B's record even if they know the ID."""
        # Create record for User 2
        cred2 = EncryptedCredential.objects.create(
            user=self.user2, tag='Safe Account', password='p1'
        )
        
        # Log in as User 1
        self.client.login(username='malay', password='password123')
        
        # Try to access User 2's edit page
        response = self.client.get(reverse('edit_credential', args=[cred2.pk]))
        # Should be a 404 since User 1 doesn't own it
        self.assertEqual(response.status_code, 404)

    def test_search_functionality(self):
        """Test tag filtering works correctly."""
        EncryptedCredential.objects.create(user=self.user1, tag='Amazon Shopping', password='p1')
        EncryptedCredential.objects.create(user=self.user1, tag='Citibank Personal', password='p2')
        
        self.client.login(username='malay', password='password123')
        response = self.client.get(reverse('credential_list') + '?tag=amazon')
        
        self.assertContains(response, 'Amazon Shopping')
        self.assertNotContains(response, 'Citibank Personal')
