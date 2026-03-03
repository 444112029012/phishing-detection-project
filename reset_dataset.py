from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

SOURCE_PATH = Path(
    r"D:\畢業專題\資料集\搞AI欄位的\phishing_dataset_Gemini_text.csv"
)

df = pd.read_csv(SOURCE_PATH)
df = df[['url', 'target', 'visible_text']]
df.info()
# print(sum(df['gemini_status'] == 'GEMINI_SUCCESS'))
# print(sum(pd.notna(df['creates_urgency'])))
# ENCODING = "utf-8-sig"
# df.to_csv(SOURCE_PATH, index=False, encoding=ENCODING)
# new_columns = [
#                 'gemini_status', #狀態欄位
#                 'fetch_status', #狀態欄位
#                 'creates_urgency', 'uses_threats', 'requests_sensitive_info',
#                 'offers_unrealistic_rewards', 'has_spelling_grammar_errors',
#                 'impersonated_brand','language_professionalism_score',
#                 'overall_phishing_likelihood_score', 'summary_of_intent'
#             ]
# df.drop('reasoning_checks_complete'  , axis=1, inplace=True)
# ENCODING = "utf-8-sig"
df.to_csv(SOURCE_PATH, index=False, encoding="utf-8-sig")