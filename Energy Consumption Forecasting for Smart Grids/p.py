# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import joblib
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
import json
import sys
import io

# Set UTF-8 encoding for console output
if sys.platform == 'win32':
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Generate sample energy consumption data
def generate_sample_data():
    """Generate realistic energy consumption data"""
    dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='H')
    
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

# Prepare data for forecasting
print("=" * 60)
print("[ENERGY CONSUMPTION FORECASTING SYSTEM]")
print("=" * 60)
print("\n[Generating sample energy consumption data...]")

df = generate_sample_data()
df.to_csv('energy_data.csv', index=False)
print(f"[OK] Generated {len(df)} hours of data")
print(f"[OK] Data range: {df['consumption_mw'].min():.2f} - {df['consumption_mw'].max():.2f} MW")

# Prepare features for ML model
print("\n[Preparing training data...]")

# Ensure timestamp is datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])

df['hour'] = df['timestamp'].dt.hour
df['day_of_week'] = df['timestamp'].dt.dayofweek
df['day_of_month'] = df['timestamp'].dt.day
df['month'] = df['timestamp'].dt.month

# Create lag features
for i in [1, 24, 168]:  # 1 hour, 1 day, 1 week
    df[f'lag_{i}'] = df['consumption_mw'].shift(i)

# Drop NaN rows
df_clean = df.dropna()

X = df_clean[['hour', 'day_of_week', 'day_of_month', 'month', 'lag_1', 'lag_24', 'lag_168']]
y = df_clean['consumption_mw']

print(f"[OK] Prepared {len(X)} training samples")

# Train model
print("\n[Training forecasting model...]")
model = LinearRegression()
model.fit(X, y)

# Evaluate model
train_score = model.score(X, y)
print(f"[OK] Model R^2 Score: {train_score:.4f}")

# Save model and scaler
joblib.dump(model, 'energy_model.pkl')
print("[OK] Model saved as 'energy_model.pkl'")

# Generate forecast for next 7 days
print("\n[Generating 7-day forecast...]")
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
    
    forecast_value = model.predict([[
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
print(f"[OK] Generated forecast: {forecast_df['forecast_mw'].min():.2f} - {forecast_df['forecast_mw'].max():.2f} MW")
print(f"[OK] Forecast saved as 'energy_forecast.csv'")

print("\n" + "=" * 60)
print("[SUCCESS] ALL SETUP COMPLETED SUCCESSFULLY!")
print("=" * 60)