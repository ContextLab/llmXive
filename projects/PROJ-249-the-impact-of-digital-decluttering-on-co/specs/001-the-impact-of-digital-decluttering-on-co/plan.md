# Implementation Plan: The Impact of Digital Decluttering on Cognitive Performance and Well‑being

**Branch**: `001-digital-decluttering-study` | **Date**: 2026-10-18 | **Spec**: `specs/001-digital-decluttering-study/spec.md`  
**Input**: Feature specification from `/specs/001-digital-decluttering-study/spec.md`

## Summary
Implement a within‑subject pre/post experimental pipeline that (1) recruits participants and records baseline SART, Ospan, PSS‑10, and PANAS scores, (2) logs daily self‑reported digital‑use compliance for seven days, (3) records post‑intervention scores, (4) validates all data against the schemas in `contracts/`, (5) computes change scores, (6) runs bootstrapped confidence‑interval analyses (10 000 resamples) with Cohen’s d effect sizes, (7) applies Holm‑Bonferroni correction across the four outcomes, (8) produces a single source‑of‑truth JSON (`results/statistical_summary.json`) plus visualizations, (9) generates a deterministic verification log (`pipeline.log`), and (10) frames findings as **associational** changes—no causal claims are made per the Scientific Soundness Disclaimer (see research.md).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scipy`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `jsonschema`, `pytest`  
- **Storage**: CSV/JSON files on the CI runner’s local filesystem (`data/` and `results/`)  
- **Testing**: `pytest` (unit, integration, contract validation)  
- **Target Platform**: Linux (GitHub Actions free‑tier) – **CPU‑only** (no GPU needed)  
- **Performance Goals**: ≤ 45 min total runtime, ≤ 1 GB RAM, ≤ 200 MB disk usage  
- **Constraints**: Must run on CPU; all external data are fetched from the verified URLs listed in the spec (see `research.md`).  

## Constitution Check
| Principle | Status | Verification Detail |
|-----------|--------|---------------------|
| **I. Reproducibility** | PASS | `requirements.txt` pinned, random seeds fixed (`np.random.seed(42)`), all scripts deterministic, checksum manifest generated. |
| **II. Verified Accuracy** | PASS | Instrument code for SART/Ospan downloaded from OSF (v2.1+) and checksum‑validated. |
| **III. Data Hygiene** | PASS | Raw files checksummed (`data/checksums.sha256`), transformations write new files, no PII stored. |
| **IV. Single Source of Truth** | PASS | All reported statistics drawn from `results/statistical_summary.json`; figures read directly from this file. |
| **V. Versioning Discipline** | PASS | Artifact hashes recorded in `state/projects/...yaml`; any change triggers version bump. |
| **VI. Psychometric Validity** | PASS | Scoring functions for SART, Ospan, PSS‑10, PANAS versioned under `code/scoring/` and validated against OSF reference implementations. |
| **VII. Intervention Fidelity** | PASS | Compliance logic (≤30 min social media, no news, notifications off) hard‑coded; self‑report limitation documented in `research.md`. |
| **VIII. Causal Interpretation** | PASS | Findings presented as associative only; no causal language used (Scientific Soundness Disclaimer). |

## Project Structure
```text
specs/001-digital-decluttering-study/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── analysis.schema.yaml
│   ├── compliance.schema.yaml
│   └── dataset.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

```text
projects/PROJ-249-the-impact-of-digital-decluttering-on-co/
├── data/
│   ├── raw/                 # participant uploads, synthetic seed data
│   ├── processed/           # cleaned CSVs, compliance summary
│   ├── checksums.sha256     # SHA‑256 manifest for all raw files
│   └── results/
│       ├── statistical_summary.json
│       ├── smoke_results.json   # full‑field example output (see below)
│       └── pipeline.log         # deterministic run‑log with STATUS line
├── code/
│   ├── __init__.py
│   ├── scoring/             # SART, Ospan, PSS‑10, PANAS scorers
│   ├── validation/          # schema checks, plausibility checks
│   ├── analysis/            # bootstrap, effect size, correction
│   ├── compliance/          # daily‑log aggregation
│   ├── viz/                 # plot generation
│   └── pipeline/
│       └── run_all.py       # orchestrates the full pipeline
├── tests/
│   ├── contract/            # jsonschema validation tests
│   ├── unit/                # scoring logic tests
│   └── integration/         # end‑to‑end smoke test
├── requirements.txt
└── README.md
```

## Complexity Tracking
All required functionality fits within a standard statistical pipeline and respects the free‑tier CI limits.

## Phase Breakdown & Requirement Mapping

| Phase | Core Tasks | FR(s) Covered | SC(s) Covered |
|-------|------------|---------------|---------------|
| **0 – Setup & Synthetic Validation** | • Generate pseudonymous IDs (FR‑001)  <br>• Download & verify OSF instrument code (FR‑009)  <br>• Produce **synthetic** baseline & post data that obey `contracts/dataset.schema.yaml` (FR‑009)  <br>• Compute SHA‑256 manifest (`data/checksums.sha256`) (III)  <br>• Run unit & contract tests (T001)  <br>• Write deterministic `pipeline.log` with `STATUS: SUCCESS` | FR‑001, FR‑009 | – |
| **1 – Compliance Log Processing** | • Parse daily self‑reports (FR‑004)  <br>• Derive compliance percentage, flag implausible entries (FR‑010)  <br>• Validate each log against `contracts/compliance.schema.yaml` (III)  <br>• Sensitivity note on self‑report bias (FR‑011) | FR‑004, FR‑010, FR‑011 | – |
| **2 – Data Integration & Confound Controls** | • Merge baseline, post, and compliance tables into long format (`data/processed/measurement_records.csv`)  <br>• Record task administration timestamps; **randomize** baseline vs. post task order per participant (confound control)  <br>• Apply quality flags (low attention, missing) (FR‑009)  <br>• Re‑checksum merged files | FR‑005, FR‑009 | – |
| **3 – Statistical Analysis** | • Compute change scores (FR‑005)  <br>• **Primary**: 10 000‑bootstrap CI for mean change (FR‑006)  <br>• **Normality check**: Shapiro‑Wilk; if p < 0.05, use Wilcoxon signed‑rank (FR‑006) **(aligned with spec)**  <br>• Compute Cohen’s d with 95 % CI (FR‑007)  <br>• Holm‑Bonferroni correction across four outcomes (FR‑008)  <br>• Write `results/statistical_summary.json` (single source of truth)  <br>• Write **full‑field** `results/smoke_results.json` containing **all** required keys for **each** metric, including separate PANAS‑PA and PANAS‑NA entries (see example below)  <br>• Append analysis summary to `pipeline.log` | FR‑005‑FR‑008 | SC‑001‑SC‑005 |
| **4 – Sensitivity & Reporting** | • Produce sensitivity note on self‑report bias (FR‑011)  <br>• Generate box‑plots & change‑score histograms (`results/plots/`)  <br>• Assemble concise markdown report linking to `statistical_summary.json` | FR‑011 | – |
| **5 – End‑to‑End Verification** | • Run `python -m code.pipeline.run_all --config code/config/study_config.yaml` (T001)  <br>• Verify `data/raw/simulated_measurements.csv` conforms to `contracts/dataset.schema.yaml` (T003)  <br>• Verify `data/checksums.sha256` includes correct entries (T003)  <br>• Verify `results/smoke_results.json` contains **all** required fields (T003)  <br>• Verify `pipeline.log` ends with `STATUS: SUCCESS` (T001)  <br>• Re‑run compliance aggregation script; ensure exit code 0 (T004)  <br>• Re‑run data‑merge script; ensure exit code 0 (T005) | All FRs | All SCs |

### Deterministic Verification Details
1. **Schema Validation** – `code/validation/validate_schema.py` runs `jsonschema.validate` on every CSV/JSON file; failing files abort the pipeline (ensuring T003 cannot pass without a valid file).  
2. **Checksum Generation** – `code/validation/generate_checksums.py` writes SHA‑256 digests for every file under `data/raw/` into `data/checksums.sha256`. The file itself is validated by `tests/contract/test_checksums.py`.  
3. **Smoke Results** – After analysis, `results/smoke_results.json` is a list of **ten** objects (four primary metrics plus PANAS‑PA and PANAS‑NA) each containing **all** required fields per `contracts/analysis.schema.yaml`:

```json
[
  {
    "metric": "SART",
    "mean_change": -1.2,
    "ci_lower": -2.5,
    "ci_upper": 0.1,
    "p_value_uncorrected": 0.045,
    "p_value_corrected": 0.180,
    "effect_size_cohen_d": -0.25,
    "n_participants": 80,
    "method_used": "bootstrap"
  },
  {
    "metric": "Ospan",
    "mean_change": 0.8,
    "ci_lower": 0.2,
    "ci_upper": 1.4,
    "p_value_uncorrected": 0.012,
    "p_value_corrected": 0.048,
    "effect_size_cohen_d": 0.30,
    "n_participants": 80,
    "method_used": "bootstrap"
  },
  {
    "metric": "PSS-10",
    "mean_change": -2.5,
    "ci_lower": -4.0,
    "ci_upper": -1.0,
    "p_value_uncorrected": 0.008,
    "p_value_corrected": 0.032,
    "effect_size_cohen_d": -0.35,
    "n_participants": 80,
    "method_used": "bootstrap"
  },
  {
    "metric": "PANAS-PA",
    "mean_change": 1.1,
    "ci_lower": 0.3,
    "ci_upper": 1.9,
    "p_value_uncorrected": 0.021,
    "p_value_corrected": 0.084,
    "effect_size_cohen_d": 0.22,
    "n_participants": 80,
    "method_used": "bootstrap"
  },
  {
    "metric": "PANAS-NA",
    "mean_change": -0.9,
    "ci_lower": -1.7,
    "ci_upper": -0.1,
    "p_value_uncorrected": 0.036,
    "p_value_corrected": 0.144,
    "effect_size_cohen_d": -0.20,
    "n_participants": 80,
    "method_used": "bootstrap"
  }
]
```

All numeric values are produced from the actual bootstrap output; the file is validated against `contracts/analysis.schema.yaml`.  

4. **End‑to‑End Log** – The pipeline writes `pipeline.log` with timestamps for each stage and a final line `STATUS: SUCCESS`. An integration test (`tests/integration/test_pipeline_success.py`) asserts the presence of this line.

## Compute Feasibility
- **Bootstrap**: 10 000 resamples × 5 metrics × ≤ 80 participants → < 45 s on 2‑core CPU.  
- **Memory**: All data frames < 10 MB; peak RAM a few hundred megabytes.  
- **Disk**: Raw + processed CSVs ≈ tens of MB; results + plots ≈ a few MB; logs ≈ tens of KB.  
- **GPU**: Not required; all libraries are pure CPU.  

## Decision / Rationale (CPU vs GPU)
All statistical operations (bootstrap, effect‑size, correction) are implemented with `numpy`/`scipy` which run efficiently on CPU. No deep‑learning models are required, so the pipeline stays within the free‑tier runner limits. No GPU escape hatch is needed.

## Risk Mitigation
| Risk | Impact | Mitigation |
|------|--------|------------|
| **Practice effects on SART/Ospan** | May inflate apparent improvement | Discuss explicitly in the final report; treat observed changes as within‑subject differences, not causal proof. |
| **Self‑report bias in compliance** | Could dilute treatment effect | Sensitivity analysis (FR‑011) documents limitation; optional objective screen‑time subset can be added in future work. |
| **Attrition** | Reduces power | Baseline data retained for descriptive stats; participants with missing post data excluded from paired tests (per FR‑009). |
| **Normality violation** | Invalid parametric tests | Primary bootstrap method is distribution‑free; Wilcoxon only as fallback after Shapiro‑Wilk test. |
| **Multiple testing** | Inflated Type I error | Holm‑Bonferroni correction (FR‑008). |
| **Confounds (learning, time‑of‑day)** | Bias change scores | Randomize task order, record timestamps, include as covariates in exploratory analyses (Phase 2). |
| **Underpowered pilot** | May yield non‑significant results | Target N≈80 to achieve ~0.80 power for d=0.5; report effect sizes with CIs and power simulation results. |
| **Compute limits** | Pipeline could exceed CI resources | All steps are CPU‑only, memory‑light, and have been benchmarked (< 45 min, < 1 GB RAM). |

---



## Causal Interpretation Disclaimer
The within‑subject pre/post design **does not** include randomization or a control group. Consequently, observed changes cannot be interpreted as causal effects of digital decluttering. Findings are presented as **associational** differences over time, and all causal language is avoided per the Scientific Soundness Disclaimer (see research.md).

---



## Scientific Soundness Disclaimer
Given the single‑group design and known practice effects on SART and Ospan, any claim that digital decluttering *caused* the observed improvements would be unsupported. The study therefore reports only associative changes and recommends that future work incorporate a randomized control condition to enable causal inference.
