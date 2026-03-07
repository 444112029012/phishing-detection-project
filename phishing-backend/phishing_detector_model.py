from xgboost import XGBClassifier
from tensorflow.keras.models import load_model
import joblib
import numpy as np
class PhishingDetectorModel:
    def __init__(self):
        self.URL_Feature_Model = self.get_URL_Feature_Model()
        self.HTMLStructure_Feature_Model = self.get_HTMLStructure_Feature_Model()
        self.HTMLContent_Feature_Scaler = self.get_HTMLContent_Feature_Scaler()
        self.HTMLContent_AI_Feature_Model = self.get_HTMLContent_AI_Feature_Model()
        self.Meta_Model = self.get_Meta_Model()
        self.feature_vector = None
    def predict(self, url_feature, html_feature, ai_feature):
        try:
            if not self.check_feature(url_feature, html_feature, ai_feature):
                print('特徵欄位不一致')
                return None
            self.set_feature_vector(url_feature, html_feature, ai_feature)
            prob = self.Meta_Model.predict_proba(self.feature_vector)[:, 1]
            return prob
        except Exception as e:
            print(f'Error: {e}')
            return None
    def check_feature(self, url_feature, html_feature, ai_feature):
        url_col = ['length_url', 'length_hostname', 'ip', 'nb_dots',
       'nb_hyphens', 'nb_at', 'nb_qm', 'nb_and', 'nb_or', 'nb_eq',
       'nb_underscore', 'nb_tilde', 'nb_percent', 'nb_slash', 'nb_star',
       'nb_colon', 'nb_comma', 'nb_semicolumn', 'nb_dollar', 'nb_space',
       'nb_www', 'nb_com', 'nb_dslash', 'http_in_path', 'https_token',
       'ratio_digits_url', 'ratio_digits_host', 'punycode', 'port',
       'tld_in_path', 'tld_in_subdomain', 'nb_subdomains',
       'abnormal_subdomain', 'prefix_suffix', 'path_extension',
       'length_words_raw', 'char_repeat', 'shortest_word_host',
       'shortest_word_path', 'longest_words_raw', 'longest_word_host',
       'longest_word_path', 'avg_words_raw', 'avg_word_host', 'avg_word_path'
        ]
        html_col = [
        'phish_hints', 'domain_in_brand', 'nb_hyperlinks', 'ratio_intHyperlinks',
        'ratio_extHyperlinks', 'ratio_extRedirection', 'ratio_extErrors',
        'external_favicon', 'links_in_tags', 'ratio_extMedia', 'safe_anchor',
        'empty_title', 'domain_in_title', 'domain_with_copyright',
        'has_meta_refresh', 'has_js_redirect'
        ]
        ai_col = ['creates_urgency', 'uses_threats', 'requests_sensitive_info',
            'offers_unrealistic_rewards', 'has_spelling_grammar_errors',
            'impersonated_brand', 'has_valid_copyright_year', 
            'is_content_login_focused', 'has_rich_navigation', 
            'has_physical_address', 'has_phone_number',
            'content_consistency_score', 'language_professionalism_score', 
            'overall_phishing_likelihood_score', 'text_length'
            ]
        try:
            if set(url_col) != set(url_feature.columns) or set(html_col) != set(html_feature.columns) or set(ai_col) != set(ai_feature.columns):
                print('特徵欄位不一致')
                print(f'url_info: {url_feature.info()}')
                print(f'html_info: {html_feature.info()}')
                print(f'ai_info: {ai_feature.info()}')
                return False
            return True
        except Exception as e:
            print(f'Error: {e}')
            return False
    def get_URL_Feature_Model(self):
        model = XGBClassifier()
        model.load_model(r"phishing-backend\\model\\url_xgb_v1.json")
        return model
    def get_HTMLStructure_Feature_Model(self):
        return load_model(r"phishing-backend\\model\\html_mlp_v1.keras")
    def get_HTMLContent_Feature_Scaler(self):
        return joblib.load(r"phishing-backend\\model\\html_scaler.pkl")
    def get_HTMLContent_AI_Feature_Model(self):
        model = XGBClassifier()
        model.load_model(r"phishing-backend\\model\\ai_xgb_v1.json")
        return model
    def get_Meta_Model(self):
        return joblib.load(r"phishing-backend\\model\\meta_model_logistic_v1.pkl")
    def get_feature_vector(self):
        return self.feature_vector
    def set_feature_vector(self, url_feature, html_feature, ai_feature):
        try:
            self.feature_vector = np.c_[self.URL_Feature_Model.predict_proba(url_feature)[:, 1], 
                                        self.HTMLStructure_Feature_Model.predict(html_feature).ravel(), 
                                        self.HTMLContent_AI_Feature_Model.predict_proba(ai_feature)[:, 1]]
        except Exception as e:
            print(f'Error: {e}')
            raise Exception(f'Error: {e}')
    def preprocess_html(self, html_feature):
        sca_col = ['links_in_tags', 'nb_hyperlinks']
        html_feature[sca_col] = self.HTMLContent_Feature_Scaler.transform(html_feature[sca_col])
        if 'url' in html_feature.columns:
            html_feature.drop(['url'], axis=1, inplace=True)
        if 'feature_extracted' in html_feature.columns:
            html_feature.drop(['feature_extracted'], axis=1, inplace=True)
        required_columns = [
            'phish_hints', 'domain_in_brand', 'nb_hyperlinks',
            'ratio_intHyperlinks', 'ratio_extHyperlinks', 'ratio_extRedirection',
            'ratio_extErrors', 'external_favicon', 'links_in_tags',
            'ratio_extMedia', 'safe_anchor', 'empty_title', 'domain_in_title',
            'domain_with_copyright', 'has_meta_refresh', 'has_js_redirect'
        ]
        if set(required_columns) != set(html_feature.columns):
            print('html_feature的欄位數需要調整')
            print(html_feature.info())
            return None
        print('html_feature特徵轉換完成')
        return html_feature

    def preprocess_ai(self, ai_feature):
        if len(ai_feature.columns) != 15:
            print('ai_feature的欄位數需要調整')
            print(ai_feature.info())
            try:
                ai_feature.drop(['url', 'ai_status', 'fetch_status', 'visible_text'], axis=1, inplace=True)
            except Exception as e:
                print(f'調整錯誤:{e}')
                return None
            print('調整完成')
        bool_col = ['creates_urgency', 'uses_threats', 'requests_sensitive_info',
            'offers_unrealistic_rewards', 'has_spelling_grammar_errors',
            'has_valid_copyright_year', 'is_content_login_focused',
            'has_rich_navigation', 'has_physical_address', 'has_phone_number']
        ai_feature[bool_col] = ai_feature[bool_col].astype(int)
        ai_feature['impersonated_brand'] = [1 if k else 0 for k in ai_feature['impersonated_brand'].notnull()]
        print('AI特徵轉換完成')
        return ai_feature 