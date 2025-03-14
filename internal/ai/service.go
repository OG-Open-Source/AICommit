package ai

import (
	"bytes"
	"encoding/json"
	"errors"
	"net/http"
)

// Service 提供 AI 相關功能
type Service struct {
	ApiKey     string
	ApiEndpoint string
	Model      string
}

// NewService 創建一個新的 AI 服務實例
func NewService(apiKey, apiEndpoint, model string) *Service {
	return &Service{
		ApiKey:     apiKey,
		ApiEndpoint: apiEndpoint,
		Model:      model,
	}
}

// GenerateCommitMessage 根據文件變更生成提交消息
func (s *Service) GenerateCommitMessage(changedFiles []string, diffs map[string]string) (string, string, error) {
	if s.ApiKey == "" {
		return "", "", errors.New("API 密鑰未配置")
	}
	
	// 構建請求
	requestBody, err := json.Marshal(map[string]interface{}{
		"model": s.Model,
		"messages": []map[string]string{
			{
				"role":    "system",
				"content": "你是一個幫助開發者生成高質量 Git 提交消息的助手。",
			},
			{
				"role":    "user",
				"content": buildPromptFromChanges(changedFiles, diffs),
			},
		},
	})
	
	if err != nil {
		return "", "", err
	}
	
	// 發送請求到 AI API
	req, err := http.NewRequest("POST", s.ApiEndpoint, bytes.NewBuffer(requestBody))
	if err != nil {
		return "", "", err
	}
	
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+s.ApiKey)
	
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return "", "", err
	}
	defer resp.Body.Close()
	
	// 處理 API 響應
	// ...
	
	return "自動生成的摘要", "自動生成的描述", nil
}

// buildPromptFromChanges 從變更構建提示
func buildPromptFromChanges(changedFiles []string, diffs map[string]string) string {
	// 構建提示文本
	// ...
	return "請基於以下變更生成一個清晰簡潔的提交消息："
} 