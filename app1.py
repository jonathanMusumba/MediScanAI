# app.py - Flask Backend for MediScan AI

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import os
import pickle
import numpy as np
from datetime import datetime
import math
import sklearn
# Note: In a real implementation, you would use scikit-learn for the ML model

app = Flask(__name__, static_folder="static", template_folder="templates")
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

# Path to store user data and medical history
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Simple "database" of hospitals (in real app, would use a proper database or API)
HOSPITALS_DB = [
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

# Function to save user medical profile
def save_user_profile(user_id, profile_data):
    filename = os.path.join(DATA_DIR, f"user_{user_id}.json")
    with open(filename, 'w') as f:
        json.dump(profile_data, f)
    return True

# Function to load user medical profile
def load_user_profile(user_id):
    filename = os.path.join(DATA_DIR, f"user_{user_id}.json")
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return None

# Function to save medical history
def save_medical_history(user_id, diagnosis_data):
    filename = os.path.join(DATA_DIR, f"history_{user_id}.json")
    history = []
    
    # Load existing history if available
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            history = json.load(f)
    
    # Add new diagnosis with timestamp
    diagnosis_data['timestamp'] = datetime.now().isoformat()
    history.append(diagnosis_data)
    
    # Save updated history
    with open(filename, 'w') as f:
        json.dump(history, f)
    
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

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    
    # Extract data from request
    user_id = data.get('userId')
    symptoms = data.get('symptoms', [])
    user_data = data.get('userData', {})
    
    # Analyze symptoms
    results = analyze_symptoms(symptoms, user_data)
    
    # Save medical history if user is logged in
    if user_id:
        save_medical_history(user_id, {
            'symptoms': symptoms,
            'results': results,
            'userData': user_data
        })
    
    return jsonify({
        'success': True,
        'results': results
    })
@app.route('/api/hospitals', methods=['POST'])
def hospitals():
    data = request.json
    print("Received Data:", data)  

    latitude = data.get('latitude')
    longitude = data.get('longitude')
    max_distance = data.get('maxDistance', 2.0)
    
    if not latitude or not longitude:
        return jsonify({
            'success': False,
            'error': 'Missing location data'
        })
    
    # Find nearby hospitals
    nearby = find_nearby_hospitals(latitude, longitude, max_distance)
    
    return jsonify({
        'success': True,
        'hospitals': nearby
    })


@app.route('/api/profile', methods=['POST'])
def save_profile():
    data = request.json
    
    user_id = data.get('userId')
    profile_data = data.get('profileData', {})
    
    if not user_id:
        return jsonify({
            'success': False,
            'error': 'Missing user ID'
        })
    
    # Save user profile
    save_user_profile(user_id, profile_data)
    
    return jsonify({
        'success': True
    })

@app.route('/api/profile/<user_id>', methods=['GET'])
def get_profile(user_id):
    # Load user profile
    profile = load_user_profile(user_id)
    
    if not profile:
        return jsonify({
            'success': False,
            'error': 'User profile not found'
        })
    
    return jsonify({
        'success': True,
        'profile': profile
    })

@app.route('/api/history/<user_id>', methods=['GET'])
def get_history(user_id):
    filename = os.path.join(DATA_DIR, f"history_{user_id}.json")
    
    if not os.path.exists(filename):
        return jsonify({
            'success': False,
            'error': 'No medical history found'
        })
    
    # Load medical history
    with open(filename, 'r') as f:
        history = json.load(f)
    
    return jsonify({
        'success': True,
        'history': history
    })

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True  )
