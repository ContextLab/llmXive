# Quickstart Guide: llmXive Follow‑up

This guide walks you through the minimal steps required to set up the project
and run the pre‑study power analysis that verifies we have enough statistical
power (≥ 0.8) for the planned Wilcoxon signed‑rank tests.

## Prerequisites

- Python 3.11+ (the environment used by the CI runner)
- Internet access (to download the required Python packages)

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

## 2. Verify configuration

The configuration file `config/settings.yaml` is already pinned with the
required seed (`2026`), hyper‑parameters, and a hard timeout of **5 hours**
(`18000` s). Feel free to inspect it if you wish.

## 3. Run the pre‑study power analysis

```bash
python code/analysis/statistical_test.py
```

This script:

* computes the required sample size for a Wilcoxon signed‑rank test
 with effect size **d = 0.5** (medium) and α = 0.05,
* enforces the project constraint of **N ≥ 30**,
* reports the achieved power at the final recommended N,
* writes the full JSON report to `results/pre_study_power.json`.

You should see a console output similar to:

```
--- Pre‑study Power Analysis ---
Target Power: 0.8 [UNRESOLVED-CLAIM: c_61f3aa76 — status=not_enough_info]
Significance Level (alpha): 0.05
Assumed Effect Size (d): 0.5 (Medium)

Calculated Minimum Sample Size (N): 28 [UNRESOLVED-CLAIM: c_b3964275 — status=not_enough_info]
Adjusting N to 30 to satisfy project constraint (N >= 30) for robustness.

Report saved to: results/pre_study_power.json
Final Recommended Sample Size (N): 30 [UNRESOLVED-CLAIM: c_235a7074 — status=not_enough_info]
```

Verify that the JSON file exists:

```bash
cat results/pre_study_power.json
```

The file contains fields such as `final_recommended_n` and
`power_achieved_at_final_n`, which must be ≥ 0.8.

## 4. Continue with the rest of the pipeline

Once the power analysis succeeds, you can proceed with the remaining
stages described in the project's `quickstart.md` (data download,
preprocessing, training, etc.). The rest of the pipeline assumes the
configuration and power‑analysis artifacts are present.
