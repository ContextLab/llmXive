import ast
import json
import os
import glob
import hashlib
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# ============================================================================
# Logging Setup
# ============================================================================

def setup_validation_logging(log_file: Optional[str] = None) -> logging.Logger:
    """
    Sets up logging for the validation module.
    """
    logger = logging.getLogger('validation')
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        if log_file:
            # Ensure directory exists before creating file handler
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger

logger = setup_validation_logging()

# ============================================================================
# File I/O Helpers
# ============================================================================

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Loads a JSON file and returns its content as a dictionary."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(file_path: str, data: Dict[str, Any]) -> None:
    """Saves a dictionary to a JSON file."""
    dir_path = os.path.dirname(file_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved output to {file_path}")

def calculate_file_checksum(file_path: str) -> str:
    """Calculates SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_checksums(data: Dict[str, Any], file_path: str) -> Dict[str, Any]:
    """Updates the checksum field in the data dictionary."""
    data['checksum'] = calculate_file_checksum(file_path)
    return data

# ============================================================================
# Input Data Loaders
# ============================================================================

def load_candidate_repos(config_path: str) -> List[Dict[str, Any]]:
    """
    Loads candidate repositories from a YAML or JSON config file.
    Returns a list of dicts with 'url' and potentially other metadata.
    """
    # For this task, we assume the config is YAML, but we can handle JSON if needed
    # Since the API surface shows 'load_candidate_repos' in validation.py, 
    # and we need to support YAML, we check dependencies. 
    # If 'yaml' is not imported, we assume JSON or simple list for now, 
    # but the task implies YAML. Let's try to import yaml safely.
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        if isinstance(config, list):
            return config
        elif isinstance(config, dict) and 'repos' in config:
            return config['repos']
        else:
            raise ValueError(f"Invalid config format in {config_path}")
    except ImportError:
        # Fallback if yaml is not available, assume JSON
        logger.warning("PyYAML not found, attempting JSON load.")
        return load_json_file(config_path)

def load_loc_metrics(loc_file: str) -> Dict[str, Any]:
    """Loads LOC metrics from T021b output."""
    return load_json_file(loc_file)

def load_cc_metrics(cc_file: str) -> Dict[str, Any]:
    """Loads Cyclomatic Complexity metrics from T021a output."""
    return load_json_file(cc_file)

def load_doc_quality_scores(scores_file: str) -> Dict[str, Any]:
    """Loads documentation quality scores from T021c output."""
    return load_json_file(scores_file)

# ============================================================================
# Rubric & Filtering Logic
# ============================================================================

def check_documentation_criteria(readme_path: str) -> bool:
    """
    Checks if a README file contains required sections: Setup, API, Architecture.
    Uses regex to find headers.
    """
    if not os.path.exists(readme_path):
        return False
    
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Error reading {readme_path}: {e}")
        return False

    # Regex to match headers like # Setup, ## API, etc.
    pattern = r'^#{1,2}\s+(Setup|API|Architecture)'
    matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
    
    # We need at least 3 of the specific sections, but the task says "Presence of Setup, API, and Architecture sections (≥ 3/4 sections)".
    # Assuming the 4th is optional or implied. We check for the presence of the 3 required.
    required_sections = {'Setup', 'API', 'Architecture'}
    found_sections = {m.capitalize() for m in matches} # Normalize case
    
    return required_sections.issubset(found_sections)

def calculate_doc_quality_score(readme_path: str) -> int:
    """Calculates a simple score based on found sections (0-4)."""
    if not os.path.exists(readme_path):
        return 0
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        pattern = r'^#{1,2}\s+(Setup|API|Architecture|Installation|Usage|Contributing)'
        matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
        return len(set(matches))
    except Exception:
        return 0

def evaluate_repository_rubric(readme_path: str, min_score: int = 3) -> bool:
    """Evaluates if a repository meets the documentation quality threshold."""
    score = calculate_doc_quality_score(readme_path)
    return score >= min_score

def apply_tolerance_filter(
    metrics_loc: Dict[str, Any], 
    metrics_cc: Dict[str, Any], 
    doc_scores: Dict[str, Any],
    tolerance_pct: float = 0.15
) -> Tuple[List[str], Dict[str, bool]]:
    """
    Filters repositories based on:
    1. High-quality docs (score >= 3)
    2. LOC and CC within ±15% tolerance of the median of the high-quality set.
    
    Returns:
        selected_repos: List of URLs that passed all filters.
        tolerance_check: Dict indicating if tolerance check passed globally.
    """
    # Step 1: Filter by Documentation Quality
    high_quality_repos = []
    for url, score_data in doc_scores.items():
        # Assuming score_data is an int or a dict with 'score'
        score = score_data if isinstance(score_data, (int, float)) else score_data.get('score', 0)
        if score >= 3:
            high_quality_repos.append(url)

    if not high_quality_repos:
        logger.warning("No repositories met the documentation quality threshold.")
        return [], {'loc': False, 'cc': False}

    # Step 2: Calculate Baseline Metrics (Median) for High-Quality Repos
    loc_values = []
    cc_values = []
    
    for url in high_quality_repos:
        # Get LOC
        if url in metrics_loc:
            loc_data = metrics_loc[url]
            loc = loc_data.get('sloc', loc_data.get('loc', 0))
            if loc > 0:
                loc_values.append(loc)
        
        # Get CC
        if url in metrics_cc:
            cc_data = metrics_cc[url]
            cc = cc_data.get('cc', 0)
            if cc > 0:
                cc_values.append(cc)

    if not loc_values or not cc_values:
        logger.warning("Insufficient metrics data to calculate baselines.")
        return [], {'loc': False, 'cc': False}

    # Calculate Medians
    loc_values.sort()
    cc_values.sort()
    median_loc = loc_values[len(loc_values) // 2]
    median_cc = cc_values[len(cc_values) // 2]

    # Step 3: Apply Tolerance Filter
    # We re-evaluate ALL high-quality repos against the median of the high-quality set.
    # Actually, the task says "Filter for high-quality docs, then apply ±15% tolerance".
    # This implies we take the high-quality set, calculate their stats, and keep those within tolerance.
    
    selected_repos = []
    tolerance_check = {'loc': True, 'cc': True}

    for url in high_quality_repos:
        is_selected = True

        # Check LOC
        if url in metrics_loc:
            loc_data = metrics_loc[url]
            loc = loc_data.get('sloc', loc_data.get('loc', 0))
            if loc > 0:
                lower_bound = median_loc * (1 - tolerance_pct)
                upper_bound = median_loc * (1 + tolerance_pct)
                if not (lower_bound <= loc <= upper_bound):
                    is_selected = False
                    tolerance_check['loc'] = False # At least one failed
        
        # Check CC
        if is_selected and url in metrics_cc:
            cc_data = metrics_cc[url]
            cc = cc_data.get('cc', 0)
            if cc > 0:
                lower_bound = median_cc * (1 - tolerance_pct)
                upper_bound = median_cc * (1 + tolerance_pct)
                if not (lower_bound <= cc <= upper_bound):
                    is_selected = False
                    tolerance_check['cc'] = False

        if is_selected:
            selected_repos.append(url)

    return selected_repos, tolerance_check

# ============================================================================
# Main Task Execution (T021d)
# ============================================================================

def main():
    """
    Implements T021d: Repository Filtering Logic.
    Inputs:
      - config/candidate_repos.yaml
      - data/raw/repo_loc_raw.json
      - data/raw/repo_cc_raw.json
      - data/raw/doc_quality_scores.json
    Output:
      - data/raw/repo_selection_rubric.json
    """
    # Define paths relative to project root (assumed to be run from project root)
    # Or use absolute paths if running from specific context. 
    # Based on task description, we assume standard project structure.
    project_root = Path(__file__).resolve().parent.parent
    config_path = project_root / "config" / "candidate_repos.yaml"
    loc_path = project_root / "data" / "raw" / "repo_loc_raw.json"
    cc_path = project_root / "data" / "raw" / "repo_cc_raw.json"
    doc_path = project_root / "data" / "raw" / "doc_quality_scores.json"
    output_path = project_root / "data" / "raw" / "repo_selection_rubric.json"

    logger.info("Starting Repository Filtering Logic (T021d)...")

    try:
        # Load Inputs
        logger.info(f"Loading candidate repos from {config_path}")
        # We don't strictly need the candidate list if we have the metrics, 
        # but we load it to ensure consistency.
        candidates = load_candidate_repos(str(config_path))
        
        logger.info(f"Loading LOC metrics from {loc_path}")
        loc_metrics = load_loc_metrics(str(loc_path))
        
        logger.info(f"Loading CC metrics from {cc_path}")
        cc_metrics = load_cc_metrics(str(cc_path))
        
        logger.info(f"Loading Doc Quality Scores from {doc_path}")
        doc_scores = load_doc_quality_scores(str(doc_path))

        # Apply Filtering Logic
        logger.info("Applying documentation quality and tolerance filters...")
        selected_repos, tolerance_check = apply_tolerance_filter(
            loc_metrics, 
            cc_metrics, 
            doc_scores,
            tolerance_pct=0.15
        )

        # Prepare Output
        output_data = {
            "selected_repos": selected_repos,
            "tolerance_check": tolerance_check,
            "total_candidates": len(candidates),
            "total_high_quality": len([r for r in doc_scores if (doc_scores[r] if isinstance(doc_scores[r], int) else doc_scores[r].get('score', 0)) >= 3]),
            "final_count": len(selected_repos)
        }

        # Save Output
        save_json_file(str(output_path), output_data)

        logger.info(f"T021d Complete. Selected {len(selected_repos)} repositories.")
        logger.info(f"Tolerance Check: LOC={tolerance_check['loc']}, CC={tolerance_check['cc']}")

        return 0

    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during T021d execution: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
