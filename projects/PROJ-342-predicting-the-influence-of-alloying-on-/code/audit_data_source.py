"""
T081: Data Source Audit
Verifies that data/ingestion_stats.json correctly identifies the source DOI
and ensures no synthetic data generation code paths were triggered.
"""
import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent

def load_ingestion_stats(stats_path: Path) -> Dict[str, Any]:
    """Loads the ingestion statistics JSON file."""
    if not stats_path.exists():
        raise FileNotFoundError(f"Ingestion stats file not found: {stats_path}")
    
    with open(stats_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def verify_source_doi(stats: Dict[str, Any]) -> bool:
    """
    Verifies that the source DOI is present and valid in the stats.
    Returns True if valid, False otherwise.
    """
    if 'source_doi' not in stats:
        logger.error("Missing 'source_doi' key in ingestion_stats.json")
        return False
    
    doi = stats['source_doi']
    if not isinstance(doi, str) or not doi.startswith('10.'):
        logger.error(f"Invalid DOI format found: {doi}")
        return False
    
    logger.info(f"Verified source DOI: {doi}")
    return True

def verify_no_synthetic_fallback(stats: Dict[str, Any]) -> bool:
    """
    Verifies that no synthetic data generation was triggered.
    Checks for specific flags or absence of 'synthetic' indicators.
    """
    # Check for explicit synthetic flags that might have been logged
    if stats.get('synthetic_fallback_triggered', False):
        logger.error("Synthetic fallback was triggered! Data integrity compromised.")
        return False
    
    # Check for 'source_doi' presence as a proxy for real data fetch
    # If we have a DOI, we assume real data was used (T012 ensures this)
    if 'source_doi' not in stats:
        logger.error("No source DOI found; cannot verify real data source.")
        return False
    
    # Check retention rate is reasonable (not 1.0 for empty data or 0.0)
    retention = stats.get('retention_rate', 0.0)
    if retention <= 0 or retention > 1:
        logger.warning(f"Unexpected retention rate: {retention}")
    
    logger.info("Verified: No synthetic data generation code paths detected.")
    return True

def verify_record_counts(stats: Dict[str, Any]) -> bool:
    """
    Verifies that record counts are present and consistent.
    """
    required_keys = ['original_count', 'kept_count', 'dropped_count']
    for key in required_keys:
        if key not in stats:
            logger.error(f"Missing required key: {key}")
            return False
        
        if not isinstance(stats[key], int) or stats[key] < 0:
            logger.error(f"Invalid value for {key}: {stats[key]}")
            return False
    
    # Consistency check
    if stats['kept_count'] + stats['dropped_count'] != stats['original_count']:
        logger.error(f"Count inconsistency: {stats['kept_count']} + {stats['dropped_count']} != {stats['original_count']}")
        return False
    
    logger.info(f"Verified record counts: {stats['original_count']} -> {stats['kept_count']} kept")
    return True

def main():
    """Main audit function."""
    project_root = get_project_root()
    stats_path = project_root / 'data' / 'ingestion_stats.json'
    
    logger.info("Starting Data Source Audit (T081)...")
    
    try:
        stats = load_ingestion_stats(stats_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in ingestion_stats.json: {e}")
        sys.exit(1)
    
    all_checks_passed = True
    
    # Run verification checks
    if not verify_source_doi(stats):
        all_checks_passed = False
    
    if not verify_no_synthetic_fallback(stats):
        all_checks_passed = False
    
    if not verify_record_counts(stats):
        all_checks_passed = False
    
    if all_checks_passed:
        logger.info("✅ Data Source Audit PASSED. All checks successful.")
        sys.exit(0)
    else:
        logger.error("❌ Data Source Audit FAILED. See logs for details.")
        sys.exit(1)

if __name__ == '__main__':
    main()