# Implementation Plan: The Impact of Nostalgia on Cognitive Flexibility in Aging Adults

**Branch**: `001-nostalgia-cognitive-flexibility` | **Date**: 2026-10-15 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-nostalgia-cognitive-flexibility/spec.md`

## Summary

**Scope reframing (flagged for spec kickback)**: No open, publicly downloadable dataset containing WCST performance together with a nostalgia-vs-control stimulus label for older adults exists; the verified-source search confirmed this. The spec's primary goal (a real-world comparison of nostalgia vs. control conditions) therefore **cannot be answered with obtainable data**, and fabricating or simulating data as if it were real evidence is prohibited. This plan instead delivers a **methodological demonstration**: a deterministic, seeded simulation of the full analysis pipeline, with every output labeled `"validity_status": "simulation"` and **no causal or real-world claims** made. The simulation demonstrates correct implementation of FR-001–FR-007 (age validation, Welch's t-test, Bonferroni correction, effect sizes with CI, sensitivity analysis, MMSE exclusion, runtime monitoring) so that, if real data are later obtained, the identical pipeline can be re-run on them.

The pipeline enforces **FR-001** (age ≥ 65 validation), **FR-006** (MMSE ≥ 24 exclusion when the `MMSE` column is present), performs the **Welch's independent-samples t-test** required by **FR-002**, applies **Bonferroni correction** (**FR-003**), computes **Hedges' g** with 95 % confidence intervals (**FR-004**; see kickback note below), flags borderline p-values using a corrected-alpha-relative band (**FR-005**; see kickback note below), and logs a warning if runtime exceeds 6 hours (**FR-007**).

**Spec kickback notes (plan supersedes; spec.md must be updated)**:
- **FR-004**: spec.md says "Cohen's d"; the plan uses **Hedges' g** because Cohen's d with a pooled SD contradicts Welch's unequal-variance test (concern scientific_soundness-47482a6d). Spec FR-004 should be updated to Hedges' g.
- **FR-005**: spec.md says the borderline range is 0.04–0.06; after Bonferroni correction the corrected α is 0.025, so a corrected p in 0.04–0.06 is already non-significant and the label is ambiguous (concerns methodology-914d4971, scientific_soundness-056e3965). The plan defines the sensitive band as corrected p ∈ **[0.020, 0.030]** (±0.005 around corrected α = 0.025). Spec FR-005 should be updated accordingly.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `pyyaml` (pinned in `requirements.txt`)
- **Storage**: Local file system under `data/` (raw, processed, stimuli, results)
- **Testing**: `pytest` (unit, integration, contract validation)
- **Target Platform**: Linux GitHub Actions free-tier runner (2 CPU, ≈7 GB RAM, ≈14 GB disk) — **CPU-first**; no GPU required.
- **Performance Goals**: End-to-end run ≤ 30 min; memory ≤ 2 GB.
- **Constraints**: Strict reproducibility (seeded randomness, checksummed data). **No network access is required at any step** (T101 remediation: the previous ingestion step attempted a dataset download and failed with exit=1; ingestion is now a pure deterministic local generator).

## Constitution Check
| Principle | Status | Implementation Detail |
|-----------|--------|-----------------------|
| I. Reproducibility | ✅ | `requirements.txt` pins exact versions; random seed fixed at 42 in `code/ingestion.py`; no external downloads; CI isolation enforced. |
| II. Verified Accuracy | ✅ | `code/reference_validator.py` checks citation title overlap ≥ 0.7 before any result is written. |
| III. Data Hygiene | ✅ | Every file under `data/` is SHA-256 checksummed; raw files never overwritten; derived files written to new paths with provenance logs. |
| IV. Single Source of Truth | ✅ | All numbers in `statistical_report.json` and `sensitivity_report.json` are produced programmatically; the paper will reference these files directly. |
| V. Versioning Discipline | ✅ | `code/utils.py` updates artifact hashes in `state/projects/PROJ-524-...yaml` after each write. |
| VI. Stimulus Fidelity | ✅ | Stimulus placeholders stored in `data/stimuli/` with recorded SHA-256; referenced by hash in analysis code; marked "simulation only". |
| VII. Behavioral Trace Integrity | ✅ | Simulated raw WCST trial logs kept in `data/raw/` alongside aggregated metrics. |

## Project Structure
```text
specs/001-nostalgia-cognitive-flexibility/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    └── output.schema.yaml

projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/
├── data/
│   ├── raw/               # Deterministic simulation output (seed = 42)
│   ├── processed/         # Cleaned dataset after FR-001, FR-006
│   ├── stimuli/           # Placeholder media files + checksums
│   └── results/
│       ├── statistical_report.json
│       ├── sensitivity_report.json
│       └── exclusion_log.json
├── code/
│   ├── __init__.py
│   ├── ingestion.py          # Deterministic simulation generator (no network)
│   ├── cleaning.py           # Implements FR-001, FR-006, missing-value handling
│   ├── analysis.py           # Welch t-test, Bonferroni, Hedges' g, CI, MDES, adjusted model
│   ├── sensitivity.py        # Threshold sweep, borderline flag (FR-005)
│   ├── runtime_monitor.py    # Emits warning if runtime > 6 h (FR-007)
│   ├── reference_validator.py
│   ├── utils.py
│   └── main.py               # Orchestrates the pipeline
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
├── requirements.txt
└── README.md
```

## Mapping of Functional Requirements to Pipeline Phases
| FR | Description | Pipeline Phase / Script | Notes |
|----|-------------|--------------------------|-------|
| FR-001 | Age ≥ 65 validation | `cleaning.py → filter_age()` | Excludes records with missing age or age < 65. |
| FR-002 | Welch's independent-samples t-test on two outcomes | `analysis.py → run_welch_test()` | Applied to `perseverative_errors` and `categories_completed`. |
| FR-003 | Bonferroni correction | `analysis.py → bonferroni_correction()` | Two comparisons ⇒ α/2 = 0.025. |
| FR-004 | Hedges' g with 95 % CI (plan supersedes spec's "Cohen's d"; flagged for kickback) | `analysis.py → compute_hedges_g()` | Bias-corrected effect size using the non-pooled variance convention consistent with Welch's test. |
| FR-005 | Borderline flag: corrected p ∈ [0.020, 0.030] (plan supersedes spec's 0.04–0.06; flagged for kickback) | `sensitivity.py → flag_borderline()` | Band is ±0.005 around the Bonferroni-corrected α = 0.025. |
| FR-006 | MMSE ≥ 24 exclusion (optional) | `cleaning.py → filter_mmse()` | Executed only if `MMSE` column present. |
| FR-007 | Runtime warning > 6 h | `runtime_monitor.py` wrapped around `main.py` | Logs warning; pipeline continues. |
| Power analysis & sample size | A priori power analysis documented and enforced | `ingestion.py` (generator size) | d = 0.5, α = 0.05, power = 0.80 ⇒ ≈128 per group; generator creates 256 participants. |
| Covariate adjustment | Adjusted linear model always fitted | `analysis.py → run_adjusted_model()` | Simulation includes `education_years` and `gender`; OLS with stimulus_type + covariates alongside the unadjusted Welch test; `adjustment_status` recorded. |

## Phase Ordering (Data-Driven Execution Flow)
1. **Data Generation** (`ingestion.py`): Deterministically generate (seed = 42, no network) **256 participants** (128 per condition) meeting all schema constraints, including covariates `education_years` and `gender`, and simulated raw WCST trial logs. Output: `data/raw/raw_dataset.csv` + `data/raw/metadata.json` with `"simulation_mode": true`.
2. **Checksum & Validation** (`utils.py`): Record SHA-256 of generated files; verify stimulus placeholder checksums; abort on mismatch.
3. **Cleaning** (`cleaning.py`): Apply FR-001, FR-006, remove rows with missing WCST metrics. Log exclusions (`exclusion_log.json`).
4. **Statistical Analysis** (`analysis.py`): Execute FR-002, FR-003, FR-004; fit the adjusted linear model; compute post-hoc MDES and record `adjustment_status`.
5. **Sensitivity Checks** (`sensitivity.py`): Perform FR-005 across α = 0.01, 0.025, 0.05 and the MMSE-exclusion sensitivity; generate `sensitivity_report.json`.
6. **Runtime Monitoring** (`runtime_monitor.py`): Wrap entire pipeline; emit warning if wall-clock > 6 h.
7. **Reporting** (`main.py`): Write `statistical_report.json`, `sensitivity_report.json`, and `exclusion_log.json`, all with `"validity_status": "simulation"`.
8. **Contract Validation** (`tests/contract/validate_output.py`): Ensure JSON files conform to `contracts/*.schema.yaml`.

## Power Analysis
Using `statsmodels.stats.power.tt_ind_solve_power` with a two-sample design, medium effect size d = 0.5, α = 0.05 (two-tailed), and power = 0.80 yields **≈128 participants per group**. The simulation generator therefore creates **256 participants total** (128 per condition), ensuring the demonstration is adequately powered. Post-hoc MDES is computed from the observed sample size and reported as a limitation.

## Risk & Mitigation
- **Dataset unavailability (root cause, spec-level)**: No open WCST + nostalgia dataset exists; the study is a simulation-only methodological demonstration. The spec's real-world goal requires new data collection or an access-gated dataset — flagged for kickback.
- **Runtime exceedance**: All steps are linear-time O(N); with N = 256 runtime < 5 min on the CI runner. The warning mechanism satisfies FR-007.
- **Multiple-comparison mis-application**: Bonferroni correction factor is derived from the number of outcomes actually tested, not hard-coded.
- **Effect-size bias**: Hedges' g (bias-corrected, non-pooled variance) is consistent with Welch's unequal-variance test.
- **Ingestion failure (T101)**: The previous network-dependent ingestion step failed (exit=1). Ingestion is now a pure local deterministic generator with no network dependency, so its output is deterministically verifiable.