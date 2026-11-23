import os
import sys
from pathlib import Path

REQUIRED_VARS = ["GITHUB_TOKEN", "DATA_PATH", "LOG_PATH"]
ENV_EXAMPLE_PATH = Path(".env.example")
ENV_FILE_PATH = Path(".env")

def check_env_file_exists():
    if not ENV_EXAMPLE_PATH.exists():
        print("ERROR: .env.example file not found.")
        print("Please create .env.example with required keys: GITHUB_TOKEN, DATA_PATH, LOG_PATH")
        return False
    return True

def check_env_vars_loaded():
    missing = []
    for var in REQUIRED_VARS:
        if var not in os.environ:
            missing.append(var)
    
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        print("Please ensure .env file is loaded or variables are set in your environment.")
        return False
    return True

def check_data_paths():
    data_path = os.environ.get("DATA_PATH")
    log_path = os.environ.get("LOG_PATH")
    
    if data_path and not Path(data_path).exists():
        print(f"WARNING: DATA_PATH does not exist: {data_path}")
        # Optionally create it
        # Path(data_path).mkdir(parents=True, exist_ok=True)
    
    if log_path and not Path(log_path).exists():
        print(f"WARNING: LOG_PATH does not exist: {log_path}")
        # Optionally create it
        # Path(log_path).mkdir(parents=True, exist_ok=True)
    
    return True

def main():
    print("Validating environment configuration...")
    
    if not check_env_file_exists():
        sys.exit(1)
    
    if not check_env_vars_loaded():
        sys.exit(1)
    
    check_data_paths()
    
    print("Environment validation passed.")

if __name__ == "__main__":
    main()
