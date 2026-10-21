# Implementation Plan: Nostalgia Cognitive Flexibility Analysis (Re‑scoped)

**Branch**: `001-nostalgia-cognitive-flexibility` | **Date**: 2026-10-20 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-nostalgia-cognitive-flexibility/spec.md`

## Summary
The specification requires testing whether a nostalgia induction improves WCST performance in adults ≥ 65 y. No open dataset provides a genuine nostalgia vs. control manipulation, so the primary empirical hypothesis **cannot be answered with publicly available data**.  
**Instead, the pipeline demonstrates the required statistical workflow** (Welch’s t‑test, Bonferroni correction, Cohen’s d with 95 % CI, sensitivity analyses, MMSE exclusion, runtime monitoring) on real WCST outcomes combined with a **synthetic stimulus assignment** for illustration only. All results are flagged with `"validity_status": "simulation"` and no causal claims about nostalgia are made.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.2`, `numpy==2.0.0`, `scipy==1.14.0`, `statsmodels==0.14.2`, `pyyaml==6.0.2` (pinned in `requirements.txt`)  
- **Compute**: CPU‑only; expected runtime < 30 min, memory < 2 GB.  
- **Reproducibility**: Fixed random seed = 42; all steps deterministic; no external network calls after initial dataset download (cached).

## Constitution Check
| Principle | Status | Implementation Detail |
|-----------|--------|-----------------------|
| I. Reproducibility | ✅ | `requirements.txt` pins exact versions; random seed fixed; CI isolation enforced. |
| II. Verified Accuracy | ✅ | `code/reference_validator.py` validates citations (title overlap ≥ 0.7). |
| III. Data Hygiene | ✅ | All files under `data/` are SHA‑256 checksummed; raw files never overwritten. |
| IV. Single Source of Truth | ✅ | Numbers in `statistical_report.json` and `sensitivity_report.json` are generated programmatically. |
| V. Versioning Discipline | ✅ | `code/utils.py` updates artifact hashes in the state YAML after each write. |
| VI. Stimulus Fidelity | ✅ | Placeholder audio files (`nostalgia.wav`, `control.wav`) stored with checksums in `data/stimuli/manifest.json`. |
| VII. Behavioral Trace Integrity | ✅ | Raw WCST trial logs (if present) are preserved under `data/raw/`. |

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
│   ├── raw/
│   │   ├── wcst_dataset.csv                # real WCST outcomes (public)
│   │   └── metadata.json                  # {"simulation_mode": true, "seed": 42}
│   ├── processed/
│   │   ├── cleaned_dataset.csv            # after FR‑001, FR‑006 filtering
│   │   └── wcst_metrics.csv               # separate metric table (participant_id, perseverative_errors, categories_completed)
│   ├── stimuli/
│   │   ├── nostalgia.wav
│   │   ├── control.wav
│   │   └── manifest.json                  # paths + SHA‑256 checksums
│   └── results/
│       ├── statistical_report.json
│       ├── sensitivity_report.json
│       └── exclusion_log.json
├── code/
│   ├── __init__.py
│   ├── ingestion.py          # loads real WCST data, adds synthetic stimulus_type
│   ├── cleaning.py           # FR‑001, FR‑006, missing‑value handling
│   ├── analysis.py           # Welch t‑test, Bonferroni, Cohen's d, CI, MDES, OLS
│   ├── sensitivity.py        # α‑sweep (0.01, 0.04, 0.05, 0.06) & MMSE‑exclusion sensitivity
│   ├── runtime_monitor.py    # logs warning if runtime > 6 h (FR‑007)
│   ├── reference_validator.py
│   ├── utils.py              # checksum, hash updates
│   └── main.py               # orchestrates the pipeline
├── tests/
│   ├── contract/
│   │   └── validate_output.py
│   ├── integration/
│   └── unit/
├── requirements.txt
└── README.md
```

## Mapping of Functional Requirements to Pipeline Phases
| FR | Description | Script / Function | Output |
|----|-------------|-------------------|--------|
| FR‑001 | Age ≥ 65 validation | `cleaning.filter_age()` | `exclusion_log.json` (age exclusions) |
| FR‑002 | Welch’s independent‑samples t‑test on two outcomes | `analysis.run_welch_test()` | `statistical_report.json` (raw & corrected p‑values) |
| FR‑003 | Bonferroni correction for two outcomes | `analysis.apply_bonferroni()` | `statistical_report.json` (corrected p‑values) |
| FR‑004 | Effect size (Cohen’s d) with 95 % CI | `analysis.compute_cohens_d()` | `statistical_report.json` (effect size & CI) |
| FR‑005 | Borderline flag for **raw** p‑values in [0.04, 0.06] | `sensitivity.flag_borderline()` | `sensitivity_report.json` (sensitivity status) |
| FR‑006 | MMSE ≥ 24 exclusion (optional) | `cleaning.filter_mmse()` | `exclusion_log.json` (MMSE exclusions) |
| FR‑007 | Runtime warning > 6 h | `runtime_monitor.wrap()` around `main` | warning in CI log |
| Power analysis & sample size | A priori power analysis (d = 0.5, α = 0.05, 80 % power) | `ingestion.generate_sample_size()` | documented in `metadata.json` |
| Covariate adjustment | OLS: outcome ~ stimulus_type + education_years + gender | `analysis.run_adjusted_model()` | `statistical_report.json` (adjustment_status) |

## Phase Ordering (Data‑Driven Execution Flow)
1. **Ingestion** – `code/ingestion.py` loads a real WCST dataset, adds a synthetic `stimulus_type` column, writes `wcst_dataset.csv` and `metadata.json`.  
2. **Checksum Verification** – `code/utils.py verify_stimuli` ensures stimulus placeholders match `manifest.json`.  
3. **Cleaning** – `code/cleaning.py` applies FR‑001 and FR‑006, writes `cleaned_dataset.csv`, `wcst_metrics.csv`, and `exclusion_log.json`.  
4. **Statistical Analysis** – `code/analysis.py` runs Welch’s tests, Bonferroni correction, Cohen’s d with 95 % CI, MDES, and adjusted OLS; writes `statistical_report.json`.  
5. **Sensitivity Analyses** – `code/sensitivity.py` performs α‑sweep (0.01, 0.04, 0.05, 0.06) and MMSE‑exclusion sensitivity; writes `sensitivity_report.json`.  
6. **Runtime Monitoring** – `code/runtime_monitor.py` wraps the entire pipeline; emits warning if wall‑clock > 6 h.  
7. **Contract Validation** – `tests/contract/validate_output.py` checks JSON files against `contracts/*.schema.yaml`.  
8. **Reporting** – `code/main.py` orchestrates steps 1‑7 and prints a concise summary.

## Power Analysis (deterministic)
Using `statsmodels.stats.power.TTestIndPower` with effect size d = 0.5, α = 0.05 (two‑tailed), power = 0.80 yields **≈128 participants per group**. The ingestion step therefore selects **128 participants** for each synthetic stimulus group (total ≈ 256) from the real WCST pool, ensuring the a priori requirement is met. Post‑hoc MDES is computed from observed variance and recorded in `statistical_report.json`.

## Risk & Mitigation
- **Dataset Unavailability** – mitigated by using a real WCST dataset for outcomes and synthetic stimulus labels for workflow demonstration. The limitation is explicitly documented; no empirical claim about nostalgia is made.  
- **Runtime Exceedance** – all steps are linear‑time; expected runtime < 5 min; warning mechanism satisfies FR‑007.  
- **Multiple‑Comparison Mis‑application** – Bonferroni factor derived from the actual number of outcomes (two).  
- **Effect‑Size Consistency** – Cohen’s d aligns with Welch’s test; no pooled‑SD misuse.  
- **Collinearity** – outcomes are reported separately; no claim of independent effects.  

---



