import logging
import sys
import os
import re
from pathlib import Path
from typing import Optional, Dict, Any, Set
from code.config import Config, ensure_directories, get_path, get_all_base_paths, set_seed, get_seed
from code.security.pii_scanner import scan_text_for_pii, scan_file_for_pii, scan_directory_for_pii, run_pii_security_check, main as pii_main

def setup_logging(log_level: int = logging.INFO) -> None:
    """Configure logging for the project."""
    log_dir = Path(Config.STATE) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "main.log"
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def scan_file_for_pii(file_path: Path) -> Dict[str, Any]:
    """Scan a single file for PII and return results."""
    from code.security.pii_scanner import PIIResult, scan_text_for_pii
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        results = scan_text_for_pii(content, str(file_path))
        return {
            "file": str(file_path),
            "matches": len(results),
            "details": [
                {
                    "type": r.pattern_type,
                    "line": r.line_number,
                    "context": r.context
                }
                for r in results
            ]
        }
    except Exception as e:
        return {"file": str(file_path), "error": str(e)}

def scan_directory_for_pii(directory: Path) -> Dict[str, Any]:
    """Scan a directory for PII and return summary."""
    from code.security.pii_scanner import scan_directory_for_pii as dir_scan
    
    results = dir_scan(directory)
    return {
        "directory": str(directory),
        "total_matches": len(results),
        "files_with_pii": len(set(r.file_path for r in results)),
        "details": [
            {
                "file": r.file_path,
                "line": r.line_number,
                "type": r.pattern_type,
                "match": r.matched_text
            }
            for r in results
        ]
    }

def main():
    """Main entry point for the research pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="llmXive Research Pipeline")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--scan-pii", action="store_true", help="Scan processed data for PII")
    parser.add_argument("--target-dir", type=str, default=None, help="Directory to scan for PII")
    parser.add_argument("--output", type=str, default=None, help="Output path for PII report")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Ensure directories exist
    ensure_directories()
    
    # Set seed if provided
    if args.seed is not None:
        set_seed(args.seed)
        logger.info(f"Random seed set to {args.seed}")
    
    # Handle PII scanning
    if args.scan_pii:
        logger.info("Running PII security scan...")
        target = Path(args.target_dir) if args.target_dir else None
        output = Path(args.output) if args.output else None
        
        report = run_pii_security_check(target_directory=target, output_file=output)
        
        if report["total_pii_found"] > 0:
            logger.error("SECURITY ALERT: PII detected in processed data!")
            sys.exit(1)
        else:
            logger.info("SECURITY CHECK PASSED: No PII detected.")
            sys.exit(0)
    
    logger.info("Pipeline initialized successfully.")
    return 0

if __name__ == "__main__":
    exit(main())
