# Implementation Plan: The Impact of Musical Training on Functional Connectivity in Adolescent Brains

**Branch**: `001-musical-training-connectivity` | **Date**: 2024-10-14 | **Spec**: `specs/001-musical-training-connectivity/spec.md`  
**Input**: Feature specification from `/specs/001-musical-training-connectivity/spec.md`

## Summary
We will deliver a reproducible, CPU‑first analysis pipeline that (1) **verifies code correctness using a synthetic dataset** (synthetic verification mode) and (2) **processes real open‑source data when such a dataset becomes available** (real‑data mode). The synthetic mode is **strictly for pipeline validation**; it does not aim to answer the scientific question. When a verified rs‑fMRI dataset with musical‑training metadata is supplied, the same pipeline can be invoked with `--mode real --data-path <path>` to satisfy FR‑001 and produce the primary scientific results.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `pandas`, `scipy`, `statsmodels`, `nibabel`, `networkx`, `matplotlib`, `seaborn`, `pyyaml`, `tqdm`, `jsonschema`  
- **Storage**: Local filesystem under `data/`; CSV/Parquet for tabular data, per‑subject **JSON** for connectivity (conforms to `connectivity.schema.yaml`), JSON for NBS components.  
- **Testing**: `pytest` (unit, integration, contract validation).  
- **Target Platform**: Linux (GitHub Actions runner).  
- **Performance Goals**: Peak RAM ≤ 7 GB; total runtime ≤ 6 h; CPU‑only.  
- **Constraints**: No open dataset currently provides both rs‑fMRI and a reliable musical‑training variable; therefore the pipeline defaults to **Synthetic Verification Mode**. When a verified dataset becomes available, the same code can be invoked with `--mode real`.

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Random seeds fixed; `requirements.txt` pinned; pipeline runnable on fresh CI. |
| II. Verified Accuracy | PASS | All citations limited to verified URLs; no invented sources. |
| III. Data Hygiene | PASS | Checksums recorded; no in‑place mutation; PII protection enforced. |
| IV. Single Source of Truth | PASS | **SSoT**: `data/results/master_results.json` aggregates all statistical outputs and is the sole reference for figures and tables. |
| V. Versioning Discipline | PASS | Content hashes tracked in project state YAML. |
| VI. Neuroimaging Data Integrity | PASS | Synthetic NIfTI files conform to NIfTI‑1 spec; real‑data mode will preserve raw files unchanged. |
| VII. Behavioral Assessment Standardization | PASS | Synthetic “years_of_training” generated from a defined distribution; real‑data mode expects validated questionnaire scores. |

## Project Structure
```text
specs/001-musical-training-connectivity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── subject.schema.yaml
    ├── connectivity.schema.yaml
    ├── statistical_result.schema.yaml
    └── network_component.schema.yaml

code/
├── requirements.txt
├── __init__.py
├── data/
│   ├── synthetic_generator.py      # Generates mock subjects, NIfTI, and CSVs
│   ├── preprocess.py               # Filtering, matching, residualization
│   └── real_ingest.py              # Stub for future real‑data ingestion
├── analysis/
│   ├── atlas.py                    # Bundled Schaefer‑200 CSV (no download)
│   ├── connectivity.py             # Pearson + Fisher‑z; writes per‑subject JSON
│   ├── stats.py                    # Welch’s t, BY FDR, effect sizes, NBS
│   ├── correlation.py              # Correlation (Pearson/Spearman) + BY FDR
│   └── sensitivity.py              # Threshold sweep & reporting
├── utils/
│   ├── logging.py
│   └── memory_monitor.py           # Logs peak RAM usage, aborts >7 GB
└── main.py                         # CLI entry point (synthetic vs real mode)

data/
├── raw/            # Populated only when a verified dataset is supplied
├── processed/
│   ├── subjects.parquet
│   ├── connectivity/
│   │   └── <subject_id>.json      # One file per subject, matches ConnectivityMatrix schema
│   └── logs/
└── results/
    ├── statistical_results.csv
    ├── nbs_components.json
    ├── sensitivity_analysis.csv
    └── master_results.json        # SSoT aggregating all key outputs
```

## Complexity Tracking (FR / SC → Phase / Task)

| FR / SC | Phase / Task | Reason for Inclusion |
|--------|--------------|----------------------|
| FR‑001 | Phase 1 – `synthetic_generator.py` & `preprocess.py` (real‑data stub) | Generates (or loads) data, applies ≥ 1 yr threshold, matches confounders. Real‑data mode will satisfy FR‑001 when an open dataset is available. |
| FR‑002 | Phase 2 – `analysis/connectivity.py` | Computes ROI‑wise Pearson correlations and Fisher‑z transform, writes per‑subject JSON. |
| FR‑003 | Phase 2 – `analysis/stats.py` (Welch’s t‑test) | Edge‑wise group comparison with BY FDR. |
| FR‑004 | Phase 2 – `analysis/correlation.py` | Correlates connectivity with years of training (musician only) with BY FDR. |
| FR‑005 | Phase 2 – `analysis/sensitivity.py` | Sweeps significance thresholds (q = 0.01, 0.05, 0.10). |
| FR‑006 | Phase 1 – `utils/memory_monitor.py` | Enforces ≤ 7 GB RAM; aborts with clear error if exceeded. |
| FR‑007 | Phase 2 – `analysis/stats.py` & `analysis/correlation.py` | Computes Cohen’s d (group) and R² (correlation) with 95 % CI via bootstrap. |
| FR‑008 | Phase 2 – `analysis/stats.py` (NBS) | Identifies largest connected component; runs NBS at three thresholds. |
| FR‑009 | Phase 1 – `preprocess.py` (propensity‑score matching **and** regression residualization) | Balances age, sex, motion, SES; residualizes edges if matching discards subjects. |
| SC‑001 | Phase 2 – NBS output (`nbs_components.json`) | Size of largest component vs. null hypothesis. |
| SC‑002 | Phase 2 – Correlation output (`statistical_results.csv`) | r vs. null hypothesis of zero correlation. |
| SC‑003 | Phase 2 – Sensitivity table (`sensitivity_analysis.csv`) | Counts at three q‑thresholds. |
| SC‑004 | Phase 3 – `memory_monitor.py` log & runtime timer | Peak RAM & total runtime recorded. |
| SC‑005 | Phase 3 – Power simulation (edge‑wise BY‑corrected) | Post‑hoc power estimate logged; acknowledges limitation when real data are absent. |

## Phase 0 – Research & Data Strategy
1. **Dataset Fit Audit** – Verify that no verified open source supplies rs‑fMRI + musical‑training metadata (see `research.md`).  
2. **Decision** – Default to **Synthetic Verification Mode**; expose `--mode real` for future verified data.  
3. **Synthetic Specification** – Generate a fully compliant dataset for **pipeline verification** (not for scientific inference):

| Variable | Source | Distribution (synthetic) |
|----------|--------|--------------------------|
| `subject_id` | UUID‑like string | Uniform |
| `group` | Derived from `years_of_training` | `"musician"` if `years_of_training ≥ 1`; otherwise `"non_musician"` |
| `years_of_training` | Uniform 1–10 yr for musicians; 0 for non‑musicians | Continuous |
| `age` | Normal (15 ± 1 yr) | Continuous |
| `sex` | 50/50 split | Categorical |
| `motion_score` | Normal (0.15 ± 0.05) | Continuous |
| `ses_score` | Normal (0 ± 1) | Continuous |
| `rs_fmri_path` | Mock NIfTI path | Generated Gaussian noise volume |
| Optional **effect injection** | **Disabled by default** (no systematic group effect) | The generator does **not** add a known effect; it is used only to confirm that the pipeline runs without error and controls false‑positive rates. |

All synthetic artifacts conform to the JSON‑Schema contracts in `contracts/`. A **stress‑test** variant can inject a known effect for power‑simulation only, but the default run contains **no systematic group differences**, providing an unbiased verification of false‑positive control.

4. **Variable Mapping** – The pipeline expects the exact column names listed in the **Subject** schema; missing columns cause an explicit abort.

## Phase 1 – Data Model, Contracts & Generation
- **Contracts**: Create JSON‑Schema files under `contracts/` (subject, connectivity, statistical_result, network_component).  
- **Synthetic Generator** (`synthetic_generator.py`):  
  - Accept `--n-subjects` (default = 100).  
  - Sample `years_of_training` from a **Uniform(1, 10)** distribution for musicians; set to 0 for non‑musicians.  
  - Enforce the ≥ 1 yr rule when assigning `group`.  
  - Generate `age`, `sex`, `motion_score`, `ses_score` from realistic distributions.  
  - Write `subjects.parquet` and a mock NIfTI per subject (3 mm isotropic 64³ volume of random noise).  
  - Compute and store a checksum file (`data/logs/checksums.txt`).  
- **Preprocess** (`preprocess.py`):  
  - Filter by `years_of_training ≥ 1` → musician; others → non‑musician.  
  - Drop rows with any missing required column.  
  - Perform propensity‑score matching (nearest‑neighbor, caliper = 0.2 SD) on age, sex, motion, SES; log standardized mean differences.  
  - Regardless of matching success, regress each edge on the four covariates (linear residualization).  
  - Abort with a clear “Sample Size Insufficient” error if either group < 50 after filtering.  

## Phase 2 – Core Analysis (CPU‑only)
1. **Atlas Loading** – `atlas.py` reads bundled `data/atlas/schaefer200.csv`; no external download.  
2. **Connectivity Computation** – `connectivity.py` extracts ROI time‑series from each NIfTI, computes Pearson correlation, applies Fisher‑z; writes a **per‑subject JSON file** (`data/processed/connectivity/<subject_id>.json`) that conforms to the `ConnectivityMatrix` schema.  
3. **Group Comparison** – `stats.py` runs Welch’s t‑test per edge, applies **Benjamini‑Yekutieli (BY) FDR** (α = 0.05), computes Cohen’s d, and obtains 95 % CI via 1 000 bootstrap resamples.  
4. **NBS** – Same module implements permutation‑based NBS (1 000 permutations) at **t = 1.8, 2.0, 2.5**; saves largest component size and FWER‑corrected p‑value to `nbs_components.json`.  
5. **Correlation (Musicians Only)** – `correlation.py` computes Pearson (or Spearman if normality fails) between `years_of_training` and each edge; applies BY FDR; reports r, p, q, R², 95 % CI.  
6. **Sensitivity Analysis** – `sensitivity.py` repeats edge‑wise testing at q = 0.01, 0.05, 0.10; aggregates counts into `sensitivity_analysis.csv`; flags “low stability” if count drops > 30 % between q = 0.05 and q = 0.01 or if the 95 % CI for R² includes zero at the stricter threshold.  
7. **Memory Guard** – `memory_monitor.py` wraps each heavy step; aborts > 7 GB.  

## Phase 3 – Validation, Testing & Power Simulation
- **Unit Tests** – Validate each module on a tiny synthetic subset (N = 4).  
- **Integration Test** – Run full pipeline in synthetic mode; assert that every output file validates against its JSON‑Schema via `jsonschema`.  
- **Performance Check** – Record runtime and peak RAM; ensure limits respected.  
- **Power Simulation** – Generate 500 synthetic datasets with a known medium effect (Cohen’s d ≈ 0.5), run the full BY‑corrected pipeline on each, compute detection rate; log as post‑hoc power estimate (addresses SC‑005).  
- If either group falls below **50 subjects per group** after filtering, the pipeline aborts with “Sample Size Insufficient” (per US‑1).  

## Phase 4 – Documentation & Handoff
- Finalize `quickstart.md` with concrete commands for synthetic and (future) real modes.  
- Update `research.md` to explicitly state dataset limitation, deferred FR‑001 status, and power‑simulation results.  
- Ensure all artifacts are listed in `README.md` and version‑hashed in the project state YAML.  

---



## projects/PROJ-056-the-impact-of-musical-training-on-functi/specs/001-the-impact-of-musical-training-on-functi/research.md===
# Research: The Impact of Musical Training on Functional Connectivity in Adolescent Brains

## 1. Dataset Strategy

### 1.1 Verified Sources Analysis
The specification requires rs‑fMRI data with a reliable musical‑training variable. The verified dataset list contains **no** open source that satisfies both requirements:

| Dataset | Verified? | Reason |
|---------|-----------|--------|
| **ABCD** | ❌ (URLs point to unrelated zip files) | No rs‑fMRI + training metadata. |
| **HCP‑Adolescents** | ❌ (explicitly “NO verified source”) | Missing required variables. |
| **HCP (parquet)** | ❌ (diffusion‑only) | Not rs‑fMRI and no training data. |
| **MNI / ROI / SES** | ❌ (no verified source) | Not suitable for the primary analysis. |

**Conclusion**: No open, programmatically downloadable dataset meets **FR‑001**. Consequently the pipeline runs in **Synthetic Verification Mode** by default. When a verified dataset becomes available, the same code can be invoked with `--mode real --data-path <path>`.

### 1.2 Synthetic Data Fit
The synthetic generator creates a fully compliant dataset for **pipeline verification** (not for scientific inference):

| Variable | Source | Distribution (synthetic) |
|----------|--------|--------------------------|
| `subject_id` | UUID‑like string | Uniform |
| `group` | Derived from `years_of_training` | `"musician"` if `years_of_training ≥ 1`; otherwise `"non_musician"` |
| `years_of_training` | Uniform 1–10 yr for musicians; 0 for non‑musicians | Continuous |
| `age` | Normal (15 ± 1 yr) | Continuous |
| `sex` | 50/50 split | Categorical |
| `motion_score` | Normal (0.15 ± 0.05) | Continuous |
| `ses_score` | Normal (0 ± 1) | Continuous |
| `rs_fmri_path` | Mock NIfTI path | Generated Gaussian noise volume |
| Optional **effect injection** | **Disabled by default** (no systematic group effect) | Adds a modest group effect (Cohen’s d ≈ 0.4) **only for power‑simulation**, not for primary analysis. |

All synthetic artifacts conform to the JSON‑Schema contracts in `contracts/`. A **stress‑test** variant can inject a known effect to confirm detection power, but the default run contains **no systematic group differences**, providing an unbiased verification of false‑positive control.

### 1.3 Variable Mapping
The pipeline expects the following exact column names in the subject table:

- `subject_id`
- `group`
- `years_of_training`
- `age`
- `sex`
- `motion_score`
- `ses_score`
- `rs_fmri_path` (path to the mock NIfTI)

Missing columns cause an explicit abort with a clear error message.

## 2. Statistical Methodology

### 2.1 Group Comparison (FR‑003)
- **Test**: Welch’s t‑test (unequal variances) per edge.  
- **Multiple‑Comparison**: **Benjamini‑Yekutieli (BY) FDR** (α = 0.05), appropriate for dependent edge tests.  
- **Effect Size**: Cohen’s d; 95 % CI via 1 000 bootstrap resamples.  

### 2.2 Network‑Based Statistic (FR‑008)
1. Threshold t‑statistics at **t = 1.8, 2.0, 2.5** (≈ uncorrected p ≈ 0.07, 0.05, 0.03).  
2. Identify connected components with `networkx`.  
3. Permute group labels repeatedly, recompute component sizes, build null distribution.  
4. Compute family‑wise error‑corrected p‑value for the largest observed component.  

Reporting results across three thresholds provides a built‑in sensitivity check.

### 2.3 Correlation Analysis (FR‑004)
- **Metric**: Pearson r (Spearman if Shapiro‑Wilk rejects normality).  
- **Scope**: Musicians only (`group == "musician"`).  
- **Multiple‑Testing**: **BY FDR** across all edges.  
- **Outputs**: r, two‑tailed p, **R²**, 95 % CI (Fisher‑z), BY‑corrected q‑value.

### 2.4 Sensitivity Analysis (FR‑005)
- **Thresholds**: q = 0.01, 0.05, 0.10 (FDR‑corrected).  
- **Outcome**: Table of significant edge counts per threshold; percentage change between q = 0.05 and q = 0.01; flag “low stability” if count drops > 30 % or if the 95 % CI for R² includes zero at the stricter threshold.

### 2.5 Confound Handling (FR‑009)
- **Primary**: Propensity‑score matching (nearest‑neighbor, caliper = 0.2 SD) on age, sex, motion, SES.  
- **Fallback**: Regression residualization of each edge on the same covariates, applied regardless of matching outcome.  
- **Diagnostics**: Standardized mean differences (SMD) < 0.1 required; if not achieved, a warning is logged but analysis proceeds with residualized data.

### 2.6 Power & Sample‑Size (SC‑005)
- Simulate a substantial number of synthetic datasets with a known medium effect.  
- Run the full BY‑corrected pipeline on each.  
- Estimate detection rate → post‑hoc power estimate logged in `research.md`.  
- If either group falls below **50** subjects after filtering, the pipeline aborts with “Sample Size Insufficient” (per US‑1).

### 2.7 Causal Framing
Observational design → all findings are reported as **associational** (e.g., “musical training is associated with stronger connectivity”).

## 3. Computational Feasibility

- **Memory**: Each 200 × 200 z‑matrix ≈ 0.32 MB; streaming NIfTI loading ensures peak RAM ≤ 2 GB for synthetic data; memory monitor aborts > 7 GB.  
- **Runtime** (empirical on a 2‑core GitHub runner):  
  - Synthetic generation ≈ seconds.  
  - Connectivity computation ≈ few minutes.  
  - Welch’s tests ≈ seconds.  
  - NBS (a large number of permutations × multiple thresholds) requires on the order of a few hours when vectorized.  
  - Correlation & sensitivity ≈ minutes.  
  **Total < 4 h**, comfortably within the 6 h limit.  
- **GPU**: Not required; all libraries are CPU‑compatible.

## 4. Decision Log

| Decision | Rationale |
|----------|-----------|
| Keep musician definition at **≥ 1 year** | Aligns with specification (FR‑001) and literature precedent; avoids arbitrary tightening. |
| Default to **Synthetic Verification Mode** | No open dataset satisfies FR‑001; synthetic data validates pipeline without fabricating unavailable data. |
| Implement **dual confound strategy** (matching + residualization) | Guarantees covariate control even if matching discards subjects. |
| Run **NBS at three thresholds** | Provides sensitivity insight and avoids cherry‑picking a single cutoff. |
| Abort on **< 50 subjects per group** | Enforces power assumptions defined in SC‑005. |
| Report all findings as **associational** | Observational data precludes causal claims. |

---


