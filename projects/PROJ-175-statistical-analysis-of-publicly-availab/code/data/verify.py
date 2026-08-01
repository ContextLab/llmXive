import os
import sys
import json
import requests
from pathlib import Path

class DataUnavailableError(Exception):
    """Raised when a required data source is unavailable or returns a non-200 status."""
    pass

def fetch_schema_sample(url: str, timeout: int = 30) -> dict:
    """
    Performs a pre-flight HEAD check on the given URL.
    
    Args:
        url: The URL to check.
        timeout: Request timeout in seconds.
        
    Returns:
        A dictionary with 'status_code' and 'url'.
        
    Raises:
        DataUnavailableError: If the URL does not return a 200 status code.
    """
    try:
        # Use HEAD to check availability without downloading the full resource
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        
        if response.status_code != 200:
            # Log the error to the download errors log if it exists, or create it
            log_path = Path("data/download_errors.log")
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            error_msg = (
                f"[HEAD_CHECK_FAILED] URL: {url} | "
                f"Status Code: {response.status_code} | "
                f"Reason: {response.reason}\n"
            )
            
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(error_msg)
            
            raise DataUnavailableError(
                f"Data source unavailable at {url}: HTTP {response.status_code} ({response.reason})"
            )
        
        return {
            "status_code": response.status_code,
            "url": url,
            "content_type": response.headers.get("Content-Type", "unknown")
        }
        
    except requests.exceptions.RequestException as e:
        log_path = Path("data/download_errors.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        error_msg = (
            f"[HEAD_CHECK_EXCEPTION] URL: {url} | "
            f"Error Type: {type(e).__name__} | "
            f"Message: {str(e)}\n"
        )
        
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(error_msg)
        
        raise DataUnavailableError(
            f"Failed to connect to data source {url}: {str(e)}"
        ) from e

def verify_data_sources(verification_report_path: str = "data/verification_report.json") -> list:
    """
    Reads the verification report and performs HEAD checks on all verified URLs.
    
    Args:
        verification_report_path: Path to the verification report JSON file.
        
    Returns:
        A list of URLs that passed the HEAD check.
        
    Raises:
        DataUnavailableError: If any URL fails the check.
        FileNotFoundError: If the verification report is missing.
    """
    report_path = Path(verification_report_path)
    if not report_path.exists():
        raise FileNotFoundError(
            f"Verification report not found at {verification_report_path}. "
            "Run T012 first to generate the verification report."
        )
    
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    
    # Expecting a structure like {"sources": [{"name": "...", "url": "...", "status": "PASS"}]}
    sources = report.get("sources", [])
    urls_to_check = [
        s["url"] for s in sources 
        if s.get("status") == "PASS" and "url" in s
    ]
    
    if not urls_to_check:
        print("No URLs to verify in the report.")
        return []
    
    passed_urls = []
    
    for url in urls_to_check:
        print(f"Pre-flight HEAD check for: {url}")
        try:
            result = fetch_schema_sample(url)
            print(f"  -> PASS (Status: {result['status_code']})")
            passed_urls.append(url)
        except DataUnavailableError as e:
            print(f"  -> FAIL: {str(e)}")
            raise e
        
    return passed_urls

def main():
    """
    Entry point for T046: Pre-flight HEAD checks.
    """
    print("Starting T046: Pre-flight HEAD checks for verified URLs...")
    
    try:
        verified_urls = verify_data_sources()
        
        # Log success
        log_entry = {
            "task": "T046",
            "status": "SUCCESS",
            "urls_verified": len(verified_urls),
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }
        
        log_path = Path("data/t046_head_check_log.json")
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_entry, f, indent=2)
            
        print(f"T046 Complete: Verified {len(verified_urls)} URLs.")
        
    except DataUnavailableError as e:
        print(f"T046 Failed: {str(e)}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"T046 Failed: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"T046 Failed with unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
