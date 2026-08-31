"""
Meta-Analysis Implementation (Task T014).

Implements Random-Effects model (DerSimonian-Laird).
Outputs: data/processed/meta_status.json, data/derived/results.json (partial)

Logic:
- Read N from study_count.json.
- If N < 10, skip and write status "skipped".
- If N >= 10, run model.
"""
import json
import math
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

def get_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if parent.name == "code":
            return parent.parent
    return current.parent

def load_json(path: Path) -> Optional[Dict]:
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)

def save_json(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_effect_sizes_and_se(path: Path) -> List[Tuple[float, float]]:
    """Load (r, se) pairs from extracted_studies.csv."""
    if not path.exists():
        return []
    results = []
    import csv
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            r_val = row.get('r')
            se_val = row.get('se') # Assuming se is calculated or present
            # If se is not present, we might need to calculate it from n
            # For simplicity, we assume it's present or use a placeholder
            if r_val and se_val:
                try:
                    r = float(r_val)
                    se = float(se_val)
                    results.append((r, se))
                except ValueError:
                    pass
    return results

def run_random_effects_model(data: List[Tuple[float, float]]) -> Dict[str, Any]:
    """
    Run DerSimonian-Laird random effects model.
    Returns pooled effect, CI, and heterogeneity stats.
    """
    if not data:
        return {"status": "failed", "reason": "No data"}

    r_vals = [d[0] for d in data]
    se_vals = [d[1] for d in data]
    w_i = [1.0 / (se ** 2) for se in se_vals]
    
    # Fixed effect estimate
    sum_w = sum(w_i)
    sum_wr = sum(w * r for w, r in zip(w_i, r_vals))
    mu_fe = sum_wr / sum_w

    # Q statistic
    q = sum(w * (r - mu_fe) ** 2 for w, r in zip(w_i, r_vals))
    k = len(data)
    df = k - 1
    
    # Tau^2 (DerSimonian-Laird)
    c = sum(w_i) - (sum(w ** 2 for w in w_i) / sum_w)
    tau_sq = max(0, (q - df) / c) if c > 0 else 0

    # Random effects weights
    w_star = [1.0 / (se ** 2 + tau_sq) for se in se_vals]
    sum_w_star = sum(w_star)
    sum_w_star_r = sum(w * r for w, r in zip(w_star, r_vals))
    mu_re = sum_w_star_r / sum_w_star

    # SE of pooled
    se_re = math.sqrt(1.0 / sum_w_star)

    # 95% CI
    z = 1.96
    ci_lower = mu_re - z * se_re
    ci_upper = mu_re + z * se_re

    # I^2
    i_sq = max(0, (q - df) / q) if q > 0 else 0

    return {
        "status": "completed",
        "pooled_effect": mu_re,
        "se": se_re,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "tau_sq": tau_sq,
        "q": q,
        "i_squared": i_sq,
        "k": k
    }

def save_results(results: Dict, path: Path) -> None:
    save_json(path, results)

def ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

def run_meta_analysis() -> int:
    import logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger("meta_analysis")
    project_root = get_project_root()

    study_count_path = project_root / "data" / "processed" / "study_count.json"
    extracted_path = project_root / "data" / "processed" / "extracted_studies.csv"
    meta_status_path = project_root / "data" / "processed" / "meta_status.json"
    results_path = project_root / "data" / "derived" / "results.json"

    study_count = load_json(study_count_path)
    if not study_count:
        logger.error("study_count.json missing")
        return 1

    N = study_count.get("N", 0)
    
    if N < 10:
        logger.info(f"N={N} < 10. Skipping meta-analysis.")
        status = {
            "status": "skipped",
            "reason": "Insufficient studies (N < 10)",
            "N": N
        }
        save_json(meta_status_path, status)
        return 0

    logger.info(f"N={N} >= 10. Running meta-analysis.")
    data = load_effect_sizes_and_se(extracted_path)
    
    if not data:
        logger.warning("No valid effect sizes found.")
        status = {"status": "skipped", "reason": "No valid data"}
        save_json(meta_status_path, status)
        return 0

    results = run_random_effects_model(data)
    save_json(meta_status_path, results)
    
    # Update main results.json with meta-analysis findings
    main_results = load_json(results_path) or {}
    main_results.update(results)
    save_json(results_path, main_results)
    
    logger.info("Meta-analysis completed.")
    return 0

def main() -> int:
    return run_meta_analysis()

if __name__ == "__main__":
    sys.exit(main())
