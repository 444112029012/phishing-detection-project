import pandas as pd
import numpy as np
from phishing_detector_model import PhishingDetectorModel
from FeatureExtractor import FeatureExtractor

df = pd.read_csv(r"D:\\畢業專題\\資料集\\終極整理\\可以直接拿去使用的\\meta_test.csv")
df_phishing = df[df['target'] == 1]
df_legitimate = df[df['target'] == 0]
df_phishing_test = df_phishing.sample(n=1)
print(df_phishing_test)

url = df_phishing_test[['length_url', 'length_hostname', 'ip', 'nb_dots',
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
        ]]

html = df_phishing_test[['phish_hints', 'domain_in_brand', 'nb_hyperlinks',
       'ratio_intHyperlinks', 'ratio_extHyperlinks', 'ratio_extRedirection',
       'ratio_extErrors', 'external_favicon', 'links_in_tags',
       'ratio_extMedia', 'safe_anchor', 'empty_title', 'domain_in_title',
       'domain_with_copyright', 'has_meta_refresh', 'has_js_redirect'
        ]]

ai = df_phishing_test[['creates_urgency', 'uses_threats', 'requests_sensitive_info',
            'offers_unrealistic_rewards', 'has_spelling_grammar_errors',
            'impersonated_brand', 'has_valid_copyright_year', 
            'is_content_login_focused', 'has_rich_navigation', 
            'has_physical_address', 'has_phone_number',
            'content_consistency_score', 'language_professionalism_score', 
            'overall_phishing_likelihood_score', 'text_length'
            ]]

detector = PhishingDetectorModel()
extractor = FeatureExtractor()
ai= detector.preprocess_ai(ai)
html = detector.preprocess_html(html)
prob = detector.predict(url, html, ai)
print('風險機率: ' + str(round(prob[0]*100,2)) + '% ')
reasons = extractor.getReason(url, html, ai, prob[0])
print(f'原因: {reasons}')
