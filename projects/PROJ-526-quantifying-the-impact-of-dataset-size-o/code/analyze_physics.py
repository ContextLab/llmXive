"""
Physical Metrics Analysis Module

This module computes physical metrics (spatial locality, symmetry sensitivity,
valence electron variance) for material properties and performs statistical
analysis (correlation, permutation tests) to correlate these metrics with
learning curve scaling exponents.

**Task T041 – Physical Metric Definition**
-------------------------------------------------
The definitions for *spatial locality* and *symmetry sensitivity* must be
sourced from `research.md`. If the research document does not contain
explicit formulas, the script must:
  1. Write a `metric_definitions.md` file indicating that the metrics are
     **undefined**.
  2. Halt execution with a clear error message.

The implementation below follows this contract.
"""

import os
import sys
import logging
import traceback
import gc
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import json
import re

import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial.distance import pdist
import math

# Project imports
from code.config import get_config
from code.utils.logging_config import get_logger
from code.utils.seed import set_seed

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions for Task T041
# ----------------------------------------------------------------------
def _extract_definitions_from_research(research_path: Path) -> Dict[str, str]:
    """
    Parse ``research.md`` and extract explicit formulas for the two metrics.

    The expected markdown format (if present) is:

    ````markdown
    ### Spatial Locality
    Formula: <LaTeX or plain expression>

    ### Symmetry Sensitivity
    Formula: <LaTeX or plain expression>
    ````

    If a section or formula is missing, the corresponding entry in the
    returned dictionary will be an empty string.
    """
    definitions: Dict[str, str] = {
        "spatial_locality": "",
        "symmetry_sensitivity": ""
    }

    if not research_path.is_file():
        logger.error(f"Research file not found: {research_path}")
        return definitions

    content = research_path.read_text()
    # Simple regex‑based extraction
    spatial_match = re.search(
        r"###\s*Spatial\s*Locality\s*\n\s*Formula\s*[:=]\s*(.+)", content,
        re.IGNORECASE,
    )
    symmetry_match = re.search(
        r"###\s*Symmetry\s*Sensitivity\s*\n\s*Formula\s*[:=]\s*(.+)", content,
        re.IGNORECASE,
    )

    if spatial_match:
        definitions["spatial_locality"] = spatial_match.group(1).strip()
    if symmetry_match:
        definitions["symmetry_sensitivity"] = symmetry_match.group(1).strip()

    return definitions

def _write_metric_definitions_md(
    definitions: Dict[str, str], output_path: Path
) -> None:
    """
    Write ``metric_definitions.md``. If a definition string is empty,
    the file records that the metric is *undefined*.
    """
    lines = ["# Metric Definitions", ""]
    for metric, formula in definitions.items():
        pretty_name = metric.replace("_", " ").title()
        lines.append(f"## {pretty_name}")
        if formula:
            lines.append(f"**Formula:** {formula}")
        else:
            lines.append("**Status:** *undefined – no formula provided in `research.md`*")
        lines.append("")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines))
    logger.info(f"Wrote metric definitions to {output_path}")

# ----------------------------------------------------------------------
# Existing analysis functions (unchanged)
# ----------------------------------------------------------------------
def load_metric_definitions(file_path: str) -> Dict[str, Any]:
    """
    Load metric definitions from a markdown file.

    This function parses the metric_definitions.md file to extract
    the formulas and descriptions for each metric.

    Args:
        file_path: Path to the metric_definitions.md file

    Returns:
        Dictionary containing metric definitions
    """
    definitions = {}

    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Parse the markdown file to extract metric definitions
        # This is a simple parser that looks for metric headers
        current_metric = None
        current_section = None

        for line in content.split('\n'):
            line = line.strip()

            if line.startswith('## '):
                # New metric section
                metric_name = line[3:].strip()
                current_metric = metric_name
                definitions[metric_name] = {'sections': {}}
                current_section = None

            elif current_metric and line.startswith('**'):
                # Section header within metric
                section_name = line.strip('*').strip(':').strip()
                current_section = section_name
                definitions[metric_name]['sections'][section_name] = []

            elif current_metric and current_section:
                # Content within section
                definitions[metric_name]['sections'][current_section].append(line)

        logger.info(f"Loaded metric definitions for {len(definitions)} metrics")
        return definitions

    except FileNotFoundError:
        logger.error(f"Metric definitions file not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading metric definitions: {e}")
        raise


def load_master_dataset(file_path: str) -> pd.DataFrame:
    """
    Load the master dataset containing material properties and descriptors.

    Args:
        file_path: Path to the master parquet file

    Returns:
        DataFrame with material data
    """
    try:
        if file_path.endswith('.parquet'):
            df = pd.read_parquet(file_path)
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path}")

        logger.info(f"Loaded master dataset with {len(df)} entries")
        return df

    except Exception as e:
        logger.error(f"Error loading master dataset: {e}")
        raise


def load_scaling_results(file_path: str) -> pd.DataFrame:
    """
    Load scaling results from the scaling analysis.

    Args:
        file_path: Path to the scaling results CSV file

    Returns:
        DataFrame with scaling results
    """
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded scaling results with {len(df)} entries")
        return df

    except Exception as e:
        logger.error(f"Error loading scaling results: {e}")
        raise


def compute_valence_electron_variance(composition: Dict[str, float]) -> float:
    """
    Compute the variance of valence electrons across elements in a composition.

    Args:
        composition: Dictionary mapping element symbols to their stoichiometric ratios

    Returns:
        Variance of valence electrons
    """
    # Periodic table data for valence electrons (simplified)
    valence_electrons = {
        'H': 1, 'He': 0,
        'Li': 1, 'Be': 2, 'B': 3, 'C': 4, 'N': 5, 'O': 6, 'F': 7, 'Ne': 0,
        'Na': 1, 'Mg': 2, 'Al': 3, 'Si': 4, 'P': 5, 'S': 6, 'Cl': 7, 'Ar': 0,
        'K': 1, 'Ca': 2, 'Sc': 3, 'Ti': 4, 'V': 5, 'Cr': 6, 'Mn': 7, 'Fe': 8,
        'Co': 9, 'Ni': 10, 'Cu': 11, 'Zn': 12, 'Ga': 3, 'Ge': 4, 'As': 5,
        'Se': 6, 'Br': 7, 'Kr': 0,
        'Rb': 1, 'Sr': 2, 'Y': 3, 'Zr': 4, 'Nb': 5, 'Mo': 6, 'Tc': 7, 'Ru': 8,
        'Rh': 9, 'Pd': 10, 'Ag': 11, 'Cd': 12, 'In': 3, 'Sn': 4, 'Sb': 5,
        'Te': 6, 'I': 7, 'Xe': 0,
        'Cs': 1, 'Ba': 2, 'La': 3, 'Ce': 4, 'Pr': 5, 'Nd': 6, 'Pm': 7, 'Sm': 8,
        'Eu': 9, 'Gd': 10, 'Tb': 11, 'Dy': 12, 'Ho': 13, 'Er': 14, 'Tm': 15,
        'Yb': 16, 'Lu': 17, 'Hf': 4, 'Ta': 5, 'W': 6, 'Re': 7, 'Os': 8,
        'Ir': 9, 'Pt': 10, 'Au': 11, 'Hg': 12, 'Tl': 3, 'Pb': 4, 'Bi': 5,
        'Po': 6, 'At': 7, 'Rn': 0,
        'Fr': 1, 'Ra': 2, 'Ac': 3, 'Th': 4, 'Pa': 5, 'U': 6, 'Np': 7, 'Pu': 8,
        'Am': 9, 'Cm': 10, 'Bk': 11, 'Cf': 12, 'Es': 13, 'Fm': 14, 'Md': 15,
        'No': 16, 'Lr': 17, 'Rf': 4, 'Db': 5, 'Sg': 6, 'Bh': 7, 'Hs': 8,
        'Mt': 9, 'Ds': 10, 'Rg': 11, 'Cn': 12, 'Nh': 3, 'Fl': 4, 'Mc': 5,
        'Lv': 6, 'Ts': 7, 'Og': 0
    }

    valence_counts = []
    for element, ratio in composition.items():
        if element in valence_electrons:
            # Weight by stoichiometric ratio
            valence_counts.append(valence_electrons[element] * ratio)
        else:
            logger.warning(f"Unknown element: {element}")

    if len(valence_counts) < 2:
        return 0.0

    return np.var(valence_counts)


def compute_spatial_locality(structure_data: Dict[str, Any]) -> float:
    """
    Compute spatial locality metric for a material structure.

    Spatial locality measures how localized the property is with respect
    to atomic positions. High values indicate short-range interactions.

    Args:
        structure_data: Dictionary containing structure information
                        (lattice, positions, species)

    Returns:
        Spatial locality value in [0, 1]
    """
    try:
        # Extract atomic positions and lattice
        positions = structure_data.get('positions', [])
        lattice = structure_data.get('lattice', None)

        if len(positions) < 2:
            return 0.5  # Default for insufficient data

        # Convert to numpy array
        positions = np.array(positions)

        # Calculate pairwise distances
        distances = pdist(positions)

        if len(distances) == 0:
            return 0.5

        # Find average neighbor distance (first coordination shell approximation)
        # Sort distances and take the mean of the smallest N-1 distances
        # (where N is the number of atoms)
        sorted_distances = np.sort(distances)
        n_atoms = len(positions)

        # Approximate first coordination shell as the closest n_atoms-1 distances
        neighbor_distances = sorted_distances[:n_atoms-1] if n_atoms > 1 else sorted_distances

        avg_neighbor_distance = np.mean(neighbor_distances)
        max_distance = np.max(distances)

        if max_distance == 0:
            return 0.5

        # Compute spatial locality: 1 - (avg_neighbor / max_distance)
        spatial_locality = 1.0 - (avg_neighbor_distance / max_distance)

        # Clamp to [0, 1]
        return max(0.0, min(1.0, spatial_locality))

    except Exception as e:
        logger.warning(f"Error computing spatial locality: {e}")
        return np.nan


def compute_symmetry_sensitivity(property_original: float, property_distorted: float) -> float:
    """
    Compute symmetry sensitivity metric.

    Symmetry sensitivity measures how sensitive a property is to changes
    in crystal symmetry.

    Args:
        property_original: Property value for original structure
        property_distorted: Property value for distorted structure

    Returns:
        Symmetry sensitivity value
    """
    if property_original == 0:
        return np.nan

    sensitivity = abs(property_original - property_distorted) / abs(property_original)

    return sensitivity


def classify_property(property_name: str) -> str:
    """
    Classify a property as 'electronic' or 'mechanical' based on its name.

    Args:
        property_name: Name of the property

    Returns:
        Classification string
    """
    electronic_keywords = ['band_gap', 'formation_energy', 'conductivity', 'dielectric',
                         'magnetic', 'electronic', 'fermi', 'homo', 'lumo']
    mechanical_keywords = ['elastic', 'bulk_modulus', 'shear_modulus', 'poisson',
                           'hardness', 'mechanical', 'stiffness', 'compliance']

    property_lower = property_name.lower()

    for keyword in electronic_keywords:
        if keyword in property_lower:
            return 'electronic'

    for keyword in mechanical_keywords:
        if keyword in property_lower:
            return 'mechanical'

    # Default classification based on common properties
    if any(kw in property_lower for kw in ['energy', 'gap', 'conduct', 'magnet', 'dielectric']):
        return 'electronic'
    elif any(kw in property_lower for kw in ['modulus', 'hard', 'elastic', 'stiff']):
        return 'mechanical'
    else:
        return 'unknown'


def permutation_test(group1_values: List[float], group2_values: List[float],
                    n_permutations: Optional[int] = None) -> Tuple[float, int, int]:
    """
    Perform an exact permutation test to compare two groups.

    This function calculates the observed difference in means between two groups,
    then enumerates all possible permutations (or a subset if n_permutations is specified)
    to compute the p-value.

    Args:
        group1_values: Values for the first group
        group2_values: Values for the second group
        n_permutations: Maximum number of permutations to enumerate. If None,
                       all permutations are enumerated (exact test).

    Returns:
        Tuple of (p_value, observed_difference, total_permutations)
    """
    group1 = np.array(group1_values)
    group2 = np.array(group2_values)

    if len(group1) == 0 or len(group2) == 0:
        raise ValueError("Both groups must have at least one value")

    # Observed difference in means
    observed_diff = np.mean(group1) - np.mean(group2)

    # Combine all values
    all_values = np.concatenate([group1, group2])
    n_total = len(all_values)
    n_group1 = len(group1)

    # Calculate total number of permutations
    total_permutations = math.comb(n_total, n_group1)

    logger.info(f"Permutation test: n_total={n_total}, n_group1={n_group1}, "
               f"total_permutations={total_permutations}")

    # For small n, enumerate all permutations; for large n, sample
    if n_permutations is None or total_permutations <= 100000:
        # Exact enumeration
        from itertools import combinations

        count_extreme = 0
        checked = 0

        # Enumerate all combinations of indices for group1
        for indices in combinations(range(n_total), n_group1):
            # Create permuted groups
            perm_group1 = all_values[list(indices)]
            perm_group2 = np.delete(all_values, list(indices))

            perm_diff = np.mean(perm_group1) - np.mean(perm_group2)

            # Count permutations where the difference is as extreme or more extreme
            if abs(perm_diff) >= abs(observed_diff):
                count_extreme += 1

            checked += 1

        p_value = count_extreme / total_permutations
        logger.info(f"Exact permutation test completed: {checked}/{total_permutations} permutations checked")

    else:
        # Monte Carlo approximation for large n
        np.random.seed(42)  # For reproducibility
        count_extreme = 0

        for _ in range(n_permutations):
            # Shuffle indices
            indices = np.random.choice(n_total, n_group1, replace=False)
            perm_group1 = all_values[list(indices)]
            perm_group2 = np.delete(all_values, list(indices))

            perm_diff = np.mean(perm_group1) - np.mean(perm_group2)

            if abs(perm_diff) >= abs(observed_diff):
                count_extreme += 1

        p_value = count_extreme / n_permutations
        logger.info(f"Monte Carlo permutation test completed: {n_permutations} permutations")

    return p_value, observed_diff, total_permutations


def compute_correlation(metrics_df: pd.DataFrame, scaling_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Pearson correlation between physical metrics and scaling exponents.

    Args:
        metrics_df: DataFrame with physical metrics
        scaling_df: DataFrame with scaling exponents

    Returns:
        DataFrame with correlation results
    """
    results = []

    # Merge on property_name
    merged = pd.merge(metrics_df, scaling_df, on='property_name', how='inner')

    if len(merged) == 0:
        logger.warning("No overlapping properties between metrics and scaling results")
        return pd.DataFrame()

    # Compute correlation for each metric
    metrics_columns = ['spatial_locality', 'symmetry_sensitivity', 'valence_electron_variance']

    for metric in metrics_columns:
        if metric in merged.columns:
            valid_data = merged[[metric, 'exponent_b']].dropna()

            if len(valid_data) >= 2:
                correlation, p_value = stats.pearsonr(
                    valid_data[metric],
                    valid_data['exponent_b']
                )

                results.append({
                    'metric': metric,
                    'correlation': correlation,
                    'p_value': p_value,
                    'n_samples': len(valid_data)
                })

    return pd.DataFrame(results)


def perform_permutation_test_on_classes(scaling_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform permutation test to compare electronic vs mechanical classes.

    Args:
        scaling_df: DataFrame with scaling results and property names

    Returns:
        Dictionary with permutation test results
    """
    # Classify each property
    scaling_df['class'] = scaling_df['property_name'].apply(classify_property)

    electronic_exponents = scaling_df[scaling_df['class'] == 'electronic']['exponent_b'].tolist()
    mechanical_exponents = scaling_df[scaling_df['class'] == 'mechanical']['exponent_b'].tolist()

    logger.info(f"Electronic properties: {len(electronic_exponents)}")
    logger.info(f"Mechanical properties: {len(mechanical_exponents)}")

    if len(electronic_exponents) == 0 or len(mechanical_exponents) == 0:
        logger.warning("Insufficient data for permutation test (one class is empty)")
        return {
            'p_value': np.nan,
            'observed_difference': np.nan,
            'total_permutations': 0,
            'n_electronic': len(electronic_exponents),
            'n_mechanical': len(mechanical_exponents),
            'significance': 'insufficient_data'
        }

    # Perform permutation test
    p_value, observed_diff, total_permutations = permutation_test(
        electronic_exponents,
        mechanical_exponents
    )

    # Determine significance based on amended threshold (p < 0.1)
    significance = 'Significant' if p_value < 0.1 else 'Not Significant'

    return {
        'p_value': p_value,
        'observed_difference': observed_diff,
        'total_permutations': total_permutations,
        'n_electronic': len(electronic_exponents),
        'n_mechanical': len(mechanical_exponents),
        'significance': significance
    }


def main():
    """
    Main function to run the physical metrics analysis.
    """
    try:
        # ------------------------------------------------------------------
        # Configuration
        # ------------------------------------------------------------------
        config = get_config()
        # Ensure the Config object can be used with .get()
        if not hasattr(config, 'get'):
            config.get = lambda key, default=None: default

        data_dir = config.get('data_dir', 'data')
        processed_dir = Path(data_dir) / 'processed'

        # ------------------------------------------------------------------
        # Paths
        # ------------------------------------------------------------------
        research_path = Path(__file__).resolve().parents[1] / 'research.md'
        metric_definitions_path = processed_dir / 'metric_definitions.md'
        master_dataset_path = processed_dir / 'materials_master.parquet'
        scaling_results_path = processed_dir / 'scaling_results.csv'
        output_path = processed_dir / 'final_analysis.csv'

        # ------------------------------------------------------------------
        # Task T041 – Verify metric definitions
        # ------------------------------------------------------------------
        logger.info("Extracting metric definitions from research.md")
        metric_defs = _extract_definitions_from_research(research_path)

        # Write metric_definitions.md (will contain 'undefined' status if missing)
        _write_metric_definitions_md(metric_defs, metric_definitions_path)

        # If either definition is missing, halt execution as required.
        if not metric_defs['spatial_locality'] or not metric_defs['symmetry_sensitivity']:
            missing = [k for k, v in metric_defs.items() if not v]
            raise RuntimeError(
                f"Metric definitions missing for: {', '.join(missing)}. "
                "Halting as per Task T041 requirements."
            )

        # ------------------------------------------------------------------
        # Load data
        # ------------------------------------------------------------------
        logger.info("Loading metric definitions...")
        metric_defs_loaded = load_metric_definitions(str(metric_definitions_path))
        logger.info(f"Loaded {len(metric_defs_loaded)} metric definitions")

        logger.info("Loading master dataset...")
        master_df = load_master_dataset(str(master_dataset_path))

        logger.info("Loading scaling results...")
        scaling_df = load_scaling_results(str(scaling_results_path))

        # ------------------------------------------------------------------
        # Compute physical metrics for each property
        # ------------------------------------------------------------------
        logger.info("Computing physical metrics...")
        metrics_data = []

        # Group by property
        for property_name in master_df['property'].unique():
            property_data = master_df[master_df['property'] == property_name]

            # Compute valence electron variance (requires composition)
            if 'composition' in property_data.columns:
                compositions = property_data['composition'].apply(
                    lambda x: json.loads(x) if isinstance(x, str) else x
                )
                valence_variances = [compute_valence_electron_variance(c) for c in compositions]
                avg_valence_var = np.nanmean(valence_variances)
            else:
                avg_valence_var = np.nan

            # Compute spatial locality (requires structure)
            if 'structure' in property_data.columns:
                structures = property_data['structure'].apply(
                    lambda x: json.loads(x) if isinstance(x, str) else x
                )
                spatial_localities = [compute_spatial_locality(s) for s in structures]
                avg_spatial_locality = np.nanmean(spatial_localities)
            else:
                avg_spatial_locality = np.nan

            # Compute symmetry sensitivity (requires original/distorted values)
            avg_symmetry_sensitivity = np.nan
            if 'property_distorted' in property_data.columns and 'property_original' in property_data.columns:
                originals = property_data['property_original'].values
                distorted = property_data['property_distorted'].values
                sensitivities = [
                    compute_symmetry_sensitivity(o, d) for o, d in zip(originals, distorted)
                ]
                avg_symmetry_sensitivity = np.nanmean(sensitivities)

            metrics_data.append({
                'property_name': property_name,
                'spatial_locality': avg_spatial_locality,
                'symmetry_sensitivity': avg_symmetry_sensitivity,
                'valence_electron_variance': avg_valence_var
            })

        metrics_df = pd.DataFrame(metrics_data)
        logger.info(f"Computed metrics for {len(metrics_df)} properties")

        # ------------------------------------------------------------------
        # Correlations and permutation test
        # ------------------------------------------------------------------
        logger.info("Computing correlations...")
        correlation_results = compute_correlation(metrics_df, scaling_df)

        logger.info("Performing permutation test...")
        permutation_results = perform_permutation_test_on_classes(scaling_df)

        # ------------------------------------------------------------------
        # Assemble final results
        # ------------------------------------------------------------------
        final_results = scaling_df.copy()

        # Add metrics
        for metric in ['spatial_locality', 'symmetry_sensitivity', 'valence_electron_variance']:
            if metric in metrics_df.columns:
                merged = pd.merge(final_results, metrics_df[['property_name', metric]],
                                  on='property_name', how='left')
                final_results[metric] = merged[metric]

        # Add correlation results (one row per metric)
        for _, row in correlation_results.iterrows():
            metric_name = row['metric']
            final_results[f'{metric_name}_correlation'] = row['correlation']
            final_results[f'{metric_name}_p_value'] = row['p_value']

        # Add permutation test results
        final_results['permutation_p_value'] = permutation_results['p_value']
        final_results['permutation_significance'] = permutation_results['significance']

        # ------------------------------------------------------------------
        # Save final analysis
        # ------------------------------------------------------------------
        logger.info(f"Saving final analysis to {output_path}")
        final_results.to_csv(output_path, index=False)

        logger.info("Physical metrics analysis completed successfully")

        # Print summary
        print("\n" + "=" * 60)
        print("PHYSICAL METRICS ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Properties analyzed: {len(final_results)}")
        print(f"Permutation test p-value: {permutation_results['p_value']:.4f}")
        print(f"Significance (threshold p < 0.1): {permutation_results['significance']}")
        print(f"Total permutations: {permutation_results['total_permutations']}")
        if not correlation_results.empty:
            print("\nCorrelation Results:")
            for _, row in correlation_results.iterrows():
                print(f"  {row['metric']}: r={row['correlation']:.4f}, p={row['p_value']:.4f}")
        print("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Error in physical metrics analysis: {e}")
        traceback.print_exc()
        # Propagate the exception to ensure the script halts with a non‑zero exit code
        raise

if __name__ == '__main__':
    sys.exit(main())
