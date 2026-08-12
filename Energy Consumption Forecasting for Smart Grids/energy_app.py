from flask import Flask, render_template, request, jsonify
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

app = Flask(__name__)

# Load model and data
try:
    model = joblib.load('energy_model.pkl')
    historical_data = pd.read_csv('energy_data.csv')
    historical_data['timestamp'] = pd.to_datetime(historical_data['timestamp'])
    forecast_data = pd.read_csv('energy_forecast.csv')
    forecast_data['timestamp'] = pd.to_datetime(forecast_data['timestamp'])
    print("\n✓ Model and data loaded successfully!")
except FileNotFoundError as e:
    print(f"\n✗ Error: {str(e)}")
    print("Run 'python setup_energy.py' first to generate the model")
    exit()

@app.route('/')
def home():
    return render_template('energy.html')

@app.route('/api/historical')
def get_historical():
    """Return historical energy data"""
    try:
        # Return last 30 days
        data = historical_data.tail(720)  # 30 days * 24 hours
        return jsonify({
            'timestamps': data['timestamp'].tolist(),
            'consumption': data['consumption_mw'].tolist(),
            'min': float(data['consumption_mw'].min()),
            'max': float(data['consumption_mw'].max()),
            'avg': float(data['consumption_mw'].mean())
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/forecast')
def get_forecast():
    """Return energy forecast data"""
    try:
        return jsonify({
            'timestamps': forecast_data['timestamp'].tolist(),
            'forecast': forecast_data['forecast_mw'].tolist(),
            'min': float(forecast_data['forecast_mw'].min()),
            'max': float(forecast_data['forecast_mw'].max()),
            'avg': float(forecast_data['forecast_mw'].mean())
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/stats')
def get_stats():
    """Return energy statistics"""
    try:
        hist_stats = {
            'current': float(historical_data['consumption_mw'].iloc[-1]),
            'min': float(historical_data['consumption_mw'].min()),
            'max': float(historical_data['consumption_mw'].max()),
            'avg': float(historical_data['consumption_mw'].mean()),
            'peak_hour': int(historical_data.groupby(historical_data['timestamp'].dt.hour)['consumption_mw'].mean().idxmax()),
            'low_hour': int(historical_data.groupby(historical_data['timestamp'].dt.hour)['consumption_mw'].mean().idxmin())
        }
        
        forecast_stats = {
            'forecast_min': float(forecast_data['forecast_mw'].min()),
            'forecast_max': float(forecast_data['forecast_mw'].max()),
            'forecast_avg': float(forecast_data['forecast_mw'].mean())
        }
        
        return jsonify({
            'historical': hist_stats,
            'forecast': forecast_stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/predict', methods=['POST'])
def predict():
    """Make custom predictions"""
    try:
        data = request.get_json()
        
        features = np.array([[
            data['hour'],
            data['day_of_week'],
            data['day_of_month'],
            data['month'],
            data['lag_1'],
            data['lag_24'],
            data['lag_168']
        ]])
        
        prediction = model.predict(features)[0]
        
        return jsonify({
            'prediction': float(prediction),
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/grid-status')
def grid_status():
    """Return grid status information"""
    try:
        current_load = float(historical_data['consumption_mw'].iloc[-1])
        avg_load = float(historical_data['consumption_mw'].mean())
        max_load = float(historical_data['consumption_mw'].max())
        
        # Calculate health metrics
        load_percentage = (current_load / max_load) * 100
        
        if load_percentage < 50:
            status = "Excellent"
            color = "green"
        elif load_percentage < 75:
            status = "Good"
            color = "yellow"
        elif load_percentage < 90:
            status = "Caution"
            color = "orange"
        else:
            status = "Critical"
            color = "red"
        
        return jsonify({
            'current_load': current_load,
            'load_percentage': load_percentage,
            'status': status,
            'color': color,
            'avg_load': avg_load,
            'max_load': max_load,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("⚡ ENERGY CONSUMPTION FORECASTING SYSTEM")
    print("=" * 60)
    print("🚀 Starting Flask server...")
    app.run(debug=True, host='127.0.0.1', port=5000)