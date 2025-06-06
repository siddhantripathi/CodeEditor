from flask import Flask, send_from_directory, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import firebase_admin
from firebase_admin import credentials, db
import bcrypt
from datetime import datetime
import os
from dotenv import load_dotenv
from firebase_config import get_firebase_credentials, get_database_url

# Load environment variables
load_dotenv()

app = Flask(__name__, 
    static_folder='../public/static',  # Updated static folder path
    template_folder='../templates'      # Updated template folder path
)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Initialize Firebase
try:
    cred = get_firebase_credentials()
    firebase_admin.initialize_app(cred, {
        'databaseURL': get_database_url()
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
    return send_from_directory('../public', 'index.html')

# Static file handling
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('../public/static', path)

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

@app.route('/playground')
def playground():
    return render_template('playground.html')

@app.route('/execute_playground', methods=['POST'])
def execute_playground():
    if not request.is_json:
        return jsonify({'error': 'Invalid request format'}), 400
        
    code = request.json.get('code')
    
    if not code:
        return jsonify({'error': 'No code provided'}), 400
    
    try:
        # Capture stdout to get print statements
        import io
        import sys
        output_buffer = io.StringIO()
        sys.stdout = output_buffer
        
        # Create a safe execution environment
        local_vars = {}
        exec(code, {'__builtins__': __builtins__}, local_vars)
        
        # Restore stdout and get the output
        sys.stdout = sys.__stdout__
        output = output_buffer.getvalue()
        
        return jsonify({
            'output': output or 'Code executed successfully (no output)',
            'error': None
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'output': None
        })

@app.route('/execute', methods=['POST'])
def execute_code():
    if not request.is_json:
        return jsonify({'error': 'Invalid request format'}), 400
        
    code = request.json.get('code')
    problem_id = request.json.get('problem_id')
    
    if not code:
        return jsonify({'error': 'No code provided'}), 400

    try:
        # Capture stdout
        import io
        import sys
        output_buffer = io.StringIO()
        sys.stdout = output_buffer
        
        # Execute the code
        local_vars = {}
        exec(code, {'__builtins__': __builtins__}, local_vars)
        
        # Get printed output
        code_output = output_buffer.getvalue()
        sys.stdout = sys.__stdout__  # Restore stdout
        
        # Run test cases
        test_results = []
        if problem_id:
            problem_data = db.reference(f'/problems/{problem_id}').get()
            if problem_data and 'test_cases' in problem_data:
                try:
                    func_name = code.split('def ')[1].split('(')[0].strip()
                    func = local_vars.get(func_name)
                    
                    if not func:
                        raise ValueError(f"Function '{func_name}' not found")
                    
                    for test_case in problem_data['test_cases']:
                        try:
                            actual_output = func(*test_case['input'])
                            passed = actual_output == test_case['output']
                            test_results.append({
                                'passed': passed,
                                'input': test_case['input'],
                                'expected': test_case['output'],
                                'actual': actual_output
                            })
                        except Exception as e:
                            test_results.append({
                                'passed': False,
                                'error': str(e)
                            })
                except Exception as e:
                    return jsonify({
                        'error': str(e),
                        'code_output': code_output,
                        'test_results': []
                    })
        
        return jsonify({
            'code_output': code_output,
            'test_results': test_results,
            'error': None
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'code_output': None,
            'test_results': None
        })

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True) 