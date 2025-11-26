import pandas as pd
import numpy as np
from joblib import load
import os

# Same prefix used in train_ddos_full.py
OUT = "outputs"
PREFIX = "ddos_full"

# Load ML artifacts created by train_ddos_full.py
scaler = load(os.path.join(OUT, f"{PREFIX}_scaler_20.joblib"))
selector = load(os.path.join(OUT, f"{PREFIX}_selector_20.joblib"))
label_encoder = load(os.path.join(OUT, f"{PREFIX}_label_encoder.joblib"))

# Load your best model (change name if needed)
model = load(os.path.join(OUT, f"{PREFIX}_gb_20.joblib"))

# Load Flow CSV
df = pd.read_csv("capture3_flows.csv")

# Extract numeric features only
X = df.select_dtypes(include=[np.number])
X = X.replace([np.inf, -np.inf], np.nan).fillna(0)

# Apply same feature selection used in training
selected_idx = selector.get_support(indices=True)
X_sel = X.iloc[:, selected_idx]

# Scale
X_scaled = scaler.transform(X_sel)

# Predict
y_pred = model.predict(X_scaled)

# Add prediction column
df["Prediction"] = y_pred
df.to_csv("capture3_flows_with_pred.csv", index=False)

print("Done! Saved predictions to capture3_flows_with_pred.csv")
print(df["Prediction"].value_counts())
