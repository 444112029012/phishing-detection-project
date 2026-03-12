# from google import genai
import os
import time
import json
import pandas as pd
import numpy as np
from llama_cpp import Llama
from pydantic import BaseModel, Field
from typing import Optional

class PhishingSchema(BaseModel):
    creates_urgency: bool
    uses_threats: bool
    requests_sensitive_info: bool
    offers_unrealistic_rewards: bool
    has_spelling_grammar_errors: bool
    impersonated_brand: str
    has_valid_copyright_year: bool
    is_content_login_focused: bool
    has_rich_navigation: bool
    has_physical_address: bool
    has_phone_number: bool
    content_consistency_score: int = Field(ge=0, le=10)
    language_professionalism_score: int = Field(ge=0, le=10)
    overall_phishing_likelihood_score: int = Field(ge=0, le=10)

class Dataset_Manager:
    def __init__(self):
        self.source_path = r"D:\\畢業專題\\資料集\\搞AI欄位的\\phishing_dataset_expansion_forEmbeddingModule_Gemini_text.csv"
        self.processed_path = r"D:\\畢業專題\\資料集\\搞AI欄位的\\Qwen3_8B_Q4_K_S\\phishing_dataset_expansion_forEmbeddingModule_Gemini_text_success.csv"
        self.filename = 'phishing_dataset_expansion_forEmbeddingModule_Gemini_text_success.csv'
        self.df = self.read_dataset()
        self.model = QwenLLM()
        self.col =['creates_urgency', 'uses_threats', 'requests_sensitive_info',
                'offers_unrealistic_rewards', 'has_spelling_grammar_errors',
                'impersonated_brand', 'has_valid_copyright_year',
                'is_content_login_focused', 'has_rich_navigation',
                'has_physical_address', 'has_phone_number',
                'content_consistency_score', 'language_professionalism_score',
                'overall_phishing_likelihood_score'
                ]

    def read_dataset(self):
        if os.path.exists(self.processed_path):
            df = pd.read_csv(self.processed_path)
            print(f'找到進度檔: {self.processed_path}，正在繼續處理')
        else:
            df = pd.read_csv(self.source_path)
            print(f'找不到進度檔: {self.processed_path}，正在從原始檔案載入')
        return df
    
    def save_df(self, df_process):
        try:
            path = self.processed_path
            if (self.df.index.equals(df_process.index) and self.df.columns.equals(df_process.columns)):
                self.df.update(df_process, overwrite=True)
                self.df.to_csv(self.processed_path, index=False, encoding='utf-8-sig')
            else:
                print("結構不一致，另存新檔")
                print(f'原始結構:{self.df.index}, {self.df.columns}')
                print(f'處理後結構:{df_process.index}, {df_process.columns}')
                path = self.processed_path.replace('_success.csv', '_error.csv')
                df_process.to_csv(path, index=False, encoding='utf-8-sig')
            print(f'資料已成功儲存至{path}')
        except Exception as e:
            print(f'儲存失敗：{e}')
    def check_col(self):
        if 'ai_status' not in self.df.columns:
            new_columns = [
                'ai_status', #狀態欄位
                'fetch_status', #狀態欄位
                'creates_urgency', 'uses_threats', 'requests_sensitive_info',
                'offers_unrealistic_rewards', 'has_spelling_grammar_errors',
                'impersonated_brand', 'has_valid_copyright_year', 
                'is_content_login_focused', 'has_rich_navigation', 
                'has_physical_address', 'has_phone_number', 
                'content_consistency_score', 'language_professionalism_score',
                'overall_phishing_likelihood_score'
            ]
            print(f'新增欄位: {new_columns}')
            for col in new_columns:
                self.df[col] = np.nan
                if col not in ['content_consistency_score', 'language_professionalism_score', 'overall_phishing_likelihood_score']:
                    self.df[col] = self.df[col].astype(object)

    def is_not_found_page(self, text):
        not_found_patterns = [
            "404",
            "the page you are looking for does not exist",
            "找不到頁面",
            "找不到網頁",
            "404 - 找不到頁面",
            "頁面不存在",
            'not found', 
            'page not found', 
            'page does not exist',
            'site not found',
            'no tenant found'
        ]
        text_lower = text.lower()
        count = sum(kw in text_lower for kw in not_found_patterns)
        return count >= 2

    def process(self):
        self.check_col()
        try:
            df_process = self.df.copy()
            
            for index, row in df_process.iterrows():
                if index < 90000:
                    continue
                elif index == 73889:
                    continue
                print(f'正在處理第{index+1}/{len(df_process)}筆資料, url:{row["url"]}')
                if row['ai_status'] == 'AI_SUCCESS' and pd.notna(row['creates_urgency']):
                    print(f'已經處理過，跳過')
                    continue
                text = str(row['visible_text'])
                if not text:
                    print('沒有text，跳過')
                    df_process.loc[index, 'fetch_status'] = 'FETCH_EMPTY'
                    df_process.loc[index, self.col] = np.nan
                    continue
                elif text.startswith('FETCH_ERROR:'):
                    print('fetch_status為FETCH_ERROR，跳過')
                    df_process.loc[index, 'fetch_status'] = 'FETCH_ERROR'
                    df_process.loc[index, self.col] = np.nan
                    continue
                elif text.startswith('FETCH_EMPTY:'):
                    print('fetch_status為FETCH_EMPTY，跳過')
                    df_process.loc[index, 'fetch_status'] = 'FETCH_EMPTY'
                    df_process.loc[index, self.col] = np.nan
                    continue
                elif len(text) < 100:
                    print('text長度小於100，跳過')
                    df_process.loc[index, 'fetch_status'] = 'FETCH_TOOSHORT'
                    df_process.loc[index, self.col] = np.nan
                    continue
                elif self.is_not_found_page(text):
                    print('頁面不存在，跳過')
                    df_process.loc[index, 'fetch_status'] = 'NOT_FOUND_PAGE'
                    df_process.loc[index, self.col] = np.nan
                    continue
                df_process.loc[index, 'fetch_status'] = 'FETCH_SUCCESS'
                response = self.model.ask(text)
                if not response:
                    df_process.loc[index, 'ai_status'] = 'AI_ERROR'
                    df_process.loc[index, self.col] = np.nan
                    print(f'AI_ERROR: {response}')
                    continue
                if response.startswith('Error:'):
                    df_process.loc[index, 'ai_status'] = response
                    df_process.loc[index, self.col] = np.nan
                    continue
                json_data = json.loads(response)
                for key, value in json_data.items():
                    df_process.loc[index, key] = value
                df_process.loc[index, 'ai_status'] = 'AI_SUCCESS'
                print(f'成功處理第{index+1}筆資料')
                if index % 500 == 0:
                    self.save_df(df_process)
        except KeyboardInterrupt:
            print(f'偵測到終止，即將存檔，並離開程式')
        except Exception as e:
            print(f'程式執行錯誤：{e}，立即存檔')
            
        finally:
            print(f'程式執行結束，即將存檔，並離開程式')
            self.save_df(df_process)
            return    
            

class QwenLLM:
    def __init__(self):
        self.model = Llama(
            model_path=r"D:\\畢業專題\\LLM\\Qwen3-8B-Q4_K_S.gguf",
            n_gpu_layers=30,
	        n_ctx=15000,
	        n_batch=2048,   # 提升預處理速度
	        n_ubatch=2048,  # 同步提升運算效率
	        flash_attn=True,
			use_mlock=True,
            type_k=8,
            type_v=8,
            verbose=False
        )
        self.system_prompt = self.system_prompt()
        self.max_retries = 1
        self.max_tokens=2500
        self.temperature=0.4
        self.response_format={"type": "json_object", "schema": PhishingSchema.model_json_schema()}

    def system_prompt(self):
        with open('prompt3.txt', 'r', encoding='utf-8') as file:
            template = file.read()
        return template

    def ask(self, text):
        ex = ''
        for attempt in range(self.max_retries):
            try:
                response = self.model.create_chat_completion(
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": f"Please analyze this text:/n {text}"}
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    response_format=self.response_format
                )
                return response["choices"][0]["message"]["content"]
            
            except Exception as e:
                ex = e
                print("❌ 錯誤：", e)
                wait = (attempt+1) * 1
                print(f"等待 {wait} 秒後重試...")
                time.sleep(wait)          

        print("⛔ 已達最大重試次數。")
        return f"Error: {ex}"

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
        self.nb_503 = 0
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
            except Exception as e:
                ex = e
                if e.code:
                    if e.code == 429:
                        print(f'模型 {self.current_model} 429錯誤，切換模型') # : {e.message}
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
                            wait = (attempt+1) ** (attempt+1) * 12
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

# KEYS = ['GEMINI_KEY1', 'GEMINI_KEY2','GEMINI_KEY3', 'GEMINI_KEY4', 'GEMINI_KEY5', 'GEMINI_KEY6']
# MODELS = ['gemini-3-flash-preview', 'gemini-2.5-flash', #'gemini-flash-latest', 'gemini-3-pro-preview', 'gemini-2.5-pro', 'gemini-2.5-flash-preview-09-2025', 
#             'gemini-2.5-flash-lite']     

# website_text = """
# """
# 
# file_path = r"D:\畢業專題\資料集\搞AI欄位的\phishing_dataset_Gemini_text.csv"
# process_file_path = r'D:\畢業專題\資料集\搞AI欄位的\llama_guard_4_12b\phishing_dataset_llama_guard_4_12b_text_success.csv'

# prompt = ''
def main():
    DM = Dataset_Manager()
    DM.process()
    
while True:
    try:
        main()
        print(f'等待20秒後重試')
        time.sleep(20)
        break
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f'程式執行錯誤:{e}')
        break

