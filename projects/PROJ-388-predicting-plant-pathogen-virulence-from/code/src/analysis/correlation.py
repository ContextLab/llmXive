import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, NamedTuple
from datetime import datetime

# Ensure we can import from the project root if run as a module, 
# but for the script entry point, we assume standard imports work 
# or we handle relative imports if necessary.
# Based on the API surface, we import specific names.

# Attempt to import from sibling modules as per API surface
try:
    from src.utils.errors import DataFetchError, AnalysisError
except ImportError:
    # Fallback if running in a context where src is not in path yet, 
    # though the task implies we are fixing/adding to this file.
    # We define minimal error classes if the import fails to ensure the file is runnable standalone for this task.
    class DataFetchError(Exception):
        def __init__(self, url, status_code):
            super().__init__(f"Failed to fetch data from {url} (Status: {status_code})")
    class AnalysisError(Exception):
        pass

logger = logging.getLogger(__name__)

class CorrelationResult(NamedTuple):
    feature_id: str
    rho: float
    p_value: float
    adj_p_value: float
    n: int

class CorrelationAnalysisResult(NamedTuple):
    results: List[CorrelationResult]
    low_power: bool
    sample_size: int

def load_tree(tree_path: str) -> Any:
    """Load phylogenetic tree (placeholder for actual implementation)."""
    if not os.path.exists(tree_path):
        raise FileNotFoundError(f"Tree file not found: {tree_path}")
    # In a real scenario, use dendropy or ete3 here
    return None

def load_merged_dataset(data_path: str) -> pd.DataFrame:
    """Load the merged dataset."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Merged dataset not found: {data_path}")
    return pd.read_parquet(data_path) if data_path.endswith('.parquet') else pd.read_csv(data_path)

def compute_phylogenetic_covariance(tree: Any) -> np.ndarray:
    """Compute phylogenetic covariance matrix from tree."""
    # Placeholder
    return np.array([])

def phylogenetic_signal_adjusted_spearman(df: pd.DataFrame, cov_matrix: np.ndarray) -> List[CorrelationResult]:
    """Placeholder for phylogenetic signal adjusted Spearman correlation."""
    return []

def run_pgl_analysis(df: pd.DataFrame, cov_matrix: np.ndarray) -> List[CorrelationResult]:
    """Placeholder for PGLS analysis."""
    return []

def benjamini_hochberg(p_values: List[float]) -> List[float]:
    """Implement Benjamini-Hochberg FDR correction."""
    n = len(p_values)
    if n == 0:
        return []
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    ranks = np.arange(1, n + 1)
    adj_p = sorted_p * n / ranks
    adj_p = np.minimum(adj_p, 1.0)
    # Ensure monotonicity
    for i in range(n - 2, -1, -1):
        adj_p[i] = min(adj_p[i], adj_p[i+1])
    # Restore order
    result = np.zeros(n)
    result[sorted_indices] = adj_p
    return result.tolist()

def filter_results_for_visualization(results: List[CorrelationResult], threshold: float = 0.5) -> List[CorrelationResult]:
    """Filter results for visualization."""
    return [r for r in results if abs(r.rho) >= threshold]

def generate_case_study_report(
    results: List[CorrelationResult], 
    sample_size: int, 
    output_path: str,
    dataset_info: Optional[Dict[str, Any]] = None
) -> None:
    """
    Generate a Descriptive Case Study report when N < 10.
    Implements the schema from T031c:
    - Sample Size
    - Limitations
    - Aggregate Statistics
    - No P-Values (Descriptive only)
    """
    if sample_size >= 10:
        raise ValueError("This function is only for low power cases (N < 10).")

    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Aggregate Statistics
    mean_rho = np.mean([r.rho for r in results]) if results else 0.0
    max_rho = max([abs(r.rho) for r in results]) if results else 0.0
    significant_count = 0 # We do not claim significance with p-values in this mode

    report_lines = [
        "# Descriptive Case Study Report",
        "",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Sample Size",
        f"- **N (Isolates/Species)**: {sample_size}",
        f"- **Status**: Low Power (N < 10)",
        "",
        "## Limitations",
        "- Statistical power is insufficient to reliably detect small to medium effects.",
        "- P-values and formal hypothesis testing (FDR) are not reported due to low sample size.",
        "- Results should be interpreted as descriptive observations only, not definitive associations.",
        "- High risk of Type II errors (false negatives).",
        "",
        "## Aggregate Statistics",
        f"- **Mean Correlation Coefficient (|ρ|)**: {abs(mean_rho):.4f}",
        f"- **Maximum Absolute Correlation (|ρ|)**: {max_rho:.4f}",
        f"- **Total Features Analyzed**: {len(results)}",
        "",
        "## Top Observations (Descriptive)",
        ""
    ]

    if not results:
        report_lines.append("No genomic features were analyzed or available.")
    else:
        # Sort by absolute correlation
        sorted_results = sorted(results, key=lambda x: abs(x.rho), reverse=True)
        report_lines.append("| Feature ID | Correlation (ρ) | Direction |")
        report_lines.append("| :--- | :--- | :--- |")
        
        for r in sorted_results:
            direction = "Positive" if r.rho > 0 else "Negative"
            report_lines.append(f"| {r.feature_id} | {r.rho:.4f} | {direction} |")

    report_lines.extend([
        "",
        "## Conclusion",
        f"With only {sample_size} data points, this analysis serves as a preliminary case study.",
        "Future work requires a larger dataset (N ≥ 30) to apply Phylogenetic Generalized Least Squares (PGLS)",
        "and generate statistically robust inferences.",
        ""
    ])

    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))

    logger.info(f"Case study report generated at {output_path}")

def main():
    """
    Main entry point for correlation analysis.
    Handles the low power (N < 10) case by generating a case study report.
    """
    # Configuration paths (relative to project root)
    # Assuming standard project structure
    base_path = Path(__file__).resolve().parent.parent.parent
    data_path = base_path / "data" / "processed" / "merged_dataset.parquet"
    tree_path = base_path / "data" / "processed" / "tree.newick"
    output_path = base_path / "output" / "case_study_report.md"

    # Check if data exists
    if not data_path.exists():
        raise FileNotFoundError(f"Required dataset not found: {data_path}")

    try:
        df = load_merged_dataset(str(data_path))
    except Exception as e:
        raise AnalysisError(f"Failed to load dataset: {e}")

    # Determine sample size
    # Assuming the dataset has a row per isolate/species
    n = len(df)
    
    logger.info(f"Loaded dataset with {n} samples.")

    if n < 10:
        logger.warning(f"Low sample size detected (N={n}). Generating descriptive case study report.")
        
        # Load features and compute correlations (Descriptive only, no p-values)
        # For the purpose of this task, we assume 'results' would be populated by a 
        # simple correlation calculation if the full pipeline were run, 
        # but since we are in the low-power branch, we simulate the structure 
        # or run a simple correlation if the data is available.
        
        # To make this runnable with real data if available:
        # We need to identify the phenotype column and feature columns.
        # Assuming 'phenotype_score' is the target and others are features.
        
        results = []
        if 'phenotype_score' in df.columns:
            target = df['phenotype_score'].dropna()
            feature_cols = [c for c in df.columns if c != 'phenotype_score' and c not in ['strain_id', 'species']]
            
            for col in feature_cols:
                if col in df.columns:
                    feature = df[col].dropna()
                    # Align indices
                    common_idx = target.index.intersection(feature.index)
                    if len(common_idx) > 1:
                        # Simple Spearman correlation (descriptive)
                        corr, _ = target.loc[common_idx].corr(feature.loc[common_idx], method='spearman')
                        if not np.isnan(corr):
                            results.append(CorrelationResult(
                                feature_id=col,
                                rho=corr,
                                p_value=0.0, # Not reported
                                adj_p_value=0.0, # Not reported
                                n=len(common_idx)
                            ))
        
        # Generate the report
        generate_case_study_report(
            results=results,
            sample_size=n,
            output_path=str(output_path),
            dataset_info={'source': str(data_path)}
        )
        
        logger.info("Case study report generation complete.")
        return

    else:
        # Standard path (N >= 10) - not implemented in this specific task scope
        # but required for the file to be complete.
        logger.info(f"Sample size {n} is sufficient for standard analysis.")
        # In a real implementation, this would call run_pgl_analysis or similar
        # and write to results.csv.
        # For this task (T031b), we focus on the N < 10 path.
        pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()