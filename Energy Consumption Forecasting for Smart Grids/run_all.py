# -*- coding: utf-8 -*-
"""
COMBINED ENERGY AND FRAUD DETECTION SYSTEM
This script combines all modules and runs them sequentially
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import joblib
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestClassifier
import json
import sys
import io

# Set UTF-8 encoding for console output
if sys.platform == 'win32':
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'

print("\n" + "=" * 80)
print("COMBINED ENERGY & FRAUD DETECTION SYSTEM - INITIALIZATION")
print("=" * 80)

# ============================================================================
# PART 1: GENERATE ENERGY CONSUMPTION DATA (from p.py)
# ============================================================================

print("\n[PHASE 1: ENERGY CONSUMPTION DATA]")
print("-" * 80)

def generate_sample_data():
    """Generate realistic energy consumption data"""
    dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='h')
    
    # Simulate energy consumption with daily and hourly patterns
    np.random.seed(42)
    base_load = 50  # Base load in MW
    daily_pattern = 30 * np.sin(2 * np.pi * np.arange(len(dates)) / 24)  # Daily cycle
    trend = 0.01 * np.arange(len(dates))  # Slight upward trend
    noise = np.random.normal(0, 5, len(dates))  # Random noise
    
    consumption = base_load + daily_pattern + trend + noise
    consumption = np.maximum(consumption, 10)  # Ensure positive values
    
    df = pd.DataFrame({
        'timestamp': dates,
        'consumption_mw': consumption
    })
    
    return df

print("[1] Generating sample energy consumption data...")
df = generate_sample_data()
df.to_csv('energy_data.csv', index=False)
print(f"    ✓ Generated {len(df)} hours of data")
print(f"    ✓ Data range: {df['consumption_mw'].min():.2f} - {df['consumption_mw'].max():.2f} MW")

# Prepare features for ML model
print("\n[2] Preparing training data for energy model...")

df['timestamp'] = pd.to_datetime(df['timestamp'])
df['hour'] = df['timestamp'].dt.hour
df['day_of_week'] = df['timestamp'].dt.dayofweek
df['day_of_month'] = df['timestamp'].dt.day
df['month'] = df['timestamp'].dt.month

# Create lag features
for i in [1, 24, 168]:  # 1 hour, 1 day, 1 week
    df[f'lag_{i}'] = df['consumption_mw'].shift(i)

df_clean = df.dropna()

X = df_clean[['hour', 'day_of_week', 'day_of_month', 'month', 'lag_1', 'lag_24', 'lag_168']]
y = df_clean['consumption_mw']

print(f"    ✓ Prepared {len(X)} training samples")

# Train energy model
print("\n[3] Training energy forecasting model...")
energy_model = LinearRegression()
energy_model.fit(X, y)

train_score = energy_model.score(X, y)
print(f"    ✓ Model R² Score: {train_score:.4f}")

joblib.dump(energy_model, 'energy_model.pkl')
print("    ✓ Model saved as 'energy_model.pkl'")

# Generate 7-day forecast
print("\n[4] Generating 7-day energy forecast...")
last_date = df['timestamp'].max()
forecast_dates = pd.date_range(start=last_date + timedelta(hours=1), periods=168, freq='h')

forecasts = []
for forecast_date in forecast_dates:
    features = {
        'hour': forecast_date.hour,
        'day_of_week': forecast_date.dayofweek,
        'day_of_month': forecast_date.day,
        'month': forecast_date.month,
        'lag_1': forecasts[-1] if forecasts else df['consumption_mw'].iloc[-1],
        'lag_24': df[df['hour'] == forecast_date.hour]['consumption_mw'].mean(),
        'lag_168': df[df['hour'] == forecast_date.hour]['consumption_mw'].mean()
    }
    
    forecast_value = energy_model.predict([[
        features['hour'],
        features['day_of_week'],
        features['day_of_month'],
        features['month'],
        features['lag_1'],
        features['lag_24'],
        features['lag_168']
    ]])[0]
    
    forecasts.append(forecast_value)

forecast_df = pd.DataFrame({
    'timestamp': forecast_dates,
    'forecast_mw': forecasts
})

forecast_df.to_csv('energy_forecast.csv', index=False)
print(f"    ✓ Forecast range: {forecast_df['forecast_mw'].min():.2f} - {forecast_df['forecast_mw'].max():.2f} MW")
print(f"    ✓ Forecast saved as 'energy_forecast.csv'")

# ============================================================================
# PART 2: CREATE FRAUD DETECTION MODEL (from create_model.py)
# ============================================================================

print("\n[PHASE 2: FRAUD DETECTION MODEL]")
print("-" * 80)

print("[5] Creating fraud detection model...")
X_fraud = np.random.randn(100, 30)
y_fraud = np.random.randint(0, 2, 100)

fraud_model = RandomForestClassifier(n_estimators=10, random_state=42)
fraud_model.fit(X_fraud, y_fraud)

joblib.dump(fraud_model, 'fraud_model.pkl')
print("    ✓ Model created and saved as 'fraud_model.pkl'")

# ============================================================================
# PART 3: DISPLAY RESULTS AND STATISTICS
# ============================================================================

print("\n[PHASE 3: RESULTS & STATISTICS]")
print("-" * 80)

print("\n[ENERGY CONSUMPTION STATISTICS]")
print(f"    • Total data points: {len(df)}")
print(f"    • Average consumption: {df['consumption_mw'].mean():.2f} MW")
print(f"    • Peak consumption: {df['consumption_mw'].max():.2f} MW")
print(f"    • Minimum consumption: {df['consumption_mw'].min():.2f} MW")
print(f"    • Standard deviation: {df['consumption_mw'].std():.2f} MW")

# Find peak and low hours
peak_hour = int(df.groupby(df['timestamp'].dt.hour)['consumption_mw'].mean().idxmax())
low_hour = int(df.groupby(df['timestamp'].dt.hour)['consumption_mw'].mean().idxmin())
print(f"    • Peak usage hour: {peak_hour}:00")
print(f"    • Lowest usage hour: {low_hour}:00")

print("\n[ENERGY FORECAST STATISTICS]")
print(f"    • Forecast period: 7 days (168 hours)")
print(f"    • Forecasted average: {forecast_df['forecast_mw'].mean():.2f} MW")
print(f"    • Forecasted peak: {forecast_df['forecast_mw'].max():.2f} MW")
print(f"    • Forecasted minimum: {forecast_df['forecast_mw'].min():.2f} MW")
print(f"    • Model R² Score: {train_score:.4f}")

print("\n[FRAUD DETECTION MODEL STATISTICS]")
print(f"    • Training samples: 100")
print(f"    • Features: 30")
print(f"    • Classes: 2 (Legitimate/Fraudulent)")
print(f"    • Estimators: 10")
print(f"    • Training accuracy: {fraud_model.score(X_fraud, y_fraud):.4f}")

# ============================================================================
# PART 4: DEMONSTRATE PREDICTIONS
# ============================================================================

print("\n[PHASE 4: DEMONSTRATION PREDICTIONS]")
print("-" * 80)

print("\n[ENERGY CONSUMPTION PREDICTIONS]")
# Predict for the next 24 hours
sample_features = np.array([
    [0, 0, 1, 1, 55.0, 60.0, 60.0],  # Midnight
    [12, 0, 1, 1, 85.0, 80.0, 80.0],  # Noon
    [18, 0, 1, 1, 90.0, 85.0, 85.0],  # Evening
])

predictions = energy_model.predict(sample_features)
times = ['00:00 (Midnight)', '12:00 (Noon)', '18:00 (Evening)']
for time, pred in zip(times, predictions):
    print(f"    • {time}: {pred:.2f} MW")

print("\n[FRAUD DETECTION PREDICTIONS]")
# Predict fraud probability for sample transactions
sample_fraud = np.random.randn(3, 30)
fraud_predictions = fraud_model.predict(sample_fraud)
fraud_probs = fraud_model.predict_proba(sample_fraud)

for i, (pred, prob) in enumerate(zip(fraud_predictions, fraud_probs)):
    status = "[FRAUDULENT]" if pred == 1 else "[LEGITIMATE]"
    fraud_prob = prob[1]  # Probability of fraud
    print(f"    • Transaction {i+1}: {status} (Fraud probability: {fraud_prob:.2%})")

# ============================================================================
# COMPLETION
# ============================================================================

print("\n" + "=" * 80)
print("[SUCCESS] ALL SYSTEMS INITIALIZED AND OPERATIONAL")
print("=" * 80)
print("\n[Generated Files]")
print("    • energy_data.csv - Historical energy consumption data")
print("    • energy_forecast.csv - 7-day energy forecast")
print("    • energy_model.pkl - Trained energy forecasting model")
print("    • fraud_model.pkl - Trained fraud detection model")
print("\n[Systems Ready]")
print("    [OK] Energy forecasting system")
print("    [OK] Fraud detection system")
print("    [OK] Data generation and preparation")
print("\n" + "=" * 80 + "\n")
