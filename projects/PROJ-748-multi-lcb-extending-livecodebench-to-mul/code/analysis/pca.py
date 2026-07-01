"""
Leave-One-Out PCA for General Code Capability (PC1).

Implements PCA excluding Python to ensure independence from the target variable
(Constitution VI override). Computes PC1 as the first principal component
representing 'General Code Capability' across non-Python languages.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np
from sklearn.decomposition import PCA

# Import project configuration
from config import get_config, get_results_path, get_data_path

# Import execution aggregators to compute Pass@k if needed
# Note: We assume execution_log.json already exists from T012
from execution.aggregators import aggregate_pass_k_by_group


def setup_logging() -> logging.Logger:
    """Configure logging for the analysis module."""
    logger = logging.getLogger("pca_analysis")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def load_execution_log(logger: logging.Logger) -> Dict[str, Any]:
    """
    Load the execution log JSON artifact.
    Expects results/artifacts/execution_log.json
    """
    config = get_config()
    results_path = get_results_path()
    log_path = results_path / "artifacts" / "execution_log.json"

    if not log_path.exists():
        logger.error(f"Execution log not found at {log_path}")
        raise FileNotFoundError(f"Execution log not found: {log_path}")

    with open(log_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_pass_k_matrix(
    execution_log: Dict[str, Any],
    exclude_languages: List[str] = ["python"],
    logger: Optional[logging.Logger] = None
) -> tuple[Dict[str, List[str]], Dict[str, Dict[str, Dict[str, float]]]]:
    """
    Extract Pass@k values for each model and language.

    Returns:
      - models: List of model identifiers
      - pass_k_data: Nested dict {model: {language: {k: value}}}
    """
    if logger is None:
        logger = setup_logging()

    # Expected structure based on T012/T016:
    # { "results": [ { "task_id": ..., "model": ..., "language": ..., "pass_1": ..., "pass_5": ..., "pass_10": ... }, ... ] }
    # OR aggregated structure. We assume raw results or aggregated by (model, language).
    # The aggregator T010 produces aggregated stats. Let's assume the execution_log contains
    # the aggregated Pass@k results per (model, language, temperature) or just (model, language).
    # For PCA, we need a matrix of (Models x Languages).
    # We will aggregate by (model, language) taking the mean across temperatures if needed,
    # or just use a specific temperature if the log is temperature-specific.
    # Assuming the log contains the final aggregated results per (model, language) pair.

    # Structure assumption:
    # execution_log = { "aggregations": [ { "model": "...", "language": "...", "pass_1": 0.8, "pass_5": 0.9, ... } ] }
    # If the log is raw tasks, we need to aggregate first.
    # Given T010 exists, we assume the log has the aggregated data or we aggregate here.
    
    # Let's handle both: if 'results' is present (raw), we aggregate. If 'aggregations' is present, we use it.
    # For robustness, we will re-aggregate if necessary using the helper from T010 if available,
    # but since we can't import internal state easily, we parse directly.

    # Expected structure from T012 (execution pipeline):
    # It writes execution_log.json. T010 writes aggregation results.
    # The task T017 says "Excludes Python when computing PC1".
    # We need a matrix: Rows = Models, Cols = Languages (excluding Python).
    # Value = Pass@k (usually Pass@1 or average). Let's use Pass@1 as the primary metric.

    data_points = {}
    models_set = set()
    languages_set = set()

    # Check structure
    if "results" in execution_log:
        # Raw results list
        items = execution_log["results"]
    elif "aggregations" in execution_log:
        items = execution_log["aggregations"]
    elif isinstance(execution_log, list):
        items = execution_log
    else:
        logger.error("Unexpected execution_log structure")
        raise ValueError("Invalid execution log structure")

    for item in items:
        model = item.get("model")
        language = item.get("language")
        pass_1 = item.get("pass_1")
        
        if not model or not language:
            continue
        
        if language in exclude_languages:
            if logger:
                logger.info(f"Skipping {language} (excluded) for model {model}")
            continue

        models_set.add(model)
        languages_set.add(language)

        if model not in data_points:
            data_points[model] = {}
        
        # Store Pass@1. If multiple entries (e.g. different temps), we might need to average.
        # For simplicity in PCA, we assume one entry per (model, language) or take the first.
        # A robust approach: average if multiple.
        if language not in data_points[model]:
            data_points[model][language] = {"pass_1_sum": 0, "count": 0}
        
        if pass_1 is not None:
            data_points[model][language]["pass_1_sum"] += pass_1
            data_points[model][language]["count"] += 1

    # Finalize averages
    final_matrix = {}
    for model in models_set:
        final_matrix[model] = {}
        for lang in languages_set:
            if lang in data_points.get(model, {}):
                stats = data_points[model][lang]
                final_matrix[model][lang] = stats["pass_1_sum"] / stats["count"] if stats["count"] > 0 else 0.0
            else:
                final_matrix[model][lang] = 0.0 # Missing data treated as 0 or NaN? Treat as 0 for now.

    return list(models_set), final_matrix


def compute_loo_pca(
    pass_k_matrix: Dict[str, Dict[str, float]],
    models: List[str],
    languages: List[str],
    target_pass_k: str = "pass_1",
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Compute Leave-One-Out PCA.
    
    Excludes 'python' from the language set.
    Computes PC1 as the first principal component.
    
    Returns:
      Dict containing PC1 scores for each model, loadings, explained variance, etc.
    """
    if logger is None:
        logger = setup_logging()

    # Ensure Python is excluded
    filtered_languages = [l for l in languages if l.lower() != "python"]
    if not filtered_languages:
        logger.error("No languages remaining after excluding Python.")
        raise ValueError("No languages available for PCA after excluding Python.")

    logger.info(f"Computing PCA on languages: {filtered_languages}")

    # Construct matrix: Rows = Models, Cols = Languages
    # Sort to ensure consistent column order
    sorted_languages = sorted(filtered_languages)
    sorted_models = sorted(models)

    matrix = []
    for model in sorted_models:
        row = []
        for lang in sorted_languages:
            val = pass_k_matrix.get(model, {}).get(lang, 0.0)
            row.append(val)
        matrix.append(row)

    X = np.array(matrix, dtype=float)

    if X.shape[0] < 2 or X.shape[1] < 2:
        logger.warning("Matrix too small for PCA. Dimensions:", X.shape)
        # Return zero scores or handle gracefully
        return {
            "pc1_scores": {m: 0.0 for m in sorted_models},
            "loadings": {},
            "explained_variance_ratio": [],
            "n_components": 0,
            "error": "Matrix dimensions insufficient for PCA"
        }

    # Perform PCA
    pca_model = PCA()
    pca_model.fit(X)

    # PC1 scores for each model (row)
    # transform returns (n_samples, n_components)
    transformed = pca_model.transform(X)
    pc1_scores = transformed[:, 0]

    # Map model names to scores
    model_scores = {model: float(score) for model, score in zip(sorted_models, pc1_scores)}

    # Loadings (how much each language contributes to PC1)
    loadings = pca_model.components_[0]
    loading_dict = {lang: float(loading) for lang, loading in zip(sorted_languages, loadings)}

    # Explained variance
    explained_var_ratio = pca_model.explained_variance_ratio_.tolist()

    result = {
        "method": "Leave-One-Out PCA (Excluding Python)",
        "excluded_languages": ["python"],
        "included_languages": sorted_languages,
        "model_pc1_scores": model_scores,
        "language_loadings": loading_dict,
        "explained_variance_ratio": explained_var_ratio,
        "n_components": len(sorted_languages),
        "total_variance_explained_by_pc1": explained_var_ratio[0] if explained_var_ratio else 0.0
    }

    logger.info(f"PCA completed. PC1 explains {result['total_variance_explained_by_pc1']:.2%} of variance.")
    return result


def save_pca_results(results: Dict[str, Any], logger: Optional[logging.Logger] = None) -> Path:
    """Save PCA results to results/artifacts/pca_results.json."""
    if logger is None:
        logger = setup_logging()

    results_path = get_results_path()
    output_path = results_path / "artifacts" / "pca_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    logger.info(f"PCA results saved to {output_path}")
    return output_path


def main():
    """Main entry point for T017."""
    logger = setup_logging()
    logger.info("Starting Leave-One-Out PCA Analysis (T017)")

    try:
        # 1. Load execution log
        execution_log = load_execution_log(logger)

        # 2. Extract Pass@k matrix (excluding Python)
        models, pass_k_matrix = extract_pass_k_matrix(execution_log, exclude_languages=["python"], logger=logger)

        if not models:
            logger.error("No models found in execution log.")
            sys.exit(1)

        # 3. Compute PCA
        pca_results = compute_loo_pca(
            pass_k_matrix, 
            models, 
            list(set(lang for langs in pass_k_matrix.values() for lang in langs)),
            logger=logger
        )

        # 4. Save results
        save_pca_results(pca_results, logger)

        logger.info("T017 completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Data not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during PCA computation: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()