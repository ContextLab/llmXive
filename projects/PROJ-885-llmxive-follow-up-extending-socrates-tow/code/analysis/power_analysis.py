"""T015: Statistical power analysis and under-powered flag.

Computes the required sample size for a paired t-test detecting a medium
effect size (d = 0.5) at 80% power and alpha = 0.05 using
statsmodels.stats.power.TTestPower().solve_power, compares it with the
actual trajectory count recorded in data/processed/generation_stats.json,
and writes data/results/power_analysis_report.json with the fields
required_n, actual_n, is_sufficient, underpowered_flag.

Fails loudly (non-zero exit) if the input file is missing or malformed.
"""

import json
import sys
from pathlib import Path

from statsmodels.stats.power import TTestPower

from llmxive_toolkit import paths

EFFECT_SIZE = 0.5
TARGET_POWER = 0.80
ALPHA = 0.05

def load_generation_stats(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"generation stats not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        stats = json.load(f)
    if not isinstance(stats, dict) or "total_count" not in stats:
        raise ValueError(f"malformed generation stats in {path}: missing 'total_count'")
    total = stats["total_count"]
    if not isinstance(total, int) or total <= 0:
        raise ValueError(f"invalid total_count in {path}: {total!r}")
    return stats

def compute_required_n(effect_size: float = EFFECT_SIZE,
                       power: float = TARGET_POWER,
                       alpha: float = ALPHA) -> int:
    analysis = TTestPower()
    n = analysis.solve_power(effect_size=effect_size, power=power,
                             alpha=alpha, alternative="two-sided")
    return int(n)

def main() -> int:
    stats_path = paths.data("processed", "generation_stats.json")
    report_path = paths.data("results", "power_analysis_report.json")

    stats = load_generation_stats(stats_path)
    actual_n = stats["total_count"]

    required_n = compute_required_n()
    is_sufficient = actual_n >= required_n
    # underpowered_flag mirrors generation_stats.json's own flag and the
    # power comparison: true if the sample cannot support 80% power at d=0.5.
    underpowered_flag = (not is_sufficient) or bool(stats.get("underpowered_flag", False))

    report = {
        "required_n": required_n,
        "actual_n": actual_n,
        "is_sufficient": is_sufficient,
        "underpowered_flag": underpowered_flag,
        "effect_size": EFFECT_SIZE,
        "power": TARGET_POWER,
        "alpha": ALPHA,
        "generation_stats_path": str(stats_path),
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
    print(f"Power analysis report written to {report_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())