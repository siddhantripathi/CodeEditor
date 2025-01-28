from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import firebase_admin
from firebase_admin import credentials, db
import bcrypt
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Initialize Firebase
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://codeeditor-db5bc-default-rtdb.firebaseio.com/'
    })
    ref = db.reference('/')
    print("Firebase connection successful!")
except Exception as e:
    print(f"Firebase connection error: {str(e)}")
    raise

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User:
    def __init__(self, user_data, user_id):
        self.id = user_id
        self.username = user_data.get('username')
        self.email = user_data.get('email')
        self.password = user_data.get('password', '')  # Handle missing password
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False

    def get_id(self):
        return str(self.id)

    @staticmethod
    def create_user(username, email, password_hash):
        users_ref = db.reference('/users')
        # First check if email exists using a direct path query
        email_query = users_ref.order_by_child('email').equal_to(email).get()
        
        if email_query:
            return None
            
        user_data = {
            'username': username,
            'email': email,
            'password': password_hash.decode('utf-8'),  # Convert bytes to string
            'created_at': datetime.utcnow().isoformat(),
            'solved_problems': []
        }
        new_user_ref = users_ref.push(user_data)
        return User(user_data, new_user_ref.key)

@login_manager.user_loader
def load_user(user_id):
    user_data = db.reference(f'/users/{user_id}').get()
    if user_data:
        return User(user_data, user_id)
    return None

@app.route('/')
def index():
    return redirect(url_for('problems'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            # Create user
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            user = User.create_user(username, email, password_hash)
            
            if user is None:
                flash('Email already registered')
                return redirect(url_for('register'))
                
            login_user(user)
            return redirect(url_for('problems'))
        except Exception as e:
            print(f"Registration error: {str(e)}")
            flash('An error occurred during registration')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            users_ref = db.reference('/users')
            users_by_email = users_ref.order_by_child('email').equal_to(email).get()
            
            if users_by_email:
                for user_id, user_data in users_by_email.items():
                    stored_password = user_data.get('password', '').encode('utf-8')
                    if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                        user = User(user_data, user_id)
                        login_user(user)
                        return redirect(url_for('problems'))
            
            flash('Invalid email or password')
        except Exception as e:
            print(f"Login error: {str(e)}")
            flash('An error occurred during login')
            
    return render_template('login.html')

@app.route('/problems')
def problems():
    problems_ref = db.reference('/problems')
    problems_data = problems_ref.get()
    problems_list = [{'id': k, **v} for k, v in problems_data.items()] if problems_data else []
    return render_template('problems.html', problems=problems_list)

@app.route('/problem/<problem_id>')
def problem(problem_id):
    problem_data = db.reference(f'/problems/{problem_id}').get()
    if not problem_data:
        return redirect(url_for('problems'))
    
    submissions = []
    if current_user.is_authenticated:
        try:
            submissions_ref = db.reference('/submissions')
            user_submissions = submissions_ref.order_by_child('user_id').equal_to(current_user.id).get()
            if user_submissions:
                submissions = [sub for sub in user_submissions.values() 
                             if sub['problem_id'] == problem_id]
                
                # Get user's last code for this problem
                last_submission = next(iter(sorted(submissions, 
                                            key=lambda x: x['created_at'], 
                                            reverse=True)), None)
                if last_submission:
                    problem_data['starter_code'] = last_submission['code']
        except Exception as e:
            print(f"Error fetching submissions: {str(e)}")
            # Continue without submissions if there's an error
            pass
    
    return render_template('problem.html', 
                         problem={'id': problem_id, **problem_data},
                         submissions=sorted(submissions, 
                                         key=lambda x: x['created_at'], 
                                         reverse=True) if submissions else [])

@app.route('/execute', methods=['POST'])
def execute_code():
    code = request.json.get('code')
    problem_id = request.json.get('problem_id')
    
    # Get problem test cases
    problem_data = db.reference(f'/problems/{problem_id}').get()
    if not problem_data or 'test_cases' not in problem_data:
        return jsonify({
            'error': 'Problem or test cases not found',
            'output': None
        })
    
    try:
        # Create a safe execution environment
        local_vars = {}
        exec(code, {'__builtins__': __builtins__}, local_vars)
        
        # Run test cases
        test_results = []
        for i, test_case in enumerate(problem_data['test_cases']):
            try:
                # Get the main function name from the code
                func_name = code.split('def ')[1].split('(')[0].strip()
                func = local_vars[func_name]
                
                # Execute the function with test inputs
                actual_output = func(*test_case['input'])
                passed = actual_output == test_case['output']
                
                test_results.append({
                    'passed': passed,
                    'expected': test_case['output'],
                    'actual': actual_output
                })
            except Exception as e:
                test_results.append({
                    'passed': False,
                    'error': str(e)
                })
        
        # Save submission for logged-in users
        if current_user.is_authenticated:
            submissions_ref = db.reference('/submissions')
            submission_data = {
                'user_id': current_user.id,
                'problem_id': problem_id,
                'code': code,
                'test_results': test_results,
                'created_at': datetime.utcnow().isoformat()
            }
            submissions_ref.push(submission_data)
        
        return jsonify({
            'output': 'Code executed successfully',
            'test_results': test_results,
            'error': None
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'output': None
        })

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True) 