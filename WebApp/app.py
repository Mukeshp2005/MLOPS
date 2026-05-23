import os
import pickle
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Paths to the models
BASE_DIR = os.path.dirname(os.path.abspath(__name__))
MODELS_DIR = os.path.join(BASE_DIR, '..', 'DAY6')

RF_MODEL_PATH = os.path.join(MODELS_DIR, 'rf_model.pkl')
SCALER_PATH = os.path.join(MODELS_DIR, 'scaler.pkl')
BLACKSPOTS_PATH = os.path.join(MODELS_DIR, 'blackspots.pkl')

# Load Models
try:
    with open(RF_MODEL_PATH, 'rb') as f:
        rf_model = pickle.load(f)
    with open(SCALER_PATH, 'rb') as f:
        scaler = pickle.load(f)
    with open(BLACKSPOTS_PATH, 'rb') as f:
        blackspots_df = pickle.load(f)
    print("Models loaded successfully!")
except Exception as e:
    print(f"Error loading models: {e}")
    rf_model, scaler, blackspots_df = None, None, None

# Target classes mapping based on LabelEncoder
TARGET_CLASSES = {0: 'Fatal', 1: 'Serious', 2: 'Slight'}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        
        # 1. Extract base features from JSON
        num_vehicles = int(data.get('Number_of_Vehicles', 1))
        num_casualties = int(data.get('Number_of_Casualties', 0))
        day_of_week = int(data.get('Day_of_Week', 1))
        road_class = int(data.get('1st_Road_Class', 1))
        road_number = int(data.get('1st_Road_Number', 1))
        road_type = int(data.get('Road_Type', 1))
        speed_limit = int(data.get('Speed_limit', 30))
        junction_detail = int(data.get('Junction_Detail', 1))
        junction_control = int(data.get('Junction_Control', 1))
        light_conditions = int(data.get('Light_Conditions', 1))
        weather_conditions = int(data.get('Weather_Conditions', 1))
        road_surface = int(data.get('Road_Surface_Conditions', 1))
        special_conditions = int(data.get('Special_Conditions_at_Site', 0))
        carriageway_hazards = int(data.get('Carriageway_Hazards', 0))
        urban_rural = int(data.get('Urban_or_Rural_Area', 1))
        
        # 2. Compute engineered features (business logic from DAY6 notebook)
        is_weekend = 1 if day_of_week in [1, 7] else 0
        high_speed = 1 if speed_limit >= 60 else 0
        multi_vehicle = 1 if num_vehicles > 1 else 0
        high_casualty = 1 if num_casualties > 2 else 0
        bad_light = 1 if light_conditions != 1 else 0
        bad_weather = 1 if weather_conditions != 1 else 0
        bad_surface = 1 if road_surface != 1 else 0
        
        # 3. Create feature array in the EXACT order expected by the model
        features = [
            num_vehicles, num_casualties, day_of_week, road_class, road_number,
            road_type, speed_limit, junction_detail, junction_control,
            light_conditions, weather_conditions, road_surface,
            special_conditions, carriageway_hazards, urban_rural,
            is_weekend, high_speed, multi_vehicle, high_casualty,
            bad_light, bad_weather, bad_surface
        ]
        
        features_array = np.array([features])
        
        # 4. Scale and predict using Hybrid Engine
        if rf_model and scaler:
            scaled_features = scaler.transform(features_array)
            proba = rf_model.predict_proba(scaled_features)[0]
            
            # The base Random Forest model is heavily biased toward 'Slight' (predicting it >70% of the time)
            # because the original AccidentsBig dataset is 85% slight accidents, and SMOTE didn't fully resolve 
            # the bias at the decision boundaries.
            # To make the UI dynamically reflect high-risk factors, we calculate an adjusted Hybrid Risk Score.
            risk_score = 0
            if high_speed: risk_score += 2
            if bad_weather: risk_score += 1
            if bad_surface: risk_score += 1
            if bad_light: risk_score += 1
            if high_casualty: risk_score += 3
            if multi_vehicle: risk_score += 1

            if risk_score >= 5 or proba[0] > 0.15:
                severity = "Fatal"
            elif risk_score >= 3 or proba[1] > 0.25:
                severity = "Serious"
            else:
                severity = "Slight"
        else:
            severity = "Model not loaded"
            
        # 5. Check Blackspot Status
        is_blackspot = False
        if blackspots_df is not None:
            # Check if this road number exists in the blackspots dataframe and is flagged
            match = blackspots_df[blackspots_df['1st_Road_Number'] == road_number]
            if not match.empty:
                status = match['is_blackspot'].values[0]
                is_blackspot = (status == 'BLACK SPOT')
        
        return jsonify({
            'success': True,
            'severity': severity,
            'is_blackspot': bool(is_blackspot),
            'road_number': road_number
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=False, port=5000)
