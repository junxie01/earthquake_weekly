#!/bin/bash

# 请将下面的 <YOUR_USERNAME> 替换为您的 GitHub 用户名
# 请将 <YOUR_REPO_NAME> 替换为您的 仓库名（如 earthquake-weekly）
GITHUB_USER="junxie01@gmail.com"
REPO_NAME="earthquake_weekly"

# 检查是否已初始化 git
if [ ! -d ".git" ]; then
    echo "Initializing Git repository..."
    git init
    git branch -M main
fi

# 检查远程仓库是否已关联
if ! git remote | grep -q "origin"; then
    echo "Adding remote origin..."
    git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git"
fi

echo "Staging files..."
git add .

echo "Committing changes..."
git commit -m "Update: Weekly earthquake report with Google News integration and beachball fixes"

echo "Pushing to GitHub..."
git push -u origin main

echo "Done! Please ensure GitHub Pages is enabled in Settings -> Pages."
