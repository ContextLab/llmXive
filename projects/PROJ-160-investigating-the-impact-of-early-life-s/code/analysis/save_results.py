"""
Task T030: Save model results to JSON and CSV formats.

This module implements the final step of User Story 2, persisting the
statistical modeling outputs to `data/processed/model_results.json`
and `data/processed/model_results_summary.csv`.

It relies on `code/analysis/results.py` for the data structures and
saving logic, ensuring consistency with the rest of the pipeline.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.analysis.results import (
    extract_results_from_models,
    save_analysis_results,
    apply_bonferroni_correction
)
from code.analysis.modeling import run_primary_analysis
from code.config_env import get_processed_dir, get_random_seed
from code.config import ensure_directories

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main() -> None:
    """
    Execute the primary analysis, extract results, apply corrections,
    and save to the specified output files.

    Output Files:
        - data/processed/model_results.json: Full detailed results.
        - data/processed/model_results_summary.csv: Aggregated summary table.
    """
    logger.info("Starting T030: Saving model results to disk.")

    # 1. Ensure output directories exist
    processed_dir = get_processed_dir()
    ensure_directories()

    # 2. Run the primary analysis (re-using T024-T028 logic)
    # This function fits the LMMs for CA3, DG, Subiculum and the CA3:DG ratio.
    logger.info("Running primary analysis (LMM fitting)...")
    try:
        model_results = run_primary_analysis()
    except Exception as e:
        logger.error(f"Primary analysis failed: {e}")
        raise

    if not model_results:
        logger.warning("No models were fitted. Check data availability.")
        # Create empty result files to satisfy schema contract
        model_results = {"models": [], "metadata": {"status": "no_data"}}

    # 3. Apply Bonferroni correction (T027 logic)
    # The correction threshold is usually 0.05 / number_of_tests.
    # Assuming 3 main subfields + 1 ratio = 4 tests.
    logger.info("Applying Bonferroni correction...")
    corrected_results = apply_bonferroni_correction(model_results)

    # 4. Prepare outputs
    output_json_path = processed_dir / "model_results.json"
    output_csv_path = processed_dir / "model_results_summary.csv"

    # 5. Save to JSON (Detailed)
    logger.info(f"Saving detailed results to {output_json_path}")
    # Ensure the structure is JSON serializable
    json_ready = json.loads(json.dumps(corrected_results, default=str))
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(json_ready, f, indent=2)

    # 6. Save to CSV (Summary)
    logger.info(f"Saving summary results to {output_csv_path}")
    save_analysis_results(corrected_results, output_csv_path)

    logger.info("T030 completed successfully. Files written.")
    print(f"Outputs generated:\n  - {output_json_path}\n  - {output_csv_path}")


if __name__ == "__main__":
    main()