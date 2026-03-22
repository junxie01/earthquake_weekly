#!/bin/bash

# 您的 GitHub 用户名和仓库名
GITHUB_USER="junxie01"
REPO_NAME="earthquake_weekly"

# 检查是否已初始化 git
if [ ! -d ".git" ]; then
    echo "Initializing Git repository..."
    git init
    git branch -M main
fi

# 检查远程仓库是否已关联（确保是 SSH）
if ! git remote | grep -q "origin"; then
    echo "Adding remote origin (SSH)..."
    git remote add origin "git@github.com:$GITHUB_USER/$REPO_NAME.git"
fi

# 1. 先获取远程更新
echo "Fetching remote changes..."
git fetch origin

# 2. 暂存本地修改（避免冲突）
echo "Stashing local changes..."
git stash push -m "local changes" 2>/dev/null || echo "No local changes to stash."

# 3. 切换到远程 main 分支的最新状态
echo "Checking out latest main branch..."
git checkout main
git reset --hard origin/main

# 4. 重新应用本地修改（如果有）
if git stash list | grep -q "local changes"; then
    echo "Applying local changes..."
    git stash pop
fi

# 5. 现在添加所有修改
echo "Adding and committing changes..."
git add .

if git diff-index --quiet HEAD --; then
    echo "No changes to commit."
else
    git commit -m "Update: UI improvements and beachball generation"
fi

# 6. 推送到 GitHub
echo "Pushing to GitHub..."
git push -u origin main

echo "Done! Your website content is now synced and updated."
