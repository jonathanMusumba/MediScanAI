
# Add these imports to your existing imports
from functools import wraps
import csv
from io import StringIO

# Add to your existing app configuration
ADMIN_DIR = os.path.join(DATA_DIR, "admins")
if not os.path.exists(ADMIN_DIR):
    os.makedirs(ADMIN_DIR)

# Initialize default admin if none exists
def initialize_admin():
    admin_file = os.path.join(ADMIN_DIR, "admins.json")
    if not os.path.exists(admin_file):
        default_admin = {
            "username": "admin",
            "email": "admin@mediscan.ai",
            "password": generate_password_hash("admin123"), # Change this in production
            "role": "superadmin",
            "created_at": datetime.now().isoformat()
        }
        
        with open(admin_file, 'w') as f:
            json.dump([default_admin], f)
        print("Default admin created")

initialize_admin()

# Admin authentication functions
def load_admins():
    """Load all admin accounts"""
    admin_file = os.path.join(ADMIN_DIR, "admins.json")
    
    if os.path.exists(admin_file):
        with open(admin_file, 'r') as f:
            return json.load(f)
    return []

def get_admin(username):
    """Get admin data by username"""
    admins = load_admins()
    for admin in admins:
        if admin['username'] == username:
            return admin
    return None

def admin_required(f):
    """Decorator for routes that require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_username' not in session:
            flash('Admin login required', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def superadmin_required(f):
    """Decorator for routes that require superadmin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_username' not in session:
            flash('Admin login required', 'danger')
            return redirect(url_for('admin_login'))
        
        admin = get_admin(session['admin_username'])
        if not admin or admin['role'] != 'superadmin':
            flash('Superadmin privileges required', 'danger')
            return redirect(url_for('admin_dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def add_admin(username, email, password, role='admin'):
    """Add a new admin account"""
    admins = load_admins()
    
    # Check if admin already exists
    for admin in admins:
        if admin['username'] == username or admin['email'] == email:
            return False
    
    # Create new admin
    new_admin = {
        "username": username,
        "email": email,
        "password": generate_password_hash(password),
        "role": role,
        "created_at": datetime.now().isoformat()
    }
    
    admins.append(new_admin)
    
    admin_file = os.path.join(ADMIN_DIR, "admins.json")
    with open(admin_file, 'w') as f:
        json.dump(admins, f)
    
    return True

def update_admin(username, data):
    """Update admin account data"""
    admins = load_admins()
    
    for i, admin in enumerate(admins):
        if admin['username'] == username:
            # Update fields (except password which has special handling)
            for key, value in data.items():
                if key != 'password':
                    admins[i][key] = value
            
            admin_file = os.path.join(ADMIN_DIR, "admins.json")
            with open(admin_file, 'w') as f:
                json.dump(admins, f)
            
            return True
    
    return False

def update_admin_password(username, new_password):
    """Update admin password"""
    admins = load_admins()
    
    for i, admin in enumerate(admins):
        if admin['username'] == username:
            admins[i]['password'] = generate_password_hash(new_password)
            
            admin_file = os.path.join(ADMIN_DIR, "admins.json")
            with open(admin_file, 'w') as f:
                json.dump(admins, f)
            
            return True
    
    return False

def delete_admin(username):
    """Delete an admin account"""
    admins = load_admins()
    
    for i, admin in enumerate(admins):
        if admin['username'] == username:
            # Don't delete the last superadmin
            superadmins = [a for a in admins if a['role'] == 'superadmin']
            if admin['role'] == 'superadmin' and len(superadmins) <= 1:
                return False
            
            admins.pop(i)
            
            admin_file = os.path.join(ADMIN_DIR, "admins.json")
            with open(admin_file, 'w') as f:
                json.dump(admins, f)
            
            return True
    
    return False

# Data management functions for admin
def get_all_users():
    """Get all users from the database"""
    users = []
    for filename in os.listdir(USERS_DIR):
        if filename.endswith('.json'):
            with open(os.path.join(USERS_DIR, filename), 'r') as f:
                user_data = json.load(f)
                # Remove password for security
                if 'password' in user_data:
                    user_data.pop('password')
                users.append(user_data)
    return users

def get_all_diagnoses():
    """Get all diagnosis records"""
    diagnoses = []
    if os.path.exists(DIAGNOSIS_DIR):
        for filename in os.listdir(DIAGNOSIS_DIR):
            if filename.endswith('.json'):
                with open(os.path.join(DIAGNOSIS_DIR, filename), 'r') as f:
                    diagnosis_data = json.load(f)
                    diagnoses.append(diagnosis_data)
    return diagnoses

def get_user_diagnoses(username):
    """Get all diagnoses for a specific user"""
    user_diagnoses = []
    for diagnosis in get_all_diagnoses():
        if diagnosis.get('username') == username:
            user_diagnoses.append(diagnosis)
    return user_diagnoses

def save_diagnosis(diagnosis_data):
    """Save a diagnosis record"""
    diagnosis_id = str(diagnosis_data.get('id', secrets.token_hex(8)))
    diagnosis_data['id'] = diagnosis_id
    
    diagnosis_file = os.path.join(DIAGNOSIS_DIR, f"{diagnosis_id}.json")
    
    with open(diagnosis_file, 'w') as f:
        json.dump(diagnosis_data, f)
    
    return diagnosis_id

def delete_diagnosis(diagnosis_id):
    """Delete a diagnosis record"""
    diagnosis_file = os.path.join(DIAGNOSIS_DIR, f"{diagnosis_id}.json")
    
    if os.path.exists(diagnosis_file):
        os.remove(diagnosis_file)
        return True
    
    return False

def update_disease_db(disease_data):
    """Update or add a disease to the database"""
    disease_id = disease_data.get('id', '').lower()
    
    # Create a proper format for storing in the disease database
    if disease_id and 'symptoms' in disease_data:
        DISEASE_DB[disease_id] = {
            "symptoms": disease_data.get('symptoms', []),
            "description": disease_data.get('description', ''),
            "recommendation": disease_data.get('recommendation', '')
        }
        return True
    
    return False

def delete_disease(disease_id):
    """Delete a disease from the database"""
    disease_id = disease_id.lower()
    
    if disease_id in DISEASE_DB:
        del DISEASE_DB[disease_id]
        return True
    
    return False

def export_users_csv():
    """Export users to CSV format"""
    output = StringIO()
    csv_writer = csv.writer(output)
    
    # Write header
    csv_writer.writerow(['Username', 'Email', 'Created At'])
    
    # Write user data
    users = get_all_users()
    for user in users:
        csv_writer.writerow([
            user.get('username', ''),
            user.get('email', ''),
            user.get('created_at', '')
        ])
    
    return output.getvalue()

def export_diagnoses_csv():
    """Export diagnoses to CSV format"""
    output = StringIO()
    csv_writer = csv.writer(output)
    
    # Write header
    csv_writer.writerow(['ID', 'Username', 'Disease', 'Symptoms', 'Date', 'Recommendation'])
    
    # Write diagnosis data
    diagnoses = get_all_diagnoses()
    for diagnosis in diagnoses:
        csv_writer.writerow([
            diagnosis.get('id', ''),
            diagnosis.get('username', ''),
            diagnosis.get('disease', ''),
            ', '.join(diagnosis.get('symptoms', [])),
            diagnosis.get('date', ''),
            diagnosis.get('recommendation', '')
        ])
    
    return output.getvalue()

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = get_admin(username)
        
        if admin and check_password_hash(admin['password'], password):
            session['admin_username'] = admin['username']
            session['admin_role'] = admin['role']
            flash('Login successful', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_username', None)
    session.pop('admin_role', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    stats = {
        'total_users': len(get_all_users()),
        'total_hospitals': len(HOSPITALS_DB),
        'total_diagnoses': len(get_all_diagnoses()),
        'total_diseases': len(DISEASE_DB)
    }
    
    # Get recent diagnoses
    recent_diagnoses = sorted(
        get_all_diagnoses(), 
        key=lambda x: x.get('date', ''), 
        reverse=True
    )[:5]
    
    return render_template(
        'admin/dashboard.html', 
        stats=stats, 
        recent_diagnoses=recent_diagnoses,
        admin_role=session.get('admin_role')
    )

@app.route('/admin/users')
@admin_required
def admin_users():
    users = get_all_users()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/<username>')
@admin_required
def admin_user_detail(username):
    user = get_user(username)
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('admin_users'))
    
    diagnoses = get_user_diagnoses(username)
    
    return render_template('admin/user_detail.html', user=user, diagnoses=diagnoses)

@app.route('/admin/users/delete/<username>', methods=['POST'])
@admin_required
def admin_delete_user(username):
    user_file = os.path.join(USERS_DIR, f"{username}.json")
    
    if os.path.exists(user_file):
        os.remove(user_file)
        flash(f'User {username} deleted', 'success')
    else:
        flash('User not found', 'danger')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/hospitals')
@admin_required
def admin_hospitals():
    return render_template('admin/hospitals.html', hospitals=HOSPITALS_DB)

@app.route('/admin/hospitals/add', methods=['GET', 'POST'])
@admin_required
def admin_add_hospital():
    if request.method == 'POST':
        hospital_id = len(HOSPITALS_DB) + 1
        hospital = {
            "id": hospital_id,
            "name": request.form.get('name'),
            "latitude": float(request.form.get('latitude')),
            "longitude": float(request.form.get('longitude')),
            "address": request.form.get('address'),
            "phone": request.form.get('phone'),
            "specialties": request.form.get('specialties').split(',')
        }
        
        HOSPITALS_DB.append(hospital)
        save_hospitals(HOSPITALS_DB)
        
        flash('Hospital added successfully', 'success')
        return redirect(url_for('admin_hospitals'))
    
    return render_template('admin/hospital_form.html', hospital=None)

@app.route('/admin/hospitals/edit/<int:hospital_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_hospital(hospital_id):
    hospital = next((h for h in HOSPITALS_DB if h['id'] == hospital_id), None)
    
    if not hospital:
        flash('Hospital not found', 'danger')
        return redirect(url_for('admin_hospitals'))
    
    if request.method == 'POST':
        hospital_index = next((i for i, h in enumerate(HOSPITALS_DB) if h['id'] == hospital_id), None)
        
        if hospital_index is not None:
            HOSPITALS_DB[hospital_index] = {
                "id": hospital_id,
                "name": request.form.get('name'),
                "latitude": float(request.form.get('latitude')),
                "longitude": float(request.form.get('longitude')),
                "address": request.form.get('address'),
                "phone": request.form.get('phone'),
                "specialties": request.form.get('specialties').split(',')
            }
            
            save_hospitals(HOSPITALS_DB)
            flash('Hospital updated successfully', 'success')
            return redirect(url_for('admin_hospitals'))
    
    return render_template('admin/hospital_form.html', hospital=hospital)

@app.route('/admin/hospitals/delete/<int:hospital_id>', methods=['POST'])
@admin_required
def admin_delete_hospital(hospital_id):
    global HOSPITALS_DB
    HOSPITALS_DB = [h for h in HOSPITALS_DB if h['id'] != hospital_id]
    
    # Update IDs to maintain sequence
    for i, hospital in enumerate(HOSPITALS_DB):
        hospital['id'] = i + 1
    
    save_hospitals(HOSPITALS_DB)
    flash('Hospital deleted successfully', 'success')
    
    return redirect(url_for('admin_hospitals'))

@app.route('/admin/diagnoses')
@admin_required
def admin_diagnoses():
    diagnoses = get_all_diagnoses()
    return render_template('admin/diagnoses.html', diagnoses=diagnoses)

@app.route('/admin/diagnoses/<diagnosis_id>')
@admin_required
def admin_diagnosis_detail(diagnosis_id):
    diagnosis_file = os.path.join(DIAGNOSIS_DIR, f"{diagnosis_id}.json")
    
    if not os.path.exists(diagnosis_file):
        flash('Diagnosis not found', 'danger')
        return redirect(url_for('admin_diagnoses'))
    
    with open(diagnosis_file, 'r') as f:
        diagnosis = json.load(f)
    
    return render_template('admin/diagnosis_detail.html', diagnosis=diagnosis)

@app.route('/admin/diagnoses/delete/<diagnosis_id>', methods=['POST'])
@admin_required
def admin_delete_diagnosis(diagnosis_id):
    if delete_diagnosis(diagnosis_id):
        flash('Diagnosis deleted successfully', 'success')
    else:
        flash('Diagnosis not found', 'danger')
    
    return redirect(url_for('admin_diagnoses'))

@app.route('/admin/diseases')
@admin_required
def admin_diseases():
    diseases = []
    for disease_id, disease_data in DISEASE_DB.items():
        disease = {
            'id': disease_id,
            'symptoms': disease_data.get('symptoms', []),
            'description': disease_data.get('description', ''),
            'recommendation': disease_data.get('recommendation', '')
        }
        diseases.append(disease)
    
    return render_template('admin/diseases.html', diseases=diseases)

@app.route('/admin/diseases/add', methods=['GET', 'POST'])
@admin_required
def admin_add_disease():
    if request.method == 'POST':
        disease_data = {
            'id': request.form.get('id').lower(),
            'symptoms': request.form.get('symptoms').split(','),
            'description': request.form.get('description'),
            'recommendation': request.form.get('recommendation')
        }
        
        if update_disease_db(disease_data):
            flash('Disease added successfully', 'success')
            return redirect(url_for('admin_diseases'))
        else:
            flash('Failed to add disease', 'danger')
    
    return render_template('admin/disease_form.html', disease=None)

@app.route('/admin/diseases/edit/<disease_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_disease(disease_id):
    disease_id = disease_id.lower()
    
    if disease_id not in DISEASE_DB:
        flash('Disease not found', 'danger')
        return redirect(url_for('admin_diseases'))
    
    disease = {
        'id': disease_id,
        'symptoms': DISEASE_DB[disease_id].get('symptoms', []),
        'description': DISEASE_DB[disease_id].get('description', ''),
        'recommendation': DISEASE_DB[disease_id].get('recommendation', '')
    }
    
    if request.method == 'POST':
        disease_data = {
            'id': disease_id,
            'symptoms': request.form.get('symptoms').split(','),
            'description': request.form.get('description'),
            'recommendation': request.form.get('recommendation')
        }
        
        if update_disease_db(disease_data):
            flash('Disease updated successfully', 'success')
            return redirect(url_for('admin_diseases'))
        else:
            flash('Failed to update disease', 'danger')
    
    return render_template('admin/disease_form.html', disease=disease)

@app.route('/admin/diseases/delete/<disease_id>', methods=['POST'])
@admin_required
def admin_delete_disease(disease_id):
    if delete_disease(disease_id):
        flash('Disease deleted successfully', 'success')
    else:
        flash('Disease not found', 'danger')
    
    return redirect(url_for('admin_diseases'))

@app.route('/admin/admins')
@superadmin_required
def admin_admins():
    admins = load_admins()
    return render_template('admin/admins.html', admins=admins)

@app.route('/admin/admins/add', methods=['GET', 'POST'])
@superadmin_required
def admin_add_admin():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'admin')
        
        if add_admin(username, email, password, role):
            flash('Admin added successfully', 'success')
            return redirect(url_for('admin_admins'))
        else:
            flash('Admin username or email already exists', 'danger')
    
    return render_template('admin/admin_form.html', admin=None)

@app.route('/admin/admins/edit/<username>', methods=['GET', 'POST'])
@superadmin_required
def admin_edit_admin(username):
    admin = get_admin(username)
    
    if not admin:
        flash('Admin not found', 'danger')
        return redirect(url_for('admin_admins'))
    
    if request.method == 'POST':
        data = {
            'email': request.form.get('email'),
            'role': request.form.get('role')
        }
        
        # Update password if provided
        password = request.form.get('password')
        if password:
            update_admin_password(username, password)
        
        if update_admin(username, data):
            flash('Admin updated successfully', 'success')
            return redirect(url_for('admin_admins'))
        else:
            flash('Failed to update admin', 'danger')
    
    return render_template('admin/admin_form.html', admin=admin)

@app.route('/admin/admins/delete/<username>', methods=['POST'])
@superadmin_required
def admin_delete_admin(username):
    # Check if trying to delete self
    if username == session.get('admin_username'):
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('admin_admins'))
    
    if delete_admin(username):
        flash('Admin deleted successfully', 'success')
    else:
        flash('Cannot delete admin or admin not found', 'danger')
    
    return redirect(url_for('admin_admins'))

@app.route('/admin/profile', methods=['GET', 'POST'])
@admin_required
def admin_profile():
    admin = get_admin(session.get('admin_username'))
    
    if not admin:
        return redirect(url_for('admin_logout'))
    
    if request.method == 'POST':
        data = {
            'email': request.form.get('email')
        }
        
        # Update password if provided
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        
        if current_password and new_password:
            if check_password_hash(admin['password'], current_password):
                update_admin_password(admin['username'], new_password)
                flash('Password updated successfully', 'success')
            else:
                flash('Current password is incorrect', 'danger')
        
        if update_admin(admin['username'], data):
            flash('Profile updated successfully', 'success')
        
        return redirect(url_for('admin_profile'))
    
    return render_template('admin/profile.html', admin=admin)

@app.route('/admin/export/users')
@admin_required
def admin_export_users():
    csv_data = export_users_csv()
    
    response = app.response_class(
        response=csv_data,
        status=200,
        mimetype='text/csv'
    )
    response.headers["Content-Disposition"] = "attachment; filename=users.csv"
    
    return response

@app.route('/admin/export/diagnoses')
@admin_required
def admin_export_diagnoses():
    csv_data = export_diagnoses_csv()
    
    response = app.response_class(
        response=csv_data,
        status=200,
        mimetype='text/csv'
    )
    response.headers["Content-Disposition"] = "attachment; filename=diagnoses.csv"
    
    return response

# Add system backup and restore functionality (for superadmins only)
@app.route('/admin/system/backup')
@superadmin_required
def admin_system_backup():
    # Create timestamp for backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join(DATA_DIR, f"backup_{timestamp}")
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Backup users
    users_backup = os.path.join(backup_dir, "users")
    os.makedirs(users_backup)
    for filename in os.listdir(USERS_DIR):
        if filename.endswith('.json'):
            src = os.path.join(USERS_DIR, filename)
            dst = os.path.join(users_backup, filename)
            with open(src, 'r') as f_src:
                data = json.load(f_src)
                with open(dst, 'w') as f_dst:
                    json.dump(data, f_dst)
    
    # Backup hospitals
    hospitals_backup = os.path.join(backup_dir, "hospitals")
    os.makedirs(hospitals_backup)
    hospital_file = os.path.join(HOSPITALS_DIR, "hospitals.json")
    if os.path.exists(hospital_file):
        with open(hospital_file, 'r') as f_src:
            data = json.load(f_src)
            with open(os.path.join(hospitals_backup, "hospitals.json"), 'w') as f_dst:
                json.dump(data, f_dst)
    
    # Backup diagnoses
    diagnoses_backup = os.path.join(backup_dir, "diagnoses")
    os.makedirs(diagnoses_backup)
    for filename in os.listdir(DIAGNOSIS_DIR):
        if filename.endswith('.json'):
            src = os.path.join(DIAGNOSIS_DIR, filename)
            dst = os.path.join(diagnoses_backup, filename)
            with open(src, 'r') as f_src:
                data = json.load(f_src)
                with open(dst, 'w') as f_dst:
                    json.dump(data, f_dst)
    
    # Backup admins
    admins_backup = os.path.join(backup_dir, "admins")
    os.makedirs(admins_backup)
    admin_file = os.path.join(ADMIN_DIR, "admins.json")
    if os.path.exists(admin_file):
        with open(admin_file, 'r') as f_src:
            data = json.load(f_src)
            with open(os.path.join(admins_backup, "admins.json"), 'w') as f_dst:
                json.dump(data, f_dst)
    
    flash(f'System backup created: backup_{timestamp}', 'success')
    return redirect(url_for('admin_dashboard'))

# Add analytics routes
@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    # Get all diagnoses
    diagnoses = get_all_diagnoses()
    
    # Count diagnoses by disease
    disease_counts = {}
    for diagnosis in diagnoses:
        disease = diagnosis.get('disease', 'unknown')
        if disease in disease_counts:
            disease_counts[disease] += 1
        else:
            disease_counts[disease] = 1
    
    # Sort by count
    sorted_diseases = sorted(disease_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Count diagnoses by month
    month_counts = {}
    for diagnosis in diagnoses:
        date_str = diagnosis.get('date', '')
        if date_str:
            try:
                date = datetime.fromisoformat(date_str)
                month_key = date.strftime('%Y-%m')
                if month_key in month_counts:
                    month_counts[month_key] += 1
                else:
                    month_counts[month_key] = 1
            except:
                pass
    
    # Sort months chronologically
    sorted_months = sorted(month_counts.items())
    
    # User growth over time
    users = get_all_users()
    user_growth = {}
    for user in users:
        date_str = user.get('created_at', '')
        if date_str:
            try:
                date = datetime.fromisoformat(date_str)
                month_key = date.strftime('%Y-%m')
                if month_key in user_growth:
                    user_growth[month_key] += 1
                else:
                    user_growth[month_key] = 1
            except:
                pass
    
    # Sort months chronologically
    sorted_user_growth = sorted(user_growth.items())
    
    # Cumulative user growth
    cumulative_users = []
    total = 0
    for month, count in sorted_user_growth:
        total += count
        cumulative_users.append((month, total))
    
    return render_template(
        'admin/analytics.html',
        disease_counts=sorted_diseases,
        month_counts=sorted_months,
        user_growth=sorted_user_growth,
        cumulative_users=cumulative_users
    )

