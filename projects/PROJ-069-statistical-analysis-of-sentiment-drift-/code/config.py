import os
from pathlib import Path
from typing import Optional
import sys

def load_environment(project_root: Optional[Path] = None) -> Path:
    """
    Load environment variables from .env file in the project root.
    
    Args:
        project_root: Optional path to project root. If None, attempts to detect it.
        
    Returns:
        Path to the project root directory.
        
    Raises:
        FileNotFoundError: If .env file is not found and required keys are missing.
    """
    if project_root is None:
        # Detect project root by looking for .env or common markers
        current = Path.cwd()
        while current != current.parent:
            if (current / ".env").exists() or (current / "code").exists():
                project_root = current
                break
            current = current.parent
        
        if project_root is None:
            project_root = Path.cwd()

    env_path = project_root / ".env"
    
    # Try to load .env if it exists
    if env_path.exists():
        try:
            # Use python-dotenv if available, otherwise parse manually
            try:
                from dotenv import load_dotenv
                load_dotenv(env_path)
            except ImportError:
                # Fallback: manual parsing
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            os.environ[key] = value
        except Exception as e:
            print(f"Warning: Could not load .env file: {e}", file=sys.stderr)
    
    return project_root

def get_fred_api_key() -> str:
    """
    Retrieve FRED API key from environment variables.
    
    Returns:
        The FRED API key string.
        
    Raises:
        KeyError: If FRED_API_KEY is not set in environment.
    """
    key = os.environ.get("FRED_API_KEY")
    if not key:
        raise KeyError(
            "FRED_API_KEY not found in environment. "
            "Please set it in your .env file or export it manually."
        )
    return key

def get_hf_token() -> Optional[str]:
    """
    Retrieve HuggingFace token from environment variables (optional).
    
    Returns:
        The HuggingFace token string, or None if not set.
    """
    return os.environ.get("HF_TOKEN")

def get_gdelt_api_key() -> Optional[str]:
    """
    Retrieve GDELT API key from environment variables (optional).
    
    Note: GDELT 2.0 API typically does not require an API key for basic access,
    but this is provided for future compatibility or premium access.
    
    Returns:
        The GDELT API key string, or None if not set.
    """
    return os.environ.get("GDELT_API_KEY")

def validate_environment(required_keys: list[str] = None) -> bool:
    """
    Validate that required environment variables are set.
    
    Args:
        required_keys: List of required environment variable names.
                      Defaults to ["FRED_API_KEY"].
                      
    Returns:
        True if all required keys are present, False otherwise.
        
    Raises:
        KeyError: If any required key is missing (when called from main).
    """
    if required_keys is None:
        required_keys = ["FRED_API_KEY"]
        
    missing = []
    for key in required_keys:
        if not os.environ.get(key):
            missing.append(key)
            
    if missing:
        print(f"Error: Missing required environment variables: {', '.join(missing)}", 
              file=sys.stderr)
        print("Please add them to your .env file in the project root.", 
              file=sys.stderr)
        return False
        
    return True

def main():
    """
    Main entry point for testing environment configuration.
    Loads .env and validates required keys.
    """
    project_root = load_environment()
    print(f"Project root detected at: {project_root}")
    
    if (project_root / ".env").exists():
        print(".env file found and loaded.")
    else:
        print("Warning: .env file not found. Using system environment variables.")
        
    # Validate required keys
    try:
        fred_key = get_fred_api_key()
        print(f"FRED API Key status: Set (length: {len(fred_key)})")
    except KeyError as e:
        print(f"FRED API Key status: MISSING - {e}")
        
    hf_token = get_hf_token()
    if hf_token:
        print(f"HF Token status: Set (length: {len(hf_token)})")
    else:
        print("HF Token status: Not set (optional)")
        
    gdelt_key = get_gdelt_api_key()
    if gdelt_key:
        print(f"GDELT API Key status: Set (length: {len(gdelt_key)})")
    else:
        print("GDELT API Key status: Not set (optional)")

if __name__ == "__main__":
    main()
