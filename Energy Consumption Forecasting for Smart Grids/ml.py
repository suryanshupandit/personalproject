from flask import Flask, render_template, request, jsonify
import joblib
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

app = Flask(__name__)

# Load your trained model
try:
    model = joblib.load('fraud_model.pkl')
    print("\n✓ Model loaded successfully!")
except FileNotFoundError:
    print("\n✗ Error: Model file not found. Run 'python create_model.py' first.\n")
    exit()

# Initialize scaler (fit on your training data if needed; here it's a placeholder)
scaler = StandardScaler()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get data from the form (sent via JS)
        data = request.get_json()
        time = float(data['time'])
        amount = float(data['amount'])
        v1 = float(data['v1'])
        v2 = float(data['v2'])
        # Add more V3-V28 as needed; for demo, assume others are 0
        v3_to_v28 = [0.0] * 26

        # Prepare input
        input_data = [time, amount, v1, v2] + v3_to_v28
        input_df = pd.DataFrame([input_data], columns=['Time', 'Amount', 'V1', 'V2'] + [f'V{i}' for i in range(3, 29)])
        scaled_data = scaler.fit_transform(input_df)  # Scale as in training

        # Predict
        prediction = model.predict(scaled_data)[0]
        prob = model.predict_proba(scaled_data)[0][1]
        result = "Fraudulent" if prediction == 1 else "Legitimate"
        return jsonify({'result': result, 'probability': round(prob, 2)})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 FRAUD DETECTION SYSTEM STARTING")
    print("=" * 50)
    app.run(debug=True, host='127.0.0.1', port=5000)