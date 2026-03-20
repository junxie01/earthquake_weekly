#!/bin/bash

# 您的 GitHub 用户名
GITHUB_USER="junxie01"
# 您的 仓库名
REPO_NAME="earthquake_weekly"

# 检查是否已初始化 git
if [ ! -d ".git" ]; then
    echo "Initializing Git repository..."
    git init
    git branch -M main
fi

# 检查远程仓库是否已关联，或者是否是旧的 HTTPS 地址
# 如果是 HTTPS 地址，我们将其改为 SSH 地址
if git remote -v | grep -q "https://github.com"; then
    echo "Updating remote origin to SSH..."
    git remote remove origin
    git remote add origin "git@github.com:$GITHUB_USER/$REPO_NAME.git"
elif ! git remote | grep -q "origin"; then
    echo "Adding remote origin (SSH)..."
    git remote add origin "git@github.com:$GITHUB_USER/$REPO_NAME.git"
fi

echo "Staging files..."
git add .

echo "Committing changes..."
git commit -m "Update: Switching to SSH and updating content" || echo "Nothing to commit"

echo "Pushing to GitHub via SSH..."
git push -u origin main

echo "Done! Please ensure GitHub Pages is enabled in Settings -> Pages."
