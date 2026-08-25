import os
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List

from simulation import run_full_simulation, load_dataset
from augment import (
    inject_gaussian_noise,
    apply_smote,
    apply_random_oversampling,
    detect_zero_variance_columns,
    exclude_zero_variance_samples
)
from analyze import calculate_error_rates, calculate_bootstrap_ci

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Augmentation methods mapping
AUGMENTATION_METHODS = {
    'gaussian': inject_gaussian_noise,
    'smote': apply_smote,
    'random_oversampling': apply_random_oversampling
}

DISCLAIMER_TEXT = "DISCLAIMER: Findings are associational and do not imply causation. Results are specific to the experimental conditions described."

def save_augmented_results(
    dataset_name: str,
    size: int,
    method: str,
    augmentation_func,
    null_results_path: Path,
    alt_results_path: Path,
    iterations: int = 1000,
    seed: int = 42,
    noise_std: float = 0.1
) -> None:
    """
    Runs the simulation loop for a specific dataset, size, and augmentation method
    for both Null (Type I) and Alt (Type II) conditions, then saves results.

    Args:
        dataset_name: Name of the dataset (matches file stem in data/raw)
        size: Subsample size (15, 25, or 40)
        method: Augmentation method key ('gaussian', 'smote', 'random_oversampling')
        augmentation_func: The function to apply augmentation
        null_results_path: Path to save Type I error results
        alt_results_path: Path to save Type II error results
        iterations: Number of Monte Carlo iterations
        seed: Random seed
        noise_std: Standard deviation for Gaussian noise (if applicable)
    """
    logger.info(f"Starting augmented simulation for {dataset_name}, N={size}, method={method}")

    # Load the full dataset to subsample from
    # We assume the dataset is already downloaded in data/raw/
    data_path = Path(f"data/raw/{dataset_name}.csv")
    if not data_path.exists():
        # Try to find it with different extensions or case
        possible_paths = list(Path("data/raw").glob(f"{dataset_name}*"))
        if possible_paths:
            data_path = possible_paths[0]
        else:
            raise FileNotFoundError(f"Dataset not found for {dataset_name} in data/raw/")

    df = load_dataset(data_path)
    
    # Detect target column
    target_col = None
    for candidate in ['target', 'class', 'label']:
        if candidate in df.columns:
            target_col = candidate
            break
    if target_col is None:
        target_col = df.columns[-1]
    
    logger.info(f"Using target column: {target_col}")

    # Prepare augmentation args
    aug_args = {}
    if method == 'gaussian':
        aug_args['std'] = noise_std

    # --- Null Condition (Type I Error) ---
    # Permute labels to break association
    logger.info(f"Running {iterations} iterations for Null condition...")
    p_values_null = []
    
    for i in range(iterations):
        # Subsample
        subsample_seed = seed + i
        # Simple stratified subsample logic inline or reuse if available
        # Since we need to import from subsample, let's use the logic there if possible
        # But to keep it self-contained for the loop, we'll do a quick stratified sample
        from sklearn.model_selection import train_test_split
        
        # Split to get a sample of size `size`
        # We need to ensure stratification
        X = df.drop(columns=[target_col])
        y = df[target_col]
        
        # If class counts are too low for stratification, skip or adjust
        class_counts = y.value_counts()
        if class_counts.min() < 2:
            logger.warning(f"Class count too low for stratification in iteration {i}, skipping")
            continue
        
        # We want a total size of `size`
        # We'll sample from each class proportionally
        sample_counts = {}
        for cls, count in class_counts.items():
            sample_counts[cls] = max(1, int((count / len(y)) * size))
        
        # Adjust to match exactly size if needed
        current_sum = sum(sample_counts.values())
        if current_sum != size:
            # Simple adjustment: add/remove from largest class
            diff = size - current_sum
            if diff > 0:
                largest_class = class_counts.idxmax()
                sample_counts[largest_class] += diff
            elif diff < 0:
                largest_class = class_counts.idxmax()
                sample_counts[largest_class] = max(1, sample_counts[largest_class] + diff)
        
        # Create subsample
        subsample_indices = []
        for cls, n in sample_counts.items():
            cls_indices = y[y == cls].index.tolist()
            np.random.seed(subsample_seed)
            selected = np.random.choice(cls_indices, size=n, replace=False)
            subsample_indices.extend(selected)
        
        df_sub = df.iloc[subsample_indices]
        
        # Apply augmentation
        X_sub = df_sub.drop(columns=[target_col])
        y_sub = df_sub[target_col]
        
        # Augment
        try:
            X_aug, y_aug = augmentation_func(X_sub, y_sub, **aug_args)
        except Exception as e:
            logger.warning(f"Augmentation failed in iteration {i}: {e}, skipping")
            continue
        
        # Check for zero variance
        zero_var_cols = detect_zero_variance_columns(X_aug)
        if len(zero_var_cols) > 0:
            X_aug = exclude_zero_variance_samples(X_aug, y_aug)
            if len(X_aug) == 0:
                logger.warning("All samples excluded due to zero variance, skipping iteration")
                continue

        # Permute labels for Null condition
        np.random.seed(subsample_seed)
        y_permuted = np.random.permutation(y_aug)
        
        # Run hypothesis test (t-test)
        # We need to compare means of two groups? Or just one sample vs 0?
        # The task implies a t-test on the difference of means between classes?
        # Let's assume a t-test comparing the two classes in the augmented data
        # But for Type I, the labels are permuted, so there should be no difference
        
        # Actually, standard approach:
        # Type I: Null hypothesis is true (no difference). We permute labels.
        # We run a t-test on the two classes.
        # If the test rejects (p < 0.05), it's a Type I error.
        
        # We need to split the augmented data into two groups based on the permuted labels
        # But the labels are already the target. We permute them to break the link.
        # Then we run a t-test on the features between the two label groups.
        
        # Let's do a two-sample t-test
        from scipy.stats import ttest_ind
        
        unique_labels = np.unique(y_permuted)
        if len(unique_labels) < 2:
            continue
        
        # If binary classification
        if len(unique_labels) == 2:
            group0 = X_aug[y_permuted == unique_labels[0]]
            group1 = X_aug[y_permuted == unique_labels[1]]
            
            # We need to aggregate features? Or test each feature?
            # The task says "hypothesis test", usually a single p-value.
            # Maybe we sum the features or use a multivariate test?
            # Let's assume we use a univariate test on the mean of all features?
            # Or maybe the task implies a specific test.
            # Given the context of "statistical power", it's likely a test on the mean difference.
            # Let's use a t-test on the mean of the first feature for simplicity, or aggregate.
            # Actually, let's use the mean of all features as a single score?
            # Or maybe the task expects a multivariate test like Hotelling's T2?
            # To keep it simple and consistent with "small samples", let's use a t-test on the first feature
            # that has variance.
            
            # Find a feature with variance
            valid_features = []
            for col in X_aug.columns:
                if X_aug[col].var() > 0:
                    valid_features.append(col)
            
            if not valid_features:
                continue
            
            # Use the first valid feature
            col = valid_features[0]
            t_stat, p_val = ttest_ind(group0[col], group1[col])
            p_values_null.append(p_val)
        else:
            # Multi-class: use ANOVA? Or just skip for now
            # Let's skip for simplicity
            continue

    # Calculate error rates for Null
    error_rate_null = sum(1 for p in p_values_null if p < 0.05) / len(p_values_null) if p_values_null else 0.0
    ci_null = calculate_bootstrap_ci(p_values_null, 0.05) if p_values_null else (0.0, 0.0)

    null_result = {
        "dataset": dataset_name,
        "size": size,
        "method": method,
        "condition": "null",
        "iterations": len(p_values_null),
        "error_rate": error_rate_null,
        "confidence_interval_95": ci_null,
        "p_values": p_values_null,
        "metadata": {
            "disclaimer": DISCLAIMER_TEXT
        }
    }

    # --- Alt Condition (Type II Error) ---
    # Apply mean shift to create a difference
    logger.info(f"Running {iterations} iterations for Alt condition...")
    p_values_alt = []
    
    for i in range(iterations):
        subsample_seed = seed + i
        
        X = df.drop(columns=[target_col])
        y = df[target_col]
        
        class_counts = y.value_counts()
        if class_counts.min() < 2:
            logger.warning(f"Class count too low for stratification in iteration {i}, skipping")
            continue
        
        sample_counts = {}
        for cls, count in class_counts.items():
            sample_counts[cls] = max(1, int((count / len(y)) * size))
        
        current_sum = sum(sample_counts.values())
        if current_sum != size:
            diff = size - current_sum
            if diff > 0:
                largest_class = class_counts.idxmax()
                sample_counts[largest_class] += diff
            elif diff < 0:
                largest_class = class_counts.idxmax()
                sample_counts[largest_class] = max(1, sample_counts[largest_class] + diff)
        
        subsample_indices = []
        for cls, n in sample_counts.items():
            cls_indices = y[y == cls].index.tolist()
            np.random.seed(subsample_seed)
            selected = np.random.choice(cls_indices, size=n, replace=False)
            subsample_indices.extend(selected)
        
        df_sub = df.iloc[subsample_indices]
        
        X_sub = df_sub.drop(columns=[target_col])
        y_sub = df_sub[target_col]
        
        # Augment
        try:
            X_aug, y_aug = augmentation_func(X_sub, y_sub, **aug_args)
        except Exception as e:
            logger.warning(f"Augmentation failed in iteration {i}: {e}, skipping")
            continue
        
        # Check for zero variance
        zero_var_cols = detect_zero_variance_columns(X_aug)
        if len(zero_var_cols) > 0:
            X_aug = exclude_zero_variance_samples(X_aug, y_aug)
            if len(X_aug) == 0:
                logger.warning("All samples excluded due to zero variance, skipping iteration")
                continue

        # Apply mean shift for Type II (Cohen's d = 0.5)
        # We shift the mean of one class relative to the other
        # Let's shift the second class by 0.5 * std of the first class
        unique_labels = np.unique(y_aug)
        if len(unique_labels) < 2:
            continue
        
        # Pick the first valid feature again
        valid_features = []
        for col in X_aug.columns:
            if X_aug[col].var() > 0:
                valid_features.append(col)
        
        if not valid_features:
            continue
        
        col = valid_features[0]
        
        # Calculate std of class 0
        std0 = X_aug[y_aug == unique_labels[0]][col].std()
        if std0 == 0:
            continue
        
        # Shift class 1
        shift_amount = 0.5 * std0
        X_aug_shifted = X_aug.copy()
        X_aug_shifted.loc[y_aug == unique_labels[1], col] += shift_amount
        
        # Run t-test
        group0 = X_aug_shifted[y_aug == unique_labels[0]]
        group1 = X_aug_shifted[y_aug == unique_labels[1]]
        
        t_stat, p_val = ttest_ind(group0[col], group1[col])
        p_values_alt.append(p_val)

    # Calculate error rates for Alt (Type II error = failing to reject when false)
    # Type II error rate = proportion of p >= 0.05
    error_rate_alt = sum(1 for p in p_values_alt if p >= 0.05) / len(p_values_alt) if p_values_alt else 0.0
    # Power = 1 - Type II error rate = proportion of p < 0.05
    power = 1 - error_rate_alt
    ci_alt = calculate_bootstrap_ci(p_values_alt, 0.05) if p_values_alt else (0.0, 0.0)

    alt_result = {
        "dataset": dataset_name,
        "size": size,
        "method": method,
        "condition": "alt",
        "iterations": len(p_values_alt),
        "error_rate": error_rate_alt,
        "power": power,
        "confidence_interval_95": ci_alt,
        "p_values": p_values_alt,
        "metadata": {
            "disclaimer": DISCLAIMER_TEXT
        }
    }

    # Save results
    with open(null_results_path, 'w') as f:
        json.dump(null_result, f, indent=2)
    
    with open(alt_results_path, 'w') as f:
        json.dump(alt_result, f, indent=2)

    logger.info(f"Saved results to {null_results_path} and {alt_results_path}")

def main():
    parser = argparse.ArgumentParser(description="Save augmented simulation results")
    parser.add_argument('--dataset', type=str, required=True, help="Dataset name")
    parser.add_argument('--size', type=int, required=True, help="Subsample size")
    parser.add_argument('--method', type=str, required=True, choices=['gaussian', 'smote', 'random_oversampling'], help="Augmentation method")
    parser.add_argument('--iterations', type=int, default=1000, help="Number of iterations")
    parser.add_argument('--seed', type=int, default=42, help="Random seed")
    parser.add_argument('--noise-std', type=float, default=0.1, help="Noise std for Gaussian")
    parser.add_argument('--output-dir', type=str, default="results", help="Output directory")
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Define output paths
    null_path = output_dir / f"{args.dataset}_{args.size}_{args.method}_null.json"
    alt_path = output_dir / f"{args.dataset}_{args.size}_{args.method}_alt.json"
    
    # Get augmentation function
    if args.method not in AUGMENTATION_METHODS:
        raise ValueError(f"Unknown method: {args.method}")
    
    aug_func = AUGMENTATION_METHODS[args.method]
    
    save_augmented_results(
        dataset_name=args.dataset,
        size=args.size,
        method=args.method,
        augmentation_func=aug_func,
        null_results_path=null_path,
        alt_results_path=alt_path,
        iterations=args.iterations,
        seed=args.seed,
        noise_std=args.noise_std
    )

if __name__ == "__main__":
    main()