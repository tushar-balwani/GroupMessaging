import json
import unittest

from src.main.db import db
from src.main.model.user import User
from src.main.run import create_app

from src.main.config import TestingConfig


class UserTestCase(unittest.TestCase):
    """This class represents the user API test case"""

    def setUp(self):
        self.app = create_app(config_name=TestingConfig)
        db.drop_all()
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
        admin = User(username='testuser', password='testpassword', is_admin=True)
        non_admin = User(username='user', password='password', is_admin=False)
        db.session.add_all([admin, non_admin])
        db.session.commit()

        self.user_id = {'admin': admin.id, 'non_admin': non_admin}

        data = {'username': 'testuser', 'password': 'testpassword'}
        self.token = json.loads(self.client.post('/login', json=data).data)['access_token']

    def tearDown(self):
        self.client.post('/logout', headers={'Authorization': f'Bearer {self.token}'})
        db.session.remove()
        db.drop_all()

    def test_list_users(self):
        """Test to list all users"""
        response = self.client.get('/users', headers={'Authorization': f'Bearer {self.token}'})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(data['users']) > 0)

    def test_create_user(self):
        """Test to create new user"""
        new_user = {'username': 'newuser', 'password': 'newpassword'}
        response = self.client.post('/users', json=new_user, headers={'Authorization': f'Bearer {self.token}'})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['user']['username'], new_user['username'])

    def test_get_user(self):
        """Test to get user details"""
        response = self.client.get(f'/users/{self.user_id["admin"]}', headers={'Authorization': f'Bearer {self.token}'})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['user']['id'], self.user_id["admin"])

    def test_get_user_not_found(self):
        """Test to get details of non-existing user"""
        response = self.client.get(f'/users/{self.user_id["admin"] + 1000}',
                                   headers={'Authorization': f'Bearer {self.token}'})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['error'], 'User not found')

    def test_update_user(self):
        """Test to update existing user"""
        data = {'username': 'test', 'password': 'test'}
        user = User(**data)
        db.session.add(user)
        db.session.commit()

        update_user = {'username': 'updateduser', 'password': 'updatedpassword'}
        response = self.client.put(f'/users/{user.id}', json=update_user,
                                   headers={'Authorization': f'Bearer {self.token}'})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['user']['username'], update_user['username'])

    def test_update_user_deactivate(self):
        """Test to deactivate user"""
        data = {'username': 'test', 'password': 'test', 'is_active': True}
        user = User(**data)
        db.session.add(user)
        db.session.commit()

        update_user = {'username': 'updateduser', 'password': 'updatedpassword', 'is_admin': True, 'is_active': False}
        response = self.client.put(f'/users/{user.id}', json=update_user,
                                   headers={'Authorization': f'Bearer {self.token}'})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['user']['username'], update_user['username'])
        self.assertEqual(data['user']['is_active'], update_user['is_active'])

    def test_update_user_not_found(self):
        """Test to update non-existing user"""
        data = {'username': 'test', 'password': 'test'}
        user = User(**data)
        db.session.add(user)
        db.session.commit()

        update_user = {'username': 'updateduser', 'password': 'updatedpassword'}
        response = self.client.put(f'/users/{user.id + 1000}', json=update_user,
                                   headers={'Authorization': f'Bearer {self.token}'})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['error'], 'User not found')

    def test_update_user_non_admin(self):
        """Test to update user details from non-admin user"""
        data = {'username': 'test', 'password': 'test', 'is_admin': False}
        user = User(**data)
        db.session.add(user)
        db.session.commit()

        token = json.loads(self.client.post('/login', json=data).data)['access_token']

        update_user = {'username': 'updateduser', 'password': 'updatedpassword'}
        response = self.client.put(f'/users/{user.id}', json=update_user,
                                   headers={'Authorization': f'Bearer {token}'})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(data['error'], 'You do not have the required role')

    def test_delete_user(self):
        """Test to delete user"""
        data = {'username': 'test', 'password': 'test'}
        user = User(**data)
        db.session.add(user)
        db.session.commit()

        response = self.client.delete(f'/users/{user.id}', headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data)['message'], 'User deleted successfully')

    def test_delete_user_not_found(self):
        """Test to delete non-existing user"""
        data = {'username': 'test', 'password': 'test'}
        user = User(**data)
        db.session.add(user)
        db.session.commit()

        response = self.client.delete(f'/users/{user.id + 1000}', headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(json.loads(response.data)['error'], 'User not found')

    def test_login_details_required(self):
        """Test login api with partial details"""
        response = self.client.post(f'/login', json={'username': 'something'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.data)['error'], 'Username and password are required')

    def test_login_invalid_details(self):
        """Test login api with invalid details"""
        response = self.client.post(f'/login', json={'username': 'something', 'password': 'something'},
                                    headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(json.loads(response.data)['error'], 'Invalid username or password')

    def test_login_invalid_password(self):
        """Test login api with invalid password"""
        data = {'username': 'test', 'password': 'test'}
        user = User(**data)
        db.session.add(user)
        db.session.commit()

        response = self.client.post(f'/login', json={'username': user.username, 'password': 'something'},
                                    headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(json.loads(response.data)['error'], 'Invalid username or password')
