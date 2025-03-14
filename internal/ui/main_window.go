package ui

import (
	"errors"
	"github.com/OG-Open-Source/aicommit/internal/git"
	"github.com/OG-Open-Source/aicommit/internal/ai"
)

// Application 代表整個應用程序
type Application struct {
	// GUI 相關字段
	// ...
	
	Repository *git.Repository
	AiService  *ai.Service
}

// NewApplication 創建一個新的應用程序實例
func NewApplication() (*Application, error) {
	// 初始化 GUI
	// ...
	
	return &Application{
		// 初始化字段
	}, nil
}

// Run 啟動應用程序
func (a *Application) Run() {
	// 啟動 GUI 主循環
	// ...
}

// OpenRepository 打開一個存儲庫
func (a *Application) OpenRepository(path string) error {
	repo, err := git.NewRepository(path)
	if err != nil {
		return err
	}
	
	a.Repository = repo
	a.RefreshUI()
	
	return nil
}

// RefreshUI 刷新用戶界面
func (a *Application) RefreshUI() {
	// 更新 UI 元素以反映存儲庫狀態
	// ...
}

// GenerateCommitMessage 生成提交消息
func (a *Application) GenerateCommitMessage() error {
	if a.Repository == nil {
		return errors.New("未打開任何存儲庫")
	}
	
	// 獲取變更的文件
	changedFiles, err := a.Repository.GetChangedFiles()
	if err != nil {
		return err
	}
	
	// 獲取差異
	diffs := make(map[string]string)
	// 獲取每個文件的差異
	// ...
	
	// 使用 AI 服務生成提交消息
	summary, description, err := a.AiService.GenerateCommitMessage(changedFiles, diffs)
	if err != nil {
		return err
	}
	
	// 更新 UI 中的摘要和描述字段
	// ...
	
	return nil
} 