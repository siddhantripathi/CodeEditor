from datetime import datetime
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data.get('_id'))
        self.username = user_data.get('username')
        self.email = user_data.get('email')
        self.password = user_data.get('password')
        self.created_at = user_data.get('created_at', datetime.utcnow())
        self.solved_problems = user_data.get('solved_problems', [])

    @staticmethod
    def create_user(mongo, username, email, password_hash):
        user_data = {
            'username': username,
            'email': email,
            'password': password_hash,
            'created_at': datetime.utcnow(),
            'solved_problems': []
        }
        result = mongo.db.users.insert_one(user_data)
        user_data['_id'] = result.inserted_id
        return User(user_data) 