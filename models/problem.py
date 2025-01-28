from datetime import datetime
from firebase_admin import db

class Problem:
    def __init__(self, problem_data, problem_id=None):
        self.id = problem_id or problem_data.get('id')
        self.title = problem_data.get('title')
        self.description = problem_data.get('description')
        self.difficulty = problem_data.get('difficulty')
        self.starter_code = problem_data.get('starter_code')
        self.test_cases = problem_data.get('test_cases', [])
        self.created_at = problem_data.get('created_at', datetime.utcnow().isoformat())

    @staticmethod
    def create_problem(title, description, difficulty, starter_code, test_cases):
        problem_data = {
            'title': title,
            'description': description,
            'difficulty': difficulty,
            'starter_code': starter_code,
            'test_cases': test_cases,
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Push to Firebase
        problems_ref = db.reference('/problems')
        new_problem_ref = problems_ref.push(problem_data)
        problem_data['id'] = new_problem_ref.key
        
        return Problem(problem_data)

    @staticmethod
    def get_all_problems():
        problems_ref = db.reference('/problems')
        problems_data = problems_ref.get()
        if not problems_data:
            return []
        
        return [Problem(data, pid) for pid, data in problems_data.items()] 