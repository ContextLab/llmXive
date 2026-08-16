"""
Hypothesis Testing Module for GitHub Issue Resolution Analysis.

Implements Kruskal-Wallis test for programming language groups with:
1. Holm-Bonferroni correction for independent tests
2. Westfall-Young permutation for label dependency

Outputs results to data/processed/hypothesis_results.json
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy import stats
from statsmodels.stats.multitest import multipletests
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_PATH = Path("data/processed/cleaned_issues.csv")
OUTPUT_PATH = Path("data/processed/hypothesis_results.json")
PERMUTATION_ITERS = 5000  # Westfall-Young permutation count


def load_cleaned_data() -> pd.DataFrame:
    """Load the cleaned dataset from CSV."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Cleaned data file not found at {DATA_PATH}. "
            "Run preprocessing pipeline first (T010/T011)."
        )
    df = pd.read_csv(DATA_PATH)
    logger.info(f"Loaded {len(df)} issues from {DATA_PATH}")
    return df


def prepare_groups_for_test(df: pd.DataFrame) -> Dict[str, np.ndarray]:
    """
    Prepare resolution time groups by programming language.

    Filters out:
    - Languages with < 30 samples (for statistical power)
    - Missing language or resolution time values

    Returns:
        Dict mapping language -> array of resolution times (hours)
    """
    # Filter valid data
    valid_df = df[
        (df['language'].notna()) &
        (df['language'] != '') &
        (df['resolution_time_hours'].notna()) &
        (df['resolution_time_hours'] >= 0)
    ].copy()

    # Group by language
    groups = valid_df.groupby('language')['resolution_time_hours'].apply(
        lambda x: x.values
    ).to_dict()

    # Filter small groups (minimum 30 samples for power)
    min_samples = 30
    filtered_groups = {
        lang: times for lang, times in groups.items()
        if len(times) >= min_samples
    }

    logger.info(f"Prepared {len(filtered_groups)} language groups (min {min_samples} samples each)")
    logger.info(f"Languages: {list(filtered_groups.keys())}")

    return filtered_groups


def perform_kruskal_wallis(groups: Dict[str, np.ndarray]) -> Tuple[float, float]:
    """
    Perform Kruskal-Wallis H-test across all language groups.

    H0: All language groups have the same median resolution time.
    H1: At least one language group has a different median.

    Returns:
        Tuple of (H statistic, p-value)
    """
    if len(groups) < 2:
        raise ValueError("Need at least 2 groups for Kruskal-Wallis test")

    sample_arrays = list(groups.values())
    h_stat, p_value = stats.kruskal(*sample_arrays)

    logger.info(f"Kruskal-Wallis H-statistic: {h_stat:.4f}")
    logger.info(f"Kruskal-Wallis p-value: {p_value:.6f}")

    return h_stat, p_value


def perform_pairwise_comparisons(
    groups: Dict[str, np.ndarray]
) -> List[Dict[str, Any]]:
    """
    Perform pairwise Mann-Whitney U tests between all language groups.

    Applies Holm-Bonferroni correction for multiple comparisons.

    Returns:
        List of pairwise comparison results with corrected p-values.
    """
    languages = list(groups.keys())
    n_langs = len(languages)
    comparisons = []
    raw_pvalues = []
    pairs = []

    # Perform all pairwise tests
    for i in range(n_langs):
        for j in range(i + 1, n_langs):
            lang1, lang2 = languages[i], languages[j]
            u_stat, p_val = stats.mannwhitneyu(
                groups[lang1], groups[lang2],
                alternative='two-sided'
            )
            raw_pvalues.append(p_val)
            pairs.append((lang1, lang2))
            comparisons.append({
                'group1': lang1,
                'group2': lang2,
                'sample1_size': len(groups[lang1]),
                'sample2_size': len(groups[lang2]),
                'u_statistic': u_stat,
                'raw_pvalue': p_val
            })

    # Apply Holm-Bonferroni correction
    if len(raw_pvalues) > 0:
        corrected = multipletests(
            raw_pvalues,
            method='holm',
            is_sorted=False
        )
        corrected_pvalues = corrected[1]

        for idx, comp in enumerate(comparisons):
            comp['holm_corrected_pvalue'] = corrected_pvalues[idx]
            comp['is_significant_holm'] = corrected_pvalues[idx] < 0.05

    logger.info(f"Performed {len(comparisons)} pairwise comparisons with Holm-Bonferroni correction")

    return comparisons


def perform_westfall_young_permutation(
    groups: Dict[str, np.ndarray],
    n_perms: int = PERMUTATION_ITERS,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Perform Westfall-Young permutation test to account for label dependency.

    This method:
    1. Computes the observed test statistic (max of all pairwise U statistics)
    2. Permutes group labels n_perms times
    3. For each permutation, computes the max statistic
    4. Calculates the proportion of permuted stats >= observed stat

    This controls the family-wise error rate (FWER) under dependency.

    Returns:
        Dict with permutation p-value and distribution statistics.
    """
    logger.info(f"Starting Westfall-Young permutation test with {n_perms} iterations...")

    # Flatten data and create label array
    all_times = []
    all_labels = []
    for lang, times in groups.items():
        all_times.extend(times)
        all_labels.extend([lang] * len(times))

    all_times = np.array(all_times)
    all_labels = np.array(all_labels)
    unique_langs = list(groups.keys())

    # Compute observed max statistic (max of all pairwise U stats)
    observed_max_stat = 0.0
    for i in range(len(unique_langs)):
        for j in range(i + 1, len(unique_langs)):
            lang1, lang2 = unique_langs[i], unique_langs[j]
            mask1 = all_labels == lang1
            mask2 = all_labels == lang2
            stat, _ = stats.mannwhitneyu(
                all_times[mask1], all_times[mask2],
                alternative='two-sided'
            )
            observed_max_stat = max(observed_max_stat, stat)

    logger.info(f"Observed max U-statistic: {observed_max_stat:.4f}")

    # Permutation loop
    rng = np.random.default_rng(random_state)
    permuted_max_stats = []

    for iter_idx in range(n_perms):
        # Permute labels
        shuffled_labels = rng.permutation(all_labels)

        # Compute max statistic for this permutation
        perm_max_stat = 0.0
        for i in range(len(unique_langs)):
            for j in range(i + 1, len(unique_langs)):
                lang1, lang2 = unique_langs[i], unique_langs[j]
                mask1 = shuffled_labels == lang1
                mask2 = shuffled_labels == lang2
                stat, _ = stats.mannwhitneyu(
                    all_times[mask1], all_times[mask2],
                    alternative='two-sided'
                )
                perm_max_stat = max(perm_max_stat, stat)

        permuted_max_stats.append(perm_max_stat)

        if (iter_idx + 1) % 1000 == 0:
            logger.info(f"Permutation {iter_idx + 1}/{n_perms} completed")

    permuted_max_stats = np.array(permuted_max_stats)

    # Calculate Westfall-Young p-value
    # Proportion of permuted max stats >= observed max stat
    wy_pvalue = np.mean(permuted_max_stats >= observed_max_stat)

    # Also compute two-sided p-value accounting for direction
    # (though U-stat is always positive, we consider the extremeness)
    wy_pvalue_two_sided = np.mean(
        np.abs(permuted_max_stats - np.mean(permuted_max_stats)) >=
        np.abs(observed_max_stat - np.mean(permuted_max_stats))
    )

    result = {
        'observed_max_statistic': float(observed_max_stat),
        'permuted_max_statistics_mean': float(np.mean(permuted_max_stats)),
        'permuted_max_statistics_std': float(np.std(permuted_max_stats)),
        'permuted_max_statistics_min': float(np.min(permuted_max_stats)),
        'permuted_max_statistics_max': float(np.max(permuted_max_stats)),
        'westfall_young_pvalue': float(wy_pvalue),
        'westfall_young_pvalue_two_sided': float(wy_pvalue_two_sided),
        'n_permutations': n_perms,
        'random_state': random_state,
        'is_significant_wy': wy_pvalue < 0.05
    }

    logger.info(f"Westfall-Young p-value: {wy_pvalue:.6f}")
    logger.info(f"Westfall-Young result: {'Significant' if wy_pvalue < 0.05 else 'Not significant'}")

    return result


def analyze_hypotheses(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Full hypothesis testing pipeline:
    1. Prepare groups
    2. Kruskal-Wallis omnibus test
    3. Pairwise comparisons with Holm-Bonferroni
    4. Westfall-Young permutation test

    Returns:
        Comprehensive results dictionary.
    """
    logger.info("Starting hypothesis testing analysis...")

    # Prepare data
    groups = prepare_groups_for_test(df)

    if len(groups) < 2:
        raise ValueError(
            f"Insufficient groups for testing. Found {len(groups)} groups. "
            "Need at least 2 language groups with >= 30 samples each."
        )

    # Kruskal-Wallis test
    h_stat, kw_pvalue = perform_kruskal_wallis(groups)

    # Pairwise comparisons
    pairwise_results = perform_pairwise_comparisons(groups)

    # Westfall-Young permutation test
    wy_results = perform_westfall_young_permutation(groups)

    # Compile results
    results = {
        'omnibus_test': {
            'test_name': 'Kruskal-Wallis H-test',
            'h_statistic': float(h_stat),
            'p_value': float(kw_pvalue),
            'degrees_of_freedom': len(groups) - 1,
            'is_significant': kw_pvalue < 0.05,
            'interpretation': (
                "There is a statistically significant difference in median resolution times "
                "across programming languages." if kw_pvalue < 0.05 else
                "There is no statistically significant difference in median resolution times "
                "across programming languages."
            )
        },
        'pairwise_comparisons': {
            'method': 'Mann-Whitney U with Holm-Bonferroni correction',
            'n_comparisons': len(pairwise_results),
            'significant_comparisons': sum(
                1 for p in pairwise_results if p['is_significant_holm']
            ),
            'comparisons': pairwise_results
        },
        'westfall_young_permutation': wy_results,
        'metadata': {
            'n_groups': len(groups),
            'group_sizes': {lang: len(times) for lang, times in groups.items()},
            'total_samples': sum(len(times) for times in groups.values()),
            'min_samples_per_group': 30,
            'permutation_iterations': PERMUTATION_ITERS
        }
    }

    logger.info("Hypothesis testing analysis complete.")
    return results


def save_results(results: Dict[str, Any], output_path: Path = OUTPUT_PATH) -> None:
    """Save results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Results saved to {output_path}")


def main() -> None:
    """Main entry point for hypothesis testing."""
    logger.info("=== Starting Hypothesis Testing Pipeline ===")

    try:
        # Load data
        df = load_cleaned_data()

        # Run analysis
        results = analyze_hypotheses(df)

        # Save results
        save_results(results)

        # Print summary
        print("\n" + "="*60)
        print("HYPOTHESIS TESTING SUMMARY")
        print("="*60)
        print(f"\nOmnibus Test (Kruskal-Wallis):")
        print(f"  H-statistic: {results['omnibus_test']['h_statistic']:.4f}")
        print(f"  p-value: {results['omnibus_test']['p_value']:.6f}")
        print(f"  Significant: {results['omnibus_test']['is_significant']}")

        print(f"\nPairwise Comparisons (Holm-Bonferroni):")
        print(f"  Total comparisons: {results['pairwise_comparisons']['n_comparisons']}")
        print(f"  Significant (α=0.05): {results['pairwise_comparisons']['significant_comparisons']}")

        print(f"\nWestfall-Young Permutation Test:")
        print(f"  p-value: {results['westfall_young_permutation']['westfall_young_pvalue']:.6f}")
        print(f"  Significant (α=0.05): {results['westfall_young_permutation']['is_significant_wy']}")

        print(f"\nResults saved to: {OUTPUT_PATH}")
        print("="*60)

    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Analysis error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
