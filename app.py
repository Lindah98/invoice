# Here we import the modules we need for our project.
from flask import Flask, render_template, request, redirect, url_for, session 
import os
from werkzeug.utils import secure_filename 
from dotenv import load_dotenv
from datetime import  datetime
from flask_sqlalchemy import SQLAlchemy 

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Set a secret key for session management

# Load environment variables
load_dotenv()

# Configure the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
db = SQLAlchemy(app)

# Set the upload directory
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create the upload directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
# We can refactor  to separate models with code.

from models import  User,Invoice
# Create the database tables if they don't exist
with app.app_context():
    db.create_all()

# Login required decorator
def login_required(func):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# Route for the landing page
@app.route('/')
def home():
    return render_template('landing_page.html')

# Route for user signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone_number = request.form['phone_number']
        username = request.form['username']
        password = request.form['password']

        # Check if the username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return 'Username already exists'

        # Insert the new user into the database
        new_user = User(first_name=first_name, last_name=last_name, phone_number=phone_number, username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('signup.html')

# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username and password are correct
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            # Successful login, set the user_id in the session
            session['user_id'] = user.id
            return redirect(url_for('upload_file'))
        else:
            return 'Invalid username or password'

    return render_template('login.html')

# Route for handling file uploads
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file uploaded', 400

        file = request.files['file']

        # Check if the file is present
        if file.filename == '':
            return 'No file selected', 400

        # Save the file to the uploads directory
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Save file metadata to the database
        invoice_number = request.form.get('invoice_number')
        user_id = session['user_id']
        invoice = Invoice(invoice_number=invoice_number, filename=filename, upload_date=datetime.now(), user_id=user_id)
        db.session.add(invoice)
        db.session.commit()

        # Here, you can perform additional operations on the uploaded file
        # such as invoice validation, parsing, etc.

        return 'File uploaded successfully'

    return render_template('upload.html')

# Route for user logout
@app.route('/logout')
def logout():
    # Clear the user_id from the session
    session.pop('user_id', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
