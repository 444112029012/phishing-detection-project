from google import genai
import os 
import time
import json
from google.genai.errors import ClientError
import pandas as pd
import numpy as np

class GeminiManager:
    def __init__(self, api_keys, models):
        self.keys = api_keys              # 多組 API keys
        self.models = models                  # 多種模型名稱
        self.key_index = 0                    # 目前使用的 key 索引
        self.model_index = 0                  # 目前使用的 model 索引
        self.max_retries = 3                  # 遇錯重試次數
        self.nb_503 = 0
        self._set_key_and_model()

    def _set_key_and_model(self):
        """設定目前使用的 key 和 model"""
        env_key_name = self.keys[self.key_index]
        api_key = os.getenv(env_key_name)
        self.client = genai.Client(api_key=api_key)
        self.current_model = self.models[self.model_index]
        print(f"🔑 使用 Key[{self.key_index + 1}]({env_key_name}) → 模型: {self.current_model}")

    def _next_model(self):
        """切換到下一個模型；如果該 key 的所有模型都用完，就切下一個 key"""
        self.model_index += 1
        if self.model_index >= len(self.models):
            self.model_index = 0
            self.key_index += 1
            if self.key_index >= len(self.keys):
                raise RuntimeError("🚫 所有 API Key 的模型都已用完！")
        self._set_key_and_model()

    def ask(self, prompt):
        """傳送 prompt，並在遇到錯誤時自動處理"""
        ex = ''
        for attempt in range(self.max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.current_model,
                    contents=prompt
                )
                self.nb_503 = 0
                return response.text
            
            # except exceptions.ResourceExhausted as e:
            #     ex = e
            #     print(f"⚠️ 模型 {self.current_model} 的額度已用完，切換下一個模型...")
            #     self._next_model()

            # except exceptions.TooManyRequests as e:
            #     ex = e
            #     wait = (attempt+1) ** (attempt) * 10
            #     print(f"🚦 呼叫太快，等待 {wait} 秒後重試...")
            #     time.sleep(wait)
            # except exceptions.InternalServerError as e:
            #     ex = e
            #     wait = (attempt+1) ** (attempt) * 10
            #     print(f"🚫 服務不可用(50x)，等待 {wait} 秒後重試...")
            #     time.sleep(wait)
            # except exceptions.PermissionDenied as e:
            #     ex = e
            #     print("🚫 API Key 無效或權限不足，切換下一個 key...")
            #     self._next_model()
            
            except Exception as e:
                ex = e
                if e.code:
                    if e.code == 429:
                        print(f'模型 {self.current_model} 429錯誤，切換模型')
                        self._next_model()
                    elif e.code == 404:
                        print('404錯誤，切換模型')
                        self._next_model()
                    elif e.code == 503:
                        self.nb_503 += 1
                        if self.nb_503 >= 5:
                            print('503錯誤，切換模型')
                            self.nb_503 = 0
                            self._next_model()
                        else:
                            wait = (attempt+1) ** (attempt) * 12
                            print(f"503錯誤:{e}, \n已累積 {self.nb_503} 次, 等待 {wait} 秒後重試...")
                            time.sleep(wait)
                    else:
                        print("❌ 其他錯誤：", e)
                        wait = (attempt+1) ** (attempt) * 12
                        print(f"等待 {wait} 秒後重試...")
                        time.sleep(wait)  
                else:
                    print("❌ 其他錯誤：", e)
                    wait = (attempt+1) ** (attempt) * 12
                    print(f"等待 {wait} 秒後重試...")
                    time.sleep(wait)          

        print("⛔ 已達最大重試次數。")
        return f"Error: {ex}"

KEYS = ['GEMINI_KEY1', 'GEMINI_KEY2','GEMINI_KEY3']
MODELS = ['gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-2.5-flash-preview-09-2025', 
            'gemini-2.5-flash-lite', 'gemini-2.5-flash-lite-preview-09-2025', 
            'gemini-2.0-flash', 'gemini-2.0-flash-001', 
            'gemini-2.0-flash-lite', 'gemini-2.0-flash-lite-001']

website_text = """
"""

file_path = 'C:\畢業專題\資料集\搞AI欄位的\phishing_dataset_expansion_forEmbeddingModule_Gemini_text.csv'
process_file_path = 'C:\畢業專題\資料集\搞AI欄位的\phishing_dataset_expansion_forEmbeddingModule_Gemini_text_success.csv'
prompt = ''
def read_dataset(file_path):
    df = pd.read_csv(file_path)
    return df

def generate_prompt(website_text):
    with open('prompt.txt', 'r', encoding='utf-8') as file:
        template = file.read()
        prompt = template.format(website_text=website_text)
    return prompt

def is_not_found_page(text):
    text_lower = text.lower()
    key = ['404', 'not found', 'page not found', 'page does not exist','Site Not Found', '找不到頁面', '頁面不存在']
    count = sum(kw in text_lower for kw in key)
    return count >= 2


def process_dataframe(df, client):
    try:
        df_process = df.copy()
        col = ['creates_urgency', 'uses_threats', 'requests_sensitive_info',
                'offers_unrealistic_rewards', 'has_spelling_grammar_errors',
                'impersonated_brand', 'language_professionalism_score',
                'overall_phishing_likelihood_score', 'summary_of_intent'
                ]
        for index, row in df_process.iterrows():
            print(f'正在處理第{index+1}/{len(df_process)}筆資料, url:{row["url"]}')
            if row['gemini_status'] == 'GEMINI_SUCCESS':
                print(f'已經處理過，跳過')
                continue
            text = row['visible_text']
            if not text:
                print('沒有text，跳過')
                df_process.loc[index, 'fetch_status'] = 'FETCH_EMPTY'
                df_process.loc[index, col] = np.nan
                df.loc[index, col] = np.nan
                continue
            elif text.startswith('FETCH_ERROR:'):
                print('fetch_status為FETCH_ERROR，跳過')
                df_process.loc[index, 'fetch_status'] = 'FETCH_ERROR'
                df_process.loc[index, col] = np.nan
                df.loc[index, col] = np.nan
                continue
            elif text.startswith('FETCH_EMPTY:'):
                print('fetch_status為FETCH_EMPTY，跳過')
                df_process.loc[index, 'fetch_status'] = 'FETCH_EMPTY'
                df_process.loc[index, col] = np.nan
                df.loc[index, col] = np.nan
                continue
            elif len(text) < 100:
                print('text長度小於100，跳過')
                df_process.loc[index, 'fetch_status'] = 'FETCH_TOOSHORT'
                df_process.loc[index, col] = np.nan
                df.loc[index, col] = np.nan
                continue
            elif is_not_found_page(text):
                print('頁面不存在，跳過')
                df_process.loc[index, 'fetch_status'] = 'NOT_FOUND_PAGE'
                df_process.loc[index, col] = np.nan
                df.loc[index, col] = np.nan
                continue
            df_process.loc[index, 'fetch_status'] = 'FETCH_SUCCESS'
            prompt = generate_prompt(text)
            response = client.ask(prompt)
            if not response:
                df_process.loc[index, 'gemini_status'] = 'GEMINI_ERROR'
                df_process.loc[index, col] = np.nan
                print(f'GEMINI_ERROR: {response}')
                continue
            if response.startswith('Error:'):
                df_process.loc[index, 'gemini_status'] = response
                df_process.loc[index, col] = np.nan
                continue
            df_process.loc[index, 'gemini_status'] = 'GEMINI_SUCCESS'
            json_string = response.replace("```json", "").replace("```", "")
            json_data = json.loads(json_string)
            for key, value in json_data.items():
                df_process.loc[index, key] = value
            print(f'成功處理第{index+1}筆資料')
        
    except KeyboardInterrupt:
        print(f'偵測到終止，即將存檔，並離開程式')
    except Exception as e:
        print(f'程式執行錯誤：{e}，立即存檔')
        
    finally:
        return df_process
    

def save_df(df, df_process, filename):
    filename = r'C:\畢業專題\資料集\搞AI欄位的\\' + filename
    try:
        if (df.index.equals(df_process.index) and df.columns.equals(df_process.columns)):
            df.update(df_process, overwrite=True)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
        else:
            print("結構不一致，另存新檔")
            filename = filename.replace('.df_processcsv', '_error.csv')
            df_process.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f'資料已成功儲存至{filename}')
    except Exception as e:
        print(f'儲存失敗：{e}')
def main():
    if os.path.exists(process_file_path):
        df = read_dataset(process_file_path)
        print(f'找到進度檔: {process_file_path}，正在繼續處理')
    else:
        df = read_dataset(file_path)
        print(f'找不到進度檔: {process_file_path}，正在從原始檔案載入')
    client = GeminiManager(KEYS, MODELS)
    if 'gemini_status' not in df.columns:
        new_columns = [
                'gemini_status', #狀態欄位
                'fetch_status', #狀態欄位
                'creates_urgency', 'uses_threats', 'requests_sensitive_info',
                'offers_unrealistic_rewards', 'has_spelling_grammar_errors',
                'impersonated_brand', 'language_professionalism_score',
                'overall_phishing_likelihood_score', 'summary_of_intent'
            ]
        print(f'新增欄位: {new_columns}')
        for col in new_columns:
            df[col] = np.nan

    try:
        df_process = process_dataframe(df, client)
        save_df(df, df_process, 'phishing_dataset_expansion_forEmbeddingModule_Gemini_text_success.csv')      
    except KeyboardInterrupt:
        save_df(df, df_process, 'phishing_dataset_expansion_forEmbeddingModule_Gemini_text_success.csv')
    except Exception as e:
        print(f'程式執行錯誤：{e}，立即存檔')
        df_process.to_csv('C:\畢業專題\資料集\搞AI欄位的\phishing_dataset_expansion_forEmbeddingModel_Gemini_text_error_2.csv', index=False, encoding='utf-8-sig')
    finally:
        print('程式執行完成')
main()
