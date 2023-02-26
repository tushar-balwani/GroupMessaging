import json
import unittest

from src.main.db import db
from src.main.model.user import User
from src.main.model.group import Group
from src.main.model.message import Message, Like

from src.main.run import create_app

from src.main.config import TestingConfig


class GroupApiTests(unittest.TestCase):
    """This class represents the group API test case"""

    def setUp(self):
        self.app = create_app(config_name=TestingConfig)
        db.drop_all()
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

        # Create test users
        user1 = User(username='user1', password='password1')
        user2 = User(username='user2', password='password2')
        db.session.add_all([user1, user2])
        db.session.commit()

        # Create test groups
        group1 = Group(name='group1')
        group2 = Group(name='group2')
        db.session.add_all([group1, group2])
        db.session.commit()

        # Create test messages
        message1 = Message(text='message1', user_id=user1.id, group_id=group1.id)
        message2 = Message(text='message2', user_id=user2.id, group_id=group1.id)
        message3 = Message(text='message3', user_id=user1.id, group_id=group2.id)
        db.session.add_all([message1, message2, message3])
        db.session.commit()

        # Create like messages
        like1 = Like(user_id=user2.id, message_id=message1.id)
        like2 = Like(user_id=user1.id, message_id=message2.id)
        db.session.add_all([like1, like2])
        db.session.commit()

        self.user_id = {'user1': user1.id, 'user2': user2.id}
        self.group_id = {'group1': group1.id, 'group2': group2.id}
        self.message_id = {'message1': message1.id, 'message2': message2.id, 'message3': message3.id}
        self.like_id = {'like1': like1.id, 'like2': like2.id}

        # Set up auth token
        resp=self.client.post('/login', json={'username': 'user1', 'password': 'password1'})
        self.token = json.loads(resp.data)['access_token']

    def tearDown(self):
        self.client.post('/logout', headers={'Authorization': f'Bearer {self.token}'})
        db.session.remove()
        db.drop_all()

    def test_list_groups(self):
        """Test to list all available groups"""
        resp = self.client.get('/groups', headers={'Authorization': f'Bearer {self.token}'})
        data = json.loads(resp.data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(json.loads(resp.data)['groups']), 2)

    def test_get_group(self):
        """Test to get group details"""
        response = self.client.get(f'/groups/{self.group_id["group1"]}',
                                   headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data)['group']['id'], self.group_id['group1'])

    def test_create_group(self):
        """Test to create new group"""
        resp = self.client.post('/groups', headers={'Authorization': f'Bearer {self.token}'},
                                json={'name': 'group3'})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(json.loads(resp.data)['group']['name'], 'group3')

    def test_create_group_already_exists(self):
        """Test creating a group with a name that already exists"""
        resp = self.client.post('/groups', headers={'Authorization': f'Bearer {self.token}'},
                                json={'name': 'group1'})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(json.loads(resp.data)['error'], 'Group with this name already exists')

    def test_delete_group(self):
        """Test to delete group"""
        group = Group(name='something')
        db.session.add(group)
        db.session.commit()

        resp = self.client.delete('/groups/{}'.format(group.id),
                                  headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.data)['message'], 'Group deleted successfully')

    def test_delete_group_not_found(self):
        """Test to delete non-existing group"""
        resp = self.client.delete('/groups/{}'.format(self.group_id['group1'] + 100),
                                  headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(json.loads(resp.data)['error'], 'Group not found')

    def test_search_group(self):
        """Test to search groups"""
        resp = self.client.post('/groups/search', json={'name': 'group'},
                                headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.data), {
            'groups': [{'id': 1, 'members': [], 'name': 'group1'}, {'id': 2, 'members': [], 'name': 'group2'}]})

    def test_add_members(self):
        """Test to add user in group"""
        resp = self.client.post(f'/groups/{self.group_id["group1"]}/members', json={'user_id': self.user_id['user1']},
                                headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(json.loads(resp.data)['message'], 'User added to group successfully')

    def test_add_members_group_not_found(self):
        """Test to add user to non-existing group"""
        resp = self.client.post(f'/groups/{self.group_id["group1"] + 1000}/members',
                                json={'user_id': self.user_id['user1']},
                                headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(json.loads(resp.data)['error'], 'Group not found')

    def test_add_members_user_not_found(self):
        """Test to add non-existing user to group"""
        resp = self.client.post(f'/groups/{self.group_id["group1"]}/members',
                                json={'user_id': self.user_id['user1'] + 1000},
                                headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(json.loads(resp.data)['error'], 'User not found')

    def test_add_members_user_already_member(self):
        """Test add user to group with user that already exists"""
        self.client.post(f'/groups/{self.group_id["group1"]}/members', json={'user_id': self.user_id['user1']},
                         headers={'Authorization': f'Bearer {self.token}'})
        resp = self.client.post(f'/groups/{self.group_id["group1"]}/members', json={'user_id': self.user_id['user1']},
                                headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(json.loads(resp.data)['error'], 'User is already a member of this group')

    def test_list_members(self):
        """Test to list all members in group"""
        resp = self.client.get(f'/groups/{self.group_id["group1"]}/members',
                               headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.data)['members'], [])

    def test_list_members_group_not_found(self):
        """Test to list members from non-existing group"""
        resp = self.client.get(f'/groups/{self.group_id["group1"] + 1000}/members',
                               headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(json.loads(resp.data)['error'], 'Group not found')

    def test_remove_members(self):
        """Test to remove members from group"""
        self.client.post(f'/groups/{self.group_id["group1"]}/members', json={'user_id': self.user_id['user1']},
                         headers={'Authorization': f'Bearer {self.token}'})
        resp = self.client.post(f'/groups/{self.group_id["group1"]}/remove_member',
                                json={'user_id': self.user_id['user1']},
                                headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.data)['group'], {'id': 1, 'members': [], 'name': 'group1'})

    def test_remove_members_group_not_found(self):
        """Test to remove members from non-existing group"""
        resp = self.client.post(f'/groups/{self.group_id["group1"] + 1000}/remove_member',
                                json={'user_id': self.user_id['user1']},
                                headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(json.loads(resp.data)['error'], 'Group not found')

    def test_remove_members_user_not_found(self):
        """Test to remove non-existing member from group"""
        resp = self.client.post(f'/groups/{self.group_id["group1"]}/remove_member',
                                json={'user_id': self.user_id['user1'] + 1000},
                                headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(json.loads(resp.data)['error'], 'User not found')

    def test_search_message(self):
        """Test to search messages in group"""
        self.client.post(f'/groups/{self.group_id["group1"]}/members', json={'user_id': self.user_id['user1']},
                         headers={'Authorization': f'Bearer {self.token}'})
        resp = self.client.post(f'/groups/{self.group_id["group1"]}/messages/search',
                                json={'query': 'm'},
                                headers={'Authorization': f'Bearer {self.token}'})
        messages = [message['text'] for message in json.loads(resp.data)['messages']]
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(messages, ['message2', 'message1'])

    def test_search_message_group_not_found(self):
        """Test to search message in non-existing group"""
        resp = self.client.post(f'/groups/{self.group_id["group1"] + 1000}/messages/search',
                                json={'query': 'm'},
                                headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(json.loads(resp.data)['error'], 'Group not found')

    def test_search_message_not_member(self):
        """Test to search message in group the user is not member of"""
        resp = self.client.post(f'/groups/{self.group_id["group1"]}/messages/search',
                                json={'query': 'm'},
                                headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(json.loads(resp.data)['error'], 'You must be a member of the group to post messages')

    def test_post_message(self):
        """Test to post new message in group"""
        self.client.post(f'/groups/{self.group_id["group1"]}/members', json={'user_id': self.user_id['user1']},
                         headers={'Authorization': f'Bearer {self.token}'})
        resp = self.client.post(f'/groups/{self.group_id["group1"]}/messages',
                                json={'text': 'welcome'},
                                headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(json.loads(resp.data)['message']['group_id'], 1)
        self.assertEqual(json.loads(resp.data)['message']['text'], 'welcome')
        self.assertEqual(json.loads(resp.data)['message']['user_id'], self.user_id['user1'])

    def test_post_message_group_not_found(self):
        """Test to post new message in non-existing group"""
        resp = self.client.post(f'/groups/{self.group_id["group1"] + 1000}/messages',
                                json={'text': 'welcome'},
                                headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(json.loads(resp.data)['error'], 'Group not found')

    def test_post_message_not_member(self):
        """Test to post message in group user is not member of"""
        resp = self.client.post(f'/groups/{self.group_id["group1"]}/messages',
                                json={'text': 'welcome'},
                                headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(json.loads(resp.data)['error'], 'You must be a member of the group to post messages')

    def test_list_messages(self):
        """Test to list all messages in group"""
        self.client.post(f'/groups/{self.group_id["group1"]}/members', json={'user_id': self.user_id['user1']},
                         headers={'Authorization': f'Bearer {self.token}'})
        resp = self.client.get(f'/groups/{self.group_id["group1"]}/messages',
                               headers={'Authorization': f'Bearer {self.token}'})
        messages = [message['text'] for message in json.loads(resp.data)['messages']]
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(messages, ['message2', 'message1'])

    def test_list_messages_group_not_found(self):
        """Test to list messages from non-existing group"""
        resp = self.client.get(f'/groups/{self.group_id["group1"] + 1000}/messages',
                               headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(json.loads(resp.data)['error'], 'Group not found')

    def test_list_messages_not_member(self):
        """Test to list messages from group user is not part of"""
        resp = self.client.get(f'/groups/{self.group_id["group1"]}/messages',
                               headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(json.loads(resp.data)['error'], 'You must be a member of the group to view messages')

    def test_get_message(self):
        """Test to get message details from group"""
        self.client.post(f'/groups/{self.group_id["group1"]}/members', json={'user_id': self.user_id['user1']},
                         headers={'Authorization': f'Bearer {self.token}'})
        resp = self.client.get(f'/groups/{self.group_id["group1"]}/messages/{self.message_id["message1"]}',
                               headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.data)['message']['text'], 'message1')

    def test_get_message_group_not_found(self):
        """Test to get message details from non-existing group"""
        resp = self.client.get(f'/groups/{self.group_id["group1"] + 1000}/messages/{self.message_id["message1"]}',
                               headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(json.loads(resp.data)['error'], 'Group not found')

    def test_get_message_not_member(self):
        """Test to get messages user is not part of"""
        resp = self.client.get(f'/groups/{self.group_id["group1"]}/messages/{self.message_id["message1"]}',
                               headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(json.loads(resp.data)['error'], 'You must be a member of the group to view messages')

    def test_get_message_not_found(self):
        """Test to get non-existing message"""
        self.client.post(f'/groups/{self.group_id["group1"]}/members', json={'user_id': self.user_id['user1']},
                         headers={'Authorization': f'Bearer {self.token}'})
        resp = self.client.get(f'/groups/{self.group_id["group1"]}/messages/{self.message_id["message1"] + 1000}',
                               headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(json.loads(resp.data)['error'], 'Message not found.')

    def test_edit_message(self):
        """Test to edit message in group"""
        self.client.post(f'/groups/{self.group_id["group1"]}/members', json={'user_id': self.user_id['user1']},
                         headers={'Authorization': f'Bearer {self.token}'})
        resp = self.client.put(f'/groups/{self.group_id["group1"]}/messages/{self.message_id["message1"]}',
                               json={'text': 'updated'},
                               headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(json.loads(resp.data)['message']['text'], 'updated')

    def test_edit_message_group_not_found(self):
        """Test to edit message in non-existing group"""
        resp = self.client.put(f'/groups/{self.group_id["group1"] + 1000}/messages/{self.message_id["message1"]}',
                               json={'text': 'updated'},
                               headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(json.loads(resp.data)['error'], 'Group not found')

    def test_edit_message_not_found(self):
        """Test to edit non-existing message"""
        resp = self.client.put(f'/groups/{self.group_id["group1"]}/messages/{self.message_id["message1"] + 1000}',
                               json={'text': 'updated'},
                               headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(json.loads(resp.data)['error'], 'Message not found')

    def test_edit_message_not_authorized(self):
        """Test to edit other users message"""
        resp = self.client.put(f'/groups/{self.group_id["group1"]}/messages/{self.message_id["message2"]}',
                               json={'text': 'updated'},
                               headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(json.loads(resp.data)['error'], 'You are not authorized to edit this message')

    def test_delete_message(self):
        """Test to delete message"""
        message = Message(text='welcome', user_id=self.user_id['user1'], group_id=self.group_id['group1'])
        db.session.add(message)
        db.session.commit()

        message_id = message.id

        self.client.post(f'/groups/{self.group_id["group1"]}/members', json={'user_id': self.user_id['user1']},
                         headers={'Authorization': f'Bearer {self.token}'})
        resp = self.client.delete(f'/groups/{self.group_id["group1"]}/messages/{message_id}',
                                  headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.data)['message'], 'Message deleted successfully')

    def test_delete_message_group_not_found(self):
        """Test to delete message from non-existing group"""
        resp = self.client.delete(f'/groups/{self.group_id["group1"] + 1000}/messages/{self.message_id["message1"]}',
                                  headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(json.loads(resp.data)['error'], 'Group not found')

    def test_delete_message_not_found(self):
        """Test to delete non-existing message"""
        resp = self.client.delete(f'/groups/{self.group_id["group1"]}/messages/{self.message_id["message1"] + 1000}',
                                  headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(json.loads(resp.data)['error'], 'Message not found')

    def test_delete_message_not_authorized(self):
        """Test to delete other users message"""
        resp = self.client.delete(f'/groups/{self.group_id["group1"]}/messages/{self.message_id["message2"]}',
                                  headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(json.loads(resp.data)['error'], 'You are not authorized to delete this message')

    def test_like_message(self):
        """Test to like a message"""
        message = Message(text='welcome', user_id=self.user_id['user2'], group_id=self.group_id['group1'])
        db.session.add(message)
        db.session.commit()

        message_id = message.id

        resp = self.client.post(f'/groups/{self.group_id["group1"]}/messages/{message_id}/like',
                                headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(json.loads(resp.data)['message'], 'Liked successfully')

    def test_like_message_group_not_found(self):
        """Test to like a message in non-existing group"""
        resp = self.client.post(f'/groups/{self.group_id["group1"] + 1000}/messages/{self.message_id["message2"]}/like',
                                headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(json.loads(resp.data)['error'], 'Group not found')

    def test_like_message_not_found(self):
        """Test to like non-existing message"""
        resp = self.client.post(f'/groups/{self.group_id["group1"]}/messages/{self.message_id["message1"] + 1000}/like',
                                headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(json.loads(resp.data)['error'], 'Message not found')

    def test_like_message_own_message(self):
        """Test to like user's own message"""
        resp = self.client.post(f'/groups/{self.group_id["group1"]}/messages/{self.message_id["message1"]}/like',
                                headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(json.loads(resp.data)['error'], 'Cannot like your own message')

    def test_like_message_already_liked(self):
        """Test to like already liked message"""
        resp = self.client.post(f'/groups/{self.group_id["group1"]}/messages/{self.message_id["message2"]}/like',
                                headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(json.loads(resp.data)['error'], 'Already liked this message')

    def test_unlike_message(self):
        """Test to unlike message"""
        resp = self.client.delete(f'/groups/{self.group_id["group1"]}/messages/{self.message_id["message2"]}/like',
                                  headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.data)['message'], 'Unliked successfully')

    def test_unlike_message_group_not_found(self):
        """Test to unlike message in non-existing group"""
        resp = self.client.delete(
            f'/groups/{self.group_id["group1"] + 1000}/messages/{self.message_id["message2"]}/like',
            headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(json.loads(resp.data)['error'], 'Group not found')

    def test_unlike_message_not_found(self):
        """Test to unlike non-existing group"""
        resp = self.client.delete(
            f'/groups/{self.group_id["group1"]}/messages/{self.message_id["message1"] + 1000}/like',
            headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(json.loads(resp.data)['error'], 'Message not found')

    def test_unlike_message_non_liked_message(self):
        """Test to unlike message which is not liked by user"""
        resp = self.client.delete(f'/groups/{self.group_id["group1"]}/messages/{self.message_id["message1"]}/like',
                                  headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(json.loads(resp.data)['error'], 'You have not liked this message')
