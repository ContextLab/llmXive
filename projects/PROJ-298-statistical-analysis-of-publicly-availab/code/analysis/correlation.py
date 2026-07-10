"""
Correlation Analysis Module for US1.

Computes Pearson correlation coefficients between Theil-Sen trend slopes
and external metrics (GitHub stars, NPM downloads).
"""
import os
import json
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

# Import from sibling modules as per API surface
from data.external import load_trend_results, save_external_metrics
from utils.state_manager import calculate_sha256


def load_trend_data_for_correlation(
    processed_data_path: Path,
    external_metrics_path: Path
) -> Tuple[Dict[str, List[float]], Dict[str, List[float]]]:
    """
    Loads trend slopes and external metrics for tags present in both datasets.

    Args:
        processed_data_path: Path to data/processed/trend_results.json
        external_metrics_path: Path to data/processed/external_metrics.json

    Returns:
        Tuple of (trend_slopes_dict, external_metrics_dict)
        Keys are tag names, values are lists of metrics (usually single value per tag for slope).
    """
    if not processed_data_path.exists():
        raise FileNotFoundError(f"Trend results not found at {processed_data_path}")
    if not external_metrics_path.exists():
        raise FileNotFoundError(f"External metrics not found at {external_metrics_path}")

    with open(processed_data_path, 'r', encoding='utf-8') as f:
        trend_results = json.load(f)

    with open(external_metrics_path, 'r', encoding='utf-8') as f:
        external_metrics = json.load(f)

    # Extract slopes from trend results
    # Structure expected: {"results": [{"tag": "...", "slope": float, ...}, ...]}
    slopes = {}
    if "results" in trend_results:
        for item in trend_results["results"]:
            tag = item.get("tag")
            slope = item.get("slope")
            if tag and slope is not None:
                slopes[tag] = [float(slope)] # List to match expected shape for correlation

    # Extract external metrics
    # Structure expected: {"github": {"tag": {"stars": float}}, "npm": {"tag": {"downloads": float}}}
    github_stars = {}
    npm_downloads = {}

    if "github" in external_metrics:
        for tag, data in external_metrics["github"].items():
            stars = data.get("stars")
            if tag and stars is not None:
                github_stars[tag] = [float(stars)]

    if "npm" in external_metrics:
        for tag, data in external_metrics["npm"].items():
            downloads = data.get("downloads")
            if tag and downloads is not None:
                npm_downloads[tag] = [float(downloads)]

    return slopes, github_stars, npm_downloads


def pearson_correlation(x: List[float], y: List[float]) -> float:
    """
    Calculates the Pearson correlation coefficient between two lists of numbers.

    Args:
        x: List of values for variable X
        y: List of values for variable Y

    Returns:
        Pearson correlation coefficient (float between -1 and 1), or 0.0 if calculation fails.
    """
    n = len(x)
    if n != len(y) or n < 2:
        return 0.0

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))

    sum_sq_x = sum((xi - mean_x) ** 2 for xi in x)
    sum_sq_y = sum((yi - mean_y) ** 2 for yi in y)

    denominator = math.sqrt(sum_sq_x * sum_sq_y)

    if denominator == 0:
        return 0.0

    return numerator / denominator


def calculate_correlations(
    trend_slopes: Dict[str, List[float]],
    github_stars: Dict[str, List[float]],
    npm_downloads: Dict[str, List[float]]
) -> Dict[str, Any]:
    """
    Computes Pearson correlations between trend slopes and external metrics.

    Only tags present in both datasets are included.

    Args:
        trend_slopes: Dict mapping tag -> [slope]
        github_stars: Dict mapping tag -> [star_count]
        npm_downloads: Dict mapping tag -> [download_count]

    Returns:
        Dictionary containing correlation results.
    """
    results = {
        "github_correlation": None,
        "npm_correlation": None,
        "tags_analyzed": [],
        "details": {}
    }

    # Find common tags
    common_tags = set(trend_slopes.keys()) & set(github_stars.keys())

    if len(common_tags) >= 2:
        x_slope = [trend_slopes[t][0] for t in common_tags]
        y_github = [github_stars[t][0] for t in common_tags]

        r_github = pearson_correlation(x_slope, y_github)
        results["github_correlation"] = r_github
        results["tags_analyzed"] = list(common_tags)
        results["details"]["github"] = {
            "count": len(common_tags),
            "correlation": r_github
        }
    else:
        results["details"]["github"] = {
            "count": len(common_tags),
            "reason": "Insufficient common tags for correlation"
        }

    # NPM correlation
    common_tags_npm = set(trend_slopes.keys()) & set(npm_downloads.keys())

    if len(common_tags_npm) >= 2:
        x_slope_npm = [trend_slopes[t][0] for t in common_tags_npm]
        y_npm = [npm_downloads[t][0] for t in common_tags_npm]

        r_npm = pearson_correlation(x_slope_npm, y_npm)
        results["npm_correlation"] = r_npm
        if "tags_analyzed" not in results or not results["tags_analyzed"]:
            results["tags_analyzed"] = list(common_tags_npm)
        results["details"]["npm"] = {
            "count": len(common_tags_npm),
            "correlation": r_npm
        }
    else:
        results["details"]["npm"] = {
            "count": len(common_tags_npm),
            "reason": "Insufficient common tags for correlation"
        }

    return results


def run_correlation_analysis(
    project_root: Path,
    trend_results_path: Optional[Path] = None,
    external_metrics_path: Optional[Path] = None
) -> Path:
    """
    Main entry point for correlation analysis. Loads data, computes correlations,
    and saves results.

    Args:
        project_root: Root directory of the project.
        trend_results_path: Optional override for trend results path.
        external_metrics_path: Optional override for external metrics path.

    Returns:
        Path to the saved correlation results file.
    """
    if trend_results_path is None:
        trend_results_path = project_root / "data" / "processed" / "trend_results.json"
    if external_metrics_path is None:
        external_metrics_path = project_root / "data" / "processed" / "external_metrics.json"

    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "correlation_results.json"

    try:
        slopes, github_stars, npm_downloads = load_trend_data_for_correlation(
            trend_results_path, external_metrics_path
        )

        correlation_results = calculate_correlations(slopes, github_stars, npm_downloads)

        # Add metadata
        correlation_results["metadata"] = {
            "method": "Pearson",
            "source_trend": str(trend_results_path.relative_to(project_root)),
            "source_external": str(external_metrics_path.relative_to(project_root))
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(correlation_results, f, indent=2)

        print(f"Correlation analysis complete. Results saved to {output_path}")
        return output_path

    except FileNotFoundError as e:
        print(f"Error: {e}")
        raise
    except Exception as e:
        print(f"Error during correlation analysis: {e}")
        raise


def main():
    """CLI entry point."""
    project_root = Path(__file__).resolve().parent.parent.parent
    run_correlation_analysis(project_root)


if __name__ == "__main__":
    main()