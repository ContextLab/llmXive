import csv
import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)

def load_metrics(input_path: str) -> pd.DataFrame:
    """Load metrics from a CSV file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Metrics file not found: {input_path}")
    return pd.read_csv(input_path)

def save_metrics(df: pd.DataFrame, output_path: str) -> None:
    """Save metrics DataFrame to a CSV file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved metrics to {output_path}")

def load_json_file(file_path: str) -> Dict:
    """Load a JSON file and return its contents as a dictionary."""
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json_file(data: Dict, file_path: str) -> None:
    """Save a dictionary to a JSON file."""
    output_file = Path(file_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved JSON to {file_path}")

def stratified_split(
    input_path: str,
    train_output_path: str,
    test_output_path: str,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split the metrics CSV into train and test sets while preserving label balance.
    
    Args:
        input_path: Path to the input metrics CSV file.
        train_output_path: Path to save the training set CSV.
        test_output_path: Path to save the test set CSV.
        test_size: Proportion of the dataset to include in the test split.
        random_state: Random seed for reproducibility.
        
    Returns:
        Tuple of (train_df, test_df) DataFrames.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the 'label' column is missing or if stratification fails.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input metrics file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    if 'label' not in df.columns:
        raise ValueError("Input CSV must contain a 'label' column for stratified splitting.")
    
    # Perform stratified split
    try:
        train_df, test_df = train_test_split(
            df,
            test_size=test_size,
            random_state=random_state,
            stratify=df['label']
        )
    except ValueError as e:
        # Handle cases where a class has too few samples for stratification
        logger.warning(f"Stratified split failed: {e}. Falling back to random split.")
        train_df, test_df = train_test_split(
            df,
            test_size=test_size,
            random_state=random_state
        )
    
    # Save to CSV
    save_metrics(train_df, train_output_path)
    save_metrics(test_df, test_output_path)
    
    logger.info(f"Split complete. Train size: {len(train_df)}, Test size: {len(test_df)}")
    return train_df, test_df

def train_test_stratified(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Wrapper for stratified split on a DataFrame.
    
    Args:
        df: Input DataFrame with a 'label' column.
        test_size: Proportion for test set.
        random_state: Random seed.
        
    Returns:
        Tuple of (train_df, test_df).
    """
    if 'label' not in df.columns:
        raise ValueError("DataFrame must contain a 'label' column.")
    return train_test_split(df, test_size=test_size, random_state=random_state, stratify=df['label'])

def train_test_random(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Wrapper for random split on a DataFrame.
    
    Args:
        df: Input DataFrame.
        test_size: Proportion for test set.
        random_state: Random seed.
        
    Returns:
        Tuple of (train_df, test_df).
    """
    return train_test_split(df, test_size=test_size, random_state=random_state)

def verify_split_distribution(
    original_df: pd.DataFrame,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    tolerance: float = 0.05
) -> bool:
    """
    Verify that the label distribution in train/test matches the original within tolerance.
    
    Args:
        original_df: Original DataFrame.
        train_df: Training set DataFrame.
        test_df: Test set DataFrame.
        tolerance: Allowed deviation (e.g., 0.05 for 5%).
        
    Returns:
        True if distributions match within tolerance, False otherwise.
    """
    if 'label' not in original_df.columns:
        return False
    
    orig_dist = original_df['label'].value_counts(normalize=True)
    train_dist = train_df['label'].value_counts(normalize=True)
    test_dist = test_df['label'].value_counts(normalize=True)
    
    # Check train distribution
    for label in orig_dist.index:
        orig_val = orig_dist.get(label, 0.0)
        train_val = train_dist.get(label, 0.0)
        if abs(orig_val - train_val) > tolerance:
            logger.warning(f"Train distribution mismatch for label {label}: {orig_val} vs {train_val}")
            return False
    
    # Check test distribution
    for label in orig_dist.index:
        orig_val = orig_dist.get(label, 0.0)
        test_val = test_dist.get(label, 0.0)
        if abs(orig_val - test_val) > tolerance:
            logger.warning(f"Test distribution mismatch for label {label}: {orig_val} vs {test_val}")
            return False
    
    return True

def calculate_baseline(train_df: pd.DataFrame) -> float:
    """Calculate the mean connectivity of the success class."""
    if 'label' not in train_df.columns or 'global_connectivity' not in train_df.columns:
        raise ValueError("DataFrame must contain 'label' and 'global_connectivity' columns.")
    
    success_df = train_df[train_df['label'] == 'success']
    if len(success_df) == 0:
        raise ValueError("No 'success' class samples found in training data.")
    
    return success_df['global_connectivity'].mean()

def calculate_20th_percentile_threshold(train_df: pd.DataFrame) -> float:
    """
    Calculate the 20th percentile of the combined distribution of connectivity and branching
    for the success class.
    """
    if 'label' not in train_df.columns:
        raise ValueError("DataFrame must contain a 'label' column.")
    
    success_df = train_df[train_df['label'] == 'success']
    if len(success_df) < 5:
        raise ValueError(f"Success class has fewer than 5 samples ({len(success_df)}). Halting pipeline.")
    
    if 'global_connectivity' not in success_df.columns or 'avg_branching_factor' not in success_df.columns:
        raise ValueError("DataFrame must contain 'global_connectivity' and 'avg_branching_factor' columns.")
    
    # Flatten both columns into a single array
    combined = pd.concat([success_df['global_connectivity'], success_df['avg_branching_factor']])
    
    threshold = combined.quantile(0.20)
    return float(threshold)

def calculate_f1_max_threshold(train_df: pd.DataFrame) -> float:
    """
    Calculate the optimal F1-score threshold for comparative analysis.
    NOTE: This is for reporting only and MUST NOT override the primary 20th percentile threshold.
    """
    if 'label' not in train_df.columns or 'global_connectivity' not in train_df.columns:
        raise ValueError("DataFrame must contain 'label' and 'global_connectivity' columns.")
    
    # Sort unique thresholds
    thresholds = sorted(train_df['global_connectivity'].unique())
    best_f1 = 0.0
    best_threshold = 0.0
    
    for thresh in thresholds:
        preds = (train_df['global_connectivity'] < thresh).astype(int)
        true_labels = (train_df['label'] == 'failure').astype(int)
        
        tp = ((preds == 1) & (true_labels == 1)).sum()
        fp = ((preds == 1) & (true_labels == 0)).sum()
        fn = ((preds == 0) & (true_labels == 1)).sum()
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = thresh
    
    return best_threshold

def predict_collapse(test_df: pd.DataFrame, threshold: float) -> pd.Series:
    """
    Predict collapse based on the threshold.
    Assumes lower connectivity indicates collapse (failure).
    """
    if 'global_connectivity' not in test_df.columns:
        raise ValueError("DataFrame must contain 'global_connectivity' column.")
    
    return (test_df['global_connectivity'] < threshold).astype(int)

def evaluate_performance(test_df: pd.DataFrame, predictions: pd.Series) -> Dict[str, Any]:
    """
    Evaluate performance metrics: Precision, Recall, F1, Confusion Matrix.
    """
    if 'label' not in test_df.columns:
        raise ValueError("DataFrame must contain 'label' column.")
    
    true_labels = (test_df['label'] == 'failure').astype(int)
    
    tp = ((predictions == 1) & (true_labels == 1)).sum()
    tn = ((predictions == 0) & (true_labels == 0)).sum()
    fp = ((predictions == 1) & (true_labels == 0)).sum()
    fn = ((predictions == 0) & (true_labels == 1)).sum()
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'accuracy': accuracy,
        'confusion_matrix': {
            'true_positive': int(tp),
            'true_negative': int(tn),
            'false_positive': int(fp),
            'false_negative': int(fn)
        }
    }

def calculate_correlation(test_df: pd.DataFrame) -> float:
    """Calculate Pearson correlation between connectivity and collapse."""
    if 'global_connectivity' not in test_df.columns or 'label' not in test_df.columns:
        raise ValueError("DataFrame must contain 'global_connectivity' and 'label' columns.")
    
    true_labels = (test_df['label'] == 'failure').astype(int)
    return float(test_df['global_connectivity'].corr(true_labels))

def run_sensitivity_analysis_threshold(
    test_df: pd.DataFrame,
    thresholds: List[float]
) -> Dict[str, Any]:
    """
    Run sensitivity analysis over a set of thresholds.
    """
    results = {}
    for thresh in thresholds:
        preds = predict_collapse(test_df, thresh)
        metrics = evaluate_performance(test_df, preds)
        results[str(thresh)] = metrics
    return results

def run_sensitivity_analysis_percentile(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    percentiles: List[int]
) -> Dict[str, Any]:
    """
    Run sensitivity analysis over a set of percentiles.
    """
    results = {}
    for p in percentiles:
        # Calculate threshold from train set
        combined = pd.concat([
            train_df[train_df['label'] == 'success']['global_connectivity'],
            train_df[train_df['label'] == 'success']['avg_branching_factor']
        ])
        thresh = combined.quantile(p / 100.0)
        
        preds = predict_collapse(test_df, thresh)
        metrics = evaluate_performance(test_df, preds)
        results[str(p)] = {'threshold': thresh, **metrics}
    return results

def calculate_null_distribution(
    test_df: pd.DataFrame,
    n_permutations: int = 1000,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Perform permutation test to establish null distribution.
    """
    import numpy as np
    
    if 'global_connectivity' not in test_df.columns or 'label' not in test_df.columns:
        raise ValueError("DataFrame must contain 'global_connectivity' and 'label' columns.")
    
    true_labels = (test_df['label'] == 'failure').astype(int).values
    connectivity = test_df['global_connectivity'].values
    
    # Observed correlation
    obs_corr = np.corrcoef(connectivity, true_labels)[0, 1]
    
    np.random.seed(random_state)
    null_corrs = []
    for _ in range(n_permutations):
        shuffled_labels = np.random.permutation(true_labels)
        corr = np.corrcoef(connectivity, shuffled_labels)[0, 1]
        null_corrs.append(corr)
    
    null_corrs = np.array(null_corrs)
    p_value = (np.sum(null_corrs >= obs_corr) + 1) / (n_permutations + 1)
    significant = p_value < 0.05
    
    return {
        'observed_correlation': float(obs_corr),
        'p_value': float(p_value),
        'significant': significant,
        'null_distribution_mean': float(np.mean(null_corrs)),
        'null_distribution_std': float(np.std(null_corrs))
    }

def calculate_linear_reasoning_index(graph_path: str) -> float:
    """
    Calculate the linear reasoning index for a graph.
    Ratio of nodes with in-degree=1 AND out-degree=1 AND total edges = total nodes - 1.
    """
    import networkx as nx
    
    try:
        with open(graph_path, 'r') as f:
            graph_data = json.load(f)
        
        G = nx.DiGraph()
        # Reconstruct graph from JSON (assuming standard format with nodes and edges)
        if 'nodes' in graph_data:
            G.add_nodes_from(graph_data['nodes'])
        if 'edges' in graph_data:
            G.add_edges_from(graph_data['edges'])
        
        n_nodes = G.number_of_nodes()
        n_edges = G.number_of_edges()
        
        if n_nodes == 0:
            return 0.0
        
        # Check condition: edges = nodes - 1
        if n_edges != n_nodes - 1:
            return 0.0
        
        # Count nodes with in-degree=1 and out-degree=1
        linear_nodes = 0
        for node in G.nodes():
            if G.in_degree(node) == 1 and G.out_degree(node) == 1:
                linear_nodes += 1
        
        return linear_nodes / n_nodes
    except Exception as e:
        logger.warning(f"Failed to calculate linear reasoning index for {graph_path}: {e}")
        return 0.0

def calculate_power_analysis(train_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate effect size (Cohen's d) and perform post-hoc power analysis.
    """
    import numpy as np
    from scipy import stats
    
    if 'label' not in train_df.columns or 'global_connectivity' not in train_df.columns:
        raise ValueError("DataFrame must contain 'label' and 'global_connectivity' columns.")
    
    success = train_df[train_df['label'] == 'success']['global_connectivity'].values
    failure = train_df[train_df['label'] == 'failure']['global_connectivity'].values
    
    if len(success) < 2 or len(failure) < 2:
        return {'effect_size': 0.0, 'power': 0.0, 'limitation_flag': True}
    
    # Cohen's d
    mean_diff = np.mean(success) - np.mean(failure)
    pooled_std = np.sqrt((np.var(success) + np.var(failure)) / 2)
    cohens_d = mean_diff / pooled_std if pooled_std > 0 else 0.0
    
    # Power analysis (simplified: using t-test power)
    n1, n2 = len(success), len(failure)
    # Approximate power using effect size and sample sizes
    # Using standard power calculation for two-sample t-test
    # This is a simplified approximation
    power = 1.0 - stats.nct.cdf(
        stats.t.ppf(0.975, n1 + n2 - 2),
        n1 + n2 - 2,
        cohens_d * np.sqrt((n1 * n2) / (n1 + n2))
    )
    
    limitation_flag = power < 0.8
    
    return {
        'effect_size': float(cohens_d),
        'power': float(power),
        'limitation_flag': limitation_flag,
        'sample_size_success': int(n1),
        'sample_size_failure': int(n2)
    }

def report_comparative_thresholds(
    threshold_config: Dict,
    f1_max_threshold: Optional[Dict],
    sensitivity_threshold_matrix: Dict,
    sensitivity_percentile_matrix: Dict
) -> Dict[str, Any]:
    """
    Generate a comparative report of thresholds.
    """
    return {
        'primary_threshold': threshold_config.get('threshold'),
        'primary_type': '20th_percentile',
        'f1_max_threshold': f1_max_threshold.get('threshold') if f1_max_threshold else None,
        'sensitivity_threshold_matrix': sensitivity_threshold_matrix,
        'sensitivity_percentile_matrix': sensitivity_percentile_matrix,
        'note': 'Primary threshold (20th percentile) mandated by FR-004. F1-max is for comparative analysis only.'
    }

def generate_results_report(
    baseline_report: Dict,
    threshold_config: Dict,
    f1_max_threshold: Optional[Dict],
    sensitivity_threshold_matrix: Dict,
    sensitivity_percentile_matrix: Dict,
    test_metrics: pd.DataFrame,
    predictions: pd.Series,
    performance_metrics: Dict,
    correlation_result: float,
    null_distribution: Dict,
    linear_reasoning_report: Dict,
    power_analysis: Dict
) -> Dict[str, Any]:
    """
    Generate the final results report combining all metrics.
    """
    return {
        'baseline': baseline_report,
        'threshold_config': threshold_config,
        'f1_max_threshold': f1_max_threshold,
        'sensitivity_threshold_matrix': sensitivity_threshold_matrix,
        'sensitivity_percentile_matrix': sensitivity_percentile_matrix,
        'test_performance': performance_metrics,
        'correlation': {
            'coefficient': correlation_result,
            'significant': null_distribution.get('significant', False)
        },
        'null_distribution': null_distribution,
        'linear_reasoning': linear_reasoning_report,
        'power_analysis': power_analysis,
        'summary': {
            'primary_threshold_used': threshold_config.get('threshold'),
            'test_accuracy': performance_metrics.get('accuracy'),
            'test_f1': performance_metrics.get('f1'),
            'power_sufficient': not power_analysis.get('limitation_flag', True)
        }
    }

def main():
    """
    Main entry point for the evaluator module.
    This function orchestrates the full evaluation pipeline.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Example usage (to be replaced by actual pipeline orchestration)
    # This is a placeholder to demonstrate the module structure
    logger.info("Evaluator module loaded.")
    logger.info("Run stratified_split, calculate_thresholds, and generate_results_report for full pipeline.")

if __name__ == "__main__":
    main()
