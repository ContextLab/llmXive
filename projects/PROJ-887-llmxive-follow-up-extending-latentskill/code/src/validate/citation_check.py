import os
import sys
import yaml
import requests
from pathlib import Path
from typing import Dict, List, Any, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/citation_check.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

def load_data_sources(config_path: str = "data_sources.yaml") -> Dict[str, Any]:
    """Load the data sources configuration file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Data sources configuration file not found: {path}")
    
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    
    if not isinstance(data, dict) or 'sources' not in data:
        raise ValueError("Invalid data_sources.yaml format: expected 'sources' key")
    
    return data

def check_url_reachability(url: str, timeout: int = 10) -> Tuple[bool, str]:
    """Check if a URL is reachable and returns HTTP status."""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            return True, f"Reachable (HTTP {response.status_code})"
        else:
            return False, f"Unreachable (HTTP {response.status_code})"
    except requests.exceptions.RequestException as e:
        return False, f"Connection failed: {str(e)}"

def check_hf_dataset_files(dataset_id: str, path_pattern: str = None) -> Tuple[bool, str, List[str]]:
    """
    Check if a HuggingFace dataset exists and verify specific file paths within it.
    
    Args:
        dataset_id: The HuggingFace dataset ID (e.g., 'latent-skills/alfworld-weights')
        path_pattern: Optional pattern to check for specific files (e.g., 'weights/alfworld/*.npz')
    
    Returns:
        Tuple of (exists, message, list_of_verified_files)
    """
    try:
        from huggingface_hub import list_repo_files, HfApi
        
        api = HfApi()
        files = list_repo_files(dataset_id, repo_type="dataset")
        
        if not files:
            return False, f"No files found in dataset {dataset_id}", []
        
        verified_files = []
        if path_pattern:
            # Simple glob-like matching for the pattern
            import fnmatch
            matched = [f for f in files if fnmatch.fnmatch(f, path_pattern.replace('*', '*'))]
            if matched:
                verified_files = matched
                return True, f"Found {len(matched)} matching files in {dataset_id}", verified_files
            else:
                return False, f"No files matching pattern '{path_pattern}' found in {dataset_id}", []
        else:
            return True, f"Dataset {dataset_id} exists with {len(files)} files", files[:5]  # Return first 5 as sample
            
    except Exception as e:
        return False, f"Error checking HF dataset {dataset_id}: {str(e)}", []

def verify_sources(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify all data sources listed in the configuration.
    
    Returns a report dictionary with verification results for each source.
    """
    sources = data.get('sources', {})
    report = {
        "verified_at": None,  # Will be set by caller if needed
        "summary": {
            "total": len(sources),
            "passed": 0,
            "failed": 0,
            "warnings": 0
        },
        "details": []
    }
    
    for source_name, source_config in sources.items():
        result = {
            "source": source_name,
            "type": source_config.get("type", "unknown"),
            "status": "unknown",
            "message": "",
            "details": {}
        }
        
        source_type = source_config.get("type")
        
        if source_type == "url":
            url = source_config.get("url")
            if not url:
                result["status"] = "failed"
                result["message"] = "No URL provided"
            else:
                reachable, msg = check_url_reachability(url)
                result["status"] = "passed" if reachable else "failed"
                result["message"] = msg
                result["details"]["url"] = url
                result["details"]["reachable"] = reachable
        
        elif source_type == "huggingface":
            dataset_id = source_config.get("dataset_id")
            path_pattern = source_config.get("path_pattern")
            
            if not dataset_id:
                result["status"] = "failed"
                result["message"] = "No dataset_id provided"
            else:
                exists, msg, files = check_hf_dataset_files(dataset_id, path_pattern)
                result["status"] = "passed" if exists else "failed"
                result["message"] = msg
                result["details"]["dataset_id"] = dataset_id
                result["details"]["path_pattern"] = path_pattern
                result["details"]["verified_files"] = files if files else []
                
                # Check for fallback if primary fails
                if not exists and "fallback" in source_config:
                    fallback = source_config["fallback"]
                    if fallback.get("type") == "url":
                        fb_url = fallback.get("url")
                        fb_reachable, fb_msg = check_url_reachability(fb_url)
                        if fb_reachable:
                            result["status"] = "warning"
                            result["message"] = f"{msg}. Fallback available: {fb_url}"
                            result["details"]["fallback_url"] = fb_url
                            result["details"]["fallback_reachable"] = fb_reachable
        
        else:
            result["status"] = "failed"
            result["message"] = f"Unknown source type: {source_type}"
        
        # Update summary
        if result["status"] == "passed":
            report["summary"]["passed"] += 1
        elif result["status"] == "failed":
            report["summary"]["failed"] += 1
        elif result["status"] == "warning":
            report["summary"]["warnings"] += 1
        
        report["details"].append(result)
    
    return report

def main():
    """Main entry point for citation check verification."""
    logger.info("Starting dataset source verification...")
    
    try:
        # Load configuration
        config = load_data_sources()
        logger.info(f"Loaded {len(config.get('sources', {}))} data sources")
        
        # Verify sources
        report = verify_sources(config)
        
        # Log results
        logger.info(f"Verification complete: {report['summary']['passed']} passed, "
                   f"{report['summary']['failed']} failed, "
                   f"{report['summary']['warnings']} warnings")
        
        for detail in report["details"]:
            status_icon = "✓" if detail["status"] == "passed" else "✗" if detail["status"] == "failed" else "⚠"
            logger.info(f"{status_icon} {detail['source']}: {detail['status']} - {detail['message']}")
        
        # Save report to file
        report_path = Path("data/results/citation_check_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        import json
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to {report_path}")
        
        # Exit with appropriate code
        if report["summary"]["failed"] > 0:
            logger.warning(f"Verification failed for {report['summary']['failed']} sources")
            sys.exit(1)
        elif report["summary"]["warnings"] > 0:
            logger.info(f"Verification completed with {report['summary']['warnings']} warnings")
            sys.exit(0)
        else:
            logger.info("All sources verified successfully")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Verification failed with exception: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    main()
