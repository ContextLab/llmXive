"""
PII Scanner using Microsoft Presidio.

Scans `data/raw/` and `data/processed/` directories for Personally Identifiable Information (PII).
This script is designed to run as a pre-commit hook or CI gate.
If PII is detected, the build MUST fail (exit code 1).
If clean, it writes an empty report to `data/logs/pii_scan_report.json`.
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import project utilities
from config import PROJECT_ROOT
from utils.logger import get_logger

# Check for optional dependency
try:
    from presidio_analyzer import AnalyzerEngine, PatternRecognizer
    from presidio_analyzer.nlp_engine import NlpEngineProvider
except ImportError:
    # This should ideally be caught by T002 requirements, but we fail loudly here if missing
    print("[CRITICAL] 'presidio-analyzer' is not installed. Please install it via requirements.txt.", file=sys.stderr)
    sys.exit(1)

logger = get_logger(__name__)

# Configuration
TARGET_DIRS = [
    "data/raw",
    "data/processed"
]
OUTPUT_FILE = "data/logs/pii_scan_report.json"
CONFIDENCE_THRESHOLD = 0.75  # Standard threshold for high confidence PII

def get_text_files(root_dir: Path) -> List[Path]:
    """Recursively find all text-based files in a directory."""
    text_extensions = {'.txt', '.csv', '.json', '.md', '.log', '.py', '.yaml', '.yml', '.xml', '.html'}
    files = []
    if not root_dir.exists():
        logger.warning(f"Directory {root_dir} does not exist. Skipping.")
        return files

    for ext in text_extensions:
        files.extend(root_dir.rglob(f"*{ext}"))
    
    # Also catch files without extension that might be text (e.g., README)
    # but skip binary-like directories if any
    for item in root_dir.rglob("*"):
        if item.is_file() and item.suffix == "":
            # Quick check if it's text
            try:
                with open(item, 'r', encoding='utf-8') as f:
                    f.read(1024)
                files.append(item)
            except (UnicodeDecodeError, PermissionError):
                continue
    
    return files

def scan_content(content: str, analyzer: AnalyzerEngine) -> List[Dict[str, Any]]:
    """Scan a string for PII and return findings."""
    results = analyzer.analyze(text=content, language="en")
    findings = []
    for r in results:
        if r.score >= CONFIDENCE_THRESHOLD:
            findings.append({
                "type": r.entity_type,
                "start": r.start,
                "end": r.end,
                "text": content[r.start:r.end],
                "score": float(r.score)
            })
    return findings

def run_pii_scan() -> Dict[str, Any]:
    """
    Main scanning logic.
    Returns a report dictionary.
    """
    logger.info("Initializing PII Scan using Presidio...")
    
    # Initialize Presidio Analyzer
    # We use the default NLP engine (SpaCy) which is included in presidio-analyzer
    try:
        analyzer = AnalyzerEngine()
        logger.info("Presidio Analyzer initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Presidio Analyzer: {e}")
        # Fail loudly if the engine can't start
        sys.exit(1)

    all_findings: List[Dict[str, Any]] = []
    files_scanned = 0
    files_with_pii = 0

    for dir_name in TARGET_DIRS:
        target_path = PROJECT_ROOT / dir_name
        if not target_path.exists():
            logger.info(f"Target directory {target_path} not found. Skipping.")
            continue

        files = get_text_files(target_path)
        logger.info(f"Found {len(files)} files in {dir_name}")

        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Skip empty files
                if not content.strip():
                    continue

                findings = scan_content(content, analyzer)
                files_scanned += 1

                if findings:
                    files_with_pii += 1
                    for finding in findings:
                        finding["file"] = str(file_path.relative_to(PROJECT_ROOT))
                        all_findings.append(finding)
                
            except Exception as e:
                logger.warning(f"Could not read file {file_path}: {e}")
                continue

    report = {
        "status": "clean" if files_with_pii == 0 else "failed",
        "files_scanned": files_scanned,
        "files_with_pii": files_with_pii,
        "findings": all_findings
    }

    return report

def main():
    """Entry point for the PII scanner."""
    logger.info("Starting PII Scan (T004b)...")
    
    report = run_pii_scan()
    
    # Ensure output directory exists
    output_path = PROJECT_ROOT / OUTPUT_FILE
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"PII Scan Report written to {OUTPUT_FILE}")

    if report["status"] == "failed":
        logger.error(f"[GATE FAILED] PII detected in {report['files_with_pii']} files.")
        for finding in report["findings"]:
            logger.error(f"  - {finding['type']} in {finding['file']}: {finding['text']}")
        sys.exit(1)
    else:
        logger.info("[GATE PASSED] No PII detected.")
        sys.exit(0)

if __name__ == "__main__":
    main()
