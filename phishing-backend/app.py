from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from phishing_detector_model import PhishingDetectorModel
from FeatureExtractor import FeatureExtractor
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
import numpy as np
import pandas as pd
import json
import time

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
        self.url_feature = None
        self.html_feature = None
        self.ai_feature = None
    
    def _setup_routes(self):
        self.app.add_url_rule('/predict', view_func=self.predict, methods=['POST', 'OPTIONS'])

    def predict(self):
        data = request.get_json()
        self.url = data.get('url')
        self.html_structure = data.get('html')
        self.html_content = data.get('text')
        if not data:
            return jsonify({'status':'error', 'message':'無效數據'}), 400
        print('特徵萃取...')
        def generate_progress():
            try:
                yield json.dumps({'status': 'progress', 'message': '正在解析網址特徵...'}) + '\n' 
                self.url_feature = self.extractor.get_URL_Feature(self.url)
                yield json.dumps({'status': 'progress', 'message': '正在解析網站結構...'}) + '\n'
                self.html_feature = self.extractor.get_HTMLStructure_Feature(self.url, self.html_structure)
                yield json.dumps({'status': 'progress', 'message': '正在解析網頁文本...'}) + '\n'
                self.ai_feature = self.extractor.get_HTMLContent_AI_Feature(self.html_content)
                yield json.dumps({'status': 'progress', 'message': '數據處理中...'}) + '\n'
                self.ai_feature = self.detector.preprocess_ai(self.ai_feature)
                self.html_feature = self.detector.preprocess_html(self.html_feature)
                yield json.dumps({'status': 'progress', 'message': '數據處理完成...'}) + '\n'
                yield json.dumps({'status': 'progress', 'message': '進行最終分析...'}) + '\n'
                prob = self.detector.predict(self.url_feature, self.html_feature, self.ai_feature)
                print(prob)
                reasons = self.extractor.getReason(self.url_feature, self.html_feature, self.ai_feature, prob[0])
                print(f'reason:{reasons}')
                yield json.dumps({'status': 'progress', 'message': '數據處理完成...'}) + '\n'
                final_result = {
                    "status": "success",
                    "message": prob[0],
                    "reasons": reasons
                }
                yield json.dumps(final_result) + '\n'
            except Exception as e:
                yield json.dumps({"status": "error", "message": str(e)}) + "\n"
        return Response(generate_progress(), mimetype='application/x-ndjson')

    def run(self, host='127.0.0.1', port=5000):
        print(f"偵測器伺服器啟動於 {host}:{port}")
        self.app.run(host=host, port=port, debug=True)
if __name__ == "__main__":
    detector = PhishingDetectorAPI()
    detector.run()