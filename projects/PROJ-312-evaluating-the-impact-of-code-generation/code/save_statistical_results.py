import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path to allow imports from sibling modules
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from analyze import (
    load_processed_data,
    perform_stratified_mwu_test,
    load_repos,
    filter_excluded_repos,
    load_spot_check_validation_rate,
    calculate_effect_size_r,
    calculate_medians,
    perform_sensitivity_analysis,
    evaluate_significance,
)
from analyze_repo_stats import calculate_medians as calculate_repo_medians

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def save_statistical_results(
    results: Dict[str, Any], output_path: str
) -> None:
    """
    Save statistical results to a JSON file.

    Args:
        results: Dictionary containing statistical test results
        output_path: Path to the output JSON file
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Statistical results saved to {output_path}")


def main() -> int:
    """
    Main function to execute the statistical results saving pipeline.

    This function:
    1. Loads processed PR data
    2. Loads excluded repos list
    3. Filters data based on excluded repos
    4. Performs stratified Mann-Whitney U test
    5. Calculates descriptive statistics
    6. Performs sensitivity analysis
    7. Saves all results to a JSON file

    Returns:
        0 on success, 1 on failure
    """
    try:
        # Define paths
        data_dir = project_root / "data"
        processed_dir = data_dir / "processed"
        output_path = str(processed_dir / "statistical_results.json")

        # Load processed data
        logger.info("Loading processed PR data...")
        pr_data = load_processed_data(str(processed_dir / "pr_turnaround.csv"))

        # Load excluded repos
        excluded_repos_path = str(processed_dir / "excluded_repos.txt")
        if excluded_repos_path and os.path.exists(excluded_repos_path):
            logger.info(f"Loading excluded repos from {excluded_repos_path}")
            with open(excluded_repos_path, "r") as f:
                excluded_repos = [line.strip() for line in f if line.strip()]
        else:
            excluded_repos = []
            logger.warning("No excluded repos file found. Proceeding without filtering.")

        # Filter data based on excluded repos
        logger.info("Filtering data based on excluded repos...")
        filtered_pr_data = filter_excluded_repos(pr_data, excluded_repos)

        # Load repo metadata for median calculations
        logger.info("Loading repo metadata...")
        repos = load_repos(str(data_dir / "raw" / "repos.json"))

        # Calculate median stars and contributors
        logger.info("Calculating median stars and contributors...")
        median_stars, median_contributors = calculate_repo_medians(repos)

        # Perform stratified Mann-Whitney U test
        logger.info("Performing stratified Mann-Whitney U test...")
        mwu_result = perform_stratified_mwu_test(filtered_pr_data)

        # Calculate effect size
        effect_size = calculate_effect_size_r(
            mwu_result["u_statistic"],
            mwu_result["sample_sizes"]["ai"] + mwu_result["sample_sizes"]["non_ai"],
        )

        # Evaluate significance
        significance = evaluate_significance(mwu_result["p_value"])

        # Get sample sizes
        sample_sizes = mwu_result["sample_sizes"]

        # Perform sensitivity analysis
        logger.info("Performing sensitivity analysis...")
        false_negative_rate = load_spot_check_validation_rate(
            str(data_dir / "spot_check" / "validation_report.csv")
        )
        sensitivity_result = perform_sensitivity_analysis(
            filtered_pr_data, false_negative_rate
        )

        # Calculate distribution statistics
        logger.info("Calculating distribution statistics...")
        distribution_stats = {}
        for group in ["ai", "non_ai"]:
            group_data = [
                pr["turnaround_hours"]
                for pr in filtered_pr_data
                if pr["is_ai"] == (group == "ai")
            ]
            if group_data:
                mean_val = sum(group_data) / len(group_data)
                median_val = sorted(group_data)[len(group_data) // 2]
                sd_val = (
                    sum((x - mean_val) ** 2 for x in group_data) / len(group_data)
                ) ** 0.5
                q1_val = sorted(group_data)[len(group_data) // 4]
                q3_val = sorted(group_data)[3 * len(group_data) // 4]
                distribution_stats[group] = {
                    "mean": mean_val,
                    "median": median_val,
                    "std_dev": sd_val,
                    "q1": q1_val,
                    "q3": q3_val,
                    "count": len(group_data),
                }

        # Compile results
        results = {
            "test_type": "Stratified Mann-Whitney U",
            "u_statistic": mwu_result["u_statistic"],
            "p_value": mwu_result["p_value"],
            "effect_size": effect_size,
            "sample_sizes": sample_sizes,
            "median_stars": median_stars,
            "median_contributors": median_contributors,
            "distribution_stats": distribution_stats,
            "significance": significance,
            "sensitivity_analysis": sensitivity_result,
            "false_negative_rate": false_negative_rate,
        }

        # Save results
        save_statistical_results(results, output_path)

        logger.info("Statistical results pipeline completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Error in statistical results pipeline: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
