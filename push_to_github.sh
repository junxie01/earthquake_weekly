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

# 1. 先把本地的修改全部暂存并提交
echo "Staging and committing local changes..."
git add .
if git diff-index --quiet HEAD --; then
    echo "No local changes to commit."
else
    git commit -m "Update: UI/Script layout optimization"
fi

# 2. 再从云端拉取 Actions 产生的新数据并自动合并（Rebase）
echo "Syncing with GitHub Actions data (pulling with rebase)..."
git pull origin main --rebase

# 3. 最后安全地推送到云端
echo "Pushing to GitHub via SSH..."
git push -u origin main

echo "Done! Your website content is now synced and updated."
