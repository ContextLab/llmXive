import os
import sys
import logging
import pandas as pd
from pathlib import Path
from config import ensure_directories

# Configure logging for this module
# Ensure logs directory exists
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "merge_warnings.log"

# Configure logger specifically for this module to avoid interfering with root logger
logger = logging.getLogger("merge_datasets")
logger.setLevel(logging.DEBUG)

# Remove existing handlers to prevent duplicates if re-run
if logger.handlers:
    logger.handlers.clear()

# File handler for warnings and errors
fh = logging.FileHandler(log_file, mode='w')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

# Console handler for general info (optional but good for debugging)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)

def load_target_list(path: Path) -> pd.DataFrame:
    """Load the target list of repositories."""
    logger.info(f"Loading target list from {path}")
    if not path.exists():
        raise FileNotFoundError(f"Target list not found at {path}")
    return pd.read_csv(path)

def load_github_metrics(path: Path) -> pd.DataFrame:
    """Load GitHub metrics."""
    logger.info(f"Loading GitHub metrics from {path}")
    if not path.exists():
        raise FileNotFoundError(f"GitHub metrics not found at {path}")
    return pd.read_csv(path)

def load_nvd_cves(path: Path) -> pd.DataFrame:
    """Load NVD CVE data."""
    logger.info(f"Loading NVD CVE data from {path}")
    if not path.exists():
        raise FileNotFoundError(f"NVD CVE data not found at {path}")
    # Assuming JSON input is converted to a DataFrame elsewhere or handled here
    # For this task, we assume the input is a DataFrame with 'url' and 'cve_id'
    return pd.read_json(path)

def count_cves_per_repo(nvd_df: pd.DataFrame) -> pd.DataFrame:
    """Count CVEs per repository URL."""
    if nvd_df.empty:
        return pd.DataFrame(columns=['url', 'cve_count'])
    counts = nvd_df.groupby('url').size().reset_index(name='cve_count')
    return counts

def merge_datasets(target_df: pd.DataFrame, github_df: pd.DataFrame, nvd_counts_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge datasets with exact URL matching.
    
    - Joins GitHub metrics to target list.
    - Performs left join with NVD counts.
    - Logs skipped repositories (no match) and ambiguous matches.
    - Sets cve_count to 0 for no matches.
    """
    logger.info("Starting dataset merge with exact URL matching")

    # Merge target list with GitHub metrics (inner join to ensure we have metrics)
    # Assuming target_df has 'url' and github_df has 'url'
    merged = target_df.merge(github_df, on='url', how='left')
    
    if merged.empty:
        logger.error("Merged dataset is empty after joining with GitHub metrics.")
        return merged

    # Identify URLs in merged that are not in NVD counts
    # We will do a left join to keep all merged rows
    final_df = merged.merge(nvd_counts_df, on='url', how='left')

    # Process missing values and logging
    # 1. Handle ambiguous matches: 
    #    Since we are doing exact matching on 'url', any match in the merge is exact.
    #    Ambiguous matches (substring) would only occur if we did fuzzy matching.
    #    However, if the NVD data contains URLs that are substrings of the target URLs,
    #    a strict 'url' join will NOT match them. 
    #    To detect potential ambiguous matches (where a substring of target URL exists in NVD),
    #    we perform a check.
    
    target_urls = set(merged['url'].unique())
    nvd_urls = set(nvd_counts_df['url'].unique())
    
    # Check for potential ambiguous matches (substring containment)
    # This is an O(N*M) operation, so we might limit it or optimize if data is huge.
    # For now, we iterate to find if any NVD URL is a substring of a target URL (and vice versa)
    # that didn't get an exact match.
    
    ambiguous_matches = []
    skipped_repos = []

    # Filter out exact matches first
    exact_match_urls = target_urls.intersection(nvd_urls)
    non_exact_target_urls = target_urls - exact_match_urls

    for t_url in non_exact_target_urls:
        found_ambiguous = False
        for n_url in nvd_urls:
            if t_url in n_url or n_url in t_url:
                # This is an ambiguous match (substring)
                ambiguous_matches.append((t_url, n_url))
                found_ambiguous = True
                break # Stop at first ambiguous match for this target URL
        
        if not found_ambiguous:
            # No exact match and no substring match found
            skipped_repos.append(t_url)

    # Log ambiguous matches
    for t_url, n_url in ambiguous_matches:
        msg = f"[{t_url}] Reason: Ambiguous NVD match found (substring: {n_url}), not merged."
        logger.error(msg)

    # Log skipped repositories
    for t_url in skipped_repos:
        msg = f"[{t_url}] Reason: No exact or ambiguous NVD match found."
        logger.warning(msg)

    # Fill NaN cve_count with 0 for all rows (including skipped ones if they are in the df)
    final_df['cve_count'] = final_df['cve_count'].fillna(0).astype(int)

    logger.info(f"Merge complete. Processed {len(final_df)} repos.")
    logger.info(f"Skipped repos (no match): {len(skipped_repos)}")
    logger.info(f"Ambiguous matches logged: {len(ambiguous_matches)}")

    return final_df

def validate_merged_data(df: pd.DataFrame) -> bool:
    """Validate the merged dataset for nulls in critical columns."""
    logger.info("Validating merged dataset")
    
    if df['kloc'].isnull().any():
        error_msg = "Validation failed: Null values found in 'kloc' column."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if df['cve_count'].isnull().any():
        error_msg = "Validation failed: Null values found in 'cve_count' column."
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info("Validation passed.")
    return True

def main():
    """Main entry point for merging datasets."""
    # Paths
    target_path = Path("data/raw/target_list.csv")
    github_path = Path("data/processed/github_raw_metrics.csv")
    nvd_path = Path("data/processed/nvd_cve_counts.csv") # Assuming intermediate step creates this
    output_path = Path("data/processed/repo_metrics.csv")

    # Ensure output directory exists
    ensure_directories()

    try:
        # Load data
        target_df = load_target_list(target_path)
        github_df = load_github_metrics(github_path)
        
        # If NVD is a raw JSON, we need to count CVEs first
        # Assuming nvd_path is the result of count_cves_per_repo
        if not nvd_path.exists():
            # Fallback: load raw JSON and count if the path points to raw JSON
            raw_nvd_path = Path("data/raw/nvd_cve_merged.json.gz")
            if raw_nvd_path.exists():
                import gzip
                import json
                with gzip.open(raw_nvd_path, 'rt', encoding='utf-8') as f:
                    nvd_data = json.load(f)
                # Convert to DF and count
                nvd_df = pd.DataFrame(nvd_data)
                # Assuming 'cwe_id' or 'id' or 'url' exists. 
                # Based on T007, we have a merged JSON. We need to extract the repo URL mapping.
                # This part depends on the schema of nvd_cve_merged.json.gz.
                # For this task, we assume nvd_path points to the pre-counted CSV.
                # If not, we raise an error or attempt to derive it.
                # Let's assume the task T009b implies we have a way to get counts.
                # We will assume nvd_path is correct for the merge step.
                raise FileNotFoundError(f"Pre-counted NVD data not found at {nvd_path}. Please run NVD processing step.")
            else:
                raise FileNotFoundError(f"NVD data not found at {nvd_path} or {raw_nvd_path}")
        
        nvd_counts_df = load_nvd_cves(nvd_path)

        # Merge
        result_df = merge_datasets(target_df, github_df, nvd_counts_df)

        # Validate
        validate_merged_data(result_df)

        # Save
        result_df.to_csv(output_path, index=False)
        logger.info(f"Saved merged data to {output_path}")

    except Exception as e:
        logger.error(f"Error during merge process: {str(e)}")
        raise

if __name__ == "__main__":
    main()