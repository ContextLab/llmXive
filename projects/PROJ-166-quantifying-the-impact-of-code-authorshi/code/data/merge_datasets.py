import os
import sys
import logging
import pandas as pd
from pathlib import Path
from config import ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/merge_warnings.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Ensure logs directory exists
ensure_directories()

def load_target_list(path: Path) -> pd.DataFrame:
    """Load the target list of repositories."""
    df = pd.read_csv(path)
    logger.info(f"Loaded target list with {len(df)} repositories from {path}")
    return df

def load_github_metrics(path: Path) -> pd.DataFrame:
    """Load GitHub metrics (authors, KLOC, etc.)."""
    df = pd.read_csv(path)
    logger.info(f"Loaded GitHub metrics with {len(df)} repositories from {path}")
    return df

def load_nvd_cves(path: Path) -> pd.DataFrame:
    """Load NVD CVE data."""
    # Handle both .json.gz and .json
    if path.suffix == '.gz':
        df = pd.read_json(path, compression='gzip')
    else:
        df = pd.read_json(path)
    
    # Ensure 'url' column exists and is string type
    if 'url' not in df.columns:
        raise ValueError("NVD data must contain a 'url' column")
    
    df['url'] = df['url'].astype(str)
    logger.info(f"Loaded NVD CVE data with {len(df)} entries from {path}")
    return df

def count_cves_per_repo(nvd_df: pd.DataFrame) -> pd.Series:
    """
    Count CVEs per repository URL using EXACT matching.
    Returns a Series indexed by URL with CVE counts.
    """
    if nvd_df.empty:
        logger.warning("NVD data is empty, returning empty CVE counts")
        return pd.Series(dtype=int)
    
    # Group by exact URL and count
    counts = nvd_df.groupby('url').size()
    logger.info(f"Counted CVEs for {len(counts)} unique URLs")
    return counts

def merge_datasets(
    target_list: pd.DataFrame,
    github_metrics: pd.DataFrame,
    nvd_counts: pd.Series
) -> pd.DataFrame:
    """
    Merge datasets using EXACT URL matching as per FR-002.
    
    - If a URL in target_list has no exact match in NVD, set cve_count to 0.
    - Flag ambiguous matches (substring matches) in logs but do NOT merge them.
    """
    # Ensure URL columns are strings for consistent comparison
    target_list = target_list.copy()
    github_metrics = github_metrics.copy()
    
    target_list['url'] = target_list['url'].astype(str)
    github_metrics['url'] = github_metrics['url'].astype(str)
    
    # Merge GitHub metrics with target list (inner join to keep only valid targets)
    merged = pd.merge(
        target_list,
        github_metrics,
        on='url',
        how='inner'
    )
    logger.info(f"Merged target list with GitHub metrics: {len(merged)} rows")
    
    # Initialize cve_count column with 0 (default for no match)
    merged['cve_count'] = 0
    
    # Find exact matches in NVD
    exact_matches = merged[merged['url'].isin(nvd_counts.index)]
    merged.loc[exact_matches.index, 'cve_count'] = merged.loc[exact_matches.index, 'url'].map(nvd_counts)
    
    # Detect and log ambiguous matches (substring matches) that were NOT exact matches
    # These are URLs in NVD that are substrings of target URLs or vice versa, but not exact
    target_urls = set(target_list['url'].unique())
    nvd_urls = set(nvd_counts.index)
    
    # Find URLs in NVD that are not exact matches but might be ambiguous
    non_exact_nvd = nvd_urls - target_urls
    
    ambiguous_count = 0
    for nvd_url in non_exact_nvd:
        for target_url in target_urls:
            if nvd_url in target_url or target_url in nvd_url:
                # This is an ambiguous match
                logger.warning(f"[{target_url}] Ambiguous match detected with NVD URL: {nvd_url} (substring match, not merged)")
                ambiguous_count += 1
                # Only log first occurrence per target to avoid spam
                break
    
    if ambiguous_count > 0:
        logger.warning(f"Total ambiguous (substring) matches flagged: {ambiguous_count}")
    
    logger.info(f"Final merged dataset has {len(merged)} rows, with CVE counts assigned via exact matching")
    return merged

def validate_merged_data(df: pd.DataFrame) -> None:
    """
    Validate the merged dataset:
    - Check for null values in kloc and cve_count
    - Ensure cve_count defaults to 0 (not null) if missing
    """
    logger.info("Validating merged dataset...")
    
    # Check for nulls in critical columns
    if df['kloc'].isnull().any():
        null_kloc_rows = df[df['kloc'].isnull()]
        logger.error(f"Found {len(null_kloc_rows)} rows with null kloc values")
        raise ValueError("Null values found in 'kloc' column. This violates data integrity requirements.")
    
    if df['cve_count'].isnull().any():
        null_cve_rows = df[df['cve_count'].isnull()]
        logger.warning(f"Found {len(null_cve_rows)} rows with null cve_count. Filling with 0.")
        df['cve_count'] = df['cve_count'].fillna(0)
    
    # Ensure cve_count is integer type
    df['cve_count'] = df['cve_count'].astype(int)
    
    logger.info("Validation passed: no null values in critical columns")

def main():
    """Main entry point for merging and validating datasets."""
    # Define paths
    base_dir = Path(__file__).parent.parent.parent
    target_list_path = base_dir / 'data' / 'raw' / 'target_list.csv'
    github_metrics_path = base_dir / 'data' / 'processed' / 'github_raw_metrics.csv'
    nvd_cve_path = base_dir / 'data' / 'raw' / 'nvd_cve_merged.json.gz'
    output_path = base_dir / 'data' / 'processed' / 'repo_metrics.csv'
    
    # Load data
    target_list = load_target_list(target_list_path)
    github_metrics = load_github_metrics(github_metrics_path)
    nvd_cves = load_nvd_cves(nvd_cve_path)
    
    # Count CVEs per repo (exact URL matching)
    nvd_counts = count_cves_per_repo(nvd_cves)
    
    # Merge datasets with validation logic
    merged_df = merge_datasets(target_list, github_metrics, nvd_counts)
    
    # Validate the merged data
    validate_merged_data(merged_df)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the final merged dataset
    merged_df.to_csv(output_path, index=False)
    logger.info(f"Saved merged dataset to {output_path}")
    
    # Print summary
    print(f"\n=== Merge Summary ===")
    print(f"Total repositories: {len(merged_df)}")
    print(f"Repositories with CVEs: {(merged_df['cve_count'] > 0).sum()}")
    print(f"Repositories without CVEs (cve_count=0): {(merged_df['cve_count'] == 0).sum()}")
    print(f"Output file: {output_path}")

if __name__ == '__main__':
    main()