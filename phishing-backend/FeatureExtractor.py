import numpy as np
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import ipaddress
import pandas as pd
import re
from pydantic import BaseModel, Field
import time
import json 
from llama_cpp import Llama

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

class QwenLLM:
    def __init__(self):
        self.model = Llama(
            model_path=r"D:\\畢業專題\\LLM\\Qwen3-8B-Q4_K_S.gguf",
            n_gpu_layers=30,
	        n_ctx=15000, #15000
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
        self.max_tokens=2048
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

    def getReason(self, reasons_list, probability):
        prob_percent = round(probability * 100, 2)
        reasons_text = "\n".join([f"- {r}" for r in reasons_list])
        system_content = "你是一個冷酷的資安系統API，只負責輸出最終的報告文字。絕對禁止輸出任何思考過程、分析步驟、或『好的』、『首先』等對話用語。"
        if prob_percent < 30:
            tone_instruction = "該網站目前看來相對安全。請以安心、客觀的語氣解釋原因，告訴使用者可以放心瀏覽。"
        elif prob_percent < 70:
            tone_instruction = "該網站存在部分可疑特徵，屬於中等風險。請提醒使用者保持警覺，不要隨意輸入密碼。"
        else:
            tone_instruction = "該網站具有極高的釣魚風險！請以強烈警告的語氣，強烈建議使用者切勿輸入任何資料。"
        prompt = f"""
        請根據以下檢測數據，寫出約 100 字的繁體中文最終評估結論。

        【檢測數據】
        釣魚機率：{prob_percent}%
        特徵分析：
        {reasons_text}

        【寫作指示】
        1. {tone_instruction}
        2. 直接給出結論，絕對不要包含「好的」、「首先」等對話用語。
        """
        try:
            response = self.model.create_chat_completion(
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=self.temperature,
                )
            raw_text = response["choices"][0]["message"]["content"]
            cleaned_text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()
            return cleaned_text
        except Exception as e:
            print('理由生成錯誤')
            return None

class FeatureExtractor:
    def __init__(self):
        self.url_extractor = None
        self.html_extractor = None
        self.ai_extractor = None
        self.llm = QwenLLM()

    def get_URL_Feature(self, url):
        results = []
        features = {}
        word_split_pattern = re.compile(r'[^a-zA-Z0-9]+')
        try:
            parsed_url = urlparse(url)
            scheme = parsed_url.scheme
            hostname = parsed_url.hostname if parsed_url.hostname else ''
            path = parsed_url.path
            query = parsed_url.query
            fragment = parsed_url.fragment

            # 1. length_url (URL 長度)
            features['length_url'] = len(url)

            # 2. length_hostname (hostname 長度)
            features['length_hostname'] = len(hostname)

            # 3. ip (檢查 hostname 是否為 IP 地址)
            features['ip'] = 0
            if hostname:
                try:
                    ipaddress.ip_address(hostname)
                    features['ip'] = 1
                except ValueError:
                    pass # 不是有效的 IP 地址

            # 4. nb_dots (點號數量)
            features['nb_dots'] = hostname.count('.')

            # 5. nb_hyphens (連字號數量)
            features['nb_hyphens'] = url.count('-')

            # 6. nb_at (@ 符號數量)
            features['nb_at'] = url.count('@')

            # 7. nb_qm (問號數量)
            features['nb_qm'] = url.count('?')

            # 8. nb_and (& 符號數量)
            features['nb_and'] = url.count('&')

            # 9. nb_or (| 符號數量) - 較少見，但仍檢查
            features['nb_or'] = url.count('|')

            # 10. nb_eq (= 符號數量)
            features['nb_eq'] = url.count('=')

            # 11. nb_underscore (_ 符號數量)
            features['nb_underscore'] = url.count('_')

            # 12. nb_tilde (~ 符號數量)
            features['nb_tilde'] = url.count('~')

            # 13. nb_percent (% 符號數量)
            features['nb_percent'] = url.count('%')

            # 14. nb_slash (/ 符號數量)
            features['nb_slash'] = url.count('/')

            # 15. nb_star (* 符號數量)
            features['nb_star'] = url.count('*')

            # 16. nb_colon (: 符號數量)
            features['nb_colon'] = url.count(':')

            # 17. nb_comma (, 符號數量)
            features['nb_comma'] = url.count(',')

            # 18. nb_semicolumn (; 符號數量)
            features['nb_semicolumn'] = url.count(';')

            # 19. nb_dollar ($ 符號數量)
            features['nb_dollar'] = url.count('$')

            # 20. nb_space (空格數量) - 通常 URL 不應該有空格，但為了魯棒性仍檢查
            features['nb_space'] = url.count(' ')

            # 21. nb_www (檢查是否有 "www")
            features['nb_www'] = 1 if 'www' in hostname.lower() else 0

            # 22. nb_com (檢查是否有 ".com") - 這裡只檢查 hostname
            features['nb_com'] = 1 if '.com' in hostname.lower() else 0

            # 23. nb_dslash (檢查是否有 "//" 且不在協議部分)
            features['nb_dslash'] = 1 if '//' in path + query + fragment else 0

            # 24. http_in_path (檢查路徑中是否有 "http" 或 "https")
            features['http_in_path'] = 1 if re.search(r'http[s]?://', path + query + fragment, re.IGNORECASE) else 0

            # 25. https_token (檢查是否為 HTTPS)
            features['https_token'] = 1 if scheme == 'https' else 0

            # 26. ratio_digits_url (URL 中數字的比例)
            digits_in_url = sum(c.isdigit() for c in url)
            features['ratio_digits_url'] = digits_in_url / len(url) if len(url) > 0 else 0

            # 27. ratio_digits_host (hostname 中數字的比例)
            digits_in_host = sum(c.isdigit() for c in hostname)
            features['ratio_digits_host'] = digits_in_host / len(hostname) if len(hostname) > 0 else 0

            # 28. punycode (檢查是否為 Punycode 編碼)
            features['punycode'] = 1 if hostname.startswith('xn--') else 0

            # 29. port (檢查是否有指定 Port)
            features['port'] = 1 if parsed_url.port else 0

            # 30. tld_in_path (頂級域名是否出現在路徑中)
            # 這裡只做簡單的泛化判斷，更精確需要完整 TLD 列表
            # 獲取 hostname 的 TLD (簡單提取最後一個點之後的部分)
            tld = hostname.split('.')[-1] if '.' in hostname else ''
            features['tld_in_path'] = 1 if tld and tld in path.lower() else 0

            # 31. tld_in_subdomain (頂級域名是否出現在子域名中)
            # 這裡我們假設子域名是 hostname 中 TLD 之前的部分
            subdomains = hostname.split('.')[:-1] if '.' in hostname else []
            features['tld_in_subdomain'] = 0
            if tld:
                for sub in subdomains:
                    if tld in sub.lower():
                        features['tld_in_subdomain'] = 1
                        break

            # 33. nb_subdomains (子域名數量)
            # 簡單計算點號數量 - 1 (假設 TLD 是一個點，IP 地址例外)
            if features['ip'] == 1: # IP 地址沒有子域名概念
                features['nb_subdomains'] = 0
            elif hostname:
                parts = hostname.split('.')
                features['nb_subdomains'] = hostname.count('.') # 這會包含 TLD 的點，後面再調整
                if hostname.count('.') >= 1: #至少有一個點才可能有子域名
                    features['nb_subdomains'] = hostname.count('.') - 1 # 減去 TLD 的點
                    if 'www' in parts[0].lower(): # 如果第一個是www，再減1
                        features['nb_subdomains'] -= 1
                    features['nb_subdomains'] = max(0, features['nb_subdomains']) # 確保不為負
            else:
                features['nb_subdomains'] = 0

            # 32. abnormal_subdomain (子域名是否異常 - 例如多個子域名，或看起來隨機的子域名)
            # 這裡做一個簡單的判斷：如果子域名數量多於2個，且包含非常規字符
            features['abnormal_subdomain'] = 0
            if features['nb_subdomains'] > 2: # 先計算 nb_subdomains
                # 可以擴展為檢查子域名中的隨機性或特殊字符
                pass

            # 34. prefix_suffix (檢查域名是否有前綴或後綴符號，如 '-')
            # 例如: google-search.com
            features['prefix_suffix'] = 0
            if hostname:
                # 檢查 hostname 本身是否包含 `-` 且不在開頭或結尾
                if '-' in hostname and not hostname.startswith('-') and not hostname.endswith('-'):
                    features['prefix_suffix'] = 1

            # 35. path_extension (檢查路徑中是否有檔案副檔名)
            features['path_extension'] = 0
            if path:
                # 查找最後一個點，並確保其後有至少一個非斜線字符
                # 且點不在路徑的開頭或結尾
                match = re.search(r'\.([a-zA-Z0-9]+)$', path)
                if match:
                    features['path_extension'] = 1

            # 36. length_words_raw: URL 中所有單詞的總長度。
            all_url_words = [word for word in word_split_pattern.split(url) if word]
            features['length_words_raw'] = sum(len(word) for word in all_url_words)

            # 37. char_repeat: URL 中是否有重複字元序列。(例如 "aa", "bbb")
            features['char_repeat'] = 0
            if re.search(r'(.)\1{1,}', url): 
                features['char_repeat'] = 1

            # 提取 hostname 和 path 中的單詞
            hostname_words = [word for word in word_split_pattern.split(hostname) if word]
            # 將 path, query, fragment 合併後再分割
            path_query_fragment = path + query + fragment
            path_words = [word for word in word_split_pattern.split(path_query_fragment) if word]

            # 38. shortest_word_host: 主機名稱中最短單詞的長度。
            features['shortest_word_host'] = min(len(word) for word in hostname_words) if hostname_words else 0

            # 39. shortest_word_path: 路徑中最短單詞的長度。
            features['shortest_word_path'] = min(len(word) for word in path_words) if path_words else 0

            # 40. longest_words_raw: URL 中最長單詞的長度。
            features['longest_words_raw'] = max(len(word) for word in all_url_words) if all_url_words else 0

            # 41. longest_word_host: 主機名稱中最長單詞的長度。
            features['longest_word_host'] = max(len(word) for word in hostname_words) if hostname_words else 0

            # 42. longest_word_path: 路徑中最長單詞的長度。
            features['longest_word_path'] = max(len(word) for word in path_words) if path_words else 0

            # 43. avg_words_raw: URL 中單詞的平均長度。
            features['avg_words_raw'] = float(features['length_words_raw']) / len(all_url_words) if all_url_words else 0.0

            # 44. avg_word_host: 主機名稱中單詞的平均長度。
            features['avg_word_host'] = float(sum(len(word) for word in hostname_words)) / len(hostname_words) if hostname_words else 0.0

            # 45. avg_word_path: 路徑中單詞的平均長度。
            features['avg_word_path'] = float(sum(len(word) for word in path_words)) / len(path_words) if path_words else 0.0

        except Exception as e:
            # 處理解析 URL 時可能發生的錯誤
            print(f"處理 URL '{url}' 時發生錯誤: {e}")
            return None

        results.append(features)
        return pd.DataFrame(results)

    def get_HTMLStructure_Feature(self, url, html):
        if html and len(html.strip())>100:
            not_found_keywords = [
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
            if sum(1 for keyword in not_found_keywords if keyword in html.lower()) >=2:
                print('網頁找不到')
                return None
            html_feature_columns = [
            'phish_hints', 'domain_in_brand', 'nb_hyperlinks', 'ratio_intHyperlinks',
            'ratio_extHyperlinks', 'ratio_extRedirection', 'ratio_extErrors',
            'external_favicon', 'links_in_tags', 'ratio_extMedia', 'safe_anchor',
            'empty_title', 'domain_in_title', 'domain_with_copyright',
            'has_meta_refresh', 'has_js_redirect'
            ]
            results=[]
            features={}
            try:
                for col in html_feature_columns:
                    features[col] = np.nan
                soup = BeautifulSoup(html, 'html.parser')
                parsed_url = urlparse(url)
                base_domain = parsed_url.netloc.split(':')[0]
                if base_domain.startswith('www.'):
                    base_domain = base_domain[4:]
                redirect_keywords = [
                    "window.location.href",
                    "location.href",
                    "location.assign",
                    "location.replace",
                    "window.navigate"
                ]
                # 15. 偵測 meta 轉向
                meta_refresh_tag = soup.find('meta', attrs={'http-equiv': lambda x: x and x.lower() == 'refresh'})
                if meta_refresh_tag:
                    content = meta_refresh_tag.get("content", "")
                    features['has_meta_refresh'] = 1.0 if "url=" in content.lower() else 0.0  # 確認是 redirect，不是單純 reload
                else:
                    features['has_meta_refresh'] = 0.0

                # 16. 偵測 JavaScript 轉向 (來自 get_html_content 的返回值)
                features['has_js_redirect'] = 1.0 if soup.find("script", string=lambda s: any(k in s for k in redirect_keywords) if s else False) else 0.0

                # --- 1. phish_hints: HTML 內容中是否存在常見的釣魚提示詞語 ---
                phish_keywords = ['login', 'signin', 'account update', 'verify account',
                                    'security alert', 'password', 'bank', 'paypal', 'credit card',
                                    '緊急', '驗證', '登入', '帳戶更新', '安全警告', '密碼']
                text_content = soup.get_text().lower()
                features['phish_hints'] = 1 if any(kw in text_content for kw in phish_keywords) else 0.0

                # --- 2. domain_in_brand: 網站內容中提及的品牌名稱是否與域名一致 ---
                brand_match = 0
                domain_parts = base_domain.split('.')
                # 改進域名提取邏輯：處理多級域名
                if len(domain_parts) >= 2:
                    # 對於常見的頂級域名，取倒數第二個部分
                    tld = domain_parts[-1]
                    if tld in ['com', 'org', 'net', 'edu', 'gov', 'mil']:
                        core_domain = domain_parts[-2]
                    else:
                        # 對於其他域名，取倒數第三個部分（如果存在）
                        core_domain = domain_parts[-3] if len(domain_parts) >= 3 else domain_parts[-2]
                else:
                    core_domain = domain_parts[0]
                title_tag = soup.find('title')
                if title_tag and core_domain in title_tag.get_text().lower():
                    brand_match = 1
                elif soup.find('meta', attrs={'name': 'description'}) and core_domain in soup.find('meta', attrs={'name': 'description'})['content'].lower():
                    brand_match = 1
                features['domain_in_brand'] = brand_match

                # --- 3. nb_hyperlinks: 網頁中超連結的總數 ---
                all_links = soup.find_all('a', href=True)
                features['nb_hyperlinks'] = len(all_links)

                # --- 4. ratio_intHyperlinks: 內部超連結的比例 ---
                # --- 5. ratio_extHyperlinks: 外部超連結的比例 ---
                internal_links = 0
                external_links = 0
                for link_tag in all_links:
                    href = link_tag['href']
                    full_url = urljoin(url, href)
                    linked_domain = urlparse(full_url).netloc
                    if linked_domain == parsed_url.netloc:
                        internal_links += 1
                    else:
                        external_links += 1
                total_links_calc = internal_links + external_links
                features['ratio_intHyperlinks'] = internal_links / total_links_calc if total_links_calc > 0 else 0.0
                features['ratio_extHyperlinks'] = external_links / total_links_calc if total_links_calc > 0 else 0.0

                # --- 6. ratio_extRedirection (外部重新導向的比例) ---
                redirect_count = 0
                for link_tag in all_links:
                    href = link_tag['href']
                    if href.startswith('#'):
                        continue
                    full_url = urljoin(url, href)
                    linked_parsed = urlparse(full_url)
                    linked_domain = linked_parsed.netloc
                    is_external = (linked_domain != parsed_url.netloc)
                    if is_external:
                        if link_tag.get('onclick') and 'window.location' in link_tag.get('onclick', ''):
                            redirect_count += 1
                        elif link_tag.get('target') == '_blank' and 'redirect' in link_tag.get_text().lower():
                            redirect_count += 1
                features['ratio_extRedirection'] = redirect_count / len(all_links) if all_links else 0.0

                # --- 7. ratio_extErrors (外部連結中返回錯誤的比例) ---
                error_count = 0
                for link_tag in all_links:
                    href = link_tag['href']
                    if href.startswith('#'):
                        continue
                    full_url = urljoin(url, href)
                    linked_parsed = urlparse(full_url)
                    linked_domain = linked_parsed.netloc
                    is_external = (linked_domain != parsed_url.netloc)
                    if is_external:
                        if 'error' in full_url.lower() or '404' in full_url or 'notfound' in full_url.lower():
                            error_count += 1
                        elif not linked_domain or linked_domain == '':
                            error_count += 1
                features['ratio_extErrors'] = error_count / len(all_links) if all_links else 0.0

                # --- 8. external_favicon: 網站是否使用來自外部域名的 Favicon ---
                favicon_link = soup.find('link', rel=lambda x: x and 'icon' in x.lower())
                features['external_favicon'] = 0.0
                if favicon_link and 'href' in favicon_link.attrs:
                    favicon_url = urljoin(url, favicon_link['href'])
                    favicon_domain = urlparse(favicon_url).netloc
                    if favicon_domain != parsed_url.netloc:
                        features['external_favicon'] = 1.0
                
                # --- 9. links_in_tags: 特定 HTML 標籤（如 <a>、<script>）中連結的數量 ---
                total_links_in_tags = 0
                for tag in soup.find_all(['a', 'script', 'img', 'link', 'iframe', 'form']):
                    if 'href' in tag.attrs:
                        total_links_in_tags += 1
                    if 'src' in tag.attrs:
                        total_links_in_tags += 1
                    if tag.name == 'form' and 'action' in tag.attrs:
                        total_links_in_tags += 1
                features['links_in_tags'] = total_links_in_tags

                # --- 10. ratio_extMedia: 外部媒體（圖片、音頻、視頻）的比例 ---
                media_tags = soup.find_all(['img', 'audio', 'video', 'source'])
                total_media = len(media_tags)
                external_media = 0
                for media_tag in media_tags:
                    src = media_tag.get('src') or media_tag.get('href')
                    if src:
                        media_url = urljoin(url, src)
                        media_domain = urlparse(media_url).netloc
                        if media_domain != parsed_url.netloc:
                            external_media += 1
                features['ratio_extMedia'] = external_media / total_media if total_media > 0 else 0.0

                # --- 11. safe_anchor: 錨點連結是否安全（例如避免指向可疑外部網站） ---
                features['safe_anchor'] = 1.0
                suspicious_keywords = ['bit.ly', 'tinyurl', 'goo.gl', 't.co', 'fb.me', 'is.gd']
                for link_tag in all_links:
                    href = link_tag['href']
                    if href.startswith('#'):
                        continue
                    full_url = urljoin(url, href)
                    linked_parsed = urlparse(full_url)
                    linked_domain = linked_parsed.netloc
                    is_external = (linked_domain != parsed_url.netloc)
                    if is_external:
                        # 檢查是否為IP地址
                        try:
                            ipaddress.ip_address(linked_domain)
                            features['safe_anchor'] = 0.0
                            break
                        except ValueError:
                            pass
                        # 檢查協議是否安全
                        if linked_parsed.scheme not in ['http', 'https', '']:
                            features['safe_anchor'] = 0.0
                            break
                        # 檢查是否為可疑的短網址服務
                        if any(keyword in linked_domain.lower() for keyword in suspicious_keywords):
                            features['safe_anchor'] = 0.0
                            break
                
                # --- 12. empty_title: 網頁標題是否為空 ---
                features['empty_title'] = 1.0 if not (soup.title and soup.title.string and soup.title.string.strip()) else 0.0

                # --- 13. domain_in_title: 域名是否出現在網頁標題中 ---
                features['domain_in_title'] = 0.0
                if soup.title and soup.title.string:
                    if base_domain in soup.title.string.lower():
                        features['domain_in_title'] = 1.0

                # --- 14. domain_with_copyright: 網站的版權資訊中是否包含域名 ---
                features['domain_with_copyright'] = 0.0
                # 檢查版權文本
                copyright_text = soup.find(text=re.compile(r'©|copyright', re.IGNORECASE))
                if copyright_text and base_domain in copyright_text.lower():
                    features['domain_with_copyright'] = 1.0
                # 檢查footer區域
                footer_tags = soup.find_all(['div', 'footer'], class_=re.compile(r'footer|copyright', re.IGNORECASE))
                for footer in footer_tags:
                    if base_domain in footer.get_text().lower():
                        features['domain_with_copyright'] = 1.0
                        break
                # 檢查所有包含版權相關文字的標籤
                copyright_tags = soup.find_all(text=re.compile(r'©|copyright|all rights reserved', re.IGNORECASE))
                for tag in copyright_tags:
                    if base_domain in tag.lower():
                        features['domain_with_copyright'] = 1.0
                        break
        
            except Exception as e:
                print(f"處理 HTML '{html}' 時發生錯誤: {e}")
                return None
            results.append(features)
            return pd.DataFrame(results)
        else:
            print('html過短或為空')
            return None

    def get_HTMLContent_AI_Feature(self, text):
        if self.is_not_found_page(text):
            print('網頁不存在')
            return None
        try:
            response = self.llm.ask(text)
            if not response:
                print('AI回復為空')
                return None
            if response.startswith('Error:'):
                print(f'AI回復錯誤:{response}')
                return None
            json_data = json.loads(response)
            results=[]
            features={}
            features['creates_urgency'] = json_data['creates_urgency']
            features['uses_threats'] = json_data['uses_threats']
            features['requests_sensitive_info'] = json_data['requests_sensitive_info']
            features['offers_unrealistic_rewards'] = json_data['offers_unrealistic_rewards']
            features['has_spelling_grammar_errors'] = json_data['has_spelling_grammar_errors']
            features['impersonated_brand'] = json_data['impersonated_brand']
            features['has_valid_copyright_year'] = json_data['has_valid_copyright_year']
            features['is_content_login_focused'] = json_data['is_content_login_focused']
            features['has_rich_navigation'] = json_data['has_rich_navigation']
            features['has_physical_address'] = json_data['has_physical_address']
            features['has_phone_number'] = json_data['has_phone_number']
            features['content_consistency_score'] = json_data['content_consistency_score']
            features['language_professionalism_score'] = json_data['language_professionalism_score']
            features['overall_phishing_likelihood_score'] = json_data['overall_phishing_likelihood_score']
            features['text_length'] = len(str(text))
            results.append(features)
            return pd.DataFrame(results)

        except Exception as e:
            print(f'AI特徵獲取時出錯:{e}')

        
    
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

    def getReason(self, url_feature, html_feature, ai_feature, prob):
        reasons_list = self.get_reason_list(url_feature, html_feature, ai_feature)
        return self.llm.getReason(reasons_list, prob)

    def get_reason_list(self, url_feature, html_feature, ai_feature):
        reasons = []

        # 確保資料存在，並轉為字典格式方便讀取 (假設傳入的是 Pandas DataFrame)
        url_data = url_feature.iloc[0].to_dict() if url_feature is not None and not url_feature.empty else {}
        html_data = html_feature.iloc[0].to_dict() if html_feature is not None and not html_feature.empty else {}
        ai_data = ai_feature.iloc[0].to_dict() if ai_feature is not None and not ai_feature.empty else {}

        # 檢查是否使用 IP 隱藏真實網域
        if url_data.get('ip') == 1:
            reasons.append("【網域異常】網址直接使用 IP 位址，這通常是為了規避網域審查的免洗惡意網站。")
        
        # 檢查 Punycode 同形異義字攻擊
        if url_data.get('punycode') == 1:
            reasons.append("【網域異常】網址使用了 Punycode (xn--) 編碼，企圖偽裝成正常字母以混淆視覺 (同形異義字攻擊)。")
        
        # 檢查 @ 符號混淆 (瀏覽器會忽略 @ 前面的字串)
        if url_data.get('nb_at', 0) > 0:
            reasons.append("【網域異常】網址包含 '@' 符號，駭客常利用此特性隱藏真實的連線目標。")
            
        # 檢查子網域氾濫
        if url_data.get('nb_subdomains', 0) >= 3:
            reasons.append("【網域混淆】網址包含異常數量的子網域，企圖構造出極長的網址來掩蓋真實主機名稱。")

        # 檢查連字號氾濫或前後綴 (如 paypal-update.com)
        if url_data.get('prefix_suffix') == 1 or url_data.get('nb_hyphens', 0) >= 2:
            reasons.append("【網域混淆】網域包含可疑的連字號前後綴，企圖偽造官方品牌網域。")

        # 檢查是否有自動跳轉
        if html_data.get('has_js_redirect') == 1.0 or html_data.get('has_meta_refresh') == 1.0:
            reasons.append("【結構異常】網頁原始碼藏有自動跳轉指令，企圖在您不注意時導向隱蔽的惡意終端頁面。")
            
        # 檢查超連結外部比例 (釣魚網站通常把連結指回真實官方網站以降低戒心)
        if html_data.get('ratio_extHyperlinks', 0) > 0.6:
            reasons.append("【結構異常】網頁內含有大量指向外部網域的超連結，缺乏正規網站應有的內部連結架構。")

        # 檢查標題與網域一致性
        if html_data.get('empty_title') == 1.0 or html_data.get('domain_in_title') == 0.0:
            reasons.append("【身分不符】網頁標題空白或與所在網域名稱毫無關聯，缺乏品牌一致性。")
            
        # 檢查釣魚暗示詞
        if html_data.get('phish_hints') == 1.0:
            reasons.append("【高危險特徵】網頁原始碼中發現大量如 login、verify 等常見的釣魚誘餌關鍵字。")

        # 檢查品牌偽冒
        impersonated = ai_data.get('impersonated_brand', str)
        if isinstance(impersonated, str) and impersonated.lower() not in ['none', 'null', '']:
            reasons.append(f"【品牌冒用】AI 語意分析發現該網頁企圖偽裝成知名品牌【{impersonated}】。")

        # 檢查威脅與急迫性
        if ai_data.get('creates_urgency') == True or ai_data.get('uses_threats') == True:
            reasons.append("【社交工程】內文使用「急迫性」或「威脅性」話術 (如帳號即將凍結)，企圖迫使您倉促行動。")

        # 檢查敏感資訊索取
        if ai_data.get('requests_sensitive_info') == True:
            reasons.append("【高危險行為】系統偵測到網頁正試圖誘導您輸入密碼、信用卡號等機密資訊。")

        # 檢查誘餌/不切實際的獎勵
        if ai_data.get('offers_unrealistic_rewards') == True:
            reasons.append("【社交工程】內容提供不切實際的獎勵或優惠，利用貪心心理進行誘騙。")
            
        # 檢查專業度與文法
        if ai_data.get('has_spelling_grammar_errors') == True:
            reasons.append("【專業度低】網頁內容存在明顯的拼寫或文法錯誤，這在嚴謹的官方網站中極少發生。")

        # 檢查聯絡資訊缺失
        if ai_data.get('has_physical_address') == False and ai_data.get('has_phone_number') == False:
            reasons.append("【來源可疑】網站缺乏實體地址與聯絡電話等正規商業網站應具備的聯絡資訊。")

        # ==========================================
        # 總結收斂
        # ==========================================
        if len(reasons) == 0:
            reasons.append("✅ 系統初步分析未發現明顯的釣魚網站特徵。")

        return reasons