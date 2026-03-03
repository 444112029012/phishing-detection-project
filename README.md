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

# 其他注意事項
 * llama-cpp-python 套件安裝時容易出錯，可參考LLM環境部屬指南
