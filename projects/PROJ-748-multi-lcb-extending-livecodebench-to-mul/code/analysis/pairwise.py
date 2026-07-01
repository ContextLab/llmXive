"""
code/analysis/pairwise.py

Implements secondary non-parametric tests (Wilcoxon signed-rank) as authorized
by Constitution Principle VI.

This module performs pairwise comparisons of model performance across languages
to determine if observed differences are statistically significant without
assuming normal distribution of the data.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
from scipy import stats

from config import get_config, get_results_path, get_logs_path
from analysis.correction import setup_logging as setup_correction_logging


def setup_logging() -> logging.Logger:
    """Configure and return the logger for pairwise analysis."""
    logger = logging.getLogger("pairwise_analysis")
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    logger.handlers = []

    # File handler
    log_path = get_logs_path() / "pairwise_analysis.log"
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(ch)

    return logger


def load_execution_log(log_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the execution log containing Pass@k results.

    Args:
        log_path: Optional path to the execution log. If None, uses default path.

    Returns:
        Dictionary containing execution log data.

    Raises:
        FileNotFoundError: If the execution log does not exist.
    """
    if log_path is None:
        results_path = get_results_path()
        log_path = results_path / "artifacts" / "execution_log.json"

    if not log_path.exists():
        raise FileNotFoundError(f"Execution log not found at {log_path}")

    with open(log_path, 'r') as f:
        return json.load(f)


def load_pca_results(pca_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load PCA results containing PC1 scores.

    Args:
        pca_path: Optional path to PCA results. If None, uses default path.

    Returns:
        Dictionary containing PCA results.
    """
    if pca_path is None:
        results_path = get_results_path()
        pca_path = results_path / "artifacts" / "pca_results.json"

    if not pca_path.exists():
        raise FileNotFoundError(f"PCA results not found at {pca_path}")

    with open(pca_path, 'r') as f:
        return json.load(f)


def extract_model_language_scores(
    execution_log: Dict[str, Any],
    pca_results: Dict[str, Any],
    pass_k: int = 1
) -> Dict[str, Dict[str, float]]:
    """
    Extract Pass@k scores for each model-language combination.

    Args:
        execution_log: The execution log data.
        pca_results: The PCA results data (for PC1 scores).
        pass_k: The Pass@k value to extract (default 1).

    Returns:
        Dictionary mapping (model, language) tuples to their Pass@k scores.
    """
    scores = {}

    # Extract Pass@k scores from execution log
    if "results" in execution_log:
        for result in execution_log["results"]:
            model = result.get("model")
            language = result.get("language")
            pass_k_key = f"pass_at_{pass_k}"

            if model and language and pass_k_key in result:
                key = (model, language)
                scores[key] = result[pass_k_key]

    return scores


def extract_pc1_scores(
    pca_results: Dict[str, Any]
) -> Dict[str, float]:
    """
    Extract PC1 (General Code Capability) scores for each model.

    Args:
        pca_results: The PCA results data.

    Returns:
        Dictionary mapping model names to their PC1 scores.
    """
    pc1_scores = {}

    if "results" in pca_results:
        for result in pca_results["results"]:
            model = result.get("model")
            pc1 = result.get("pc1_score")

            if model and pc1 is not None:
                pc1_scores[model] = pc1

    return pc1_scores


def wilcoxon_signed_rank_test(
    paired_data: List[Tuple[float, float]]
) -> Tuple[float, float]:
    """
    Perform Wilcoxon signed-rank test on paired data.

    Args:
        paired_data: List of (value1, value2) tuples for paired observations.

    Returns:
        Tuple of (statistic, p-value) from the Wilcoxon test.
    """
    if len(paired_data) < 2:
        return 0.0, 1.0

    data1 = np.array([x[0] for x in paired_data])
    data2 = np.array([x[1] for x in paired_data])

    # Remove pairs where either value is NaN
    valid_mask = ~(np.isnan(data1) | np.isnan(data2))
    if np.sum(valid_mask) < 2:
        return 0.0, 1.0

    data1_valid = data1[valid_mask]
    data2_valid = data2[valid_mask]

    try:
        statistic, p_value = stats.wilcoxon(data1_valid, data2_valid)
        return float(statistic), float(p_value)
    except Exception as e:
        logging.warning(f"Wilcoxon test failed: {e}")
        return 0.0, 1.0


def compare_models_pairwise(
    model_a: str,
    model_b: str,
    scores: Dict[str, Dict[str, float]],
    languages: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Compare two models using Wilcoxon signed-rank test across languages.

    Args:
        model_a: First model name.
        model_b: Second model name.
        scores: Dictionary of (model, language) -> score.
        languages: Optional list of languages to include. If None, uses common languages.

    Returns:
        Dictionary containing test results.
    """
    if languages is None:
        # Find common languages
        langs_a = {lang for (m, lang) in scores.keys() if m == model_a}
        langs_b = {lang for (m, lang) in scores.keys() if m == model_b}
        languages = list(langs_a & langs_b)

    if len(languages) < 2:
        return {
            "model_a": model_a,
            "model_b": model_b,
            "n_pairs": 0,
            "statistic": 0.0,
            "p_value": 1.0,
            "significant": False,
            "languages": []
        }

    # Extract paired scores
    paired_data = []
    for lang in languages:
        score_a = scores.get((model_a, lang))
        score_b = scores.get((model_b, lang))

        if score_a is not None and score_b is not None:
            paired_data.append((score_a, score_b))

    if len(paired_data) < 2:
        return {
            "model_a": model_a,
            "model_b": model_b,
            "n_pairs": len(paired_data),
            "statistic": 0.0,
            "p_value": 1.0,
            "significant": False,
            "languages": languages
        }

    statistic, p_value = wilcoxon_signed_rank_test(paired_data)

    return {
        "model_a": model_a,
        "model_b": model_b,
        "n_pairs": len(paired_data),
        "statistic": statistic,
        "p_value": p_value,
        "significant": p_value < 0.05,
        "languages": languages
    }


def run_all_pairwise_comparisons(
    scores: Dict[str, Dict[str, float]],
    models: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Run pairwise Wilcoxon tests for all model combinations.

    Args:
        scores: Dictionary of (model, language) -> score.
        models: Optional list of models to compare. If None, uses all models in scores.

    Returns:
        List of comparison results.
    """
    if models is None:
        models = list(set(model for (model, _) in scores.keys()))

    comparisons = []

    for i, model_a in enumerate(models):
        for model_b in models[i + 1:]:
            result = compare_models_pairwise(model_a, model_b, scores)
            comparisons.append(result)

    return comparisons


def calculate_effect_size_r(
    statistic: float,
    n: int
) -> float:
    """
    Calculate effect size r for Wilcoxon test.

    r = Z / sqrt(N)
    where Z is approximated from the statistic.

    Args:
        statistic: The Wilcoxon statistic.
        n: Number of pairs.

    Returns:
        Effect size r.
    """
    if n <= 1:
        return 0.0

    # Approximate Z from the statistic
    # For large N, Z ≈ (statistic - mean) / std
    # Mean = n*(n+1)/4, Var = n*(n+1)*(2n+1)/24
    mean = n * (n + 1) / 4
    variance = n * (n + 1) * (2 * n + 1) / 24

    if variance <= 0:
        return 0.0

    z = (statistic - mean) / np.sqrt(variance)
    r = abs(z) / np.sqrt(n)

    return float(min(r, 1.0))


def save_pairwise_results(
    results: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> Path:
    """
    Save pairwise comparison results to JSON.

    Args:
        results: List of comparison results.
        output_path: Optional output path. If None, uses default path.

    Returns:
        Path to the saved file.
    """
    if output_path is None:
        results_path = get_results_path()
        output_path = results_path / "artifacts" / "pairwise_comparison.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    return output_path


def run_pairwise_pipeline(
    execution_log_path: Optional[Path] = None,
    pca_results_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    pass_k: int = 1
) -> Dict[str, Any]:
    """
    Run the complete pairwise comparison pipeline.

    Args:
        execution_log_path: Path to execution log.
        pca_results_path: Path to PCA results.
        output_path: Path for output results.
        pass_k: Pass@k value to use for comparison.

    Returns:
        Dictionary containing pipeline results and output path.
    """
    logger = setup_logging()
    logger.info("Starting pairwise comparison pipeline")

    # Load data
    execution_log = load_execution_log(execution_log_path)
    pca_results = load_pca_results(pca_results_path)

    # Extract scores
    scores = extract_model_language_scores(execution_log, pca_results, pass_k)
    logger.info(f"Extracted scores for {len(scores)} model-language combinations")

    # Get unique models
    models = list(set(model for (model, _) in scores.keys()))
    logger.info(f"Found {len(models)} models: {models}")

    # Run pairwise comparisons
    comparisons = run_all_pairwise_comparisons(scores, models)

    # Add effect sizes
    for comp in comparisons:
        if comp["n_pairs"] >= 2:
            comp["effect_size_r"] = calculate_effect_size_r(
                comp["statistic"],
                comp["n_pairs"]
            )
        else:
            comp["effect_size_r"] = 0.0

    # Save results
    output_path = save_pairwise_results(comparisons, output_path)
    logger.info(f"Saved pairwise comparison results to {output_path}")

    # Summary statistics
    significant_count = sum(1 for c in comparisons if c["significant"])
    summary = {
        "total_comparisons": len(comparisons),
        "significant_comparisons": significant_count,
        "significance_rate": significant_count / len(comparisons) if comparisons else 0,
        "models_compared": models,
        "pass_k": pass_k
    }

    logger.info(f"Pipeline complete. {significant_count}/{len(comparisons)} comparisons significant")

    return {
        "summary": summary,
        "comparisons": comparisons,
        "output_path": str(output_path)
    }


def main():
    """Main entry point for the pairwise analysis script."""
    logger = setup_logging()
    logger.info("Running pairwise Wilcoxon signed-rank analysis")

    try:
        results = run_pairwise_pipeline()

        # Print summary
        print("\n" + "="*60)
        print("PAIRWISE COMPARISON SUMMARY")
        print("="*60)
        print(f"Total comparisons: {results['summary']['total_comparisons']}")
        print(f"Significant comparisons: {results['summary']['significant_comparisons']}")
        print(f"Significance rate: {results['summary']['significance_rate']:.2%}")
        print(f"Models compared: {', '.join(results['summary']['models_compared'])}")
        print(f"Pass@k: {results['summary']['pass_k']}")
        print(f"Output saved to: {results['output_path']}")
        print("="*60)

        return 0

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())