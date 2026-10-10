# Implementation Plan: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

**Branch**: `feature/motif-rsfc` | **Date**: 2026-10-10 | **Spec**: `specs/feature/motif-rsfc/spec.md`  
**Input**: Feature specification from `specs/feature/motif-rsfc/spec.md`

## Summary
We will build a reproducible, end‑to‑end pipeline that (1) downloads resting‑state functional MRI data, (2) generates synthetic structural connectomes when diffusion data are unavailable, (3) computes rsFC matrices and global efficiency, (4) enumerates **all 13** undirected 3‑node motifs, (5) generates degree‑preserving null models (≥ 1000 iterations) and computes motif‑z‑scores, (6) performs partial Pearson and Spearman correlations controlling for structural global degree **and additional covariates**, applies Bonferroni correction across 13 motifs, runs a permutation test (≥ 1000 permutations), conducts VIF diagnostics and, when needed, switches to ridge regression or PCA, (7) conducts a power‑analysis for N = 50, α = 0.05/13, power = 0.80, and (8) produces a PDF report containing scatter plots, confidence intervals, VIF diagnostics, the required disclaimer string, and the power‑analysis result.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `scipy`, `pandas`, `networkx`, `matplotlib`, `seaborn`, `statsmodels`, `reportlab`, `datasets` (for OpenNeuro), `tqdm`  
- **Storage**: Local filesystem (`data/raw/`, `data/processed/`, `data/logs/`, `results/`)  
- **Testing**: `pytest` (unit & integration) + contract validation tests  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ~7 GB RAM, ~14 GB disk)  
- **Performance Goals**: Motif enumeration ≤ 300 s per subject; PDF generation ≤ 2 min; total runtime ≤ 6 h on CI  
- **Constraints**: CPU‑first; no GPU required; deterministic seeds (`seed=42`)  

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| **I. Reproducibility** | ✅ | Fixed seeds, `requirements.txt`, CI‑downloaded data each run |
| **II. Verified Accuracy** | ⏳ | Citations will be verified in `research.md` |
| **III. Data Hygiene** | ✅ | Raw files stored unchanged; derived files have provenance metadata |
| **IV. Single Source of Truth** | ✅ | Every figure/statistic traces to a single row in `data/processed/` |
| **V. Versioning Discipline** | ✅ | Content hashes recorded in `state/`; timestamps managed by platform |
| **VI. Structural Data Integrity** | ✅ | Synthetic binary connectomes are generated reproducibly; provenance recorded |
| **VII. Statistical Transparency** | ✅ | Scripts log test parameters, seeds, library versions, and full results |

## Data Availability
- **OpenNeuro ds000228 (Midnight Scan Club)** provides publicly downloadable resting‑state fMRI for 10 subjects and is accessible via the Hugging Face `datasets` library.  
- **Synthetic Structural Connectomes** are generated in‑pipeline using a degree‑preserving random graph model (Maslov‑Sneppen) seeded at 42. This synthetic data serves as the structural modality because no open dataset currently offers diffusion tractography at the required resolution.  
- The pipeline will **abort with a clear error** if the OpenNeuro download fails and synthetic generation cannot be performed, preventing any fabrication of missing modalities.

## FR/SC Traceability
| Requirement | Plan Element(s) | Notes |
|-------------|-----------------|-------|
| **FR‑001** (Download) | T002 – Data Ingestion & Validation | Downloads rs‑fMRI from OpenNeuro; generates synthetic structural adjacency if diffusion unavailable |
| **FR‑002** (Structural) | T004 – Parcellation | Generates binary undirected adjacency matrices (synthetic or real) |
| **FR‑003** (rsFC) | T005 – Functional Calc | Pearson correlation matrices & global efficiency on thresholded graph |
| **FR‑004** (Motifs) | T006 – Motif Quant, T006b – Secondary Null | Enumerates **13** undirected 3‑node motifs, computes z‑scores |
| **FR‑005** (Correlation) | T007 – Stats Analysis (Global) | Multivariate GLM / ridge regression, VIF check, Bonferroni (α = 0.05/13) |
| **FR‑006** (Permutation) | T007 – Stats Analysis (Global) | ≥ 1000 permutations per motif |
| **FR‑007** (Report) | T008 – Reporting | PDF with plots, CI, VIF, disclaimer, power analysis |
| **FR‑008** (Logging) | T017 – Utils/Logging | `pipeline.log` records all steps, warnings, errors |
| **FR‑009** (Disclaimer) | T008 – Reporting | Mandatory string verified via PDF text search |
| **FR‑010** (Power) | T007 – Stats Analysis (Global) | Power‑analysis module reports minimum detectable r for N = 50, α_adj = 0.05/13, power = 0.80 |
| **SC‑001** (≥ 95 % subjects) | T002 – Validation logic (`actual ≥ 0.95*target`) | Logs warning if threshold not met |
| **SC‑002** (Motif ≤ 300 s) | T006 – Timeout guard (300 s) | Aborts with warning if exceeded |
| **SC‑003** (All p‑values logged) | T007 – Stats Output | JSON/CSV contains raw & corrected p‑values for all **13** motifs |
| **SC‑004** (PDF ≤ 2 min, ≤ 5 MB) | T008 – Report generation | Benchmarked for CI; file size limit enforced |
| **SC‑005** (Power analysis present) | T007 – Power module | Minimum detectable r reported in PDF |

## Project Structure
### Documentation (this feature)
```
specs/feature/motif-rsfc/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── analysis_results.schema.yaml
│   ├── dataset.schema.yaml
│   ├── motif_profile.schema.yaml
│   ├── output.schema.yaml
│   ├── results.schema.yaml
│   └── structural_connectome.schema.yaml
└── tasks.md
```

### Source Code (single‑project layout)
```
code/
├── __init__.py
├── config.py            # paths, seeds, constants
├── data_loader.py       # OpenNeuro download, synthetic structural generation, missing‑data handling
├── motif_analysis.py    # 3‑node enumeration, null models, z‑scores
├── correlation_analysis.py  # GLM, ridge, PCA, VIF, permutation, power
├── report_generator.py  # PDF creation (ReportLab + matplotlib)
├── utils.py             # logging, validation of constants, metadata JSON writer
└── main.py              # orchestration

tests/
├── unit/
│   ├── test_motif.py
│   └── test_correlation.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schemas.py

data/
├── raw/                 # placeholder (no required files for open dataset)
├── processed/
│   ├── <subj>/structural.npy
│   ├── <subj>/rsfc.npy
│   ├── <subj>/motif_profile.json
│   ├── <subj>/metadata.json          # conforms to structural_connectome.schema.yaml
│   └── manifest.json
├── logs/
│   └── pipeline.log
└── manifest.json        # cohort summary

results/
└── results.pdf
```

**Structure Decision**: Single‑project layout (Option 1) is optimal for a research pipeline; no separate services or front‑ends are required.

## Task List (8‑15 substantive tasks)
| ID | Task | Description | Deliverable | FR/SC |
|----|------|-------------|------------|-------|
| **T001** | Directory Setup | Create `code/`, `tests/`, `data/raw/`, `data/processed/`, `data/logs/`, `results/`, `state/` with placeholder `__init__.py` & `.gitkeep`. | Folder hierarchy | FR‑001, FR‑008 |
| **T002** | Data Ingestion & Validation | Programmatic OpenNeuro download for rs‑fMRI; generate synthetic structural adjacency if diffusion unavailable; write `manifest.json`; enforce SC‑001 (`actual ≥ 0.95*target`). | Processed `.npy` files + `manifest.json` | FR‑001, SC‑001 |
| **T003** | Linting Config | Add `.flake8` and `pyproject.toml` (Black settings) and configure pre‑commit hook. | `.flake8`, `pyproject.toml` | FR‑008 (code quality) |
| **T004** | Parcellation | Apply Schaefer‑100 atlas to synthetic/real diffusion data → binary undirected adjacency (`structural.npy`). | `structural.npy` per subject | FR‑002 |
| **T005** | Functional Calc | Compute Pearson correlation matrix from rs‑fMRI → `rsfc.npy`; threshold absolute correlations >0.2; calculate global efficiency on the weighted graph → `efficiency.csv`. | `rsfc.npy`, `efficiency.csv` | FR‑003 |
| **T006** | Motif Quant | Enumerate **13** undirected 3‑node motifs, generate ≥ 1000 degree‑preserving null graphs, compute z‑scores, enforce SC‑002 (≤ 300 s). | `motif_profile.json` per subject | FR‑004, SC‑002 |
| **T006b** | Secondary Null Model | Build null graphs preserving both degree sequence and global motif counts to test robustness. | `motif_sensitivity.json` | FR‑004 (robustness) |
| **T007** | Stats Analysis (Global) | Multivariate GLM (or ridge if VIF ≥ 5) – predictors: motif z‑scores + covariates; outcomes: rsFC strength & global efficiency; control: structural global degree; VIF diagnostics; Bonferroni; ≥ 1000 permutations; PCA when needed; power analysis (N = 50, α_adj, power = 0.80). | `correlation_results.json` | FR‑005, FR‑006, FR‑010, SC‑003, SC‑005 |
| **T007c** | Stats Analysis (Regional) | Correlate motif density within canonical networks (e.g., DMN) with local rsFC strength; Bonferroni across regions. | `regional_results.json` | FR‑005 (additional evidence) |
| **T008** | Reporting | Generate `results.pdf` with one page per motif: scatter plot, CI, partial Pearson **and** Spearman, raw & Bonferroni‑corrected p‑values, empirical p‑value, VIF, disclaimer string, power‑analysis section. | `results/results.pdf` | FR‑007, FR‑009, SC‑004 |
| **T009** | Data Model Documentation | Write `data-model.md` describing entities, relationships, file formats, and manifest schema. | `data-model.md` | FR‑008 |
| **T010** | Structural Metadata | For each subject, write `metadata.json` conforming to `structural_connectome.schema.yaml` (includes seed, file paths, status). | `metadata.json` per subject | FR‑008 |
| **T011** | Contract Tests | Implement schema validation tests using `jsonschema`; run in `tests/contract/`. | Test suite passes | FR‑008 |
| **T017** | Utils/Logging | Implement `utils.py` with global constants (`seed=42`, `bonferroni_alpha=0.0125`, `permutation_count=1000`, `vif_threshold=5`), logger setup (`pipeline.log`), validation of constants, and metadata JSON writer. | `utils.py`, `pipeline.log` | FR‑008, FR‑010 |

## Complexity Tracking
No principle violations detected; all tasks are necessary to satisfy the functional and success criteria without unnecessary bloat.

## Addressing Previously Rejected Tasks
- **T001** now explicitly creates the required directory hierarchy.  
- **T003** supplies concrete linting configuration files.  
- **T009** provides a complete `data-model.md`.  
- **T017** delivers a full `utils.py` implementation with constant validation and logging, and ensures `pipeline.log` exists.

---

