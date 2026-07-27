"""
Machine learning pipeline: trains an XGBoost model to predict
temperature anomalies (for microclimate grid) using synthetic features.
Saves model + SHAP explainer.
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import shap
import joblib
import random

# Generate synthetic dataset (replace with real data in production)
def generate_synthetic_data(n=10000):
    np.random.seed(42)
    # Features: elevation, urban_density, veg_index, distance_to_water, time_of_day
    elevation = np.random.uniform(0, 500, n)
    urban_density = np.random.uniform(0, 100, n)
    veg_index = np.random.uniform(0, 1, n)
    water_dist = np.random.uniform(0, 10, n)
    hour = np.random.randint(0, 24, n)
    # Target: temperature anomaly relative to baseline
    anomaly = (elevation * 0.01 - urban_density * 0.02 + veg_index * 0.5
               - water_dist * 0.1 + np.sin(hour/24 * 2*np.pi) * 1.5
               + np.random.normal(0, 0.5, n))
    df = pd.DataFrame({
        'elevation': elevation,
        'urban_density': urban_density,
        'veg_index': veg_index,
        'water_dist': water_dist,
        'hour': hour,
        'anomaly': anomaly
    })
    return df

def train():
    data = generate_synthetic_data()
    X = data.drop('anomaly', axis=1)
    y = data['anomaly']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
    model.fit(X_train_scaled, y_train)
    
    # Save model and scaler
    joblib.dump(model, 'model.pkl')
    joblib.dump(scaler, 'scaler.pkl')
    
    # SHAP explainer (using a sample of training data)
    explainer = shap.TreeExplainer(model, X_train_scaled[:100])
    joblib.dump(explainer, 'explainer.pkl')
    
    print("Model trained and saved.")

if __name__ == "__main__":
    train()