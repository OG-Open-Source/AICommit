import requests
import json
import os
from PyQt5.QtCore import QSettings

class AIService:
    """AI 服務類，用於與不同的 AI 服務提供商進行交互"""
    
    # 預設端點
    DEFAULT_ENDPOINTS = {
        "OpenAI": "https://api.openai.com/v1",
        "Anthropic Claude": "https://api.anthropic.com/v1",
        "Google Gemini": "https://generativelanguage.googleapis.com/v1beta",
        "Mistral AI": "https://api.mistral.ai/v1",
        "Cohere": "https://api.cohere.ai/v1",
        "自定義": None  # 需要用戶指定
    }
    
    # 是否需要端點
    NEEDS_ENDPOINT = {
        "OpenAI": False,
        "Anthropic Claude": False,
        "Google Gemini": False,
        "Mistral AI": False,
        "Cohere": False,
        "自定義": True
    }
    
    # 是否使用 OpenAI 兼容 API
    OPENAI_COMPATIBLE = {
        "OpenAI": True,
        "Anthropic Claude": False,
        "Google Gemini": False,
        "Mistral AI": False,
        "Cohere": False,
        "自定義": True
    }
    
    # 通用提示詞設定
# 修改 SYSTEM_PROMPT 和 USER_PROMPT_TEMPLATE 變量

    SYSTEM_PROMPT = "You are a commit message assistant that generates professional GitHub commit messages conforming to the Keep A Changelog guidelines."

    USER_PROMPT_TEMPLATE = """Please generate a GitHub Commit Message that conforms to the Keep A Changelog guidelines based on the following code changes.

**Code Changes:**  
```diff
{diff_content}
```

**Output Format:**  
- Directly output the final Commit Message without any interaction.  
- Use the Keep A Changelog categories, including `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, and `Security`. Automatically categorize the changes based on the content of the diff; omit any categories that are not applicable.  
- Do not include the diff itself; only describe the changes made.  
- Provide concise and professional change descriptions to ensure readability and consistency.
- Pay special attention to any "# @Status:" comments in the code, as they indicate the developer's intention for the changes.

Please generate the Commit Message according to the above requirements and output it directly without interacting further."""
    
    # 測試連接的提示詞
    TEST_SYSTEM_PROMPT = "You are a test assistant."
    TEST_USER_PROMPT = "Testing. Just say `Hi` and nothing else."
    
    def __init__(self):
        self.settings = QSettings("OG-Open-Source", "CommitLogAssistant")
        self.load_settings()
    
    def load_settings(self):
        """從設定中載入 AI 服務設定"""
        self.provider = self.settings.value("ai/provider", "OpenAI")
        self.api_key = self.settings.value("ai/api_key", "")
        
        # 獲取端點，如果沒有設定則使用默認端點
        custom_endpoint = self.settings.value("ai/endpoint", "")
        if custom_endpoint:
            self.endpoint = custom_endpoint
        elif self.provider in self.DEFAULT_ENDPOINTS:
            self.endpoint = self.DEFAULT_ENDPOINTS[self.provider]
        else:
            self.endpoint = ""
        
        self.model = self.settings.value("ai/model", "")
        self.temperature = float(self.settings.value("ai/temperature", 0.7))
        self.max_tokens = int(self.settings.value("ai/max_tokens", 1000))
    
    def get_commit_content(self, diff_content):
        """根據代碼差異同時獲取提交摘要和描述"""
        # 根據不同的提供商使用不同的 API 調用方式
        if self.OPENAI_COMPATIBLE.get(self.provider, False):
            return self._openai_compatible_content_request(diff_content)
        elif self.provider == "Anthropic Claude":
            return self._anthropic_content_request(diff_content)
        elif self.provider == "Google Gemini":
            return self._gemini_content_request(diff_content)
        elif self.provider == "Cohere":
            return self._cohere_content_request(diff_content)
        else:
            return {"error": f"不支持的 AI 提供商: {self.provider}"}
    
    def _openai_compatible_content_request(self, diff_content):
        """使用 OpenAI 兼容 API 發送請求，同時獲取摘要和描述"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 修改提示詞，要求生成純摘要和描述
        content_prompt = """Please analyze the following code changes and generate both a summary and a detailed description for a commit message.

**Code Changes:**  
```diff
{diff_content}
```

**Output Format:**  
Return a JSON object with the following structure:
```json
{{
  "type": "Added|Changed|Deprecated|Removed|Fixed|Security",
  "scope": "optional scope",
  "summary": "A concise one-line summary of the changes without any prefix",
  "description": "A more detailed description of the changes, explaining what was done and why"
}}
```

- Pay special attention to any "# @Status:" comments in the code, as they indicate the developer's intention for the changes.
- Choose the most appropriate type based on the nature of the changes.
- The scope is optional and can be omitted if not applicable.
- The summary should be brief (under 50 characters if possible) and to the point.
- The summary should NOT include the type or scope prefix (e.g., just "Added support for..." instead of "Added: Added support for...").
- The description should provide more context and details about the changes.

Please generate the response according to the above requirements and output it directly as a valid JSON object."""
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": content_prompt.format(diff_content=diff_content)}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        try:
            response = requests.post(f"{self.endpoint}/chat/completions", headers=headers, json=data)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if "choices" not in result or len(result["choices"]) == 0:
                        return {"error": f"API 回應缺少 choices 欄位: {json.dumps(result)}"}
                    
                    if "message" not in result["choices"][0]:
                        return {"error": f"API 回應缺少 message 欄位: {json.dumps(result)}"}
                    
                    # 解析 AI 回應中的 JSON
                    content = result["choices"][0]["message"]["content"].strip()
                    
                    # 嘗試提取 JSON 部分
                    try:
                        # 首先嘗試直接解析整個內容
                        commit_data = json.loads(content)
                        return {
                            "type": commit_data.get("type", "Changed"),
                            "scope": commit_data.get("scope", ""),
                            "summary": commit_data.get("summary", ""),
                            "description": commit_data.get("description", "")
                        }
                    except json.JSONDecodeError:
                        # 如果直接解析失敗，嘗試從文本中提取 JSON 部分
                        import re
                        json_match = re.search(r'```json\s*({.*?})\s*```', content, re.DOTALL)
                        if json_match:
                            try:
                                commit_data = json.loads(json_match.group(1))
                                return {
                                    "type": commit_data.get("type", "Changed"),
                                    "scope": commit_data.get("scope", ""),
                                    "summary": commit_data.get("summary", ""),
                                    "description": commit_data.get("description", "")
                                }
                            except json.JSONDecodeError:
                                pass
                        
                        # 如果仍然無法解析 JSON，嘗試從文本中提取信息
                        return self._extract_commit_info_from_text(content)
                    
                except Exception as e:
                    return {"error": f"解析 API 回應時出錯: {str(e)}, 回應內容: {response.text[:200]}..."}
            else:
                return {"error": f"API 錯誤: {response.status_code} - {response.text}"}
        except Exception as e:
            return {"error": f"請求 API 時出錯: {str(e)}"}
    
    def _extract_commit_info_from_text(self, text):
        """從文本中提取提交信息"""
        # 嘗試使用正則表達式提取信息
        import re
        
        # 嘗試找到類型和摘要
        type_summary_match = re.search(r"(Added|Changed|Deprecated|Removed|Fixed|Security)(\s*\[([^\]]+)\])?:\s*(.+)", text, re.IGNORECASE | re.MULTILINE)
        
        if type_summary_match:
            commit_type = type_summary_match.group(1)
            commit_scope = type_summary_match.group(3) or ""
            summary = type_summary_match.group(4).strip()
            
            # 嘗試找到描述（假設描述在摘要之後的段落中）
            description_parts = text.split(summary, 1)
            description = description_parts[1].strip() if len(description_parts) > 1 else ""
            
            return {
                "type": commit_type,
                "scope": commit_scope,
                "summary": summary,
                "description": description
            }
        else:
            # 如果無法提取結構化信息，將整個文本作為摘要返回
            return {
                "type": "Changed",
                "scope": "",
                "summary": text.split("\n")[0] if text else "",
                "description": "\n".join(text.split("\n")[1:]) if text and "\n" in text else ""
            }
    
    def _anthropic_content_request(self, diff_content):
        """使用 Anthropic API 發送請求"""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": self.USER_PROMPT_TEMPLATE.format(diff_content=diff_content)}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        try:
            response = requests.post(f"{self.endpoint}/messages", headers=headers, json=data)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if "content" not in result or len(result["content"]) == 0:
                        return {"error": f"API 回應缺少 content 欄位: {json.dumps(result)}"}
                    
                    return {"suggestion": result["content"][0]["text"]}
                except Exception as e:
                    return {"error": f"解析 API 回應時出錯: {str(e)}, 回應內容: {response.text[:200]}..."}
            else:
                return {"error": f"API 錯誤: {response.status_code} - {response.text}"}
        except Exception as e:
            return {"error": f"請求 Anthropic API 時出錯: {str(e)}"}
    
    def _gemini_content_request(self, diff_content):
        """使用 Google Gemini API 發送請求"""
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "contents": [
                {"role": "user", "parts": [{"text": self.USER_PROMPT_TEMPLATE.format(diff_content=diff_content)}]}
            ],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens
            }
        }
        
        try:
            response = requests.post(
                f"{self.endpoint}/models/{self.model}:generateContent?key={self.api_key}", 
                headers=headers, 
                json=data
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if "candidates" not in result or len(result["candidates"]) == 0:
                        return {"error": f"API 回應缺少 candidates 欄位: {json.dumps(result)}"}
                    
                    if "content" not in result["candidates"][0]:
                        return {"error": f"API 回應缺少 content 欄位: {json.dumps(result)}"}
                    
                    if "parts" not in result["candidates"][0]["content"] or len(result["candidates"][0]["content"]["parts"]) == 0:
                        return {"error": f"API 回應缺少 parts 欄位: {json.dumps(result)}"}
                    
                    return {"suggestion": result["candidates"][0]["content"]["parts"][0]["text"]}
                except Exception as e:
                    return {"error": f"解析 API 回應時出錯: {str(e)}, 回應內容: {response.text[:200]}..."}
            else:
                # 處理常見的 Gemini API 錯誤
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_message = error_data["error"].get("message", "未知錯誤")
                        error_code = error_data["error"].get("code", 0)
                        error_status = error_data["error"].get("status", "")
                        
                        # 處理配額超出錯誤
                        if error_code == 429 or "quota" in error_message.lower():
                            return {"error": f"Google Gemini API 配額已超出。請稍後再試或增加配額限制。\n詳細信息: {error_message}"}
                        
                        return {"error": f"Google Gemini API 錯誤 ({error_code}): {error_message}\n狀態: {error_status}"}
                    
                    return {"error": f"API 錯誤: {response.status_code} - {response.text}"}
                except Exception:
                    return {"error": f"API 錯誤: {response.status_code} - {response.text}"}
        except Exception as e:
            return {"error": f"請求 Google Gemini API 時出錯: {str(e)}"}
    
    def _cohere_content_request(self, diff_content):
        """使用 Cohere API 發送請求"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model,
            "message": self.USER_PROMPT_TEMPLATE.format(diff_content=diff_content),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        try:
            response = requests.post(f"{self.endpoint}/chat", headers=headers, json=data)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if "text" not in result:
                        return {"error": f"API 回應缺少 text 欄位: {json.dumps(result)}"}
                    
                    return {"suggestion": result["text"]}
                except Exception as e:
                    return {"error": f"解析 API 回應時出錯: {str(e)}, 回應內容: {response.text[:200]}..."}
            else:
                return {"error": f"API 錯誤: {response.status_code} - {response.text}"}
        except Exception as e:
            return {"error": f"請求 Cohere API 時出錯: {str(e)}"}
    
    def test_connection(self):
        """測試與 AI 服務的連接"""
        try:
            # 根據不同的提供商使用不同的 API 調用方式
            if self.OPENAI_COMPATIBLE.get(self.provider, False):
                return self._test_openai_compatible()
            elif self.provider == "Anthropic Claude":
                return self._test_anthropic()
            elif self.provider == "Google Gemini":
                return self._test_gemini()
            elif self.provider == "Cohere":
                return self._test_cohere()
            else:
                return {"error": f"不支持的 AI 提供商: {self.provider}"}
        except Exception as e:
            return {"error": f"連接測試錯誤: {str(e)}"}
    
    def _test_openai_compatible(self):
        """測試 OpenAI 兼容 API 連接"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 對於自定義服務或標準 OpenAI 兼容服務，發送一個簡單的聊天請求
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.TEST_SYSTEM_PROMPT},
                {"role": "user", "content": self.TEST_USER_PROMPT}
            ],
            "max_tokens": 5,
            "temperature": 0  # 使用 0 溫度確保回應一致
        }
        
        try:
            response = requests.post(f"{self.endpoint}/chat/completions", headers=headers, json=data)
            
            if response.status_code == 200:
                return {"success": True, "response": response.json()}
            else:
                # 如果聊天請求失敗，嘗試獲取模型列表
                models_response = requests.get(f"{self.endpoint}/models", headers=headers)
                if models_response.status_code == 200:
                    return {"success": True, "response": models_response.json()}
                else:
                    return {"error": f"API 錯誤: {response.status_code} - {response.text}"}
        except Exception as e:
            return {"error": f"連接錯誤: {str(e)}"}
    
    def _test_anthropic(self):
        """測試 Anthropic API 連接"""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        # 發送簡單的消息請求
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": self.TEST_USER_PROMPT}
            ],
            "max_tokens": 5,
            "temperature": 0  # 使用 0 溫度確保回應一致
        }
        
        response = requests.post(f"{self.endpoint}/messages", headers=headers, json=data)
        
        if response.status_code == 200:
            return {"success": True, "response": response.json()}
        else:
            return {"error": f"API 錯誤: {response.status_code} - {response.text}"}
    
    def _test_gemini(self):
        """測試 Google Gemini API 連接"""
        headers = {
            "Content-Type": "application/json"
        }
        
        # 發送簡單的生成請求
        data = {
            "contents": [
                {"role": "user", "parts": [{"text": self.TEST_USER_PROMPT}]}
            ],
            "generationConfig": {
                "temperature": 0,
                "maxOutputTokens": 5
            }
        }
        
        response = requests.post(
            f"{self.endpoint}/models/{self.model}:generateContent?key={self.api_key}", 
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            return {"success": True, "response": response.json()}
        else:
            # 如果生成請求失敗，嘗試獲取模型信息
            model_response = requests.get(
                f"{self.endpoint}/models/{self.model}?key={self.api_key}", 
                headers=headers
            )
            if model_response.status_code == 200:
                return {"success": True, "response": model_response.json()}
            else:
                return {"error": f"API 錯誤: {response.status_code} - {response.text}"}
    
    def _test_cohere(self):
        """測試 Cohere API 連接"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 發送簡單的聊天請求
        data = {
            "model": self.model,
            "message": self.TEST_USER_PROMPT,
            "temperature": 0,
            "max_tokens": 5
        }
        
        response = requests.post(f"{self.endpoint}/chat", headers=headers, json=data)
        
        if response.status_code == 200:
            return {"success": True, "response": response.json()}
        else:
            # 如果聊天請求失敗，嘗試獲取模型列表
            models_response = requests.get(f"{self.endpoint}/models", headers=headers)
            if models_response.status_code == 200:
                return {"success": True, "response": models_response.json()}
            else:
                return {"error": f"API 錯誤: {response.status_code} - {response.text}"} 