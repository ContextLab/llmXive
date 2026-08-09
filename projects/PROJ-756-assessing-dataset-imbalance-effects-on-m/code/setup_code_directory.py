"""
Helper module to create code directory and requirements.
"""
import os
import sys
from pathlib import Path

def create_code_directory():
    """
    Create code directory and requirements.txt.
    """
    project_root = Path.cwd()
    code_dir = project_root / "code"
    code_dir.mkdir(parents=True, exist_ok=True)
    
    # __init__.py
    init_file = code_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# Code package\n")
    
    # requirements.txt
    req_file = code_dir / "requirements.txt"
    if not req_file.exists():
        req_file.write_text("""pandas>=2.0.0
scikit-learn>=1.3.0
shap>=0.43.0
magpie>=3.0.0
datasets>=2.14.0
numpy>=1.24.0
scipy>=1.11.0
pyyaml>=6.0.0
cvxpy>=1.4.0
requests>=2.31.0
matplotlib>=3.7.0
seaborn>=0.12.0
ruff>=0.1.0
black>=23.0.0
pytest>=7.4.0
""")
    
    print(f"Created code directory: {code_dir}")

def main():
    create_code_directory()

if __name__ == "__main__":
    main()