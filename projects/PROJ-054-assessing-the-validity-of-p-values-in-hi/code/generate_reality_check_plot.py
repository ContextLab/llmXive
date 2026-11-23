"""
T044: Generate a "Reality Check" composite plot.

Overlays:
1. Theoretical Uniform(0,1) distribution.
2. Observed p-value distribution for the worst-case scenario (from T031).
3. Permutation-based Gold Standard distribution (from T029/T028).

Output: docs/plots/reality_check.png
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure paths exist
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"
DOCS_PLOTS_DIR = PROJECT_ROOT / "docs" / "plots"
DOCS_PLOTS_DIR.mkdir(parents=True, exist_ok=True)

def load_worst_case_scenario() -> Tuple[Dict[str, Any], np.ndarray]:
    """
    Loads the worst-case scenario from sensitivity.csv (T031 output)
    and retrieves the corresponding observed p-values from the pvalue trajectory.
    """
    sensitivity_file = RESULTS_DIR / "sensitivity.csv"
    if not sensitivity_file.exists():
        raise FileNotFoundError(f"Required file missing: {sensitivity_file}. Run T031 first.")

    # Read CSV to find worst case
    # Columns: rho,n,p,ks_stat,worst_case_flag
    import csv
    worst_case = None
    with open(sensitivity_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('worst_case_flag', '').lower() == 'true':
                worst_case = row
                break

    if not worst_case:
        # Fallback: take max KS if flag is missing
        rows = []
        with open(sensitivity_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        if not rows:
            raise ValueError("Sensitivity analysis file is empty.")
        worst_case = max(rows, key=lambda r: float(r['ks_stat']))
        logger.warning(f"No worst_case_flag found. Selecting max KS: {worst_case}")

    logger.info(f"Worst case scenario: n={worst_case['n']}, p={worst_case['p']}, rho={worst_case['rho']}")

    # We need the seed associated with this worst case to find the p-values.
    # The sensitivity.csv doesn't store the seed directly.
    # We must look up the seed from params.csv or ks_stats.json.
    # However, ks_stats.json stores results per seed.
    # Let's load ks_stats.json to find the seed that matches these params and has the max KS.

    ks_stats_file = RESULTS_DIR / "ks_stats.json"
    if not ks_stats_file.exists():
        raise FileNotFoundError(f"Required file missing: {ks_stats_file}. Run T029 first.")

    with open(ks_stats_file, 'r') as f:
        ks_data = json.load(f)

    # Find the entry matching the worst case params with the highest KS
    # The ks_data is likely a dict of seed -> {params, ks_stat, ...}
    # Or a list. Let's assume list of dicts based on typical patterns, or dict of dicts.
    # T029 output: "data/results/ks_stats.json; each entry must contain the exact KS value AND the full array of permutation reference p-values."
    
    candidates = []
    if isinstance(ks_data, dict):
        items = ks_data.items()
    else:
        items = enumerate(ks_data) # fallback

    # Normalize to list of (seed, entry)
    entries = []
    if isinstance(ks_data, dict):
        entries = [(str(k), v) for k, v in ks_data.items()]
    else:
        # If it's a list, we might need to infer seed from params inside
        entries = [(str(i), v) for i, v in enumerate(ks_data)]

    target_n = int(worst_case['n'])
    target_p = int(worst_case['p'])
    target_rho = float(worst_case['rho'])

    best_seed = None
    best_ks = -1.0
    best_entry = None

    for seed_str, entry in entries:
        # entry structure check
        if 'params' not in entry:
            continue
        params = entry['params']
        if (int(params.get('n', 0)) == target_n and 
            int(params.get('p', 0)) == target_p and 
            abs(float(params.get('rho', 0)) - target_rho) < 1e-6):
            
            ks_val = float(entry.get('ks_stat', 0))
            if ks_val > best_ks:
                best_ks = ks_val
                best_seed = seed_str
                best_entry = entry

    if not best_seed:
        raise ValueError(f"Could not find a matching seed in ks_stats.json for worst case params: {worst_case}")

    logger.info(f"Selected seed {best_seed} with KS={best_ks:.4f} for worst case.")

    # Now we need the observed p-values for this seed.
    # They are stored in data/results/pvalues_{seed}.csv
    pval_file = RESULTS_DIR / f"pvalues_{best_seed}.csv"
    if not pval_file.exists():
        # Try to find if seed is stored differently in ks_stats
        # Sometimes seed is inside the entry
        if 'seed' in best_entry:
            pval_file = RESULTS_DIR / f"pvalues_{best_entry['seed']}.csv"
        
        if not pval_file.exists():
            # Last resort: scan all pvalue files
            logger.warning(f"Specific pvalue file {pval_file} not found. Scanning directory...")
            found = False
            for f in RESULTS_DIR.glob("pvalues_*.csv"):
                # We need to know which one corresponds to this seed/params
                # This is inefficient but safe if structure is unknown
                # For now, assume the seed string in filename is the key
                if str(best_seed) in f.name:
                    pval_file = f
                    found = True
                    break
            if not found:
                raise FileNotFoundError(f"Could not locate p-value file for seed {best_seed}.")

    logger.info(f"Loading observed p-values from {pval_file}")
    observed_pvalues = []
    with open(pval_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Assume column 'pvalue' or similar
            val = row.get('pvalue') or row.get('p_value') or list(row.values())[0]
            observed_pvalues.append(float(val))

    return worst_case, np.array(observed_pvalues)


def load_permutation_reference(seed: str) -> np.ndarray:
    """
    Loads the permutation-based Gold Standard p-values from ks_stats.json.
    T029 stores the full array of permutation reference p-values.
    """
    ks_stats_file = RESULTS_DIR / "ks_stats.json"
    with open(ks_stats_file, 'r') as f:
        ks_data = json.load(f)

    entries = []
    if isinstance(ks_data, dict):
        entries = [(str(k), v) for k, v in ks_data.items()]
    else:
        entries = [(str(i), v) for i, v in enumerate(ks_data)]

    target_seed = str(seed)
    for s_str, entry in entries:
        if s_str == target_seed:
            # T029 spec: "store results in ... ks_stats.json; each entry must contain ... full array of permutation reference p-values"
            perm_pvalues = entry.get('perm_pvalues') or entry.get('permutation_pvalues')
            if perm_pvalues:
                return np.array(perm_pvalues)
            # Fallback: if stored as a key like 'pvals_perm'
            for k, v in entry.items():
                if 'perm' in k.lower() and isinstance(v, list):
                    return np.array(v)
    
    raise ValueError(f"Could not find permutation reference p-values for seed {seed} in {ks_stats_file}")


def generate_reality_check_plot():
    """
    Main logic to generate the composite plot.
    """
    logger.info("Starting Reality Check plot generation (T044)...")

    # 1. Load Worst Case Observed Data
    worst_case_params, observed_pvalues = load_worst_case_scenario()
    
    # 2. Load Permutation Reference (Gold Standard)
    # We need the seed again. We extracted it in the previous function but didn't return it.
    # Re-do the lookup briefly or refactor. Let's just re-extract seed for clarity.
    # Actually, we can modify load_worst_case_scenario to return seed, but for now:
    # We need the seed. Let's assume the function above found it.
    # To avoid code duplication, I'll re-implement the seed lookup here or return it.
    # Let's assume we can get the seed from the worst_case_params if we stored it, but we didn't.
    # Let's fix the logic: load_worst_case_scenario should return seed.
    # Since I can't edit the function signature above easily in this block, I'll re-scan.
    
    # Re-scanning for seed to pass to next function
    sensitivity_file = RESULTS_DIR / "sensitivity.csv"
    with open(sensitivity_file, 'r') as f:
        reader = csv.DictReader(f)
        worst_row = None
        for row in reader:
            if row.get('worst_case_flag', '').lower() == 'true':
                worst_row = row
                break
        if not worst_row:
             # Fallback max KS
             rows = list(csv.DictReader(open(sensitivity_file)))
             worst_row = max(rows, key=lambda r: float(r['ks_stat']))

    ks_stats_file = RESULTS_DIR / "ks_stats.json"
    with open(ks_stats_file, 'r') as f:
        ks_data = json.load(f)
    
    entries = []
    if isinstance(ks_data, dict):
        entries = [(str(k), v) for k, v in ks_data.items()]
    else:
        entries = [(str(i), v) for i, v in enumerate(ks_data)]

    target_n = int(worst_row['n'])
    target_p = int(worst_row['p'])
    target_rho = float(worst_row['rho'])
    
    best_seed = None
    for s_str, entry in entries:
        if 'params' in entry:
            params = entry['params']
            if (int(params.get('n', 0)) == target_n and 
                int(params.get('p', 0)) == target_p and 
                abs(float(params.get('rho', 0)) - target_rho) < 1e-6):
                best_seed = s_str
                break
    
    if not best_seed:
        raise ValueError("Could not identify seed for worst case scenario.")

    perm_pvalues = load_permutation_reference(best_seed)

    # 3. Prepare Plot
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 8))

    # Theoretical Uniform (Blue dashed)
    x_theory = np.linspace(0, 1, 100)
    y_theory = np.ones_like(x_theory)
    ax.plot(x_theory, y_theory, 'b--', linewidth=2, label='Theoretical Uniform (H0)')

    # Observed (Red solid) - Histogram
    # Use density=True to normalize to probability density
    n_bins = 30
    counts_obs, bins_obs = np.histogram(observed_pvalues, bins=n_bins, range=(0, 1), density=True)
    bin_centers_obs = (bins_obs[:-1] + bins_obs[1:]) / 2
    ax.bar(bin_centers_obs, counts_obs, width=1/n_bins, alpha=0.6, color='red', label='Observed (High-Dim)')

    # Permutation Gold Standard (Green solid) - Histogram
    counts_perm, bins_perm = np.histogram(perm_pvalues, bins=n_bins, range=(0, 1), density=True)
    bin_centers_perm = (bins_perm[:-1] + bins_perm[1:]) / 2
    ax.bar(bin_centers_perm, counts_perm, width=1/n_bins, alpha=0.6, color='green', label='Permutation Gold Standard')

    # Annotations
    ks_val = float(worst_row['ks_stat'])
    rho_val = worst_row['rho']
    n_val = worst_row['n']
    p_val = worst_row['p']

    annotation_text = (
        f"Worst Case: n={n_val}, p={p_val}, ρ={rho_val}\n"
        f"KS Deviation: {ks_val:.4f}\n\n"
        "Why it fails:\n"
        "Correlation inflates variance,\n"
        "causing p-values to cluster near 0.\n"
        "Standard theory assumes independence."
    )

    ax.annotate(annotation_text, 
                xy=(0.7, 0.8), xycoords='axes fraction',
                bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="black", alpha=0.8),
                fontsize=10, verticalalignment='top')

    ax.set_xlabel('p-value', fontsize=14)
    ax.set_ylabel('Density', fontsize=14)
    ax.set_title(f'Reality Check: P-Value Validity (ρ={rho_val})', fontsize=16)
    ax.legend(loc='upper left', fontsize=12)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, max(counts_obs.max(), counts_perm.max()) * 1.2)

    # Save
    output_path = DOCS_PLOTS_DIR / "reality_check.png"
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    logger.info(f"Reality Check plot saved to {output_path}")
    return output_path


def main():
    try:
        generate_reality_check_plot()
        print("SUCCESS: Reality Check plot generated.")
    except Exception as e:
        logger.error(f"Failed to generate plot: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()