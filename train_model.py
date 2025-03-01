# model.py - Machine Learning Model for Disease Prediction

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import pickle
import os

# In a real implementation, we would use actual medical data
# This is a simplified example for demonstration purposes

# Function to generate synthetic medical data
def generate_synthetic_data(n_samples=1000):
    """
    Generate synthetic dataset for disease prediction
    """
    # Define diseases and their common symptoms
    diseases = {
        "malaria": ["fever", "chills", "headache", "fatigue", "muscle_ache", 
                   "nausea", "vomiting"],
        
        "typhoid": ["fever", "headache", "abdominal_pain", "fatigue", 
                   "constipation", "weakness"],
        
        "influenza": ["fever", "chills", "cough", "sore_throat", "runny_nose", 
                     "muscle_ache", "fatigue", "headache"],
        
        "uti": ["urinary_pain", "frequent_urination", "fever", "cloudy_urine", 
               "strong_odor"],
        
        "common_cold": ["runny_nose", "cough", "sore_throat", "mild_headache", 
                       "sneezing"]
    }
    
    # All possible symptoms
    all_symptoms = set()
    for symptoms in diseases.values():
        all_symptoms.update(symptoms)
    all_symptoms = sorted(list(all_symptoms))
    
    # Create empty dataframe
    columns = all_symptoms + ['age', 'gender']
    df = pd.DataFrame(0, index=range(n_samples), columns=columns)
    
    # Add target column (disease)
    df['disease'] = ""
    
    # Fill with synthetic data
    disease_names = list(diseases.keys())
    genders = ['M', 'F']
    
    for i in range(n_samples):
        # Select random disease
        disease = np.random.choice(disease_names)
        df.loc[i, 'disease'] = disease
        
        # Set typical symptoms for this disease (with some randomness)
        disease_symptoms = diseases[disease]
        for symptom in disease_symptoms:
            # 85% chance of having each typical symptom
            if np.random.random() < 0.85:
                df.loc[i, symptom] = 1
        
        # Add some random other symptoms (noise)
        other_symptoms = [s for s in all_symptoms if s not in disease_symptoms]
        for symptom in np.random.choice(other_symptoms, size=np.random.randint(0, 3)):
            df.loc[i, symptom] = 1
        
        # Set demographic data
        df.loc[i, 'age'] = np.random.randint(1, 85)
        df.loc[i, 'gender'] = np.random.choice(genders)
    
    # Convert gender to numeric
    label_encoder = LabelEncoder()
    df['gender'] = label_encoder.fit_transform(df['gender'])
    
    return df, all_symptoms

# Train model function
def train_model(df, features, target='disease'):
    """
    Train a RandomForest model for disease prediction
    """
    X = df[features]
    y = df[target]
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train model
    model = RandomForestClassifier(
        n_estimators=100, 
        max_depth=10,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    # Evaluate model
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred)
    
    print(f"Model Accuracy: {accuracy:.4f}")
    print("\nClassification Report:")
    print(report)
    
    return model

# Function to save model
def save_model(model, filename='disease_prediction_model.pkl'):
    """
    Save trained model to file
    """
    with open(filename, 'wb') as f:
        pickle.dump(model, f)
    print(f"Model saved to {filename}")

# Function to load model
def load_model(filename='disease_prediction_model.pkl'):
    """
    Load trained model from file
    """
    if os.path.exists(filename):
        with open(filename, 'rb') as f:
            model = pickle.load(f)
        return model
    else:
        print(f"Model file {filename} not found")
        return None

# Function to predict disease
def predict_disease(symptoms, age, gender, model=None, all_symptoms=None):
    """
    Predict disease based on symptoms and patient info
    
    Parameters:
    - symptoms: list of symptom strings
    - age: patient age (integer)
    - gender: 'M' or 'F'
    - model: trained model (if None, will try to load from file)
    - all_symptoms: list of all possible symptoms
    
    Returns:
    - Dictionary with predictions and probabilities
    """
    # If model not provided, try to load from file
    if model is None:
        model = load_model()
        if model is None:
            return {"error": "Model not found"}
    
    # Prepare input data
    if all_symptoms is None:
        # This would come from the model metadata in a real implementation
        print("Error: all_symptoms list is required")
        return {"error": "Symptom list not provided"}
    
    # Create feature vector
    features = all_symptoms + ['age', 'gender']
    input_data = pd.DataFrame(0, index=[0], columns=features)
    
    # Set symptoms
    for symptom in symptoms:
        symptom = symptom.lower().replace(' ', '_')
        if symptom in all_symptoms:
            input_data.loc[0, symptom] = 1
    
    # Set demographic data
    input_data.loc[0, 'age'] = age
    input_data.loc[0, 'gender'] = 0 if gender == 'M' else 1
    
    # Get prediction
    disease = model.predict(input_data)[0]
    probabilities = model.predict_proba(input_data)[0]
    
    # Get class names and their probabilities
    classes = model.classes_
    probs = {cls: float(prob) for cls, prob in zip(classes, probabilities)}
    
    # Sort by probability
    sorted_probs = {k: v for k, v in sorted(
        probs.items(), key=lambda item: item[1], reverse=True
    )}
    
    return {
        "predicted_disease": disease,
        "confidence": probs[disease],
        "all_probabilities": sorted_probs
    }

# Main execution
if __name__ == "__main__":
    print("Generating synthetic medical data...")
    df, all_symptoms = generate_synthetic_data(n_samples=5000)
    
    print("\nTraining disease prediction model...")
    features = all_symptoms + ['age', 'gender']
    model = train_model(df, features)
    
    # Save model and feature list
    save_model(model)
    
    # Save feature list for future reference
    with open('model_features.pkl', 'wb') as f:
        pickle.dump({'all_symptoms': all_symptoms}, f)
    
    print("\nTesting prediction with sample input:")
    test_symptoms = ["fever", "headache", "fatigue"]
    test_age = 35
    test_gender = "M"
    
    prediction = predict_disease(
        test_symptoms, test_age, test_gender, 
        model=model, all_symptoms=all_symptoms
    )
    
    print(f"Symptoms: {test_symptoms}")
    print(f"Patient: {test_age} year old {test_gender}")
    print(f"Predicted disease: {prediction['predicted_disease']}")
    print(f"Confidence: {prediction['confidence']:.2f}")
    print("\nAll possibilities:")
    for disease, prob in prediction['all_probabilities'].items():
        print(f"- {disease}: {prob:.2f}")