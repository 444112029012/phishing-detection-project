# 專案名稱: ModaGuard
<img width="200" height="auto" alt="icon" src="https://github.com/user-attachments/assets/6c5564f4-cb48-43a1-a0f1-8cd302a1da08" />

# 模型架構概要
 採堆疊架構，三個維度特徵模型上堆疊最終輸出模型
<img width="7811" height="2452" alt="釣魚系統_模型架構" src="https://github.com/user-attachments/assets/921f2d28-4d75-481c-8223-a27ca5617ac2" />
#### 後改用SLM取代GEMINI API

# 系統資料流概要
<img width="650" height="305" alt="image" src="https://github.com/user-attachments/assets/b27fbaa6-e50c-4b74-b47d-a80ba15adb2e" />

# 系統類別概要
<img width="650" height="auto" alt="釣魚專題_類別圖" src="https://github.com/user-attachments/assets/f92dbc31-56aa-4e7c-b4df-35a2ff1b814d" />


# 資料集資料蒐集概要
<img width="650" height="auto" alt="資料蒐集流程" src="https://github.com/user-attachments/assets/11909ea5-4a49-41d0-9585-8b84b3707838" />

<hr>
<i>更多圖表參考「圖」資料夾</i>

# SLM
模型: Qwen3-8B-Q4_K_S <br>
來源: https://huggingface.co/unsloth/Qwen3-8B-GGUF <br>
雲端連結: https://drive.google.com/file/d/1i2YSx83ghAWA7efxUfzgwZDBNfw8jnyr/view?usp=drive_link <br>

# 資料集資訊
## URL
 * 用於基模型訓練: Train_Base_URL
 * 用於元模型訓練: Dataset_Meta_Set
## HTML
 * 用於基模型訓練: Train_Base_HTML
 * 用於元模型訓練: Dataset_Meta_Set
## AI
 * 用於基模型訓練: Train_Base_AI
 * 用於元模型訓練: Dataset_Meta_Set
 * 注意: 模型訓練時需要新增欄位「text_length」，記錄網頁文本長度，此欄位對於模型效果有顯著影響
### 註: Dataset_Meta_Set拆出20%做為測試集(meta_test)


### 資料集連結: https://drive.google.com/drive/folders/1jWLVY82goJM3t9FVoLrSrQUbv8p5UQy_?usp=sharing

<hr>
# 模型資訊(使用meta_test測試)

<img width="747" height="144" alt="螢幕擷取畫面 2026-04-21 160640" src="https://github.com/user-attachments/assets/408d80f6-e7d0-43ed-9b9c-a237e8e2afc5" />
<img width="454" height="145" alt="螢幕擷取畫面 2026-04-21 160627" src="https://github.com/user-attachments/assets/f2f58265-8da7-4f8e-beeb-c5f1afdede68" />


# 其他注意事項
 * llama-cpp-python 套件安裝時容易出錯，可參考LLM環境部屬指南

# 當前成果
 * 前端 :<img width="437" height="425" alt="image" src="https://github.com/user-attachments/assets/1a4a41e1-58e7-49dd-bc92-b562e1ba3580" />
 * 後端:模型製作完畢

# 實際使用方式
 * 專案載入
 * slm模型載入，並調整連接路徑
 * 將「phishing-detector-extension」資料夾新增到CHROME擴充功能
 * 本機安裝好需要的套件模組
 * 啟動app.py檔(phishing-backend/app.py)
<hr>

### 文件連結
https://docs.google.com/document/d/12ymwbhiMN6RNxSNASU7RHOLjXNR3hopWngHtuOy1UoY/edit?tab=t.0


