from datetime import datetime

class Problem:
    def __init__(self, problem_data):
        self.id = str(problem_data.get('_id'))
        self.title = problem_data.get('title')
        self.description = problem_data.get('description')
        self.difficulty = problem_data.get('difficulty')
        self.starter_code = problem_data.get('starter_code')
        self.test_cases = problem_data.get('test_cases', [])
        self.created_at = problem_data.get('created_at', datetime.utcnow())

    @staticmethod
    def create_problem(mongo, title, description, difficulty, starter_code, test_cases):
        problem_data = {
            'title': title,
            'description': description,
            'difficulty': difficulty,
            'starter_code': starter_code,
            'test_cases': test_cases,
            'created_at': datetime.utcnow()
        }
        result = mongo.db.problems.insert_one(problem_data)
        problem_data['_id'] = result.inserted_id
        return Problem(problem_data) 