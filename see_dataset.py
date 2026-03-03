import pandas as pd
import numpy as np
import os

df_o = pd.read_csv('D:\\畢業專題\\資料集\\搞AI欄位的\\Qwen3_8B_Q4_K_S\\phishing_dataset_expansion_forEmbeddingModule_Gemini_text_success.csv')
df_e = pd.read_csv('D:\\畢業專題\\資料集\\搞AI欄位的\\phishing_dataset_expansion_forEmbeddingModule_Gemini_text.csv')
print(df_o.info())
# print(df_e.info())
# df_o.update(df_e, overwrite=True)
# print(df_o.info())
#df_o.to_csv('D:\\畢業專題\\資料集\\搞AI欄位的\\Qwen3_8B_Q4_K_S\\phishing_dataset_expansion_forEmbeddingModule_Gemini_text_success.csv', index=False, encoding='utf-8-sig')
# if (df_o.index.equals(df_e.index) and df_o.columns.equals(df_e.columns)):
#     df_o.update(df_e, overwrite=True)
#     df_o.to_csv('D:\\畢業專題\\資料集\\搞AI欄位的\\Qwen3_8B_Q4_K_S\\phishing_dataset_Gemini_text_succes.csv', index=False, encoding='utf-8-sig')
# else:
#     print("結構不一致，無法合併")
#     print(df_o.index)
#     print(df_e.index)
#     print(df_o.columns)
#     print(df_e.columns)
# for index, row in df.iterrows():
#   if df.loc[index, 'gemini_status'] == 'GEMINI_SUCCESS' and pd.isna(row['creates_urgency']):
#     print(index)
#     print(df.loc[index])