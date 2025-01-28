from datetime import datetime

class Submission:
    def __init__(self, submission_data):
        self.id = str(submission_data.get('_id'))
        self.user_id = submission_data.get('user_id')
        self.problem_id = submission_data.get('problem_id')
        self.code = submission_data.get('code')
        self.status = submission_data.get('status')
        self.runtime = submission_data.get('runtime')
        self.created_at = submission_data.get('created_at', datetime.utcnow())

    @staticmethod
    def create_submission(mongo, user_id, problem_id, code, status, runtime):
        submission_data = {
            'user_id': user_id,
            'problem_id': problem_id,
            'code': code,
            'status': status,
            'runtime': runtime,
            'created_at': datetime.utcnow()
        }
        result = mongo.db.submissions.insert_one(submission_data)
        submission_data['_id'] = result.inserted_id
        return Submission(submission_data) 