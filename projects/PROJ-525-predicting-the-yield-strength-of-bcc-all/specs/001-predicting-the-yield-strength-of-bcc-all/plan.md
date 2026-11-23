# Implementation Plan: Predicting Yield Strength of BCC Alloys

**Branch**: `001-bcc-yield-strength` | **Date**: 2024-10-21 | **Spec**: `specs/001-bcc-yield-strength/spec.md`  
**Input**: Feature specification from `/specs/001-bcc-yield-strength/spec.md`

## Summary
Implement a reproducible, CPU‑first machine‑learning pipeline that (1) downloads the public MPEA database, (2) filters exclusively for BCC‑phase alloys with valid yield‑strength measurements, (3) normalizes compositions, (4) engineers scalar compositional descriptors (δ, VEC, mixing entropy, mixing enthalpy, electronegativity difference) together with an Isometric Log‑Ratio (ILR) transformation, (5) performs a stratified 80/20 train‑test split (if N ≥ 80) or halts with `DATA_SCARCITY`, (6) trains Random Forest, Gradient Boosting, and Ridge regression models using Repeated 5‑Fold CV (10 repeats), (7) evaluates mean R², MAE, RMSE, bootstrapped 95 % CI for R², and permutation‑importance with confidence, (8) logs all rejected entries, aggregation actions, and descriptor‑error events, and (9) writes a JSON results file that satisfies the contracts.

Each functional requirement (FR‑001…FR‑008) and success criterion (SC‑001, SC‑002, SC‑005, SC‑006) is mapped to a concrete phase or step below.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `scipy`, `periodictable`, `pymatgen`, `requests`, `pyyaml`  
- **Storage**: Local filesystem (`data/raw`, `data/processed`, `data/logs`, `reports`)  
- **Testing**: `pytest` (unit tests for download, feature engineering, modeling)  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, ≤ 6 h)  
- **Constraints**: CPU‑first; no GPU required; all external data must be fetched from open sources; must halt gracefully on data‑scarcity or unavailable source.  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | `requirements.txt` pins exact versions; all random seeds (`random_state=42`) are fixed; the pipeline is deterministic. |
| II. Verified Accuracy | The only external identifier cited is the MPEA database DOI `10.1038/s41597-020-00768-9` (the canonical source required by FR‑001); no dataset URLs beyond this canonical DOI and the verified sources listed in `research.md` are introduced. Descriptor justifications cite independent peer-reviewed literature (Zhang et al. 2008; Senkov et al.; George et al.), not the MPEA source itself. |
| III. Data Hygiene | Raw data is stored under `data/raw` immutable; processed files are written to new paths; checksums are recorded in `state/`. |
| IV. Single Source of Truth | All figures/tables are generated from `reports/results.json`; no manual transcription. |
| V. Versioning Discipline | Every artifact will be hashed by the platform; the plan does not rely on mutable external files. |
| VI. Compositional Feature Integrity | Descriptor formulas are defined in `data-model.md`; elemental properties are sourced from the `periodictable` library (a static reference). |
| VII. Crystal‑Structure Specificity | Filtering logic explicitly requires `crystal_structure == "BCC"` before any downstream step. |

## Project Structure
```text
specs/001-predicting-the-yield-strength-of-bcc-all/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── bcc_alloy.schema.yaml
    ├── compositional_descriptor.schema.yaml
    └── results.schema.yaml

projects/PROJ-525-predicting-the-yield-strength-of-bcc-all/
├── data/
│   ├── raw/                 # MPEA download (immutable)
│   ├── processed/           # Filtered & engineered CSVs
│   └── logs/                # rejected_entries.log, aggregation.log, descriptor_errors.log
├── code/
│   ├── __init__.py
│   ├── download.py          # FR‑001, FR‑002
│   ├── features.py          # FR‑003, FR‑003.1
│   ├── models.py            # FR‑005, FR‑006
│   └── utils.py
├── tests/
│   ├── test_download.py
│   ├── test_features.py
│   └── test_models.py
├── reports/
│   └── results.json         # validated against contracts/results.schema.yaml
├── state/
│   └── projects/PROJ-525...yaml
└── requirements.txt
```

## Phase Mapping (FR / SC Coverage)

| Phase | Description | FR(s) addressed | SC(s) addressed |
|-------|-------------|-----------------|-----------------|
| **Phase 0 – Data Acquisition** | Resolve DOI `10.1038/s41597-020-00768-9`; download MPEA; verify presence of required columns (`composition`, `yield_strength`, `crystal_structure`). | FR‑001 | – |
| **Phase 0.5 – Metadata & Confounding Variable Handling** | Identify optional columns for testing temperature, strain‑rate, and processing history. If present, filter to entries measured under standard (room‑temperature, standard strain‑rate) conditions and log exclusions; if the metadata is absent for some or all rows, log `CONFOUNDING_METADATA_MISSING` and record the limitation in `reports/results.json`. Yield strength is treated as a *construct measured under heterogeneous conditions*; the results report explicitly states which fraction of entries carried testing-condition metadata so the construct-validity boundary of SC‑001 is transparent. | – | – |
| **Phase 1 – Filtering & Scarcity Check** | Remove rows with missing `yield_strength` or non‑BCC `crystal_structure`; normalize compositions to sum = 1.0; write `rejected_entries.log`. Halt with exit‑code 1 & message `DATA_SCARCITY: Insufficient BCC alloys (N < 80)` if post‑filter count < 80. | FR‑001, FR‑002, FR‑004 | – |
| **Phase 2 – Duplicate Aggregation** | Group by identical composition; average yield values, compute std‑dev, log to `aggregation.log`. | FR‑007 | SC‑005 |
| **Phase 3 – Descriptor Error Guard** | Compute scalar descriptors; catch domain errors (e.g., `log(0)`); assign 0.0, log alloy IDs to `descriptor_errors.log`. | FR‑008 | SC‑006 |
| **Phase 4 – Feature Engineering (Inside CV)** | For each training fold: calculate δ, VEC, mixing entropy, mixing enthalpy (using `data/raw/nist_janaf_params.json`), electronegativity diff, and ILR coordinates. Each alloy's derived features are produced as a **`CompositionalDescriptor`** entity and assembled into a **`CombinedFeatureSet`** (both defined in `data-model.md` and validated against `contracts/compositional_descriptor.schema.yaml`). **Descriptor Justification (independent literature)**: • δ (atomic radius mismatch) quantifies lattice distortion, the primary solid‑solution strengthening mechanism in BCC refractory HEAs (Senkov et al., refractory high‑entropy alloy strengthening studies; Zhang et al., Adv. Eng. Mater. 10 (2008) δ/Δχ/ΔHmix solid‑solution phase‑formation rules). • VEC correlates with electronic structure and phase stability (Guo et al., VEC-based FCC/BCC phase prediction for HEAs). • Mixing entropy and mixing enthalpy quantify configurational disorder and thermodynamic interaction, linked to solid‑solution formation and strengthening (Zhang et al. 2008; George et al., Nat. Rev. Mater. HEA reviews). • Electronegativity difference reflects charge-transfer/chemical mismatch (Zhang et al. 2008 Δχ rule). **Status acknowledgement**: these descriptors are physically motivated *heuristics* widely used in the HEA literature for phase/strength correlation; they are not validated causal mechanisms for yield strength, and this study reports them as associational predictors only. | FR‑003, FR‑003.1 | – |
| **Phase 5 – Feature Selection (Inside CV)** | Apply L1‑regularized linear model *or* Recursive Feature Elimination on the combined feature set; enforce that at least one scalar and one ILR feature survive. Halt with `COMPLEMENTARITY_FAILURE` if violated. | FR‑003.1 (complementarity) | – |
| **Phase 6 – Model Training & Repeated CV** | Train RF, GB, Ridge on each training fold; evaluate on hold‑out fold; repeat 5‑fold CV 10 times. Record mean R², MAE, RMSE. | FR‑005 | – |
| **Phase 7 – Bootstrap Confidence Intervals** | For each model, bootstrap 1000 resamples of the hold‑out predictions; compute percentile 95 % CI for R². | FR‑006 | – |
| **Phase 8 – Permutation Importance** | Perform permutation importance on the full filtered dataset (using the best‑performing model); report top‑5 features. Reported for predictive insight only; not interpreted causally. | FR‑006 | – |
| **Phase 9 – Reporting** | Assemble `reports/results.json` conforming to `contracts/results.schema.yaml` (the model‑performance results contract). Include CI, feature‑importance ranks, stability metrics, practical‑utility flag (`MAE ≤ 50 MPa`), the descriptor‑error count (SC‑006), the aggregation record (SC‑005), and the confounding-metadata coverage fraction from Phase 0.5. | – | SC‑001, SC‑002, SC‑005, SC‑006 |
| **Phase 10 – Exit & Logging** | Write overall runtime log; ensure exit code 0 on success. | – | – |

## Statistical Power & Sample-Size Justification

The N ≥ 80 threshold is a spec-mandated minimum (FR‑004), not a derived power requirement. An honest a priori assessment on the **actual independent sample size** (repeated CV reuses the same N observations; it does not create independent validation observations):

- With N = 80 and the combined feature set (~10–30 predictors after selection), a standard F-test power analysis for R² (α = 0.05) gives approximately **0.80 power to detect a large effect (Cohen's f² ≈ 0.35, i.e., R² ≈ 0.26)**, but only **~0.35–0.50 power for a medium effect (f² ≈ 0.15, i.e., R² ≈ 0.13)**.
- **Power limitation (explicit acknowledgement)**: the study is therefore adequately powered only for large composition–strength associations; a non-significant result cannot be interpreted as evidence of no relationship. This limitation is reported verbatim in `reports/results.json` and carried into any manuscript.
- If the post-filter N substantially exceeds 80 (the MPEA database is expected to contain more BCC entries), power improves accordingly; the actual N and the corresponding detectable effect size at [deferred] power are computed and reported at runtime.

## Complexity Tracking
No additional architectural complexity is required beyond the linear pipeline described. All steps are CPU‑tractable on the free runner; memory usage stays < 5 GB for < 10 k rows.