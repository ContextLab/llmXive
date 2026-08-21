"""
Meta-analysis module implementing Random-Effects and Fixed-Effects models.
Handles convergence failures and gate logic based on study count.
"""
import json
import sys
import math
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import statsmodels.api as sm
from statsmodels.stats.meta_analysis import combine_effects

# Import shared utilities from the project API surface
from utils.logger import get_logger, log_error_context
from utils.config import get_project_root

logger = get_logger(__name__)


def load_study_count_from_json(path: Path) -> int:
    """Load N from study_count.json."""
    if not path.exists():
        raise FileNotFoundError(f"Missing study count. Run T014a first: {path}")
    with open(path, 'r') as f:
        data = json.load(f)
    return int(data.get('N', 0))


def load_effect_sizes_and_se(extracted_studies_path: Path) -> Tuple[List[float], List[float]]:
    """
    Load effect sizes (r) and standard errors from extracted_studies.csv.
    Only includes rows with valid 'r' and 'n' values.
    """
    if not extracted_studies_path.exists():
        raise FileNotFoundError(f"Extracted studies file not found: {extracted_studies_path}")

    effects = []
    ses = []

    with open(extracted_studies_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            r_val = row.get('r')
            n_val = row.get('n')

            if r_val is None or n_val is None:
                continue

            try:
                r = float(r_val)
                n = int(float(n_val))
            except (ValueError, TypeError):
                continue

            if n <= 2:
                continue

            # Calculate Standard Error for r using Fisher's z transformation approximation
            # SE_z = 1 / sqrt(N - 3)
            # Convert r to z, but for the meta-analysis model, we often use the SE of z
            # However, statsmodels combine_effects expects effect sizes and their SEs.
            # We will use the SE of the Fisher Z transformed correlation.
            z = 0.5 * math.log((1 + r) / (1 - r))
            se_z = 1.0 / math.sqrt(n - 3)

            effects.append(z)
            ses.append(se_z)

    return effects, ses


def run_random_effects_model(effects: List[float], ses: List[float]) -> Dict[str, Any]:
    """
    Run Random-Effects meta-analysis using statsmodels.
    Handles convergence failures by falling back to Fixed-Effects.
    """
    if len(effects) == 0:
        return {
            'status': 'failed',
            'reason': 'No valid effect sizes provided',
            'model_type': None
        }

    effects_arr = np.array(effects)
    ses_arr = np.array(ses)

    # Weights for Random Effects (DerSimonian-Laird)
    # statsmodels combine_effects handles this internally if we specify method='DL'
    # but we need to handle the result extraction carefully.

    result = {
        'model_type': 'random_effects',
        'reliability': 'reliable',
        'convergence_warning': False
    }

    try:
        # statsmodels.stats.meta_analysis.combine_effects
        # Returns (combined_effect, combined_se, ci_lower, ci_upper, z, p_value)
        # We need to calculate I-squared separately or extract it from the model object if available.
        # statsmodels doesn't have a direct high-level "MetaAnalysis" class that returns I2 easily in older versions.
        # We will use the low-level calculation for I2 to ensure precision.

        # Calculate Q statistic
        # Q = sum(w_i * (theta_i - theta_bar)^2) where w_i = 1/se_i^2 for Fixed, but for DL we need tau^2 first.
        # Let's use the DL method to estimate tau^2 first.

        w_fixed = 1.0 / (ses_arr ** 2)
        theta_bar_fixed = np.sum(w_fixed * effects_arr) / np.sum(w_fixed)
        Q = np.sum(w_fixed * (effects_arr - theta_bar_fixed) ** 2)
        df = len(effects) - 1

        if df <= 0:
            raise ValueError("Not enough studies to calculate heterogeneity (df <= 0)")

        # DerSimonian-Laird estimator for tau^2
        C = np.sum(w_fixed) - (np.sum(w_fixed ** 2) / np.sum(w_fixed))
        tau_sq = max(0, (Q - df) / C) if C > 0 else 0

        # Random Effects Weights
        w_re = 1.0 / (ses_arr ** 2 + tau_sq)
        theta_re = np.sum(w_re * effects_arr) / np.sum(w_re)
        se_re = math.sqrt(1.0 / np.sum(w_re))

        # 95% CI
        z_score = 1.96
        ci_lower = theta_re - z_score * se_re
        ci_upper = theta_re + z_score * se_re

        # I-squared calculation
        # I^2 = max(0, (Q - df) / Q) * 100
        i_squared = max(0, (Q - df) / Q * 100) if Q > 0 else 0.0

        # P-value for combined effect (Z-test)
        z_stat = theta_re / se_re if se_re != 0 else 0
        p_value = 2 * (1 - statsmodels.stats.weightstats.ztost._norm.cdf(abs(z_stat))) # Approximation
        # Correct p-value calculation using scipy.stats.norm if available, else manual
        try:
            from scipy import stats
            p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        except ImportError:
            # Fallback manual p-value for normal distribution
            p_value = 2 * (0.5 * (1 + math.erf(-abs(z_stat) / math.sqrt(2))))

        result.update({
            'pooled_effect_z': float(theta_re),
            'pooled_effect_r': float(0.5 * math.log((1 + np.tanh(theta_re)) / (1 - np.tanh(theta_re)))), # Inverse Fisher
            'se': float(se_re),
            'ci_lower': float(ci_lower),
            'ci_upper': float(ci_upper),
            'i_squared': float(round(i_squared, 2)),
            'tau_squared': float(tau_sq),
            'q_statistic': float(Q),
            'p_value': float(p_value)
        })

    except Exception as e:
        logger.warning(f"Random-Effects model failed: {e}. Falling back to Fixed-Effects.")
        result['convergence_warning'] = True
        result['model_type'] = 'fixed_effects_fallback'
        result['reliability'] = 'unreliable'

        # Fallback to Fixed-Effects
        w_fixed = 1.0 / (ses_arr ** 2)
        theta_fe = np.sum(w_fixed * effects_arr) / np.sum(w_fixed)
        se_fe = math.sqrt(1.0 / np.sum(w_fixed))

        ci_lower = theta_fe - 1.96 * se_fe
        ci_upper = theta_fe + 1.96 * se_fe

        result.update({
            'pooled_effect_z': float(theta_fe),
            'pooled_effect_r': float(0.5 * math.log((1 + np.tanh(theta_fe)) / (1 - np.tanh(theta_fe)))),
            'se': float(se_fe),
            'ci_lower': float(ci_lower),
            'ci_upper': float(ci_upper),
            'i_squared': 0.0, # Not applicable for fixed effects in this context
            'tau_squared': 0.0,
            'q_statistic': float(Q),
            'p_value': float(2 * (1 - stats.norm.cdf(abs(theta_fe / se_fe))))
        })

    return result


def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save meta-analysis results to JSON."""
    ensure_directory(output_path.parent)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Meta-analysis results saved to {output_path}")


def run_meta_analysis(extracted_studies_path: Path, study_count_path: Path, output_path: Path, status_path: Path) -> Dict[str, Any]:
    """
    Main entry point for meta-analysis task T014.
    Implements gate logic: if N < 10, skip analysis and write status.
    """
    # 1. Load Study Count
    try:
        N = load_study_count_from_json(study_count_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

    logger.info(f"Loaded study count: N = {N}")

    # 2. Gate Logic
    if N < 10:
        logger.info(f"Skipping meta-analysis: N ({N}) < 10")
        status_result = {
            'status': 'skipped',
            'reason': 'Insufficient studies',
            'N': N,
            'egger_skipped_reason': "Skipped: Insufficient studies (N < 10) for Egger's regression"
        }
        save_results(status_result, status_path)
        # We still need to write a placeholder or partial result to results.json if expected by downstream tasks
        # However, the spec says T014 outputs meta_status.json. T016 handles the final results.json.
        # But T014 also says "If N >= 10: ... output data/derived/results.json".
        # So if N < 10, we do not write results.json here.
        return status_result

    # 3. Load Data
    try:
        effects, ses = load_effect_sizes_and_se(extracted_studies_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

    if len(effects) == 0:
        logger.warning("No valid effect sizes found in extracted studies.")
        status_result = {
            'status': 'skipped',
            'reason': 'No valid effect sizes found',
            'N': N,
            'egger_skipped_reason': "Skipped: No valid effect sizes"
        }
        save_results(status_result, status_path)
        return status_result

    # 4. Run Model
    logger.info(f"Running meta-analysis on {len(effects)} studies.")
    results = run_random_effects_model(effects, ses)
    results['N'] = N
    results['status'] = 'completed'

    # 5. Save Results
    # The task description says: "If N >= 10: ... output data/derived/results.json"
    # But T016 also writes to results.json. To avoid conflict, we save to a temporary file
    # or let T016 merge. The spec says T014 outputs results.json if N>=10.
    # We will save to results.json as requested, but T016 might overwrite or merge.
    # Given T016 is the orchestrator, it likely merges T014, T021, T022 outputs.
    # We will save the meta-analysis specific part to results_meta.json or similar,
    # but the prompt says "output data/derived/results.json".
    # Let's assume T016 reads this and merges.
    save_results(results, output_path)

    # Also save status
    status_result = {
        'status': 'completed',
        'N': N,
        'model_type': results.get('model_type'),
        'reliability': results.get('reliability')
    }
    save_results(status_result, status_path)

    return results


def main():
    """CLI entry point for T014."""
    project_root = get_project_root()
    extracted_path = project_root / "data" / "processed" / "extracted_studies.csv"
    count_path = project_root / "data" / "processed" / "study_count.json"
    results_path = project_root / "data" / "derived" / "results.json"
    status_path = project_root / "data" / "processed" / "meta_status.json"

    try:
        run_meta_analysis(extracted_path, count_path, results_path, status_path)
        logger.info("Meta-analysis completed successfully.")
    except Exception as e:
        logger.error(f"Meta-analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
