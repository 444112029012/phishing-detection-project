from flask import Flask, request, jsonify
from flask_cors import CORS
from phishing_detector_model import PhishingDetectorModel
from FeatureExtractor import FeatureExtractor
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
import numpy as np
import pandas as pd

class PhishingDetectorAPI:
    def __init__(self, name=__name__):
        self.app = Flask(name)
        CORS(self.app)
        self._setup_routes()
        self.url = None
        self.html_structure = None
        self.html_content = None
        self.detector = PhishingDetectorModel()
        self.extractor = FeatureExtractor()
    
    def _setup_routes(self):
        self.app.add_url_rule('/check', view_func=self.check, methods=['POST', 'OPTIONS'])
        self.app.add_url_rule('/predict', view_func=self.predict, methods=['POST', 'OPTIONS'])
    
    def check(self):
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "無效的數據"}), 400
        self.url = data.get('url')
        self.html_structure = data.get('html')
        self.html_content = data.get('text')

        return jsonify({
            "status": "success",
            "url_received": self.url,
            "message": None
        })

    def predict(self):
        data = request.get_json()
        if not data:
            return jsonify({'status':'error', 'message':'無效數據'}), 400
        print('特徵萃取...')
        url_feature = self.extractor.get_URL_Feature(self.url)
        html_feature = self.extractor.get_HTMLStructure_Feature(self.url, self.html_structure)
        ai_feature = self.extractor.get_HTMLContent_AI_Feature(self.html_content)
        ai_feature = self.detector.preprocess_ai(ai_feature)
        html_feature = self.detector.preprocess_html(html_feature)
        prob = self.detector.predict(url_feature, html_feature, ai_feature)
        print(prob)
        return jsonify({
            'status':'success',
            'message': prob[0]
        })

    def run(self, host='127.0.0.1', port=5000):
        print(f"偵測器伺服器啟動於 {host}:{port}")
        self.app.run(host=host, port=port, debug=True)
if __name__ == "__main__":
    detector = PhishingDetectorAPI()
    detector.run()