"""
Evaluation script for Dream-State Learning project.

This script loads JSON result files produced by ``code/train.py`` and
performs a paired statistical analysis.  It has been hardened to tolerate
missing or incomplete data (e.g. when only a single seed has been run)
without raising ``TypeError`` – a situation that previously caused the
pipeline to fail.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# Ensure the project root is on the import path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import Config
from utils.logger import get_logger
from eval.statistical_analysis import (
    load_accuracy_results,
    run_ttest_paired,
    analyze_model_performance,
    save_analysis_report,
)
from eval.reporting import save_comparison_report, generate_interpretation

logger = get_logger(__name__)

def load_training_results(results_dir: Path) -> Dict[str, Any]:
    """
    Load all JSON result files from ``results_dir``.  Files that cannot be
    parsed are skipped with a warning.
    """
    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")

    results: Dict[str, Any] = {}
    for result_file in results_dir.glob("*.json"):
        try:
            with open(result_file, "r") as f:
                data = json.load(f)
                results[result_file.stem] = data
                logger.info(f"Loaded {result_file.name}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse {result_file.name}: {e}")
        except Exception as e:
            logger.error(f"Error loading {result_file.name}: {e}")

    return results

def run_statistical_analysis(results: Dict[str, Any], config: Config) -> Dict[str, Any]:
    """
    Extract experimental and baseline accuracies from ``results`` and run a
    paired t‑test.  If insufficient data are present, a descriptive
    placeholder is returned instead of raising.
    """
    experimental: List[float] = []
    baseline: List[float] = []

    for key, data in results.items():
        # Keys containing ``dream`` or ``experimental`` are treated as
        # experimental; ``baseline`` or ``wake`` are treated as baseline.
        lower_key = key.lower()
        if ("dream" in lower_key) or ("experimental" in lower_key):
            if "accuracy" in data:
                experimental.append(data["accuracy"])
        elif ("baseline" in lower_key) or ("wake" in lower_key):
            if "accuracy" in data:
                baseline.append(data["accuracy"])

    if len(experimental) < 2 or len(baseline) < 2:
        logger.warning(
            "Insufficient results for paired statistical analysis "
            f"(experimental={len(experimental)}, baseline={len(baseline)})."
        )
        return {
            "error": "Insufficient results for paired analysis",
            "experimental_count": len(experimental),
            "baseline_count": len(baseline),
        }

    # Paired t‑test
    t_stat, p_value = run_ttest_paired(experimental, baseline)

    analysis = {
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "experimental_mean": float(sum(experimental) / len(experimental)),
        "baseline_mean": float(sum(baseline) / len(baseline)),
        "experimental_count": len(experimental),
        "baseline_count": len(baseline),
        "significance_level": config.get("significance_level", 0.05),
        "is_significant": p_value < config.get("significance_level", 0.05),
    }

    return analysis

def generate_evaluation_report(
    results: Dict[str, Any],
    analysis: Dict[str, Any],
    output_dir: Path,
) -> Path:
    """
    Produce a JSON report that combines the raw results, the statistical
    analysis, and a human‑readable interpretation.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Extract values needed for the interpretation; handle missing keys
    exp_mean = analysis.get("experimental_mean")
    base_mean = analysis.get("baseline_mean")
    diff = None
    if exp_mean is not None and base_mean is not None:
        diff = exp_mean - base_mean
    p_value = analysis.get("p_value")
    alpha = analysis.get("significance_level", 0.05)

    # Guard against ``None`` values – ``generate_interpretation`` expects
    # real numbers.
    if exp_mean is None or base_mean is None or p_value is None:
        interpretation = "Insufficient data to generate a statistical interpretation."
    else:
        interpretation = generate_interpretation(
            exp_mean=exp_mean,
            base_mean=base_mean,
            diff=diff,
            p_value=p_value,
            alpha=alpha,
        )

    report = {
        "timestamp": str(Path(output_dir).parent),
        "results_summary": {
            "total_runs": len(results),
            "files_processed": list(results.keys()),
        },
        "statistical_analysis": analysis,
        "interpretation": interpretation,
    }

    report_path = output_dir / "evaluation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Evaluation report saved to {report_path}")
    return report_path

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate Dream-State Learning training results"
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default="data/results/",
        help="Directory containing training result JSON files (default: data/results/)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/results/",
        help="Directory to save the evaluation report (default: data/results/)",
    )

    args = parser.parse_args()

    config = Config()
    logger.info(f"Loading results from {args.results_dir}")
    results = load_training_results(Path(args.results_dir))

    if not results:
        logger.error("No results found to evaluate")
        sys.exit(1)

    logger.info(f"Loaded {len(results)} result files")
    logger.info("Running statistical analysis")
    analysis = run_statistical_analysis(results, config)

    logger.info("Generating evaluation report")
    report_path = generate_evaluation_report(results, analysis, Path(args.output_dir))

    # Print a concise summary for the CLI user
    print("\n" + "=" * 50)
    print("EVALUATION SUMMARY")
    print("=" * 50)
    print(f"Total runs analyzed: {len(results)}")
    if "p_value" in analysis:
        print(f"Paired t-test p-value: {analysis['p_value']:.4f}")
        print(
            f"Statistically significant (α={config.get('significance_level', 0.05)}): {analysis.get('is_significant', False)}"
        )
    print(f"Report saved to: {report_path}")
    print("=" * 50)

    return 0

if __name__ == "__main__":
    sys.exit(main())