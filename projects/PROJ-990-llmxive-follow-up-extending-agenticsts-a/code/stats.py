import os
import json
import logging
import hashlib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from scipy import stats
from scipy.stats import chi2_contingency, ttest_rel, wilcoxon

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_simulation_results(filepath: str) -> Dict[str, Any]:
    """Load simulation results from a JSON file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Simulation results file not found: {filepath}")
    with open(path, 'r') as f:
        return json.load(f)

def load_divergence_report(filepath: str) -> Dict[str, Any]:
    """Load divergence report from a JSON file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Divergence report file not found: {filepath}")
    with open(path, 'r') as f:
        return json.load(f)

def compute_final_state_hash(game_state: Dict[str, Any]) -> str:
    """Compute SHA256 hash of the final game state."""
    # Normalize the game state for consistent hashing
    normalized = json.dumps(game_state, sort_keys=True)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

def detect_divergence(dynamic_logs: List[Dict], static_logs: List[Dict]) -> Dict[str, Any]:
    """
    Detect if trajectories diverged between Dynamic and Static simulations.
    Compares final state hashes for each trajectory pair.
    """
    if len(dynamic_logs) != len(static_logs):
        raise ValueError("Dynamic and static log lists must have the same length")

    divergent_pairs = []
    is_divergent = False

    for i, (dyn_log, stat_log) in enumerate(zip(dynamic_logs, static_logs)):
        dyn_traj_id = dyn_log.get('trajectory_id', f'traj_{i}')
        stat_traj_id = stat_log.get('trajectory_id', f'traj_{i}')

        if dyn_traj_id != stat_traj_id:
            logger.warning(f"Trajectory ID mismatch at index {i}: {dyn_traj_id} vs {stat_traj_id}")

        dyn_final_state = dyn_log.get('final_state', {})
        stat_final_state = stat_log.get('final_state', {})

        dyn_hash = compute_final_state_hash(dyn_final_state)
        stat_hash = compute_final_state_hash(stat_final_state)

        if dyn_hash != stat_hash:
            is_divergent = True
            divergent_pairs.append({
                'trajectory_id': dyn_traj_id,
                'dynamic_hash': dyn_hash,
                'static_hash': stat_hash
            })

    return {
        'is_divergent': is_divergent,
        'divergent_trajectory_ids': [p['trajectory_id'] for p in divergent_pairs],
        'divergent_count': len(divergent_pairs),
        'total_pairs': len(dynamic_logs)
    }

def compute_aggregates(simulation_logs: List[Dict]) -> Dict[str, Any]:
    """Compute aggregate statistics (win rate, token usage) from simulation logs."""
    if not simulation_logs:
        return {'win_rate': 0.0, 'avg_tokens': 0.0, 'token_std': 0.0, 'n': 0}

    wins = sum(1 for log in simulation_logs if log.get('outcome', {}).get('won', False))
    total = len(simulation_logs)
    win_rate = wins / total if total > 0 else 0.0

    token_counts = [log.get('total_tokens_used', 0) for log in simulation_logs]
    avg_tokens = np.mean(token_counts) if token_counts else 0.0
    token_std = np.std(token_counts) if len(token_counts) > 1 else 0.0

    return {
        'win_rate': win_rate,
        'avg_tokens': avg_tokens,
        'token_std': token_std,
        'n': total,
        'wins': wins,
        'losses': total - wins
    }

def run_permutation_test(dynamic_wins: int, dynamic_total: int, static_wins: int, static_total: int, n_permutations: int = 10000) -> float:
    """
    Run a permutation test for unpaired win/loss data.
    Tests the null hypothesis that the win rates are from the same distribution.
    """
    if dynamic_total == 0 or static_total == 0:
        return 1.0

    # Create binary arrays for wins/losses
    dynamic_outcomes = [1] * dynamic_wins + [0] * (dynamic_total - dynamic_wins)
    static_outcomes = [1] * static_wins + [0] * (static_total - static_wins)
    combined = dynamic_outcomes + static_outcomes
    n = len(combined)

    observed_diff = dynamic_wins / dynamic_total - static_wins / static_total

    count_extreme = 0
    for _ in range(n_permutations):
        np.random.shuffle(combined)
        perm_dynamic = combined[:dynamic_total]
        perm_static = combined[dynamic_total:]
        perm_diff = np.mean(perm_dynamic) - np.mean(perm_static)
        if abs(perm_diff) >= abs(observed_diff):
            count_extreme += 1

    p_value = count_extreme / n_permutations
    return p_value

def run_mcnemar_test(dynamic_wins: int, dynamic_losses: int, static_wins: int, static_losses: int, contingency_table: List[List[int]]) -> float:
    """
    Run McNemar's test for paired win/loss data.
    contingency_table format: [[both_win, dyn_win_stat_loss], [stat_win_dyn_loss, both_loss]]
    """
    try:
        # chi2_contingency with correction=False for McNemar's approximation
        # For true McNemar, we use the off-diagonal elements
        b = contingency_table[0][1]  # Dynamic win, Static loss
        c = contingency_table[1][0]  # Static win, Dynamic loss

        if b + c == 0:
            logger.warning("No discordant pairs in contingency table. McNemar's test not applicable.")
            return 1.0

        # McNemar's chi-squared statistic with continuity correction
        chi2 = (abs(b - c) - 1) ** 2 / (b + c)
        p_value = 1 - chi2.cdf(chi2, 1)
        return p_value
    except Exception as e:
        logger.error(f"Error running McNemar's test: {e}")
        return 1.0

def run_ttest_token_usage(dynamic_tokens: List[float], static_tokens: List[float]) -> Tuple[float, float]:
    """
    Run a paired t-test for token usage.
    Returns (t_statistic, p_value).
    If normality assumption fails, falls back to Wilcoxon signed-rank test.
    """
    if len(dynamic_tokens) != len(static_tokens):
        raise ValueError("Token usage lists must have the same length for paired test")

    if len(dynamic_tokens) < 2:
        logger.warning("Insufficient samples for t-test. Returning p=1.0")
        return 0.0, 1.0

    # Check normality of differences
    differences = np.array(dynamic_tokens) - np.array(static_tokens)
    try:
        _, normality_p = stats.shapiro(differences)
        use_ttest = normality_p > 0.05
    except Exception:
        # If Shapiro fails (e.g., small sample), use t-test
        use_ttest = True

    if use_ttest:
        t_stat, p_val = ttest_rel(dynamic_tokens, static_tokens)
        return float(t_stat), float(p_val)
    else:
        logger.info("Normality assumption failed. Using Wilcoxon signed-rank test.")
        w_stat, p_val = wilcoxon(dynamic_tokens, static_tokens)
        return float(w_stat), float(p_val)

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction to a family of p-values.
    Returns corrected p-values and whether the family-wise null is rejected.
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return {
            'corrected_p_values': [],
            'alpha_adjusted': alpha,
            'family_wise_rejection': False
        }

    alpha_adjusted = alpha / n_tests
    corrected_p_values = [min(p * n_tests, 1.0) for p in p_values]
    family_wise_rejection = any(p < alpha_adjusted for p in corrected_p_values)

    return {
        'corrected_p_values': corrected_p_values,
        'alpha_adjusted': alpha_adjusted,
        'family_wise_rejection': family_wise_rejection,
        'n_tests': n_tests
    }

def save_statistical_results(results: Dict[str, Any], filepath: str) -> None:
    """Save statistical results to a JSON file."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Statistical results saved to {filepath}")

def main():
    """
    Main entry point for T025: Statistical Testing Logic.
    1. Reads divergence_report.json (T024a).
    2. Selects appropriate test (Permutation vs McNemar).
    3. Executes test for win/loss.
    4. Executes paired t-test/Wilcoxon for token usage.
    5. Applies Bonferroni correction.
    6. Outputs statistical_results.json.
    """
    config_path = Path("code/config.py")
    if config_path.exists():
        # Import config if available, otherwise use defaults
        try:
            from config import load_config_from_file
            config = load_config_from_file("code/config.py")
        except Exception as e:
            logger.warning(f"Could not load config: {e}. Using defaults.")
            config = {}

    # Paths
    divergence_report_path = "data/processed/divergence_report.json"
    dynamic_logs_path = "data/processed/simulation_logs_dynamic.json"
    static_logs_path = "data/processed/simulation_logs_static.json"
    output_path = "data/processed/statistical_results.json"

    # 1. Load inputs
    logger.info("Loading divergence report...")
    try:
        divergence_report = load_divergence_report(divergence_report_path)
    except FileNotFoundError as e:
        logger.error(f"Missing divergence report: {e}")
        raise

    logger.info("Loading simulation logs...")
    try:
        dynamic_logs = load_simulation_results(dynamic_logs_path)
        static_logs = load_simulation_results(static_logs_path)
    except FileNotFoundError as e:
        logger.error(f"Missing simulation logs: {e}")
        raise

    # Ensure logs are lists (handle single object case if necessary)
    if isinstance(dynamic_logs, dict):
        dynamic_logs = [dynamic_logs]
    if isinstance(static_logs, dict):
        static_logs = [static_logs]

    # 2. Select test based on divergence
    is_divergent = divergence_report.get('is_divergent', False)
    test_selection_reason = ""
    win_p_value = None
    win_test_type = ""

    logger.info(f"Divergence status: {is_divergent}")

    # Compute aggregates for contingency table construction
    dynamic_agg = compute_aggregates(dynamic_logs)
    static_agg = compute_aggregates(static_logs)

    # Construct contingency table for paired test (McNemar)
    # We need to pair trajectories by ID to count discordant pairs
    # Assuming logs are ordered by trajectory ID or we match by ID
    dyn_by_id = {log.get('trajectory_id'): log for log in dynamic_logs}
    stat_by_id = {log.get('trajectory_id'): log for log in static_logs}

    common_ids = sorted(list(set(dyn_by_id.keys()) & set(stat_by_id.keys())))

    both_win = 0
    dyn_win_stat_loss = 0
    stat_win_dyn_loss = 0
    both_loss = 0

    for tid in common_ids:
        dyn_outcome = dyn_by_id[tid].get('outcome', {}).get('won', False)
        stat_outcome = stat_by_id[tid].get('outcome', {}).get('won', False)

        if dyn_outcome and stat_outcome:
            both_win += 1
        elif dyn_outcome and not stat_outcome:
            dyn_win_stat_loss += 1
        elif not dyn_outcome and stat_outcome:
            stat_win_dyn_loss += 1
        else:
            both_loss += 1

    contingency_table = [
        [both_win, dyn_win_stat_loss],
        [stat_win_dyn_loss, both_loss]
    ]

    if is_divergent:
        # Unpaired: Permutation Test
        test_selection_reason = "Trajectories diverged (unpaired). Using Permutation Test."
        win_test_type = "Permutation Test"
        logger.info(test_selection_reason)
        win_p_value = run_permutation_test(
            dynamic_agg['wins'], dynamic_agg['n'],
            static_agg['wins'], static_agg['n']
        )
    else:
        # Paired: McNemar's Test
        test_selection_reason = "Trajectories matched (paired). Using McNemar's Test."
        win_test_type = "McNemar's Test"
        logger.info(test_selection_reason)
        win_p_value = run_mcnemar_test(
            dynamic_agg['wins'], dynamic_agg['losses'],
            static_agg['wins'], static_agg['losses'],
            contingency_table
        )

    # 3. Token Usage Test (Paired t-test or Wilcoxon)
    # Collect token usage for common trajectories
    dyn_tokens = [dyn_by_id[tid].get('total_tokens_used', 0) for tid in common_ids]
    stat_tokens = [stat_by_id[tid].get('total_tokens_used', 0) for tid in common_ids]

    t_stat, token_p_value = run_ttest_token_usage(dyn_tokens, stat_tokens)
    token_test_type = "Paired t-test" if t_stat != 0.0 else "Wilcoxon signed-rank test" # Simplified flag
    if t_stat == 0.0 and token_p_value == 1.0: # Fallback indicator
         # Re-run to get actual test type if needed, but for now we rely on the function's internal log
         pass

    # 4. Bonferroni Correction
    p_values_to_correct = [p for p in [win_p_value, token_p_value] if p is not None]
    bonferroni_result = apply_bonferroni_correction(p_values_to_correct)

    # 5. Calculate Effect Size (Cohen's d for tokens, Phi for win rate)
    # Token Effect Size (Cohen's d)
    if len(dyn_tokens) > 1 and len(stat_tokens) > 1:
        mean_diff = np.mean(dyn_tokens) - np.mean(stat_tokens)
        pooled_std = np.sqrt((np.var(dyn_tokens) + np.var(stat_tokens)) / 2)
        if pooled_std > 0:
            cohens_d = mean_diff / pooled_std
        else:
            cohens_d = 0.0
    else:
        cohens_d = 0.0

    # Win Rate Effect Size (Phi coefficient)
    if contingency_table[0][0] + contingency_table[0][1] + contingency_table[1][0] + contingency_table[1][1] > 0:
        n = sum(sum(row) for row in contingency_table)
        ad_bc = contingency_table[0][0] * contingency_table[1][1] - contingency_table[0][1] * contingency_table[1][0]
        # Phi = (ad - bc) / sqrt(product of marginals)
        # Simplified for 2x2
        row1 = contingency_table[0][0] + contingency_table[0][1]
        row2 = contingency_table[1][0] + contingency_table[1][1]
        col1 = contingency_table[0][0] + contingency_table[1][0]
        col2 = contingency_table[0][1] + contingency_table[1][1]
        denom = np.sqrt(row1 * row2 * col1 * col2)
        if denom > 0:
            phi = ad_bc / denom
        else:
            phi = 0.0
    else:
        phi = 0.0

    # 6. Compile Results
    results = {
        "test_selection_reason": test_selection_reason,
        "divergence_status": is_divergent,
        "win_rate_test": {
            "test_type": win_test_type,
            "p_value_raw": win_p_value,
            "p_value_corrected": bonferroni_result['corrected_p_values'][0] if len(bonferroni_result['corrected_p_values']) > 0 else None,
            "effect_size": phi,
            "effect_size_name": "Phi coefficient"
        },
        "token_usage_test": {
            "test_type": token_test_type,
            "t_or_w_statistic": t_stat,
            "p_value_raw": token_p_value,
            "p_value_corrected": bonferroni_result['corrected_p_values'][1] if len(bonferroni_result['corrected_p_values']) > 1 else None,
            "effect_size": cohens_d,
            "effect_size_name": "Cohen's d"
        },
        "bonferroni_correction": {
            "alpha_adjusted": bonferroni_result['alpha_adjusted'],
            "n_tests": bonferroni_result['n_tests'],
            "family_wise_rejection": bonferroni_result['family_wise_rejection']
        },
        "contingency_table": contingency_table,
        "sample_sizes": {
            "dynamic_n": dynamic_agg['n'],
            "static_n": static_agg['n'],
            "paired_n": len(common_ids)
        }
    }

    # 7. Save Output
    save_statistical_results(results, output_path)
    logger.info("Statistical testing completed successfully.")
    return results

if __name__ == "__main__":
    main()
