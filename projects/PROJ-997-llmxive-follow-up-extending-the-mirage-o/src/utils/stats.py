import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)

class TTestResult:
    """Container for paired t-test results."""
    def __init__(self, statistic: float, p_value: float, method: str = "paired_ttest"):
        self.statistic = statistic
        self.p_value = p_value
        self.method = method

    def to_dict(self) -> Dict[str, Any]:
        return {
            "statistic": float(self.statistic),
            "p_value": float(self.p_value),
            "method": self.method
        }

class StatisticalComparisonReport:
    """Container for the full statistical comparison report including Bonferroni correction."""
    def __init__(self, acceptance_test: TTestResult, score_test: TTestResult, adjusted_alpha: float):
        self.acceptance_test = acceptance_test
        self.score_test = score_test
        self.adjusted_alpha = adjusted_alpha

    def to_dict(self) -> Dict[str, Any]:
        # The task specifically asks for a single JSON with the Bonferroni corrected t-test structure.
        # Since we are testing two metrics (acceptance_rate and reasoning_score), we apply Bonferroni correction.
        # The task schema: {"p_value": float, "statistic": float, "method": "bonferroni_corrected_t_test", "adjusted_alpha": float}
        # We will output the results for the primary metric (acceptance_rate) as the main entry, 
        # but the prompt implies a single output file. 
        # Given the schema request, we will output the result for the acceptance_rate test as the primary "bonferroni_corrected_t_test" entry,
        # and potentially include the score test in a more detailed structure if needed, 
        # but strictly adhering to the requested schema for the main file:
        
        # However, the task says "Perform paired t-test on acceptance rates AND final continuous reasoning scores".
        # The schema provided: {"p_value": float, "statistic": float, "method": "bonferroni_corrected_t_test", "adjusted_alpha": float}
        # This schema fits one test. To be comprehensive, we will output a JSON that contains both, 
        # but the primary "bonferroni_corrected" result will be for the acceptance rate as it's the policy metric.
        # Actually, the prompt asks to generate `t_test_results.json` with that specific schema. 
        # If we must choose one, acceptance_rate is the policy decision metric.
        # But a better interpretation is that the file contains the results of the *comparison* which involves these tests.
        # Let's structure it to include both, but ensure the schema keys exist for the main result (acceptance).
        # Or, perhaps the "method" implies the correction applied to the set.
        
        # Let's produce a JSON that includes both tests, but the top-level keys match the request for the main finding.
        # To be safe and complete:
        return {
            "acceptance_rate_test": {
                "p_value": float(self.acceptance_test.p_value),
                "statistic": float(self.acceptance_test.statistic),
                "method": "bonferroni_corrected_t_test",
                "adjusted_alpha": float(self.adjusted_alpha)
            },
            "reasoning_score_test": {
                "p_value": float(self.score_test.p_value),
                "statistic": float(self.score_test.statistic),
                "method": "bonferroni_corrected_t_test",
                "adjusted_alpha": float(self.adjusted_alpha)
            },
            "summary": {
                "acceptance_rate_significant": self.acceptance_test.p_value < self.adjusted_alpha,
                "reasoning_score_significant": self.score_test.p_value < self.adjusted_alpha
            }
        }

def load_metrics_from_json(file_path: Path, key: str) -> List[float]:
    """
    Loads a list of float values from a JSON file.
    Expects the file to contain a JSON object with the specified key mapping to a list of numbers.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if key not in data:
        raise KeyError(f"Key '{key}' not found in {file_path}. Available keys: {list(data.keys())}")
    
    values = data[key]
    if not isinstance(values, list):
        raise TypeError(f"Expected list for key '{key}', got {type(values)}")
    
    return [float(v) for v in values]

def perform_paired_ttest(group1: List[float], group2: List[float], correction_factor: float = 1.0) -> TTestResult:
    """
    Performs a paired t-test between two groups.
    Applies Bonferroni correction by dividing the alpha or multiplying the p-value.
    Here, we return the raw p-value and statistic, and the caller handles the correction logic for the report,
    or we can apply it here if we assume this function is called for the corrected result.
    The task asks to "Apply Bonferroni correction".
    Standard approach: p_corrected = p_raw * n_tests.
    We will return the raw statistic and the raw p-value, and let the report builder handle the specific 
    'adjusted_alpha' calculation, or we can return the corrected p-value.
    The schema asks for "p_value" and "method: bonferroni_corrected_t_test".
    This implies the p_value in the JSON should be the corrected one.
    """
    if len(group1) != len(group2):
        raise ValueError(f"Group lengths must match: {len(group1)} vs {len(group2)}")
    if len(group1) < 2:
        raise ValueError("Need at least 2 samples for a paired t-test")
    
    statistic, p_value = stats.ttest_rel(group1, group2)
    
    # Apply Bonferroni correction to the p-value
    # If this function is called for one of multiple tests, the correction factor is the number of tests.
    # The task implies we are doing 2 tests (acceptance and score).
    # So correction_factor should be 2.
    corrected_p_value = min(p_value * correction_factor, 1.0)
    
    return TTestResult(statistic=statistic, p_value=corrected_p_value, method="bonferroni_corrected_t_test")

def run_statistical_comparison(
    baseline_path: Path, 
    proxy_path: Path, 
    output_path: Path
) -> StatisticalComparisonReport:
    """
    Loads baseline and proxy metrics, performs paired t-tests on acceptance_rate and reasoning_score,
    applies Bonferroni correction (for 2 tests), and writes the results to a JSON file.
    """
    logger.info(f"Loading baseline metrics from {baseline_path}")
    baseline_acceptance = load_metrics_from_json(baseline_path, "acceptance_rate")
    # T027 outputs a single float for acceptance_rate? 
    # Let's check the schema: "acceptance_rate": float. 
    # If it's a single float, we can't do a t-test. 
    # The task says "Perform paired t-test on acceptance rates ... from T027 and T028".
    # This implies T027 and T028 must output *lists* of acceptance decisions (per sample) or the metrics must be aggregated per sample.
    # Re-reading T027: "Output results to data/processed/baseline_metrics.json with schema ... acceptance_rate: float".
    # If T027 outputs a single aggregate float, a t-test is impossible.
    # However, T027B and T028 logic often involves per-sample evaluation.
    # The task T029 assumes we have the data to do the test.
    # If the JSONs contain a single float, we must have stored per-sample data elsewhere or the task description implies 
    # that T027/T028 should have stored per-sample decisions.
    # Looking at T027: "Calculate ... binary 'acceptance_rate'". This is singular.
    # But for a t-test, we need a distribution.
    # Hypothesis: The "acceptance_rate" in the JSON is a summary, but we need the per-sample boolean decisions.
    # If T027/T028 did not output per-sample lists, we cannot perform the test.
    # However, the task T029 says "from T027 and T028".
    # Let's assume the JSONs might contain a list of per-sample scores if the implementation of T027/T028 was adjusted to support this,
    # OR we need to re-read the T027 description. "Output results to ... with schema ... acceptance_rate: float".
    # This is a conflict. A t-test requires N samples.
    # Perhaps the "acceptance_rate" in the JSON is actually a list of booleans or scores?
    # Or maybe the task implies we should have stored the per-sample decisions.
    # Given the constraint "Do not re-author", and the schema in T027 says `float`, this might be a problem.
    # BUT, T029 is the task to implement the test. If the data isn't there, the test fails.
    # However, in research pipelines, often the "metrics" file for a test set is a summary, but the raw per-sample data is available.
    # Let's look at T028: "Output Schema: ... acceptance_rate: float".
    # If both are single floats, we cannot run a t-test.
    # Wait, T027 says "Calculate ... binary 'acceptance_rate'".
    # Maybe the JSON contains a list of per-sample acceptances? 
    # Let's assume the JSON structure for T027/T028 actually contains a list of per-sample decisions (e.g., "acceptance_decisions": [0, 1, 1, 0...]) 
    # or "reasoning_scores": [0.5, 0.8, ...].
    # If the schema in T027/T028 was strictly a single float, T029 is impossible.
    # Given the instruction to "Implement statistical comparison", I must assume the input files contain the necessary per-sample data.
    # I will assume the keys are "acceptance_decisions" (list of 0/1) and "reasoning_scores" (list of floats) 
    # OR that the "acceptance_rate" key actually holds the list of decisions.
    # Let's try to load "acceptance_rate" as a list. If it's a float, we fail loudly.
    # Actually, looking at T027 description again: "Output results to ... with schema ... acceptance_rate: float".
    # This is very specific. 
    # Is it possible the t-test is on the *reasoning scores* only? 
    # "Perform paired t-test on acceptance rates and final continuous reasoning scores".
    # If "acceptance_rate" is a single float, we can't test it.
    # Maybe the "acceptance_rate" is the mean, and we need the standard deviation? No, t-test needs samples.
    # Perhaps the task implies that T027/T028 *should* have output per-sample data, and the schema description in T027/T028 was a simplification or error in the prompt generation?
    # OR, maybe the "acceptance_rate" in the JSON is actually a list of booleans?
    # Let's assume the JSONs contain per-sample data for the test to work. 
    # I will try to load "acceptance_decisions" first, then fallback to "acceptance_rate" if it's a list?
    # No, the task says "from T027 and T028".
    # Let's assume the JSONs have keys "acceptance_decisions" (list) and "reasoning_scores" (list).
    # If the files only have a single float, this code will raise an error, which is "Fail Loudly".
    
    # Correction: The task T029 says "from T027 and T028".
    # If T027/T028 only output a single float, the t-test is impossible.
    # However, I must implement the code. I will assume the JSONs contain per-sample lists.
    # I will use keys "acceptance_decisions" and "reasoning_scores" as they are the most logical for a t-test.
    # If the actual JSONs from T027/T028 use "acceptance_rate" as a list, I will handle that.
    # Let's assume the JSONs have:
    # baseline_metrics.json: { "acceptance_decisions": [0, 1, ...], "reasoning_scores": [0.5, ...] }
    # proxy_metrics.json: { "acceptance_decisions": [1, 1, ...], "reasoning_scores": [0.6, ...] }
    
    # If the keys are different, the code will fail, which is correct behavior for missing data.
    
    # Let's try to load "acceptance_decisions" and "reasoning_scores".
    # If those don't exist, try "acceptance_rate" and "reasoning_score" assuming they might be lists.
    
    try:
        baseline_acceptance = load_metrics_from_json(baseline_path, "acceptance_decisions")
    except KeyError:
        # Fallback if the key is 'acceptance_rate' but it's a list (unlikely given schema, but possible)
        baseline_acceptance = load_metrics_from_json(baseline_path, "acceptance_rate")
    
    try:
        proxy_acceptance = load_metrics_from_json(proxy_path, "acceptance_decisions")
    except KeyError:
        proxy_acceptance = load_metrics_from_json(proxy_path, "acceptance_rate")

    try:
        baseline_scores = load_metrics_from_json(baseline_path, "reasoning_scores")
    except KeyError:
        baseline_scores = load_metrics_from_json(baseline_path, "reasoning_score")

    try:
        proxy_scores = load_metrics_from_json(proxy_path, "reasoning_scores")
    except KeyError:
        proxy_scores = load_metrics_from_json(proxy_path, "reasoning_score")

    # Bonferroni correction: 2 tests (acceptance and score)
    n_tests = 2
    alpha = 0.05
    adjusted_alpha = alpha / n_tests

    logger.info(f"Performing paired t-test on acceptance decisions (n={len(baseline_acceptance)})")
    acceptance_test = perform_paired_ttest(baseline_acceptance, proxy_acceptance, correction_factor=n_tests)

    logger.info(f"Performing paired t-test on reasoning scores (n={len(baseline_scores)})")
    score_test = perform_paired_ttest(baseline_scores, proxy_scores, correction_factor=n_tests)

    report = StatisticalComparisonReport(
        acceptance_test=acceptance_test,
        score_test=score_test,
        adjusted_alpha=adjusted_alpha
    )

    # Write the report to JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report.to_dict(), f, indent=2)
    
    logger.info(f"Statistical comparison results written to {output_path}")
    return report

def main():
    """Entry point for T029."""
    logging.basicConfig(level=logging.INFO)
    project_root = Path(__file__).parent.parent.parent
    baseline_path = project_root / "data" / "processed" / "baseline_metrics.json"
    proxy_path = project_root / "data" / "processed" / "proxy_metrics.json"
    output_path = project_root / "data" / "processed" / "t_test_results.json"

    try:
        run_statistical_comparison(baseline_path, proxy_path, output_path)
        logger.info("T029 completed successfully.")
    except Exception as e:
        logger.error(f"T029 failed: {e}")
        raise

if __name__ == "__main__":
    main()
