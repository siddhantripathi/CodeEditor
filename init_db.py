import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://codeeditor-db5bc-default-rtdb.firebaseio.com/'
})

# Get a reference to the problems node
problems_ref = db.reference('/problems')

# Sample problems
sample_problems = {
    'two-sum': {
        'title': 'Two Sum',
        'description': 'Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.',
        'difficulty': 'Easy',
        'starter_code': 'def two_sum(nums, target):\n    # Your code here\n    pass',
        'test_cases': [
            {'input': [[2, 7, 11, 15], 9], 'output': [0, 1]},
            {'input': [[3, 2, 4], 6], 'output': [1, 2]}
        ],
        'video_id': 'KLlXCFG5TnA',  # Example YouTube video ID
        'created_at': datetime.utcnow().isoformat()
    },
    'palindrome': {
        'title': 'Palindrome Number',
        'description': 'Given an integer x, return true if x is a palindrome, and false otherwise.',
        'difficulty': 'Easy',
        'starter_code': 'def is_palindrome(x):\n    # Your code here\n    pass',
        'test_cases': [
            {'input': [121], 'output': True},
            {'input': [-121], 'output': False},
            {'input': [10], 'output': False}
        ],
        'created_at': datetime.utcnow().isoformat()
    },
    
}

# Set the problems in the database
problems_ref.set(sample_problems)
print("Sample problems initialized successfully!") 