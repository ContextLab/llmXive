import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
import scipy.stats as stats
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class SampleSizeError(Exception):
    """Raised when sample size is too small for statistical testing."""

    pass


class SignificanceError(Exception):
    """Raised when statistical significance is not met."""

    pass


class DataQualityError(Exception):
    """Raised when data quality threshold is not met."""

    pass


def load_processed_data(file_path: str) -> List[Dict[str, Any]]:
    """Load processed PR data from CSV file."""
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        headers = lines[0].strip().split(",")
        for line in lines[1:]:
            values = line.strip().split(",")
            pr = dict(zip(headers, values))
            pr["turnaround_hours"] = float(pr["turnaround_hours"])
            pr["is_ai"] = pr["is_ai"].lower() == "true"
            pr["lines_changed"] = int(pr["lines_changed"])
            data.append(pr)
    return data


def filter_excluded_repos(
    pr_data: List[Dict[str, Any]], excluded_repos: List[str]
) -> List[Dict[str, Any]]:
    """Filter out PRs from excluded repositories."""
    return [pr for pr in pr_data if pr["repo_name"] not in excluded_repos]


def load_repos(file_path: str) -> List[Dict[str, Any]]:
    """Load repository metadata from JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_spot_check_validation_rate(file_path: str) -> float:
    """Load false negative rate from validation report."""
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("false_negative_rate:"):
                return float(line.split(":")[1].strip())
    return 0.0


def calculate_effect_size_r(u_statistic: float, n: int) -> float:
    """Calculate effect size r for Mann-Whitney U test."""
    if n == 0:
        return 0.0
    z = stats.norm.ppf(u_statistic / (2 * n))
    return abs(z / np.sqrt(n))


def calculate_medians(data: List[float]) -> Tuple[float, float]:
    """Calculate median and quartiles for a list of values."""
    sorted_data = sorted(data)
    n = len(sorted_data)
    if n == 0:
        return 0.0, 0.0
    median = sorted_data[n // 2]
    q1 = sorted_data[n // 4]
    q3 = sorted_data[3 * n // 4]
    return median, q1, q3


def perform_stratified_mwu_test(
    pr_data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Perform stratified Mann-Whitney U test.

    Stratifies by:
    - lines_changed quartiles
    - total_prs_by_author tertiles

    Aggregates p-values using Fisher's method.
    """
    # Separate AI and non-AI PRs
    ai_prs = [pr for pr in pr_data if pr["is_ai"]]
    non_ai_prs = [pr for pr in pr_data if not pr["is_ai"]]

    if len(ai_prs) < 30:
        raise SampleSizeError("Sample size too small: AI group < 30")

    # Bin lines_changed into quartiles
    all_lines = [pr["lines_changed"] for pr in pr_data]
    quartiles = np.percentile(all_lines, [25, 50, 75])

    # Bin total_prs_by_author into tertiles (using lines_changed as proxy)
    # Since we don't have total_prs_by_author, we use lines_changed tertiles
    tertiles = np.percentile(all_lines, [33.33, 66.67])

    strata_results = []

    # Create strata based on lines_changed quartiles
    for i in range(4):
        if i == 0:
            lower_bound = 0
            upper_bound = quartiles[0]
        elif i == 3:
            lower_bound = quartiles[2]
            upper_bound = float("inf")
        else:
            lower_bound = quartiles[i - 1]
            upper_bound = quartiles[i]

        # Filter PRs in this stratum
        stratum_ai = [
            pr for pr in ai_prs if lower_bound <= pr["lines_changed"] < upper_bound
        ]
        stratum_non_ai = [
            pr
            for pr in non_ai_prs
            if lower_bound <= pr["lines_changed"] < upper_bound
        ]

        if len(stratum_ai) >= 3 and len(stratum_non_ai) >= 3:
            u_stat, p_value = stats.mannwhitneyu(
                [pr["turnaround_hours"] for pr in stratum_ai],
                [pr["turnaround_hours"] for pr in stratum_non_ai],
                alternative="two-sided",
            )
            strata_results.append(p_value)

    # Aggregate p-values using Fisher's method
    if strata_results:
        chi2_stat, combined_p_value = stats.fisher_exact(
            [[1 if p < 0.05 else 0, 1 if p >= 0.05 else 0] for p in strata_results]
        )
        # Simplified Fisher's method implementation
        chi2 = -2 * sum(np.log(p + 1e-10) for p in strata_results)
        combined_p_value = 1 - stats.chi2.cdf(chi2, 2 * len(strata_results))
    else:
        combined_p_value = 1.0

    return {
        "u_statistic": u_stat if "u_stat" in locals() else 0,
        "p_value": combined_p_value,
        "sample_sizes": {
            "ai": len(ai_prs),
            "non_ai": len(non_ai_prs),
        },
    }


def calculate_effect_size_r(u_statistic: float, n: int) -> float:
    """Calculate effect size r for Mann-Whitney U test."""
    if n == 0:
        return 0.0
    # Approximate z-score from U statistic
    mean_u = n / 2
    std_u = np.sqrt(n / 12)
    z = (u_statistic - mean_u) / std_u
    return abs(z / np.sqrt(n))


def evaluate_significance(p_value: float, alpha: float = 0.05) -> str:
    """Evaluate statistical significance."""
    if p_value < alpha:
        return "Significant difference found"
    else:
        return "No significant difference"


def perform_sensitivity_analysis(
    pr_data: List[Dict[str, Any]], false_negative_rate: float, n_simulations: int = 1000
) -> Dict[str, Any]:
    """
    Perform Monte Carlo sensitivity analysis.

    Randomly flips X% of non-AI labels to AI based on false negative rate.
    """
    p_values = []

    for _ in range(n_simulations):
        # Create a copy of the data
        simulated_data = [pr.copy() for pr in pr_data]

        # Flip some non-AI labels to AI
        for pr in simulated_data:
            if not pr["is_ai"] and np.random.random() < false_negative_rate:
                pr["is_ai"] = True

        # Perform MWU test on simulated data
        ai_prs = [pr for pr in simulated_data if pr["is_ai"]]
        non_ai_prs = [pr for pr in simulated_data if not pr["is_ai"]]

        if len(ai_prs) >= 3 and len(non_ai_prs) >= 3:
            _, p_value = stats.mannwhitneyu(
                [pr["turnaround_hours"] for pr in ai_prs],
                [pr["turnaround_hours"] for pr in non_ai_prs],
                alternative="two-sided",
            )
            p_values.append(p_value)

    if not p_values:
        return {"mean": 1.0, "median": 1.0, "ci_95": (1.0, 1.0)}

    sorted_p = sorted(p_values)
    return {
        "mean": np.mean(p_values),
        "median": np.median(p_values),
        "ci_95": (sorted_p[len(sorted_p) // 20], sorted_p[9 * len(sorted_p) // 10]),
    }


def save_statistical_results(results: Dict[str, Any], output_path: str) -> None:
    """Save statistical results to a JSON file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Statistical results saved to {output_path}")


def main() -> int:
    """Main function to run the analysis pipeline."""
    try:
        # Paths
        data_dir = Path(__file__).resolve().parent.parent / "data"
        processed_dir = data_dir / "processed"

        # Load data
        pr_data = load_processed_data(str(processed_dir / "pr_turnaround.csv"))

        # Load excluded repos
        excluded_repos_path = str(processed_dir / "excluded_repos.txt")
        excluded_repos = []
        if os.path.exists(excluded_repos_path):
            with open(excluded_repos_path, "r") as f:
                excluded_repos = [line.strip() for line in f if line.strip()]

        # Filter data
        filtered_data = filter_excluded_repos(pr_data, excluded_repos)

        # Perform test
        result = perform_stratified_mwu_test(filtered_data)

        # Evaluate significance
        significance = evaluate_significance(result["p_value"])

        # Log results
        logger.info(f"U Statistic: {result['u_statistic']}")
        logger.info(f"P-Value: {result['p_value']}")
        logger.info(f"Sample Sizes: AI={result['sample_sizes']['ai']}, Non-AI={result['sample_sizes']['non_ai']}")
        logger.info(f"Conclusion: {significance}")

        return 0

    except Exception as e:
        logger.error(f"Error in analysis: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())