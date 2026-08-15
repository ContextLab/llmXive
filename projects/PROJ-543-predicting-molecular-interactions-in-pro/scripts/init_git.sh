#!/bin/bash
# Script to initialize the git repository if it doesn't exist
# and ensure .gitignore is applied.

set -e

# Check if .git directory exists
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
else
    echo "Git repository already exists."
fi

# Ensure .gitignore exists (should be created by this task)
if [ ! -f ".gitignore" ]; then
    echo "Error: .gitignore file not found. Please run the task that creates it."
    exit 1
fi

# Add the .gitignore and keep files
echo "Adding .gitignore and directory markers..."
git add .gitignore
git add data/raw/.gitkeep
git add data/processed/.gitkeep
git add data/results/.gitkeep
git add data/reference/.gitkeep
git add tests/.gitkeep
git add specs/.gitkeep
git add code/.gitkeep

# Commit if there are changes
if ! git diff --cached --quiet; then
    git commit -m "chore: initialize git repo with .gitignore and directory structure"
    echo "Git repository initialized and committed."
else
    echo "No changes to commit."
fi