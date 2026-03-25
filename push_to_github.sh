#!/bin/bash

# 您的 GitHub 用户名和仓库名
GITHUB_USER="junxie01"
REPO_NAME="earthquake_weekly"

# 确保 images 目录存在
mkdir -p images

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

# 2. 暂存本地修改（包括图片文件）
echo "Stashing local changes..."
git stash push -m "local changes" -u 2>/dev/null || echo "No local changes to stash."

# 3. 切换到远程 main 分支的最新状态
echo "Checking out latest main branch..."
git checkout main
git reset --hard origin/main

# 4. 重新应用本地修改（如果有）
if git stash list | grep -q "local changes"; then
    echo "Applying local changes..."
    git stash pop
fi

# 5. 确保 images 目录存在
mkdir -p images

# 6. 检测并修复 Git 冲突标记
echo "Checking for Git merge conflicts..."

# 检查常见文件中的冲突标记
CONFLICT_FILES=()
for file in script.js data.json fetch_data.py; do
    if [ -f "$file" ]; then
        if grep -q "<<<<<<<" "$file"; then
            CONFLICT_FILES+=($file)
            echo "Found conflict in $file, cleaning..."
            # 移除冲突标记，保留本地版本
            sed -i '' '/<<<<<<</,/=======/d' "$file"
            sed -i '' '/>>>>>>>.*$/d' "$file"
            echo "Cleaned conflicts in $file"
        fi
    fi
done

# 7. 现在添加所有修改（包括新的图片文件）
echo "Adding and committing changes..."
git add .

if git diff-index --quiet HEAD --; then
    echo "No changes to commit."
else
    git commit -m "Update: UI improvements and beachball generation"
fi

# 8. 推送到 GitHub
echo "Pushing to GitHub..."
git push -u origin main

echo "Done! Your website content is now synced and updated."

# 9. 显示冲突修复信息
if [ ${#CONFLICT_FILES[@]} -gt 0 ]; then
    echo "\n=== Conflict Resolution Summary ==="
    echo "Fixed conflicts in the following files:"
    for file in "${CONFLICT_FILES[@]}"; do
        echo "- $file"
    done
    echo "==================================="
fi
