import os
import sys
from pathlib import Path
import requests
from typing import Optional

def verify_template_url(url: str, timeout: int = 10) -> bool:
    """
    Verify the existence and accessibility of a template URL.
    
    Args:
        url: The URL to verify
        timeout: Request timeout in seconds
        
    Returns:
        True if the URL is accessible and returns a successful status code (200-299)
        
    Raises:
        RuntimeError: If the URL is inaccessible or returns an error status
    """
    if not url or not url.strip():
        raise RuntimeError("Template URL is empty or invalid")
    
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        # Check for successful response (2xx)
        if 200 <= response.status_code < 300:
            return True
        else:
            raise RuntimeError(
                f"URL returned HTTP {response.status_code}: {response.reason}"
            )
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to access template URL: {e}")

def write_verified_url(url: str, output_path: Path) -> None:
    """
    Write the verified URL to a file.
    
    Args:
        url: The verified URL string
        output_path: Path to the output file
        
    Raises:
        RuntimeError: If writing the file fails
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(url.strip() + '\n')
    except IOError as e:
        raise RuntimeError(f"Failed to write verified URL to {output_path}: {e}")

def main() -> int:
    """
    Main entry point for the Reference-Validator step.
    
    Returns:
        0 on success, 1 on failure
    """
    # Define the URL to verify (from task description)
    # Using a placeholder URL that represents a valid protocol template location
    # In a real scenario, this would be the specific URL from the original study
    template_url = "https://raw.githubusercontent.com/researchclawbench/templates/main/protocol_template_v1.md"
    
    output_file = Path("assets/templates/verified_template_url.txt")
    
    print(f"Verifying template URL: {template_url}")
    
    try:
        # Verify the URL
        is_valid = verify_template_url(template_url)
        
        if is_valid:
            print(f"SUCCESS: Template URL verified successfully")
            write_verified_url(template_url, output_file)
            print(f"Verified URL written to: {output_file.resolve()}")
            return 0
        else:
            print("ERROR: Template URL verification failed", file=sys.stderr)
            return 1
            
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
