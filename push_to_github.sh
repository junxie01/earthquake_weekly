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
    git remote add origin "git@github.com:$GITHUB_USER/$REPO_NAME.git"
fi

echo "Pulling latest changes from GitHub (handling Actions updates)..."
git pull origin main --rebase

echo "Staging files..."
git add .

echo "Committing changes..."
# 检查是否有内容需要提交，避免报错
if git diff-index --quiet HEAD --; then
    echo "No local changes to commit."
else
    git commit -m "Update: Weekly report stats and layout optimization"
fi

echo "Pushing to GitHub via SSH..."
git push -u origin main

echo "Done! Your website content is now synced."
