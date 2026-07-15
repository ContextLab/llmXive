"""
Script to verify and initialize linting and formatting configuration.
This script ensures that .flake8, pyproject.toml (with black/isort config),
and .pre-commit-config.yaml are present and valid.
"""
import os
import sys
import toml
from pathlib import Path

REQUIRED_FILES = [
    ".flake8",
    "pyproject.toml",
    ".pre-commit-config.yaml",
]

def check_file_exists(path: str) -> bool:
    """Check if a file exists in the project root."""
    full_path = Path(path)
    if not full_path.exists():
        print(f"[FAIL] Missing file: {full_path}")
        return False
    print(f"[OK] Found: {full_path}")
    return True

def validate_pyproject_config() -> bool:
    """Validate that pyproject.toml contains necessary tool configs."""
    path = Path("pyproject.toml")
    if not path.exists():
        return False

    try:
        with open(path, "r") as f:
            config = toml.load(f)

        required_sections = ["tool.black", "tool.isort", "tool.pytest.ini_options"]
        missing = [s for s in required_sections if s not in config.get("tool", {}) and s not in config]
        
        # Check for build-system as well
        if "build-system" not in config:
            missing.append("build-system")

        if missing:
            print(f"[WARN] Missing sections in pyproject.toml: {missing}")
            return False
        
        print("[OK] pyproject.toml contains required configurations")
        return True
    except Exception as e:
        print(f"[FAIL] Error parsing pyproject.toml: {e}")
        return False

def validate_flake8_config() -> bool:
    """Validate .flake8 configuration."""
    path = Path(".flake8")
    if not path.exists():
        return False
    
    try:
        with open(path, "r") as f:
            content = f.read()
        
        if "[flake8]" not in content:
            print("[FAIL] .flake8 missing [flake8] section")
            return False
        
        # Check for essential settings
        if "max-line-length" not in content:
            print("[WARN] .flake8 missing max-line-length setting")
        
        print("[OK] .flake8 is valid")
        return True
    except Exception as e:
        print(f"[FAIL] Error reading .flake8: {e}")
        return False

def validate_precommit_config() -> bool:
    """Validate .pre-commit-config.yaml."""
    path = Path(".pre-commit-config.yaml")
    if not path.exists():
        return False

    try:
        import yaml
        with open(path, "r") as f:
            config = yaml.safe_load(f)
        
        if "repos" not in config:
            print("[FAIL] .pre-commit-config.yaml missing 'repos' key")
            return False
        
        repo_names = [r.get("repo", "") for r in config["repos"]]
        required_repos = ["black", "flake8", "isort"]
        found_repos = []
        
        for req in required_repos:
            if any(req in repo for repo in repo_names):
                found_repos.append(req)
        
        missing_repos = set(required_repos) - set(found_repos)
        if missing_repos:
            print(f"[WARN] Missing pre-commit hooks for: {missing_repos}")
        
        print(f"[OK] .pre-commit-config.yaml is valid (found: {found_repos})")
        return True
    except Exception as e:
        print(f"[FAIL] Error parsing .pre-commit-config.yaml: {e}")
        return False

def main():
    print("=== Linting and Formatting Configuration Check ===")
    
    all_ok = True
    
    # Check file existence
    for f in REQUIRED_FILES:
        if not check_file_exists(f):
            all_ok = False
    
    # Validate content
    if not validate_pyproject_config():
        all_ok = False
    
    if not validate_flake8_config():
        all_ok = False
    
    if not validate_precommit_config():
        all_ok = False
    
    print("\n" + "="*50)
    if all_ok:
        print("SUCCESS: All linting and formatting tools are configured.")
        print("To run pre-commit hooks: pre-commit run --all-files")
        print("To run flake8 manually: flake8 code/ tests/")
        print("To run black manually: black code/ tests/")
        sys.exit(0)
    else:
        print("FAILURE: Some configurations are missing or invalid.")
        sys.exit(1)

if __name__ == "__main__":
    main()