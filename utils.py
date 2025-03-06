import pickle
import pandas as pd
import numpy as np
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def load_models():
    """Load trained models and scaler"""
    try:
        with open('MODEL/random_forest.pkl', 'rb') as f:
            rf_model = pickle.load(f)
        with open('MODEL/xgboost.pkl', 'rb') as f:
            xgb_model = pickle.load(f)
        with open('MODEL/scaler.pkl', 'rb') as f:
            scaler = pickle.load(f)
        return rf_model, xgb_model, scaler
    except Exception as e:
        logger.error(f"❌ Error loading models: {e}")
        raise

def load_datasets():
    """Load supporting datasets"""
    try:
        crop_info = pd.read_csv('attached_assets/crop_info.csv')
        fertilizers = pd.read_csv('attached_assets/fertilizers.csv')
        pesticides = pd.read_csv('attached_assets/pesticides.csv')
        return crop_info, fertilizers, pesticides
    except Exception as e:
        logger.error(f"❌ Error loading datasets: {e}")
        raise

def predict_yield(data, rf_model, xgb_model, scaler):
    """Make yield predictions using both models"""
    try:
        # Prepare input data
        input_data = np.array([
            data['soil_ph'],
            data['nitrogen'],
            data['phosphorus'],
            data['potassium'],
            data['temperature'],
            data['humidity'],
            data['rainfall']
        ]).reshape(1, -1)

        # Scale input data
        scaled_data = scaler.transform(input_data)

        # Get predictions from both models
        rf_pred = rf_model.predict(scaled_data)[0]
        xgb_pred = xgb_model.predict(scaled_data)[0]

        # Average the predictions
        final_prediction = (rf_pred + xgb_pred) / 2

        return {
            'yield': round(final_prediction, 2),
            'confidence': min(rf_model.score(scaled_data, [rf_pred]), 
                            xgb_model.score(scaled_data, [xgb_pred])) * 100
        }

    except Exception as e:
        logger.error(f"❌ Prediction error: {e}")
        raise

def get_crop_info(crop_name):
    """Get crop information"""
    crop_info, _, _ = load_datasets()
    crop_data = crop_info[crop_info['Crop'] == crop_name].iloc[0]
    return {
        'optimal_temp': crop_data['Optimal_Temperature (°C)'],
        'soil_type': crop_data['Soil_Type'],
        'growing_season': crop_data['Growing_Season']
    }

def get_fertilizer_info(crop_name):
    """Get fertilizer recommendations"""
    _, fertilizers, _ = load_datasets()
    fert_data = fertilizers[fertilizers['Crop'] == crop_name].iloc[0]
    return {
        'name': fert_data['Recommended_Fertilizer'],
        'method': fert_data['Application_Method']
    }

def get_pesticide_info(crop_name):
    """Get pesticide recommendations"""
    _, _, pesticides = load_datasets()
    pest_data = pesticides[pesticides['Crop'] == crop_name].iloc[0]
    return {
        'pest': pest_data['Common_Pests'],
        'name': pest_data['Recommended_Pesticide'],
        'method': pest_data['Application_Method']
    }