# LLM 環境部署指南 

本文件詳述如何從零開始配置 llama-cpp-python 環境，並針對 RTX 3060 (6GB VRAM) 進行 16,000 Tokens 長文本分析的效能最佳化。

# 第一階段：硬體基礎與系統工具安裝

在開始之前，請確保系統為 Windows 10/11，且 GPU 驅動程式已更新至最新版。

## 1. Visual Studio 2022 (MSVC 編譯器)

這是編譯 C++ 核心的必備工具。

下載位址：Visual Studio Community

安裝重點：在安裝程式中，必須勾選 「使用 C++ 的桌面開發 (Desktop development with C++)」。

詳細事項：請確保右側選單中包含：

MSVC v143 - VS 2022 C++ x64/x86 生成工具

Windows 11/10 SDK

## 2. NVIDIA CUDA Toolkit

讓 GPU 能夠執行平行運算的工具包。

建議版本：CUDA 12.1 或 12.4

下載位址：CUDA Toolkit Archive

安裝位置：預設通常為 C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x

詳細事項：安裝後請檢查系統環境變數 (Path)，確保包含以下路徑：

...\CUDA\v12.x\bin

...\CUDA\v12.x\libnvvp

# 第二階段：Python 環境與路徑初始化

## 1. 建立虛擬環境

### 建立環境
python -m venv phishing_env

### 啟動環境 (PowerShell)
.\phishing_env\Scripts\Activate.ps1


## 2. 啟動編譯器「隱藏」路徑 (關鍵步驟)

Windows 預設不會讓 cl.exe 出現在全局路徑中。每次重新開啟視窗進行編譯前，必須執行此腳本：

### 載入 MSVC 編譯器環境 (路徑視你的 VS 版本而定)
& "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"

### 驗證編譯器是否可用
cl
nvcc --version


# 第三階段：強迫編譯安裝 (解決版本衝突)

當 MSVC 版本太新導致 CUDA 噴出「Unsupported Version」錯誤時，必須使用以下「暴力編譯」策略，透過旗標強制忽略衝突。

## 1. 注入極限編譯參數

### 設定編譯規則：開啟 CUDA、全架構支援、並忽略版本衝突
$env:CMAKE_ARGS = "-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=all -DCMAKE_CUDA_FLAGS='-allow-unsupported-compiler'"


## 2. 執行強制現場編譯

### --force-reinstall 確保捨棄舊暫存
### --no-cache-dir 確保現場重新編譯，不套用預編譯檔
pip install llama-cpp-python --force-reinstall --no-cache-dir



程式碼範例

from llama_cpp import Llama

llm = Llama(
    model_path="path/to/model.gguf",
    n_gpu_layers=30,
    n_ctx=16384,
    type_k=8,        # 開啟 KV 量化
    type_v=8,
    n_batch=2048,
    flash_attn=True,
    verbose=False
)


⚠️ 常見坑點與解決方案 (Troubleshooting)

1. 輸出結果為空 JSON {}

原因：通常是顯存（VRAM）壓榨太滿，導致 JSON 運算緩衝區失敗。

對策：將 n_gpu_layers 從 32 降到 30。

2. 編譯噴出 "Could not find CUDA"

原因：PowerShell 沒抓到 CUDA 路徑。

對策：手動檢查環境變數 Path，或在執行 pip 前再次確認 nvcc 指令是否生效。

3. 資料結構不一致 (多了新欄位)

原因：LLM 偶爾會吐出多餘欄位，導致 Pandas DataFrame 合併失敗。

對策：使用 df_o.update(df_e)，以正確結構 (df_o) 為準，只更新有的欄位，自動忽略多餘部分。

4. 效能掉速 (16k tokens)

原因：文本太長，GPU 頻寬飽和。

對策：務必檢查 type_k=8, type_v=8 是否有設定，這能將顯存佔用從 2.5GB 砍到 1.3GB 左右。

文件紀錄日期：2024年畢業專題開發實錄
