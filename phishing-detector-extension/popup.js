// 監聽 "獲取網頁資訊" 按鈕的點擊事件
document.getElementById('getInfoButton').addEventListener('click', () => {
  const urlDisplay = document.getElementById('urlDisplay');
  const textDisplay = document.getElementById('textContent');
  const htmlDisplay = document.getElementById('htmlContent');

  // 設定載入中的提示
  urlDisplay.value = "載入中...";
  textDisplay.value = "載入中...";
  htmlDisplay.value = "載入中...";

  // 1. 查詢當前活動的、在目前視窗的分頁
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    // 檢查是否成功獲取到分頁
    if (tabs.length === 0) {
      urlDisplay.value = "錯誤：找不到活動分頁。";
      textDisplay.value = "";
      htmlDisplay.value = "";
      return;
    }

    const tab = tabs[0];
    const tabId = tab.id;

    // 2. [新任務] 獲取 URL - 這不需要注入腳本
    // tab 物件本身就包含 URL
    urlDisplay.value = tab.url;

    // 3. [更新任務] 在該分頁上執行腳本以獲取文本和 HTML
    chrome.scripting.executeScript(
      {
        target: { tabId: tabId }, // 指定要注入腳本的分頁 ID
        func: getPageContent,      // 要在該分頁上執行的函數
      },
      (injectionResults) => {
        // 這是 executeScript 的回呼函數

        // 檢查執行過程中是否有錯誤
        if (chrome.runtime.lastError) {
          const errorMsg = `錯誤： ${chrome.runtime.lastError.message}`;
          textDisplay.value = errorMsg;
          htmlDisplay.value = errorMsg;
          return;
        }

        // 檢查結果
        if (injectionResults && injectionResults.length > 0 && injectionResults[0].result) {
          const content = injectionResults[0].result;

          // content 現在是一個物件 { text: "...", html: "..." }
          textDisplay.value = content.text || "無法獲取文本。";
          htmlDisplay.value = content.html || "無法獲取 HTML。";
          const resultDisplay = document.getElementById('result');
          fetch("http://127.0.0.1:5000/check", {
            method: "POST", // 指定 HTTP 方法
            headers: {
              "Content-Type": "application/json" // 設定 MIME Type，告知伺服器 Body 的格式
            },
            // 將 JS Object 序列化為 JSON 字串
            body: JSON.stringify({
              url: tab.url,
              text: content.text,
              html: content.html
            })
          })
            .then(response => {
              if (!response.ok) throw new Error("網路請求失敗");
              return response.json(); // 解析 Response Body 中的 JSON
            })
            .then(data => {
              // 這裡的 data 已經是 Python 回傳的 JSON 物件
              console.log("分析成功:", data.message);
              document.getElementById('result').textContent = data.message;
            })
            .catch(error => {
              console.error("Fetch Error:", error);
            });

        } else {
          // 這種情況可能發生在無法注入腳本的頁面 (例如 Chrome 內部頁面)
          const errorMsg = "無法在此頁面上執行腳本。";
          textDisplay.value = errorMsg;
          htmlDisplay.value = errorMsg;
        }
      }
    );
  });
});

// 綁定新的按鈕 ID
document.getElementById('getPredict').addEventListener('click', () => {
  const resultDisplay = document.getElementById('result');
  resultDisplay.textContent = "資料擷取與模型分析中，請稍候...";

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs.length === 0) return;
    const tab = tabs[0];

    // 執行腳本抓取網頁內容
    chrome.scripting.executeScript(
      {
        target: { tabId: tab.id },
        func: getPageContent, // 你原本寫好的那個抓取函式
      },
      (injectionResults) => {
        if (chrome.runtime.lastError) {
          resultDisplay.textContent = `錯誤：${chrome.runtime.lastError.message}`;
          return;
        }

        if (injectionResults && injectionResults.length > 0 && injectionResults[0].result) {
          const content = injectionResults[0].result;

          // 將 URL、純文字、HTML 三大特徵發送給後端模型
          fetch("http://127.0.0.1:5000/predict", {  // 🌟 這裡可以改成 /predict
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              url: tab.url,
              text: content.text,
              html: content.html
            })
          })
            .then(response => {
              if (!response.ok) throw new Error("伺服器無回應");
              return response.json();
            })
            .then(data => {
              // 顯示最終預測結果
              resultDisplay.textContent = `預測結果：${data.message}`;
            })
            .catch(error => {
              console.error("Fetch Error:", error);
              resultDisplay.textContent = "無法連線到預測伺服器。";
            });
        }
      }
    );
  });
});

/**
 * 這是在目標網頁上 *實際執行* 的函數。
 * 它會回傳一個包含文本和 HTML 的物件。
 */
function getPageContent() {
  const pageText = document.body ? document.body.innerText : "";

  // document.documentElement.outerHTML 會獲取整個 <html> 標籤及其所有內容
  const pageHtml = document.documentElement ? document.documentElement.outerHTML : "";

  return {
    text: pageText,
    html: pageHtml
  };
}
