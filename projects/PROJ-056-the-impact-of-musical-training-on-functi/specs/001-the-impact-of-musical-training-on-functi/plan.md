# Implementation Plan: The Impact of Musical Training on Functional Connectivity in Adolescent Brains

**Branch**: `001-musical-training-connectivity` | **Date**: 2024-10-13 | **Spec**: `specs/001-musical-training-connectivity/spec.md`  
**Input**: Feature specification from `/specs/001-musical-training-connectivity/spec.md`

## Summary
The project will implement a reproducible, CPU‑first pipeline that (1) ingests resting‑state fMRI and behavioral metadata (synthetic by default, real if a verified source becomes available), (2) filters and matches subjects into “musician” (≥1 yr training) and “non‑musician” groups while controlling for age, sex, motion, and SES, (3) computes ROI‑wise functional connectivity matrices, (4) performs edge‑wise Welch’s t‑tests with **Benjamini‑Yekutieli (BY) FDR** correction, (5) runs Network‑Based Statistic (NBS) for topological validation across multiple primary thresholds, (6) correlates connectivity strength with years of training within musicians using BY‑corrected results, and (7) conducts a threshold‑sensitivity sweep (q = 0.01, 0.05, 0.10). All steps respect the 7 GB RAM limit and the ≤6 h runtime budget on a GitHub Actions free‑tier runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `pandas`, `scipy`, `statsmodels`, `nibabel`, `networkx`, `matplotlib`, `seaborn`, `pyyaml`, `tqdm`, `jsonschema`  
- **Storage**: Local file system (`data/`); CSV/Parquet for tabular data, NumPy `.npy` for matrices, JSON for NBS components.  
- **Testing**: `pytest` (unit, integration, contract validation).  
- **Target Platform**: Linux (GitHub Actions runner).  
- **Performance Goals**: Peak RAM ≤ 7 GB; total wall‑clock ≤ 6 h; CPU‑only (no GPU required).  
- **Constraints**: No open dataset currently satisfies FR‑001; therefore **FR‑001 is deferred** until such a dataset is available. Synthetic mode provides a verification scaffold but does **not** replace the requirement for real data.

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Random seeds fixed; `requirements.txt` pinned; pipeline runnable on fresh CI runner. |
| II. Verified Accuracy | PASS | All citations limited to verified URLs; missing variables are reported, not fabricated. |
| III. Data Hygiene | PASS | Checksums recorded; no in‑place mutation; PII scan enforced. |
| IV. Single Source of Truth | PASS | All statistics derived from files under `data/`; no manual transcription. |
| V. Versioning Discipline | PASS | Content hashes tracked in project state YAML. |
| VI. Neuroimaging Data Integrity | PASS | Raw (or mock) NIfTI files preserved; preprocessing parameters logged. |
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
│   ├── preprocess.py               # Filtering, matching, regression residualization
│   └── mock_nifti.py               # Minimal NIfTI writer for schema compliance
├── analysis/
│   ├── atlas.py                    # Loads bundled Schaefer‑200 CSV (no download)
│   ├── connectivity.py             # Pearson correlation + Fisher‑z
│   ├── stats.py                    # Welch’s t‑test, BY FDR, effect sizes, NBS
│   ├── correlation.py              # Correlation (Pearson or Spearman) + BY FDR
│   └── sensitivity.py              # Threshold sweep & reporting
├── utils/
│   ├── logging.py
│   └── memory_monitor.py           # Logs peak RAM usage
└── main.py                         # CLI entry point (synthetic vs real mode)

data/
├── raw/            # Populated only when a verified dataset is supplied
├── processed/
│   ├── subjects.parquet
│   ├── connectivity_matrices.npy
│   └── logs/
└── results/
    ├── statistical_results.csv
    ├── nbs_components.json
    └── sensitivity_analysis.csv

tests/
├── unit/
├── integration/
└── contract/
```

## Complexity Tracking
| FR / SC | Phase / Task | Reason for Inclusion |
|--------|--------------|----------------------|
| FR‑001 | Phase 1 – `data/synthetic_generator.py` & `data/preprocess.py` | Loads (or generates) data, applies ≥1 yr threshold, matches confounders. **Deferred** until real data available. |
| FR‑002 | Phase 2 – `analysis/connectivity.py` | Computes ROI‑wise Pearson correlations and Fisher‑z transform. |
| FR‑003 | Phase 2 – `analysis/stats.py` (Welch’s t‑test) | Edge‑wise group comparison with BY FDR. |
| FR‑004 | Phase 2 – `analysis/correlation.py` | Correlates connectivity with years of training (musician only) with BY FDR. |
| FR‑005 | Phase 2 – `analysis/sensitivity.py` | Sweeps significance thresholds (q = 0.01, 0.05, 0.10) and reports counts. |
| FR‑006 | Phase 1 – `utils/memory_monitor.py` | Enforces ≤7 GB RAM; aborts if exceeded. |
| FR‑007 | Phase 2 – `analysis/stats.py` & `analysis/correlation.py` | Computes Cohen’s d (group) and reports R² for correlations; 95 % CIs via bootstrap. |
| FR‑008 | Phase 2 – `analysis/stats.py` (NBS) | Identifies largest connected component; runs NBS at three primary thresholds (t = 1.8, 2.0, 2.5). |
| FR‑009 | Phase 1 – `data/preprocess.py` (propensity‑score matching **and** regression residualization) | Balances age, sex, motion, SES; residualization always applied to avoid bias if matching fails. |
| SC‑001 | Phase 2 – NBS output (`nbs_components.json`) | Size of largest component vs. null distribution. |
| SC‑002 | Phase 2 – Correlation output (`statistical_results.csv`) | r vs. null hypothesis of zero correlation. |
| SC‑003 | Phase 2 – Sensitivity table (`sensitivity_analysis.csv`) | Counts at three q‑thresholds. |
| SC‑004 | Phase 3 – `utils/memory_monitor.py` log & runtime timer | Peak RAM & total runtime recorded. |
| SC‑005 | Phase 0 & Phase 3 – Power simulation (edge‑wise BY‑corrected) | Post‑hoc power estimate logged; acknowledges multiple‑comparison burden. |

## Phase Plan

### Phase 0 – Research & Data Strategy
1. **Dataset Fit Audit** – Verify that no verified source provides required rs‑fMRI + musical‑training metadata (see `research.md`).  
2. **Decision** – Default to **Synthetic Verification Mode**; expose a `--mode real` flag for future verified data.  
3. **Synthetic Specification** – Generate an adequately sized cohort (balanced groups) with realistic confound distributions; create mock NIfTI files (3 D volumes of random noise) to satisfy `nibabel` loader.  
4. **Documentation** – Record the “prototype‑only” status; flag SC‑005 as conditionally satisfied.

### Phase 1 – Data Model & Contracts
- Create JSON‑Schema files under `contracts/` (subject, connectivity, statistical_result, **network_component**).  
- Implement `data/synthetic_generator.py` to produce `subjects.parquet` and mock NIfTI files adhering to the schemas.  
- Implement `data/preprocess.py` to (a) filter by `years_of_training ≥ 1` for musicians, (b) drop subjects missing any required field, (c) attempt propensity‑score matching (caliper = 0.2 SD) on age, sex, motion, SES; regardless of matching outcome, **regress out** these covariates from each edge of the connectivity matrix; if matching reduces a group below 50, log a warning but continue with residualized data.  

### Phase 2 – Core Analysis (CPU‑only)
1. **Atlas Loading** – `analysis/atlas.py` reads a bundled CSV (`data/atlas/schaefer200.csv`) containing ROI indices and network assignments; **no external download**.  
2. **Connectivity Computation** – `analysis/connectivity.py` extracts ROI time‑series from each NIfTI (or mock NIfTI) using the atlas, computes Pearson correlation matrix, applies Fisher‑z.  
3. **Group Comparison** – `analysis/stats.py` runs Welch’s t‑test per edge, applies **Benjamini‑Yekutieli (BY) FDR** (α = 0.05), computes Cohen’s d and 95 % CI via 1 000 bootstrap resamples.  
4. **NBS** – Same module implements permutation‑based NBS (1 000 permutations) at **three primary t‑thresholds** (t = 1.8, 2.0, 2.5). Largest component size and FWER‑corrected p‑value saved to `data/results/nbs_components.json`.  
5. **Correlation & Effect Size** – `analysis/correlation.py` computes Pearson (or Spearman if Shapiro‑Wilk fails) between `years_of_training` and each edge within musicians; applies **BY FDR** across edges; reports r, 95 % CI, R², and q‑value.  
6. **Sensitivity** – `analysis/sensitivity.py` repeats edge‑wise testing using **q‑values** at thresholds 0.01, 0.05, 0.10; aggregates counts into `sensitivity_analysis.csv`; flags “low stability” if the count drops > 30 % between 0.05 and 0.01 or if the 95 % CI for R² includes zero at the stricter threshold.  
7. **Memory Guard** – `utils/memory_monitor.py` wraps each heavy step; aborts with clear error if RAM > 7 GB.

### Phase 3 – Validation & Testing
- **Unit Tests** – Validate each module on a tiny synthetic subset (N = 4).  
- **Integration Test** – Run full pipeline in synthetic mode; assert that output files conform to their JSON‑Schemas via `jsonschema`.  
- **Performance Check** – Record runtime and peak RAM; ensure limits respected.  
- **Power Simulation** – Run 500 simulated datasets with known effect size d ≈ 0.5, apply full BY‑corrected pipeline, estimate detection rate; log result as post‑hoc power estimate (addresses SC‑005).  

### Phase 4 – Documentation & Handoff
- Finalize `quickstart.md` with commands for synthetic and (future) real modes.  
- Update `research.md` to explicitly state the dataset limitation, the deferred status of FR‑001, and the power‑simulation approach.  
- Ensure all artifacts are listed in `README.md` and version‑hashed in the project state YAML.

---

