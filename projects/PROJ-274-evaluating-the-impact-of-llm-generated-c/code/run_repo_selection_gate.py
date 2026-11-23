import json
import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
from utils.run_metadata import load_metadata
from utils.setup_paths import ensure_project_dirs

# Ensure project directories exist before attempting file operations
ensure_project_dirs()

logger = logging.getLogger(__name__)

def verify_data_freshness(rubric_path: str, metadata_path: str) -> bool:
    """
    Verify that the repo_selection_rubric.json was generated in the current run session.
    Checks if RUN_ID in rubric matches RUN_ID in run_metadata.json.
    """
    try:
        with open(rubric_path, 'r') as f:
            rubric_data = json.load(f)
        
        rubric_run_id = rubric_data.get('run_id')
        
        if not rubric_run_id:
            logger.warning(f"RUN_ID not found in {rubric_path}. Forcing re-run.")
            return False
        
        metadata = load_metadata()
        if not metadata:
            logger.error(f"Could not load run metadata from {metadata_path}")
            return False
        
        current_run_id = metadata.get('RUN_ID')
        
        if rubric_run_id != current_run_id:
            logger.warning(f"RUN_ID mismatch: Rubric has {rubric_run_id}, current run is {current_run_id}. Forcing re-run.")
            return False
        
        logger.info(f"Data freshness verified: RUN_ID {current_run_id} matches.")
        return True
    except FileNotFoundError as e:
        logger.error(f"File not found during freshness check: {e}")
        return False
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in rubric file: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during freshness check: {e}")
        return False

def verify_tolerances(rubric_path: str) -> bool:
    """
    Verify that the repo_selection_rubric.json confirms all selected repositories
    meet the ±15% tolerance criteria and high-quality rubric.
    """
    try:
        with open(rubric_path, 'r') as f:
            rubric_data = json.load(f)
        
        # Check tolerance results
        tolerance_check = rubric_data.get('tolerance_check', {})
        loc_pass = tolerance_check.get('loc', False)
        cc_pass = tolerance_check.get('cc', False)
        
        # Check high-quality documentation status
        selected_repos = rubric_data.get('selected_repos', [])
        if not selected_repos:
            logger.error("No repositories selected in rubric.")
            return False
        
        # Verify all selected repos have high-quality docs (score >= 3/4)
        all_high_quality = True
        for repo in selected_repos:
            doc_score = repo.get('doc_quality_score', 0)
            if doc_score < 3:
                logger.warning(f"Repository {repo.get('url')} has doc quality score {doc_score} < 3")
                all_high_quality = False
        
        if not all_high_quality:
            logger.error("Not all selected repositories meet high-quality documentation criteria.")
            return False
        
        if not (loc_pass and cc_pass):
            logger.error(f"Tolerance check failed: LOC={loc_pass}, CC={cc_pass}")
            return False
        
        logger.info("All tolerance and quality checks passed.")
        return True
    except FileNotFoundError as e:
        logger.error(f"Rubric file not found: {e}")
        return False
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in rubric file: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during tolerance verification: {e}")
        return False

def main():
    """
    T021f Gate: Verify repo selection meets criteria and data is fresh.
    Blocks Phase 4 (T076) and T021e if verification fails.
    """
    project_root = Path(__file__).parent.parent
    rubric_path = project_root / 'data' / 'raw' / 'repo_selection_rubric.json'
    metadata_path = project_root / 'state' / 'run_metadata.json'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger.info("Starting T021f Repo Selection Gate Verification...")
    
    # Step 1: Verify data freshness
    if not verify_data_freshness(str(rubric_path), str(metadata_path)):
        logger.error("DATA FRESHNESS CHECK FAILED. Pipeline aborted.")
        logger.error("Action: Re-run Phase 2 tasks (T021a-T021d) to regenerate rubric.")
        sys.exit(1)
    
    # Step 2: Verify tolerances and quality
    if not verify_tolerances(str(rubric_path)):
        logger.error("TOLERANCE/QUALITY CHECK FAILED. Pipeline aborted.")
        logger.error("Action: Adjust candidate repos or tolerance parameters and re-run Phase 2.")
        sys.exit(1)
    
    logger.info("T021f Gate PASSED. Pipeline may proceed to Phase 4 and T021e.")
    sys.exit(0)

if __name__ == '__main__':
    main()