// popup.js 完整程式碼

// 確保 HTML 完全載入後才執行綁定
document.addEventListener('DOMContentLoaded', function () {
  const scanButton = document.getElementById('scanButton');
  const statusArea = document.getElementById('statusArea');

  scanButton.addEventListener('click', async () => {
    // ==========================================
    // 1. 防呆鎖定：點擊瞬間反灰按鈕
    // ==========================================
    scanButton.disabled = true;
    scanButton.innerText = "🔄 正在擷取網頁資訊...";
    scanButton.style.cursor = "not-allowed";
    statusArea.innerText = ""; // 清空之前的結果
    statusArea.style.color = "#333";

    try {
      // ==========================================
      // 2. 抓取當前分頁 URL
      // ==========================================
      let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

      // ==========================================
      // 3. 注入腳本：抓取 HTML 結構與純文字
      // ==========================================
      let injectionResults = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => {
          // 這段程式碼會在使用者當前瀏覽的網頁中執行
          return {
            html: document.documentElement.outerHTML,
            text: document.body.innerText
          };
        }
      });

      const pageData = injectionResults[0].result;

      // 更新狀態提示，讓使用者知道前端工作做完了
      scanButton.innerText = "🧠 AI 模型分析中 (約需幾秒鐘)...";
      statusArea.innerHTML = "✅ 網頁資訊獲取成功！<br>⏳ 正在等待後端伺服器運算...";

      // ==========================================
      // 4. 直接將資料打包發送給 Flask 後端
      // ==========================================
      const response = await fetch("http://127.0.0.1:5000/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: tab.url,
          html: pageData.html,
          text: pageData.text
        })
      });

      // 檢查伺服器是否回傳錯誤 (例如 500)
      if (!response.ok) {
        throw new Error(`伺服器回應錯誤 (狀態碼: ${response.status})`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
      while (true) {
        const { done, value } = await reader.read()
        if (done) {
          break;
        }
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n').filter(line => line.trim() !== '');
        for (let line of lines) {
          const data = JSON.parse(line);
          if (data.status === 'progress') {
            statusArea.innerHTML = `
                            <div style="padding: 10px; background-color: #e3f2fd; border-radius: 5px; margin-top: 10px; border-left: 4px solid #2196f3;">
                                <span style="color: #1565c0; font-weight: bold;">🔄 ${data.message}</span>
                            </div>
                        `;
            await sleep(500);
          }
          else if (data.status === 'success') {
            // 將後端回傳的結果印在畫面上 (這裡先保留你原本看特徵陣列的需求)
            let probability = Number(data.message);
            let displayPercentage = (probability * 100).toFixed(2);
            let aiSummary = data.reasons || "系統未提供詳細分析理由。";

            // 3. 根據機率決定 UI 的顏色與警告層級 (這招 UX 超加分！)
            let boxColor = probability > 0.5 ? '#ffebee' : '#e8f5e9'; // 高風險用淺紅，低風險用淺綠
            let borderColor = probability > 0.5 ? '#f44336' : '#4caf50'; // 邊框顏色 (紅/綠)
            let titleText = probability > 0.5 ? '偵測到風險！' : '網站相對安全';
            let titleColor = probability > 0.5 ? 'red' : 'green';

            // 4. 畫出超專業的最終結果卡片
            statusArea.innerHTML = `
                <div style="padding: 12px; background-color: ${boxColor}; border-radius: 8px; margin-top: 15px; border-left: 5px solid ${borderColor}; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="color: ${titleColor}; font-size: 16px; font-weight: bold; margin-bottom: 5px;">
                        ${titleText}
                    </div>
                    
                    <div style="font-size: 15px; color: #333; font-weight: bold; margin-bottom: 10px;">
                        釣魚風險指數: <span style="color: #d32f2f; font-size: 18px;">${displayPercentage}%</span>
                    </div>
                    
                    <hr style="border: 0; border-top: 1px dashed #ccc; margin: 10px 0;">
                    
                    <div style="font-size: 13px; color: #444; line-height: 1.6; text-align: justify;">
                        <span style="font-weight: bold; color: #1565c0;">AI評估：</span><br>
                        ${aiSummary}
                    </div>
                </div>
            `;
          }
          else if (data.status === 'error') {
            statusArea.innerHTML = `<span style="color: red;">⚠️ 分析失敗：${data.message}</span>`;
          }
        }
      }
    } catch (error) {
      // 捕捉任何網路斷線或擴充功能權限錯誤
      console.error("發生錯誤:", error);
      statusArea.innerHTML = `<span style="color: red;">❌ 發生錯誤：${error.message}</span>`;
    } finally {
      // ==========================================
      // 6. 最終清理：解除鎖定，讓按鈕可以再次被點擊
      // ==========================================
      scanButton.disabled = false;
      scanButton.innerText = "🛡️ 一鍵安全掃描";
      scanButton.style.cursor = "pointer";
    }
  });
});