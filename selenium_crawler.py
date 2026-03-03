import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException
import os

# --- 設定 ---
FILE_NAME = "C:\畢業專題\資料集\phishing_dataset_in_progress.csv"  # 你的資料集檔案名稱
NEW_FILE_NAME = 'C:\畢業專題\資料集\搞AI欄位的\phishing_dataset_in_progress_test.csv'
NEW_COLUMN_NAME = 'visible_text'                    # 我們要創建的新欄位
SAVE_INTERVAL = 10                                  # 每處理 N 筆資料就儲存一次，防止中斷
RENDER_WAIT_TIME = 3                                # 載入頁面後，等待 JS 渲染的秒數

def setup_driver():
    """初始化 Selenium WebDriver"""
    print("正在初始化 WebDriver...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # 在背景執行，不開啟瀏覽器視窗
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    # --- [!!! 新增此區塊以提高安全性 !!!] ---
    # 設定瀏覽器的下載行為
    prefs = {
        # "download.default_directory": "/dev/null",  # 將下載指向一個無效位置 (Linux/macOS)
        "download.default_directory": "NUL",      # (如果是 Windows, 用這個)
        "download.prompt_for_download": False,      # 不詢問下載位置
        "download.directory_upgrade": True,
        "profile.default_content_settings.popups": 0, # 封鎖彈出視窗
        "safebrowsing.enabled": False,                # 關閉安全瀏覽 (避免它干擾爬蟲)
        "profile.default_content_setting_values.automatic_downloads": 2 # *** 關鍵：禁止自動下載 ***
    }
    options.add_experimental_option("prefs", prefs)
    # --- [安全設定結束] ---
    try:
        # 自動下載並設定 ChromeDriver
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # 設定頁面載入和腳本執行的超時時間
        driver.set_page_load_timeout(30)  # 30秒內頁面必須載入
        driver.set_script_timeout(10)   # 10秒內腳本必須執行完畢
        print("WebDriver 初始化完成。")
        return driver
    except Exception as e:
        print(f"WebDriver 初始化失敗: {e}")
        print("請確保你已安裝 Google Chrome 瀏覽器。")
        return None

def fetch_visible_text(driver, url):
    """
    (爬取文本的方法)
    使用 Selenium 爬取指定 URL 的可見文本 (document.body.innerText)
    """
    if not isinstance(url, str) or not url.strip():
        return "FETCH_ERROR: Invalid URL"
        
    # 確保 URL 有 http/https 協議頭
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'http://' + url

    try:
        driver.get(url)
        page_source_lower = driver.page_source.lower()
        
        if "dns_probe_finished_nxdomain" in page_source_lower or "err_name_not_resolved" in page_source_lower:
            print(f"  [Info] 網站不存在 (DNS): {url}")
            return "FETCH_ERROR: DNS_PROBE_FINISHED_NXDOMAIN"
        if "err_connection_refused" in page_source_lower:
            print(f"  [Info] 連線被拒: {url}")
            return "FETCH_ERROR: ERR_CONNECTION_REFUSED"
        if "err_connection_timed_out" in page_source_lower:
            print(f"  [Info] 連線超時: {url}")
            return "FETCH_ERROR: ERR_CONNECTION_TIMED_OUT"

        # 等待固定的秒數，讓 JavaScript 有時間渲染頁面
        time.sleep(RENDER_WAIT_TIME)
        
        # 執行 JS 來獲取 innerText
        text = driver.execute_script("return document.body.innerText;")

        if text is None:
             return "FETCH_EMPTY: 頁面未回傳可見文本"

        # --- [!!! 這是你要求的新清潔邏輯 !!!] ---
        
        # 1. 將文本按 "換行" 拆分為陣列
        lines = text.split('\n')
        
        # 2. 遍歷每一行，去除前後空白，並只保留 "非空" 的行
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        
        # 3. 如果過濾後沒有任何內容，回傳 EMPTY
        if not non_empty_lines:
            if "<frame" in page_source_lower:
                return "FETCH_EMPTY: 頁面為 <frame> 結構"
            return "FETCH_EMPTY: 頁面未回傳可見文本 (清潔後)"
            
        # 4. 將乾淨的行用 "單一空格" 串接成一個字串
        cleaned_text = '\n'.join(non_empty_lines)
        print(f'清潔後的文本: {cleaned_text}')
        return cleaned_text
        # --- [清潔邏輯結束] ---
            
        
    except TimeoutException:
        print(f"  [Error] 頁面載入超時: {url}")
        return "FETCH_ERROR: Page load timed out"
    except WebDriverException as e:
        error_msg = str(e).split('\n')[0]
        print(f"  [Error] WebDriver 錯誤: {error_msg}")
        return f"FETCH_ERROR: {error_msg}"
    except Exception as e:
        error_msg = str(e).split('\n')[0]
        print(f"  [Error] 未知錯誤: {error_msg}")
        return f"FETCH_ERROR: Unknown error - {error_msg}"

def process_dataset(df, driver, column_name, file_to_save):
    """
    (主要處理方法)
    遍歷 DataFrame，呼叫爬蟲，並即時更新資料集
    """
    total_rows = len(df)
    print(f"總共 {total_rows} 筆資料需要處理...")
    
    # 遍歷 DataFrame 的每一行
    for index, row in df.iterrows():
        
        # 檢查 'visible_text' 欄位是否為空 (pd.isna) 或為空字串
        # 如果已有內容，則跳過，實現「斷點續爬」
        if pd.isna(row[column_name]) or row[column_name] == "":
            url = row['url']
            print(f"正在處理第 {index+1}/{total_rows} 筆: {url}")
            
            # (呼叫爬取文本的方法)
            visible_text = fetch_visible_text(driver, url)
            
            # (將文本回傳後，直接更新資料集)
            # 使用 .at 來精確、快速地更新單一儲存格
            df.at[index, column_name] = visible_text
            
            # 每隔 N 筆資料就儲存一次檔案
            if (index + 1) % SAVE_INTERVAL == 0:
                print(f"--- 已處理 {index+1} 筆，正在儲存進度... ---")
                df.to_csv(file_to_save, index=False)
                
        else:
            # 如果該欄位已有資料，則跳過
            print(f"跳過第 {index+1}/{total_rows} 筆 (已有資料)")

    print("所有資料處理完畢。")
    return df

# --- 主程式執行 ---
if __name__ == "__main__":
    
    # 1. 讀入資料集
    if os.path.exists(NEW_FILE_NAME):
        # 如果新檔案已存在，表示我們上次跑到一半，從這裡繼續
        print(f"找到進度檔: {NEW_FILE_NAME}。正在載入並繼續任務...")
        try:
            df = pd.read_csv(NEW_FILE_NAME)
        except Exception as e:
            print(f"讀取 {NEW_FILE_NAME} 時發生錯誤: {e}。")
            print(f"將嘗試從原始檔案 {FILE_NAME} 重新開始。")
            try:
                df = pd.read_csv(FILE_NAME)
            except Exception as e_orig:
                 print(f"連讀取 {FILE_NAME} 都失敗: {e_orig}。程式終止。")
                 exit()
    else:
        # 如果新檔案不存在，表示這是第一次執行，從原始檔案載入
        print(f"找不到進度檔。正在從原始檔案 {FILE_NAME} 載入...")
        try:
            df = pd.read_csv(FILE_NAME)
            print(f"成功讀取資料集: {FILE_NAME}")
        except FileNotFoundError:
            print(f"錯誤: 找不到原始檔案 '{FILE_NAME}'。請確認檔案名稱與路徑。")
            exit()
        except Exception as e:
            print(f"讀取 {FILE_NAME} 時發生錯誤: {e}")
            exit()

    # 2. 若資料集不存在我們需要的欄位，就先創建欄位
    if NEW_COLUMN_NAME not in df.columns:
        print(f"找不到欄位 '{NEW_COLUMN_NAME}'，正在新增...")
        df[NEW_COLUMN_NAME] = ""  # 初始化為空字串
    else:
        print(f"找到欄位 '{NEW_COLUMN_NAME}'，將繼續處理未填滿的資料。")
        # 將可能的 NaN (Not a Number) 轉為空字串，方便後續判斷
        df[NEW_COLUMN_NAME] = df[NEW_COLUMN_NAME].fillna("")

    # 初始化 Selenium Driver
    driver = setup_driver()
    
    if driver:
        try:
            # 3. 傳入資料集進行處理
            df_updated = process_dataset(df, driver, NEW_COLUMN_NAME, NEW_FILE_NAME)
            
            # (最後回傳新資料集) - 並儲存最終版本
            print("正在儲存最終資料集...")
            df_updated.to_csv(NEW_FILE_NAME, index=False)
            print("任務完成！")
            
        except KeyboardInterrupt:
            # 如果使用者手動中斷 (Ctrl+C)
            print("\n偵測到手動中斷... 正在儲存目前進度...")
            df.to_csv(NEW_FILE_NAME, index=False)
            print("進度已儲存。")
        except Exception as e:
            print(f"主程式發生錯誤: {e}")
            print("正在嘗試儲存目前進度...")
            df.to_csv(NEW_FILE_NAME, index=False)
        finally:
            # 無論如何都要關閉瀏覽器
            print("正在關閉 WebDriver...")
            driver.quit()