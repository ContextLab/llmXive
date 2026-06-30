"""
Power Analysis for Epistemic Resilience Study.

Calculates the theoretical minimum sample size (N) required to detect
a specific effect size with desired statistical power.

Parameters:
- Effect Size (Cohen's h): 0.5 (Medium effect)
- Alpha: 0.05
- Power: 0.80

This script does NOT require the fetched dataset; it performs a theoretical
calculation based on statistical power analysis principles.
"""
import math
import json
from pathlib import Path
from statsmodels.stats.power import zt_ind_solve_power
from statsmodels.stats.proportion import proportion_difference

# Constants defined in the task description
COHEN_H = 0.5
ALPHA = 0.05
POWER = 0.80

def calculate_sample_size():
    """
    Calculates the minimum sample size per group needed for a two-proportion
    Z-test (independent samples) given Cohen's h, alpha, and power.

    Returns:
        int: The calculated sample size per group (rounded up).
    """
    # statsmodels uses effect_size for proportions which corresponds to Cohen's h
    # for a two-sample proportion test.
    # We assume a two-sided test (default).
    # effect_size = h = 0.5
    # alpha = 0.05
    # power = 0.80
    # ratio = 1.0 (equal sample sizes in both groups: clean vs mislead)

    n_per_group = zt_ind_solve_power(
        effect_size=COHEN_H,
        alpha=ALPHA,
        power=POWER,
        ratio=1.0,
        alternative='two-sided'
    )

    # Round up to the nearest integer
    return math.ceil(n_per_group)

def generate_report(n_per_group):
    """
    Generates a markdown report with the power analysis results.
    """
    total_n = n_per_group * 2
    report = f"""# Power Analysis Report

## Parameters
- **Effect Size (Cohen's h)**: {COHEN_H} (Medium effect)
- **Significance Level (Alpha)**: {ALPHA}
- **Statistical Power (1 - Beta)**: {POWER}
- **Test Type**: Two-sample Z-test for proportions (two-sided)

## Results
- **Minimum Sample Size per Group**: {n_per_group}
- **Total Minimum Sample Size (N)**: {total_n}

## Interpretation
To detect a medium effect size (Cohen's h = 0.5) in the difference of proportions
between the clean and misleading context groups with 80% power at a 0.05 significance level,
a minimum of **{n_per_group}** items are required per condition (Clean and Mislead).

The total dataset size required is **{total_n}** items.

## Validation Gate
The project specification requires:
1. Theoretical N >= 200
2. Actual Dataset Size >= 200

Calculated Theoretical N: {total_n}
Status: {"PASS" if total_n >= 200 else "FAIL - Increase power or effect size sensitivity"}
"""
    return report

def main():
    """
    Main entry point to calculate sample size and write the report.
    """
    # Calculate
    n_per_group = calculate_sample_size()
    total_n = n_per_group * 2

    # Generate report content
    report_content = generate_report(n_per_group)

    # Ensure output directory exists
    output_dir = Path("data/analysis")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write report
    output_path = output_dir / "power_analysis_report.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    # Write JSON summary for programmatic access
    json_summary = {
        "cohen_h": COHEN_H,
        "alpha": ALPHA,
        "power": POWER,
        "n_per_group": n_per_group,
        "total_n": total_n,
        "gate_pass": total_n >= 200
    }
    json_path = output_dir / "power_analysis_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_summary, f, indent=2)

    print(f"Power analysis complete.")
    print(f"Sample size per group: {n_per_group}")
    print(f"Total sample size: {total_n}")
    print(f"Report written to: {output_path}")
    print(f"Summary written to: {json_path}")

if __name__ == "__main__":
    main()