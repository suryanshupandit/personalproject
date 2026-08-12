import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

# Create a simple trained model for demonstration
X_train = np.random.randn(100, 30)
y_train = np.random.randint(0, 2, 100)

model = RandomForestClassifier(n_estimators=10, random_state=42)
model.fit(X_train, y_train)

# Save the model
joblib.dump(model, 'fraud_model.pkl')
print("✓ Model created and saved as 'fraud_model.pkl'")
