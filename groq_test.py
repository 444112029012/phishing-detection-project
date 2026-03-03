import os
from groq import Groq
import pandas as pd
import numpy as np
class GroqManager:
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
        api_key = os.environ.get(env_key_name)
        self.client = Groq(api_key=api_key)
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
                messages=[{'role': 'user', 'content': prompt}]
                print(messages)
                response = self.client.chat.completions.create(
                    model=self.current_model,
                    messages=messages
                )
                self.nb_503 = 0
                return response.choices[0].message.content
            
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

KEYS =  ['GROQ_API_KEY1']
MODELS = ['meta-llama/llama-guard-4-12b']

def read_dataset(file_path):
    df = pd.read_csv(file_path)
    return df

def generate_prompt(website_text):
    #prompt
    with open('prompt3.txt', 'r', encoding='utf-8') as file:
        template = file.read()
        prompt = template.format(website_text=website_text)
    return prompt
file_path = r"D:\畢業專題\資料集\搞AI欄位的\phishing_dataset_Gemini_text.csv"
df = read_dataset(file_path)
client = GroqManager(KEYS, MODELS)
for index, row in df.iterrows():
            # if index < 30000:
            #     continue
            print(f'正在處理第{index+1}/{len(df)}筆資料, url:{row["url"]}')
            text = str(row['visible_text'])
            if not text:
                print('沒有text，跳過')
                continue
            elif text.startswith('FETCH_ERROR:'):
                print('fetch_status為FETCH_ERROR，跳過')
                continue
            elif text.startswith('FETCH_EMPTY:'):
                print('fetch_status為FETCH_EMPTY，跳過')
                continue
            elif len(text) < 100:
                print('text長度小於100，跳過')
                continue
            prompt = generate_prompt(text)
            response = client.ask(prompt)
            if not response:
                print(f'AI_ERROR: {response}')
                continue
            print(response)
            break
            if response.startswith('Error:'):
                df.loc[index, 'ai_status'] = response
                df.loc[index, col] = np.nan
                continue
            
            json_string = response.replace("```json", "").replace("```", "")
            json_data = json.loads(json_string)
            print(json_data)
            for key, value in json_data.items():
                df.loc[index, key] = value
            df.loc[index, 'ai_status'] = 'AI_SUCCESS'
            print(f'成功處理第{index+1}筆資料')