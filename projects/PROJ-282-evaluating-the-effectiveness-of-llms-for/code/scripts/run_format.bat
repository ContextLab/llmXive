@echo off
setlocal

echo Running Black (Formatting)...
cd code
python -m black .

echo Running Ruff (Auto-fix)...
python -m ruff check . --fix

echo Formatting complete.
