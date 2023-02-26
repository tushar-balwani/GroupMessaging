# Group Messaging APIs

This is a group messaging API that allows users to create groups, send messages, and like messages. The API is built using Flask and SQLAlchemy.

## Endpoints
### Users

1. list users: `/users`
2. get user: `/users/:user_id`
3. create user: `/users`
4. update user: `/users/:user_id`
5. delete user: `/users/:user_id`
6. login: `/login`
7. logout: `/logout`

*Only Admin user can access user APIs
### Groups

1. list groups: `/groups`
2. get group: `/groups/:group_id`
3. create group: `/groups`
4. delete group: `/groups/:group_id`
5. search group: `/groups/search`
6. add member: `/groups/:group_id/members`
7. remove member: `/groups/:group_id/remove_member`
8. list members: `/groups/:group_id/members`
9. search message in group: `/groups/:group_id/messages/search`
10. list messages: `/groups/:group_id/messages`
11. get message: `/groups/:group_id/messages/:message_id`
12. post message: `/groups/:group_id/messages`
13. delete message: `/groups/:group_id>/messages/:message_id`
14. edit message: `/groups/:group_id/messages/:message_id`
15. like message: `/groups/:group_id/messages/:message_id/like`
16. unlike message: `/groups/:group_id/messages/:message_id/like`