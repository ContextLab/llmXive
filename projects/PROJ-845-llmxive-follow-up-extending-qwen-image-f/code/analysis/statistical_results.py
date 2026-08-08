"""
Module to create and persist StatisticalResult records based on the contracts schema.
"""
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

from utils.logger import get_logger

logger = get_logger(__name__)


def create_statistical_result(
    test_type: str,
    statistic: float,
    p_value: float,
    corrected_p_value: float,
    conclusion: str,
    correction_method: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Creates a StatisticalResult dictionary matching the schema in contracts/statistical_result.schema.yaml.

    Schema fields:
    - test_type: str (e.g., "ANOVA", "t-test")
    - statistic: float (F-statistic or t-statistic)
    - p_value: float (raw p-value)
    - corrected_p_value: float (Bonferroni corrected)
    - conclusion: str (interpretation of the result)
    - correction_method: str (e.g., "Bonferroni")
    - metadata: Dict[str, Any] (optional additional context)
    """
    result = {
        "test_type": test_type,
        "statistic": statistic,
        "p_value": p_value,
        "corrected_p_value": corrected_p_value,
        "conclusion": conclusion,
        "correction_method": correction_method,
        "metadata": metadata or {},
        "generated_at": datetime.utcnow().isoformat()
    }
    return result


def save_statistical_results(
    results: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Saves a list of StatisticalResult dictionaries to a JSON file.
    Ensures the output directory exists.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Saving {len(results)} statistical results to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info("Successfully saved statistical results.")


def main() -> None:
    """
    Main entry point to load computed statistics from the stats module,
    apply corrections (if not already done), create StatisticalResult records,
    and write them to data/processed/statistical_results.json.

    This function assumes that prior tasks (T030, T031, T032) have populated
    the necessary data or that this script is called after those computations.
    For this implementation, we expect the caller to pass in the computed
    statistics or we re-calculate them if data is available in the processed folder.
    
    However, to strictly follow the task of 'creating records and writing them',
    and assuming the statistical analysis (T030-T032) has been run and stored
    or is available via imports, we will structure this to accept inputs or 
    read from a temporary state if necessary. 
    
    Since T030-T032 are completed, we assume the data exists in a processed state
    or we can re-run the analysis if the raw data (model outputs) exists.
    
    For this task, we will simulate the consumption of results from T030-T032
    by expecting them to be passed or read from a standard location if they were
    written by previous steps. If not, we will construct a minimal example 
    to demonstrate the record creation logic, but in a real pipeline, 
    this would consume the actual outputs of T030-T032.
    
    Given the constraints of a single script implementation without a running
    pipeline state, we will implement the logic to read from a hypothetical
    'raw_analysis_output.json' if it exists, or raise an error if not,
    to ensure we are not fabricating data.
    """
    # Attempt to load raw analysis results if they exist (produced by T030-T032)
    # In a real pipeline, these would be the direct outputs of the stats module.
    # If not present, we cannot fabricate results.
    
    # We will look for a file that T030-T032 would have produced.
    # Since T032 is completed, we assume the corrected stats are available.
    # Let's assume the previous tasks wrote a file 'data/processed/analysis_stats.json'
    # containing the raw and corrected stats.
    
    input_path = "data/processed/analysis_stats.json"
    
    if not os.path.exists(input_path):
        # If the file doesn't exist, we cannot fabricate data.
        # However, for the purpose of this task implementation, we must show
        # the code that creates the records. In a real execution, this would fail.
        # To make this script runnable and demonstrative without fabricating
        # the *input* data (which must be real), we will check if the file exists.
        # If it doesn't, we raise an error as per "Fail loudly".
        logger.error(f"Required input file {input_path} not found. "
                     "Ensure T030-T032 have been executed and saved results here.")
        raise FileNotFoundError(
            f"Input file {input_path} not found. "
            "Statistical results cannot be created without real analysis data."
        )

    with open(input_path, 'r', encoding='utf-8') as f:
        analysis_data = json.load(f)

    results = []

    # Process ANOVA result
    if 'anova' in analysis_data:
        anova = analysis_data['anova']
        result = create_statistical_result(
            test_type="ANOVA",
            statistic=anova['f_statistic'],
            p_value=anova['raw_p_value'],
            corrected_p_value=anova['corrected_p_value'],
            conclusion="Significant difference in means" if anova['corrected_p_value'] < 0.05 else "No significant difference in means",
            correction_method=anova.get('correction_method', "Bonferroni"),
            metadata={"groups": anova.get('groups', [])}
        )
        results.append(result)

    # Process Pairwise T-tests
    if 'pairwise_t_tests' in analysis_data:
        for t_test in analysis_data['pairwise_t_tests']:
            conclusion = (
                f"Difference significant between {t_test['group1']} and {t_test['group2']}"
                if t_test['corrected_p_value'] < 0.05
                else f"No significant difference between {t_test['group1']} and {t_test['group2']}"
            )
            result = create_statistical_result(
                test_type="t-test",
                statistic=t_test['t_statistic'],
                p_value=t_test['raw_p_value'],
                corrected_p_value=t_test['corrected_p_value'],
                conclusion=conclusion,
                correction_method=t_test.get('correction_method', "Bonferroni"),
                metadata={
                    "group1": t_test['group1'],
                    "group2": t_test['group2'],
                    "difference": t_test.get('mean_difference')
                }
            )
            results.append(result)

    if not results:
        logger.warning("No statistical results found in input data.")
        return

    output_path = "data/processed/statistical_results.json"
    save_statistical_results(results, output_path)

    logger.info(f"Created {len(results)} StatisticalResult records.")


if __name__ == "__main__":
    main()