import os
import json
import csv
import requests
from pathlib import Path
from typing import List, Dict, Any, Tuple
from data.logging_config import get_logger

logger = get_logger(__name__)

BASELINE_URL = "https://huggingface.co/datasets/codeparrot/codeparrot-small/resolve/main/data/train-00000-of-00001.csv"
BASELINE_DIR = Path("data/baseline_corpus")
BASELINE_FILE = BASELINE_DIR / "codeparrot_sample.csv"
OUTPUT_FILE = BASELINE_DIR / "estimated_fp_rate.json"

# Keywords that would incorrectly label a generic code snippet as "Disclosing"
# if our heuristic (e.g., presence of "copilot", "llm") were applied blindly.
# Since the baseline corpus is generic code, any match here is a False Positive.
DISCLOSURE_KEYWORDS = ["copilot", "llm", "generated", "ai", "assistant"]

def download_baseline_corpus() -> Path:
    """
    Downloads the real CodeParrot Small dataset CSV from Hugging Face.
    Raises an exception if the download fails.
    """
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading baseline corpus from {BASELINE_URL}...")
    
    try:
        response = requests.get(BASELINE_URL, stream=True, timeout=120)
        response.raise_for_status()
        
        with open(BASELINE_FILE, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"Baseline corpus saved to {BASELINE_FILE}")
        return BASELINE_FILE
    except requests.RequestException as e:
        logger.error(f"Failed to download baseline corpus: {e}")
        raise RuntimeError(f"Could not fetch real data from {BASELINE_URL}. "
                           "The pipeline requires real data and cannot proceed with synthetic fallbacks.") from e

def estimate_false_positive_rate(csv_path: Path) -> float:
    """
    Calculates the false positive rate by applying disclosure keywords
    to the generic CodeParrot corpus.
    
    Since CodeParrot is generic code, any PR/row containing disclosure keywords
    is a False Positive for our "LLM-generated" detection heuristic.
    
    Returns:
        float: The ratio of rows flagged as 'Disclosing' to total rows.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Baseline corpus not found at {csv_path}. Run download first.")

    total_rows = 0
    fp_count = 0

    logger.info(f"Processing baseline corpus to estimate FP rate: {csv_path}")

    # The CodeParrot CSV typically has columns: 'content', 'lang', etc.
    # We check the 'content' field for keywords.
    with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        # Verify expected columns
        if 'content' not in reader.fieldnames:
            # Fallback if the CSV structure is different (e.g., 'text')
            content_col = 'text' if 'text' in reader.fieldnames else None
            if not content_col:
                raise ValueError(f"Could not find 'content' or 'text' column in {csv_path}. Found: {reader.fieldnames}")
        else:
            content_col = 'content'

        for row in reader:
            total_rows += 1
            text = row.get(content_col, "").lower()
            
            # Check if any disclosure keyword is present
            if any(keyword in text for keyword in DISCLOSURE_KEYWORDS):
                fp_count += 1
            
            # Log progress every 100k rows if the file is large
            if total_rows % 100000 == 0:
                logger.info(f"Processed {total_rows} rows...")

    if total_rows == 0:
        raise ValueError("Baseline corpus is empty.")

    fp_rate = fp_count / total_rows
    logger.info(f"False Positive Rate calculated: {fp_rate:.6f} ({fp_count}/{total_rows})")
    return fp_rate

def main():
    """
    Main entry point for T018:
    1. Download the real baseline corpus.
    2. Estimate the false positive rate.
    3. Save results to data/baseline_corpus/estimated_fp_rate.json.
    """
    logger.info("Starting T018: False Positive Estimation using External Baseline Corpus")

    # Step 1: Download Real Data
    csv_path = download_baseline_corpus()

    # Step 2: Calculate FP Rate
    fp_rate = estimate_false_positive_rate(csv_path)

    # Step 3: Save Results
    result = {
        "fp_rate": fp_rate,
        "total_samples": int(csv_path.stat().st_size), # Approximate size metric
        "methodology": "Keyword match on CodeParrot Small (generic code)",
        "keywords_checked": DISCLOSURE_KEYWORDS
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Results saved to {OUTPUT_FILE}")
    return result

if __name__ == "__main__":
    main()
