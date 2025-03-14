package git

import (
	"errors"
	"os/exec"
	"strings"
)

// Repository 表示一個 Git 存儲庫
type Repository struct {
	Path   string
	Branch string
}

// NewRepository 創建一個新的 Repository 實例
func NewRepository(path string) (*Repository, error) {
	repo := &Repository{
		Path: path,
	}
	
	// 檢查是否是一個有效的 Git 儲存庫
	if !repo.IsValid() {
		return nil, errors.New("不是有效的 Git 儲存庫")
	}
	
	// 獲取當前分支
	branch, err := repo.GetCurrentBranch()
	if err != nil {
		return nil, err
	}
	repo.Branch = branch
	
	return repo, nil
}

// IsValid 檢查路徑是否是一個有效的 Git 儲存庫
func (r *Repository) IsValid() bool {
	cmd := exec.Command("git", "-C", r.Path, "rev-parse", "--is-inside-work-tree")
	return cmd.Run() == nil
}

// GetCurrentBranch 獲取當前分支名稱
func (r *Repository) GetCurrentBranch() (string, error) {
	cmd := exec.Command("git", "-C", r.Path, "symbolic-ref", "--short", "HEAD")
	output, err := cmd.Output()
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(string(output)), nil
}

// GetChangedFiles 獲取已修改但未提交的文件列表
func (r *Repository) GetChangedFiles() ([]string, error) {
	// 實現獲取已修改文件的邏輯
	// ...
	return []string{}, nil
}

// CommitChanges 提交變更
func (r *Repository) CommitChanges(summary string, description string) error {
	// 實現提交變更的邏輯
	// ...
	return nil
} 