# Implementation Plan: Exploring the Correlation Between Crystal Structure and Thermal Conductivity in Perovskites

**Branch**: `001-correlation-perovskites` | **Date**: 2026-06-28 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-correlation-perovskites/spec.md`

## Summary
The project must ingest perovskite crystal structures via the Materials Project API, merge them with experimentally measured thermal conductivity values from peer‑reviewed literature/NIST, compute crystallographic distortion descriptors, perform stratified correlation analysis, and build a validated multiple‑linear regression model with 5‑fold cross‑validation. All steps are deterministic, reproducible, and respect the functional and success criteria (FR‑001 – FR‑015, SC‑001 – SC‑005).

**Known Limitations**: This plan acknowledges several methodological constraints that may affect results: (1) DFT-optimized crystal structures may not capture real-sample defects/grain boundaries; (2) major confounds (synthesis method, measurement technique) are uncontrolled; (3) stratified analysis may be underpowered with N < 80; (4) Slack temperature correction may not apply to all chemistry classes. These are documented in research.md and reported in final outputs.

## Technical Context
- **Language/Version**: Python 3.9  
- **Primary Dependencies**: `pymatgen==2023.9.1`, `pandas==2.2.2`, `numpy==1.26.4`, `scikit-learn==1.5.0`, `statsmodels==0.14.2`, `matplotlib==3.9.0`, `seaborn==0.13.2`, `requests==2.32.3`, `tqdm==4.66.5`  
- **Storage**: CSV files under `data/` (raw, cleaned, descriptors) and PNG figures under `figures/`  
- **Testing**: `pytest` with deterministic seeds; contract tests validate schema compliance.  
- **Target Platform**: Linux CI runner (GitHub Actions free tier) – CPU‑only.  
- **Project Type**: Library/CLI for reproducible scientific workflow.  
- **Performance Goals**: Entire pipeline ≤ 5 h on free‑tier CI; peak RAM ≤ 5 GB.  
- **Constraints**: No GPU, no external heavy models, strict deterministic randomness.  

## Constitution Check
| Principle | Check |
|-----------|-------|
| I. Reproducibility | All scripts accept a `--seed` argument; `requirements.txt` pins exact versions. |
| II. Verified Accuracy | All citations (e.g., Slack 1979, Smith et al. 2021) are verified by the Reference‑Validator. |
| III. Data Hygiene | Raw API responses are saved with SHA‑256 checksums; every transformation writes a new file. |
| IV. Single Source of Truth | Every figure/table references a row in `data/merged_perovskite.csv`. |
| V. Versioning Discipline | Content hashes recorded in `state/projects/...yaml`. |
| VI. Computational Determinism | `random_state=42` used throughout; double‑precision arithmetic enforced. |
| VII. Dataset Provenance | **CONFLICT**: Constitution VII permits Materials Project thermal properties endpoint OR NIST, but FR‑010 explicitly requires peer‑reviewed experimental literature only (excluding DFT-calculated MP values). FR‑010 is the active requirement; Constitution VII requires amendment to align with spec. |

All principles satisfied except Principle VII which has a documented conflict requiring spec-level amendment. The plan can proceed to Phase 0 research with this acknowledgment.

## Project Structure
```text
specs/001-correlation-perovskites/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── merged_perovskite.schema.yaml

src/
├── ingest/
│   ├── fetch_structures.py          # Materials Project API download
│   └── fetch_thermal.py            # Load literature/NIST CSVs
├── cleaning/
│   └── clean_merge.py              # Apply FR‑001, FR‑002, FR‑010, FR‑013
├── descriptors/
│   └── compute_descriptors.py      # FR‑003, FR‑008
├── analysis/
│   ├── correlation.py              # FR‑004, FR‑009, FR‑014
│   └── regression.py               # FR‑005, FR‑006, FR‑011, FR‑012
├── utils/
│   └── validation.py               # VIF, causal‑language check (FR‑007)
└── main.py                         # Orchestrates pipeline

tests/
├── contract/
│   └── test_schema.py
├── unit/
│   ├── test_ingest.py
│   ├── test_descriptors.py
│   └── test_analysis.py
└── integration/
    └── test_full_pipeline.py
```

## Complexity Tracking
All functional requirements are mapped to concrete modules:

| FR | Module(s) | Description |
|----|-----------|-------------|
| FR‑001 | `src/ingest/fetch_structures.py` | Materials Project API fetch + ABX₃ filter |
| FR‑002 | `src/ingest/fetch_thermal.py` + `src/cleaning/clean_merge.py` | Merge & null removal |
| FR‑003 | `src/descriptors/compute_descriptors.py` | Compute tilting, variance, tolerance, volume |
| FR‑004 | `src/analysis/correlation.py` | Pearson/Spearman + multiple‑comparison correction |
| FR‑005 | `src/analysis/regression.py` | Linear regression with 5‑fold CV |
| FR‑006 | `src/analysis/regression.py` | Held‑out test evaluation (R², RMSE) |
| FR‑007 | `src/utils/validation.py` | Causal‑language scanner |
| FR‑008 | `src/utils/validation.py` | VIF calculation & exclusion |
| FR‑009 | `src/analysis/correlation.py` | Sensitivity sweep of p‑value thresholds |
| FR‑010 | `src/cleaning/clean_merge.py` | Provenance field enforcement |
| FR‑011 | `src/analysis/regression.py` | Feature‑importance report |
| FR‑012 | `src/analysis/regression.py` | Scatter plots with 95 % CI |
| FR‑013 | `src/cleaning/clean_merge.py` | Slack temperature normalization |
| FR‑014 | `src/analysis/correlation.py` | Stratify by chemistry class |
| FR‑015 | `src/analysis/regression.py` (report generation) | Include R² > 0.5 justification |

All success criteria (SC‑001 – SC‑005) are verified by unit/integration tests and final report generation.

---