# app.py - Enhanced Flask Backend for MediScan AI

from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import json
import os
import pickle
import numpy as np
from datetime import datetime
import math
import sklearn
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.utils import secure_filename
# Note: In a real implementation, you would use scikit-learn for the ML model

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config['UPLOAD_FOLDER'] = 'static/uploads/profiles'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Helper function to check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
app.secret_key = secrets.token_hex(16)  # For session management
CORS(app)  # Allow cross-origin requests

# Load disease database
DISEASE_DB = {
    "malaria": {
        "symptoms": ["fever", "chills", "headache", "fatigue", "muscle_ache", "nausea", "vomiting"],
        "description": "Malaria is a serious disease caused by a parasite that is transmitted via the bite of infected mosquitoes. Symptoms usually appear within 10-15 days after the infective bite.",
        "recommendation": "Seek immediate medical attention. Malaria requires proper diagnosis and treatment with antimalarial medications."
    },
    "typhoid": {
        "symptoms": ["fever", "headache", "abdominal_pain", "fatigue", "constipation", "weakness"],
        "description": "Typhoid fever is a bacterial infection caused by Salmonella typhi. It spreads through contaminated food and water or through close contact with someone who's infected.",
        "recommendation": "Consult a doctor for proper diagnosis and antibiotic treatment. Stay hydrated and get plenty of rest."
    },
    "influenza": {
        "symptoms": ["fever", "chills", "cough", "sore_throat", "runny_nose", "muscle_ache", "fatigue", "headache"],
        "description": "Influenza (flu) is a contagious respiratory illness caused by influenza viruses. It can cause mild to severe illness and can lead to hospitalization or death in severe cases.",
        "recommendation": "Rest, stay hydrated, and take over-the-counter fever reducers. Consult a doctor if symptoms are severe or you're in a high-risk group."
    },
    "uti": {
        "symptoms": ["urinary_pain", "frequent_urination", "fever", "cloudy_urine", "strong_odor"],
        "description": "A urinary tract infection (UTI) is an infection in any part of the urinary system. Most infections involve the lower urinary tract — the bladder and the urethra.",
        "recommendation": "Consult a doctor for proper diagnosis and antibiotic treatment. Drink plenty of water to help flush out bacteria."
    },
    "common_cold": {
        "symptoms": ["runny_nose", "cough", "sore_throat", "mild_headache", "sneezing"],
        "description": "The common cold is a viral infection of your nose and throat. It's usually harmless, although it might not feel that way.",
        "recommendation": "Rest, stay hydrated, and use over-the-counter cold medications for symptom relief. Consult a doctor if symptoms persist beyond 10 days."
    }
}

# Paths to store data
DATA_DIR = "data"
USERS_DIR = os.path.join(DATA_DIR, "users")
HOSPITALS_DIR = os.path.join(DATA_DIR, "hospitals")
DIAGNOSIS_DIR = os.path.join(DATA_DIR, "diagnoses")
RESET_TOKENS = os.path.join(DATA_DIR, "reset_tokens")

# Create necessary directories
for directory in [DATA_DIR, USERS_DIR, HOSPITALS_DIR, DIAGNOSIS_DIR, RESET_TOKENS]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Load hospitals from file or initialize with default values
def load_hospitals():
    hospital_file = os.path.join(HOSPITALS_DIR, "hospitals.json")
    if os.path.exists(hospital_file):
        with open(hospital_file, 'r') as f:
            return json.load(f)
    else:
        # Initialize with default hospitals
        default_hospitals = [
            {
                "id": 1,
                "name": "City General Hospital",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "address": "123 Medical Avenue, New York, NY",
                "phone": "+1 (555) 123-4567",
                "specialties": ["General Medicine", "Emergency Care", "Surgery"]
            },
            {
                "id": 2,
                "name": "Community Health Center",
                "latitude": 40.7200,
                "longitude": -74.0100,
                "address": "456 Wellness Street, New York, NY",
                "phone": "+1 (555) 987-6543",
                "specialties": ["Family Medicine", "Pediatrics", "Mental Health"]
            },
            {
                "id": 3,
                "name": "St. Mary's Medical Center",
                "latitude": 40.7180,
                "longitude": -73.9975,
                "address": "789 Care Boulevard, New York, NY",
                "phone": "+1 (555) 456-7890",
                "specialties": ["Cardiology", "Neurology", "Oncology"]
            },
            {
                "id": 4,
                "name": "Urgent Care Clinic",
                "latitude": 40.7150,
                "longitude": -74.0075,
                "address": "101 Emergency Drive, New York, NY",
                "phone": "+1 (555) 789-0123",
                "specialties": ["Urgent Care", "X-ray Services", "Minor Injuries"]
            }
        ]
        save_hospitals(default_hospitals)
        return default_hospitals

# Save hospitals to file
def save_hospitals(hospitals):
    hospital_file = os.path.join(HOSPITALS_DIR, "hospitals.json")
    with open(hospital_file, 'w') as f:
        json.dump(hospitals, f)

# Initialize hospitals
HOSPITALS_DB = load_hospitals()

# Helper function to calculate distance between two coordinates
def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two points using Haversine formula
    Returns distance in kilometers
    """
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Earth radius in kilometers
    
    return c * r

# User management functions
def save_user(username, email, password):
    """Save a new user to the database"""
    user_file = os.path.join(USERS_DIR, f"{username}.json")
    
    # Check if user already exists
    if os.path.exists(user_file):
        return False
    
    # Create new user
    user_data = {
        "username": username,
        "email": email,
        "password": generate_password_hash(password),
        "created_at": datetime.now().isoformat(),
        "profile": {}  # Will store medical profile here
    }
    
    with open(user_file, 'w') as f:
        json.dump(user_data, f)
    
    return True

def get_user(username):
    """Get user data by username"""
    user_file = os.path.join(USERS_DIR, f"{username}.json")
    
    if not os.path.exists(user_file):
        return None
    
    with open(user_file, 'r') as f:
        return json.load(f)

def get_user_by_email(email):
    """Find a user by email"""
    for filename in os.listdir(USERS_DIR):
        if filename.endswith('.json'):
            with open(os.path.join(USERS_DIR, filename), 'r') as f:
                user_data = json.load(f)
                if user_data.get('email') == email:
                    return user_data
    return None

def update_user_profile(username, profile_data):
    """Update user profile data"""
    user_file = os.path.join(USERS_DIR, f"{username}.json")
    
    if not os.path.exists(user_file):
        return False
    
    with open(user_file, 'r') as f:
        user_data = json.load(f)
    
    user_data['profile'] = profile_data
    
    with open(user_file, 'w') as f:
        json.dump(user_data, f)
    
    return True

def save_reset_token(email, token):
    """Save password reset token"""
    token_file = os.path.join(RESET_TOKENS, f"{token}.json")
    
    token_data = {
        "email": email,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(hours=1)).isoformat()
    }
    
    with open(token_file, 'w') as f:
        json.dump(token_data, f)

def verify_reset_token(token):
    """Verify if a reset token is valid"""
    token_file = os.path.join(RESET_TOKENS, f"{token}.json")
    
    if not os.path.exists(token_file):
        return None
    
    with open(token_file, 'r') as f:
        token_data = json.load(f)
    
    # Check if token has expired
    expires_at = datetime.fromisoformat(token_data['expires_at'])
    if datetime.now() > expires_at:
        # Delete expired token
        os.remove(token_file)
        return None
    
    return token_data['email']

def update_password(email, new_password):
    """Update user password"""
    user_data = get_user_by_email(email)
    if not user_data:
        return False
    
    username = user_data['username']
    user_file = os.path.join(USERS_DIR, f"{username}.json")
    
    user_data['password'] = generate_password_hash(new_password)
    
    with open(user_file, 'w') as f:
        json.dump(user_data, f)
    
    return True

# Medical history functions
def save_diagnosis(username, diagnosis_data):
    """Save diagnosis data for a user"""
    user_history_dir = os.path.join(DIAGNOSIS_DIR, username)
    if not os.path.exists(user_history_dir):
        os.makedirs(user_history_dir)
    
    # Generate a unique ID for this diagnosis
    diagnosis_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Add timestamp and metadata for future ML training
    diagnosis_data['timestamp'] = datetime.now().isoformat()
    diagnosis_data['diagnosis_id'] = diagnosis_id
    
    # Save the individual diagnosis
    diagnosis_file = os.path.join(user_history_dir, f"{diagnosis_id}.json")
    with open(diagnosis_file, 'w') as f:
        json.dump(diagnosis_data, f)
    
    # Also update the summary file for quick access
    summary_file = os.path.join(user_history_dir, "summary.json")
    summary = []
    
    if os.path.exists(summary_file):
        with open(summary_file, 'r') as f:
            summary = json.load(f)
    
    # Add a summary entry
    summary.append({
        'diagnosis_id': diagnosis_id,
        'timestamp': diagnosis_data['timestamp'],
        'symptoms': diagnosis_data['symptoms'],
        'results': [r['disease'] for r in diagnosis_data['results'][:3]]  # Top 3 results
    })
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f)
    
    return diagnosis_id

def get_user_diagnosis_history(username):
    """Get summary of user's diagnosis history"""
    summary_file = os.path.join(DIAGNOSIS_DIR, username, "summary.json")
    
    if not os.path.exists(summary_file):
        return []
    
    with open(summary_file, 'r') as f:
        return json.load(f)

def get_diagnosis_detail(username, diagnosis_id):
    """Get detailed information about a specific diagnosis"""
    diagnosis_file = os.path.join(DIAGNOSIS_DIR, username, f"{diagnosis_id}.json")
    
    if not os.path.exists(diagnosis_file):
        return None
    
    with open(diagnosis_file, 'r') as f:
        return json.load(f)

# Hospital management functions
def add_hospital(hospital_data):
    """Add a new hospital to the database"""
    global HOSPITALS_DB
    
    # Generate a new ID
    new_id = 1
    if HOSPITALS_DB:
        new_id = max(h['id'] for h in HOSPITALS_DB) + 1
    
    # Create new hospital
    new_hospital = {
        "id": new_id,
        "name": hospital_data.get('name', ''),
        "latitude": float(hospital_data.get('latitude', 0)),
        "longitude": float(hospital_data.get('longitude', 0)),
        "address": hospital_data.get('address', ''),
        "phone": hospital_data.get('phone', ''),
        "specialties": hospital_data.get('specialties', '').split(',')
    }
    
    # Add to the database
    HOSPITALS_DB.append(new_hospital)
    
    # Save to file
    save_hospitals(HOSPITALS_DB)
    
    return new_id

def update_hospital(hospital_id, hospital_data):
    """Update an existing hospital"""
    global HOSPITALS_DB
    
    hospital_id = int(hospital_id)
    
    # Find the hospital
    for i, hospital in enumerate(HOSPITALS_DB):
        if hospital['id'] == hospital_id:
            # Update the hospital
            HOSPITALS_DB[i] = {
                "id": hospital_id,
                "name": hospital_data.get('name', hospital['name']),
                "latitude": float(hospital_data.get('latitude', hospital['latitude'])),
                "longitude": float(hospital_data.get('longitude', hospital['longitude'])),
                "address": hospital_data.get('address', hospital['address']),
                "phone": hospital_data.get('phone', hospital['phone']),
                "specialties": hospital_data.get('specialties', ','.join(hospital['specialties'])).split(',')
            }
            
            # Save to file
            save_hospitals(HOSPITALS_DB)
            return True
    
    return False

def delete_hospital(hospital_id):
    """Delete a hospital"""
    global HOSPITALS_DB
    
    hospital_id = int(hospital_id)
    
    # Filter out the hospital
    HOSPITALS_DB = [h for h in HOSPITALS_DB if h['id'] != hospital_id]
    
    # Save to file
    save_hospitals(HOSPITALS_DB)
    
    return True

# Function to analyze symptoms and predict disease
def analyze_symptoms(symptoms, user_data=None):
    """
    Analyze symptoms and predict possible diseases
    Returns disease predictions with confidence scores
    
    In a real implementation, this would use a machine learning model
    Here we use a simplified rule-based approach for demonstration
    """
    results = []
    
    # Convert symptoms to lowercase and normalize
    normalized_symptoms = [s.lower().replace(' ', '_') for s in symptoms]
    
    for disease, data in DISEASE_DB.items():
        disease_symptoms = data["symptoms"]
        
        # Count matching symptoms
        matches = sum(1 for s in normalized_symptoms if s in disease_symptoms)
        
        # Calculate match percentage
        if len(disease_symptoms) > 0:
            match_percent = (matches / len(disease_symptoms)) * 100
        else:
            match_percent = 0
            
        # Only include diseases with significant match
        if match_percent > 20:
            results.append({
                "disease": disease,
                "match_percent": match_percent,
                "description": data["description"],
                "recommendation": data["recommendation"]
            })
    
    # Sort by match percentage
    results.sort(key=lambda x: x["match_percent"], reverse=True)
    
    # In a real system, we would use additional factors like:
    # - User's age, gender, location, medical history
    # - Symptom duration and severity
    # - Recent outbreaks in the area
    
    return results

# Function to find nearby hospitals
def find_nearby_hospitals(latitude, longitude, max_distance=2.0):
    """
    Find hospitals within the specified distance (in km)
    """
    nearby = []
    
    for hospital in HOSPITALS_DB:
        distance = calculate_distance(
            latitude, longitude,
            hospital["latitude"], hospital["longitude"]
        )
        
        if distance <= max_distance:
            hospital_info = hospital.copy()
            hospital_info["distance"] = round(distance, 1)
            nearby.append(hospital_info)
    
    # Sort by distance
    nearby.sort(key=lambda x: x["distance"])
    
    return nearby

# Utility to send emails for password reset
def send_reset_email(email, token):
    """Send password reset email"""
    # In a real application, configure these properly
    from_email = "noreply@mediscan.example.com"
    smtp_server = "smtp.example.com"
    smtp_port = 587
    smtp_user = "user"
    smtp_password = "password"
    
    # Create the email
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = email
    msg['Subject'] = "MediScan AI - Password Reset"
    
    body = f"""
    Hello,
    
    You have requested to reset your password for MediScan AI.
    Please click the link below to reset your password:
    
    http://localhost:5001/reset-password/{token}
    
    This link will expire in 1 hour.
    
    If you did not request this, please ignore this email.
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        # In a real application, uncomment this to actually send emails
        # server = smtplib.SMTP(smtp_server, smtp_port)
        # server.starttls()
        # server.login(smtp_user, smtp_password)
        # server.send_message(msg)
        # server.quit()
        
        # For now, just print the email content
        print(f"Would send email to {email} with token {token}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Define routes

# Main routes
@app.route('/')
def home():
    if 'username' in session:
        return render_template('index.html', logged_in=True, username=session['username'])
    return render_template('index.html', logged_in=False)
@app.template_filter('datetime')
def format_datetime(value, format='%Y-%m-%d %H:%M'):
    """Format a datetime object to a readable string"""
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return value
    return value.strftime(format)
# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user_data = get_user(username)
        
        if user_data and check_password_hash(user_data['password'], password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate input
        if not all([username, email, password, confirm_password]):
            flash('All fields are required', 'error')
        elif password != confirm_password:
            flash('Passwords do not match', 'error')
        elif get_user(username):
            flash('Username already exists', 'error')
        elif get_user_by_email(email):
            flash('Email already registered', 'error')
        else:
            # Create the user
            save_user(username, email, password)
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user_data = get_user_by_email(email)
        
        if user_data:
            # Generate a reset token
            token = secrets.token_urlsafe(32)
            save_reset_token(email, token)
            
            # Send reset email
            if send_reset_email(email, token):
                flash('Password reset link sent to your email', 'success')
            else:
                flash('Error sending reset email', 'error')
        else:
            # Don't reveal if email exists
            flash('If the email exists, a password reset link will be sent', 'info')
    
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)
    
    if not email:
        flash('Invalid or expired reset token', 'error')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
        else:
            if update_password(email, password):
                flash('Password updated successfully', 'success')
                return redirect(url_for('login'))
            else:
                flash('Error updating password', 'error')
    
    return render_template('reset_password.html', token=token)

# User dashboard and profile
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user_data = get_user(username)
    history = get_user_diagnosis_history(username)
    
    return render_template('dashboard.html', 
                          user=user_data, 
                          history=history)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user_data = get_user(username)
    
    if request.method == 'POST':
        # Process allergies - combine selected options with other text
        allergies_select = request.form.getlist('allergies_select')
        allergies_other = request.form.get('allergies_other')
        
        # Process chronic conditions - combine selected options with other text
        chronic_select = request.form.getlist('chronic_conditions_select')
        chronic_other = request.form.get('chronic_conditions_other')
        
        # Handle photo upload
        photo_path = user_data.get('profile', {}).get('photo_path', None)
        if 'profile_photo' in request.files:
            file = request.files['profile_photo']
            if file and file.filename and allowed_file(file.filename):
                # Add timestamp to ensure unique filenames even with same file upload
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = secure_filename(f"{username}_{timestamp}_{file.filename}")
                
                # Ensure upload directory exists
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                # Save the file
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                # Delete old file if it exists
                if photo_path:
                    old_file_path = os.path.join(app.static_folder, photo_path)
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                
                # Store the relative path from static directory
                photo_path = f"uploads/profiles/{filename}"
        
        profile_data = {
            'age': request.form.get('age'),
            'gender': request.form.get('gender'),
            'height': request.form.get('height'),
            'weight': request.form.get('weight'),
            'blood_type': request.form.get('blood_type'),
            'allergies': allergies_select,
            'allergies_other': allergies_other,
            'chronic_conditions': chronic_select,
            'chronic_conditions_other': chronic_other,
            'medications': request.form.get('medications'),
            'photo_path': photo_path
        }
        
        update_user_profile(username, profile_data)
        flash('Profile updated successfully', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html', user=user_data)
# Hospital management
@app.route('/hospitals', methods=['GET'])
def hospitals_list():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    return render_template('hospitals.html', hospitals=HOSPITALS_DB)

@app.route('/hospitals/add', methods=['GET', 'POST'])
def add_hospital_route():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        hospital_data = {
            'name': request.form.get('name'),
            'latitude': request.form.get('latitude'),
            'longitude': request.form.get('longitude'),
            'address': request.form.get('address'),
            'phone': request.form.get('phone'),
            'specialties': request.form.get('specialties')
        }
        
        add_hospital(hospital_data)
        flash('Hospital added successfully', 'success')
        return redirect(url_for('hospitals_list'))
    
    return render_template('hospital_form.html', hospital=None)

@app.route('/hospitals/edit/<hospital_id>', methods=['GET', 'POST'])
def edit_hospital(hospital_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    hospital = next((h for h in HOSPITALS_DB if h['id'] == int(hospital_id)), None)
    
    if not hospital:
        flash('Hospital not found', 'error')
        return redirect(url_for('hospitals_list'))
    
    if request.method == 'POST':
        hospital_data = {
            'name': request.form.get('name'),
            'latitude': request.form.get('latitude'),
            'longitude': request.form.get('longitude'),
            'address': request.form.get('address'),
            'phone': request.form.get('phone'),
            'specialties': request.form.get('specialties')
        }
        
        update_hospital(hospital_id, hospital_data)
        flash('Hospital updated successfully', 'success')
        return redirect(url_for('hospitals_list'))
    
    return render_template('hospital_form.html', hospital=hospital)

@app.route('/hospitals/delete/<hospital_id>', methods=['POST'])
def delete_hospital_route(hospital_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    delete_hospital(hospital_id)
    flash('Hospital deleted successfully', 'success')
    return redirect(url_for('hospitals_list'))
# Add to app.py
@app.route('/diagnosis/<diagnosis_id>')
def diagnosis_detail(diagnosis_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    diagnosis = get_diagnosis_detail(username, diagnosis_id)
    
    if not diagnosis:
        flash('Diagnosis not found', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('diagnosis_detail.html', diagnosis=diagnosis)
# Add to app.py
@app.route('/history')
def medical_history():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    history = get_user_diagnosis_history(username)
    
    return render_template('history.html', history=history)
# Add to app.py
@app.route('/symptom-checker')
def symptom_checker():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    return render_template('symptom_checker.html')
# API Routes
@app.route('/api/analyze', methods=['POST'])
def analyze():
    # Check authentication for API requests
    if request.json and 'username' in request.json:
        username = request.json.get('username')
        # In a real app, you'd verify API tokens here
    else:
        username = session.get('username')
    
    data = request.json
    
    # Extract data from request
    symptoms = data.get('symptoms', [])
    user_data = data.get('userData', {})
    
    # Analyze symptoms
    results = analyze_symptoms(symptoms, user_data)
    
    # Save diagnosis if user is authenticated
    diagnosis_id = None
    if username:
        diagnosis_data = {
            'symptoms': symptoms,
            'results': results,
            'userData': user_data
        }
        diagnosis_id = save_diagnosis(username, diagnosis_data)
    
    return jsonify({
        'success': True,
        'results': results,
        'diagnosis_id': diagnosis_id
    })

@app.route('/api/hospitals', methods=['GET', 'POST'])
def hospitals_api():
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'hospitals': HOSPITALS_DB
        })
    
    # Find nearby hospitals
    data = request.json
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    max_distance = data.get('maxDistance', 2.0)
    
    if not latitude or not longitude:
        return jsonify({
            'success': False,
            'error': 'Missing location data'
        })
    
    nearby = find_nearby_hospitals(latitude, longitude, max_distance)
    
    return jsonify({
        'success': True,
        'hospitals': nearby
    })

@app.route('/api/history/<username>', methods=['GET'])
def history_api(username):
    # In a real app, check authorization here
    
    history = get_user_diagnosis_history(username)
    
    return jsonify({
        'success': True,
        'history': history
    })

@app.route('/api/diagnosis/<username>/<diagnosis_id>', methods=['GET'])
def diagnosis_detail_api(username, diagnosis_id):
    # In a real app, check authorization here
    
    diagnosis = get_diagnosis_detail(username, diagnosis_id)
    
    if not diagnosis:
        return jsonify({
            'success': False,
            'error': 'Diagnosis not found'
        })
    
    return jsonify({
        'success': True,
        'diagnosis': diagnosis
    })

# Export anonymized data for training (admin function)
@app.route('/api/export-training-data', methods=['GET'])
def export_training_data():
    if 'username' not in session:
        return jsonify({
            'success': False,
            'error': 'Unauthorized'
        })
    
    # In a real app, check if user is admin
    
    # Collect anonymized diagnosis data
    training_data = []
    
    for username_dir in os.listdir(DIAGNOSIS_DIR):
        user_dir = os.path.join(DIAGNOSIS_DIR, username_dir)
        if os.path.isdir(user_dir):
            for diagnosis_file in os.listdir(user_dir):
                if diagnosis_file != "summary.json" and diagnosis_file.endswith('.json'):
                    with open(os.path.join(user_dir, diagnosis_file), 'r') as f:
                        diagnosis = json.load(f)
                        
                        # Anonymize the data
                        anonymized = {
                            'symptoms': diagnosis['symptoms'],
                            'results': [r['disease'] for r in diagnosis['results']],
                            'timestamp': diagnosis['timestamp']
                        }
                        
                        # Add user demographic data without identifiers
                        if 'userData' in diagnosis:
                            user_data = diagnosis['userData']
                            if isinstance(user_data, dict):
                                anonymized['demographics'] = {
                                    'age': user_data.get('age'),
                                    'gender': user_data.get('gender')
                                }
                        
                        training_data.append(anonymized)
    
    return jsonify({
        'success': True,
        'data': training_data
    })

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True  )