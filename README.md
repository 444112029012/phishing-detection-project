# 模型架構概要
 採堆疊架構，三個維度特徵模型上堆疊最終輸出模型
<img width="3084" height="978" alt="釣魚系統_模型架構" src="https://github.com/user-attachments/assets/d96019be-0af7-4dda-88ab-20b432ed1759" />

# 系統資料流概要
<img width="650" height="305" alt="image" src="https://github.com/user-attachments/assets/b27fbaa6-e50c-4b74-b47d-a80ba15adb2e" />

# 資料及資料蒐集概要
<img width="1790" height="2511" alt="資料蒐集流程" src="https://github.com/user-attachments/assets/9e9ab228-c9a0-483c-a022-915483eb49cc" />
註:爬蟲剛開始使用 request + selenium ，後改用 request + playwright
<hr>
<i>更多圖表參考「圖」資料夾</i>

# SLM
模型: Qwen3-8B-Q4_K_S <br>
來源: https://huggingface.co/unsloth/Qwen3-8B-GGUF <br>
雲端連結: https://drive.google.com/file/d/1i2YSx83ghAWA7efxUfzgwZDBNfw8jnyr/view?usp=drive_link <br>

# 資料集資訊
## URL
 * 用於基模型訓練: phishing_dataset_combine2_url
 * 用於元模型訓練: phishing_dataset_expansion_forEmbeddingModule_url
## HTML
 * 用於基模型訓練: phishing_dataset_html_combine2_html
 * 用於元模型訓練: phishing_dataset_expansion_forEmbeddingModule_html
## AI
 * 用於基模型訓練: phishing_dataset_Gemini_text_success + phishing_dataset_expansion_1_Gemini_text_success
 * 用於元模型訓練: phishing_dataset_expansion_forEmbeddingModule_Gemini_text_success
 * 注意: 模型訓練時需要新增欄位「text_length」，記錄網頁文本長度，此欄位對於模型效果有顯著影響
## 資料集連結: https://drive.google.com/drive/folders/1jWLVY82goJM3t9FVoLrSrQUbv8p5UQy_?usp=sharing

# 模型資訊
## URL
  * 模型: XGBoost
  * 資料量: 147225
  * ROG AUC: 0.9917
## HTML
  * 模型: MLP
  * 資料量: 81632
  * ROG AUC: 0.8453
## AI
  * 模型: XGBoost
  * 資料量: 32862
  * ROG AUC: 0.8921
## META-MODEL
  * 模型: Logistic
  * 資料量: 32704
  * ROG AUC: 0.9982
  * Log Loss: 0.0128 

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
