import joblib
import numpy as np


class Model:
    def __init__(self, model_file, scaler_file):
        self.model = joblib.load(model_file)
        self.scaler = joblib.load(scaler_file)

    def predict(self, history):
        last_60_days_close = history["Close"].tail(60).values
        last_60_days_close_scaled = self.scaler.transform(last_60_days_close.reshape(-1, 1))

        X = np.reshape(last_60_days_close_scaled, (1, -1, 1))
        y_pred = self.scaler.inverse_transform(self.model.predict(X))

        return y_pred.item()
