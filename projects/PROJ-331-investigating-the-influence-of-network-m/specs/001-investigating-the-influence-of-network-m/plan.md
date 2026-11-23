# Implementation Plan: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

**Branch**: `feature/motif-rsfc` | **Date**: 2026-10-22 | **Spec**: `specs/feature/motif-rsfc/spec.md`  
**Input**: Feature specification from `specs/feature/motif-rsfc/spec.md`

## Summary
Create a fully reproducible, CPU‑first pipeline that (1) streams the open HCP diffusion‑derived **pre‑computed streamlines** and resting‑state functional parquet files, (2) builds binary undirected structural connectomes using the Schaefer‑100 atlas from these streamlines (no raw DWI tractography required), (3) computes rsFC matrices after nuisance regression, (4) enumerates all subgraphs with a small number of nodes (including 4‑node subgraphs) (13 undirected classes total) with ≥ 1000 degree‑preserving null models and a 300 s timeout guard, (5) correlates motif z‑scores with rsFC strength and global efficiency using **partial Pearson and Spearman correlations**, **optionally** controlling for structural global node degree and any available covariates, applies Bonferroni correction across the **52 primary tests** (13 × 2 × 2), runs ≥ 1000 permutation tests, reports VIF and pairwise‑r diagnostics, and (6) generates a PDF report containing per‑motif visualisations, statistics, power‑analysis, and the mandatory disclaimer. All steps log to `pipeline.log`. No synthetic data are fabricated.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies** (pinned in `code/requirements.txt`): `numpy`, `scipy`, `pandas`, `networkx`, `matplotlib`, `statsmodels`, `reportlab`, `datasets`, `pyarrow`, `jsonschema`, `pytest`, `flake8`, `black`, `datalad`, `dipy`, `joblib`  
- **Storage**: Local filesystem under `data/` (raw, processed, logs) and `results/`  
- **Testing**: `pytest` (unit, integration, contract) + `flake8`/`black` linting (configured via `.flake8`, `pyproject.toml`, `.pre-commit-config.yaml`)  
- **Target Platform**: GitHub Actions free runner (2 CPU cores, ~7 GB RAM, ~14 GB disk, ≤6 h)  
- **Performance Goals**: Motif enumeration ≤ 300 s/subject, PDF generation ≤ 2 min and ≤ 5 MB, overall wall‑clock ≤ 4 h  
- **Constraints**: CPU‑first; all external URLs are verified open and programmatically accessible (see Dataset Strategy).  
- **Randomness**: Fixed seed = 42 for streamlines handling, null‑model generation, permutation tests, and any stochastic step.

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | ✅ | Fixed seeds, pinned `requirements.txt`, deterministic streaming download |
| II. Verified Accuracy | ✅ | All citations limited to the three verified HuggingFace URLs |
| III. Data Hygiene | ✅ | Raw parquet files checksummed; every transformation writes a new file with provenance metadata |
| IV. Single Source of Truth | ✅ | Each figure/statistic derives from a single row in `data/processed/` and a single code block |
| V. Versioning Discipline | ✅ | SHA‑256 content hashes of all derived artifacts are written to `state/projects/PROJ-331-investigating-the-influence-of-network-m.yaml` (Task T021) |
| VI. Structural Data Integrity | ✅ | Raw diffusion‑derived streamlines stored unchanged; derived binary connectomes saved with explicit provenance |
| VII. Statistical Transparency | ✅ | All statistical scripts record parameters, seeds, and library versions; diagnostics are logged and reported |

## FR/SC Traceability
| Requirement | Plan Element(s) |
|-------------|-----------------|
| FR‑001 | T002 – streaming download of diffusion‑derived streamlines and functional parquet, checksum, manifest |
| FR‑002 | T004 – apply Schaefer‑100 parcellation to **pre‑computed streamlines**, produce binary undirected adjacency (`structural.npy`) per subject; generate `structural_connectome.json` metadata (see Task T023) |
| FR‑003 | T005 – rsFC Pearson matrix (`rsfc.npy`) after **nuisance regression** (global signal & head‑motion), then compute mean strength & global efficiency |
| FR‑003 | T005b – aggregate per‑subject metrics (`subject_metrics.csv`) |
| FR‑004 | T006 – enumerate all 3‑node (4 classes) and Multi‑node (9 classes) motifs, generate ≥ 1000 Maslov–Sneppen null graphs (seed = 42). Compute z‑scores as `(N_obs − μ)/σ`. If σ = 0, set `z = 0`. Enforce **300 s timeout**; on timeout abort and fall back to **3‑node‑only** enumeration. Handle zero‑variance/disconnected graphs. |
| FR‑005 | T007 – partial Pearson & Spearman correlations between each motif and each functional metric (strength, global efficiency), **optionally** controlling for structural global degree and any available covariates, Bonferroni correction across **52 primary tests** (α ≈ 0.00096), VIF ≥ 5 warning, pairwise \|r\| ≥ 0.9 warning, ≥ 1000 permutation tests; write `correlation_results.json` |
| FR‑006 | T007 – permutation test ≥ 1000 shuffles (same step as above) |
| FR‑007 | T008 – `results.pdf` with one page per motif: scatter plot + 95 % CI, partial Pearson & Spearman r, raw p, Bonferroni‑corrected p, empirical permutation p, VIF warning, flagged predictor pairs, zero‑variance notes; include power‑analysis section and mandatory disclaimer |
| FR‑008 | T001 – directory hierarchy creation; T017 – structured `pipeline.log` |
| FR‑009 | T008 – disclaimer insertion and verification via PDF text search |
| FR‑010 | T010 – power‑analysis module (target = 0.80, α = 0.05/52); fallback for N < 30 with remedial suggestions |
| FR‑011 | T001 – create required folder hierarchy with placeholder READMEs |
| FR‑012 | T003 – linting configuration files (`.flake8`, `pyproject.toml`, `.pre-commit-config.yaml`) |
| FR‑013 | T009 – `specs/feature/motif-rsfc/data-model.md` |
| FR‑014 | T017 – `code/utils.py` with parameter validation, logging, timeout helper, disclaimer check |
| FR‑018 | T018 – generate `results.json` matching `contracts/results.schema.yaml` and validate via contract tests |
| FR‑019 | T022 – generate `analysis_results.json` conforming to `contracts/analysis_results.schema.yaml` and validate via contract tests |
| FR‑020 | T023 – validate `structural_connectome.json` against `contracts/structural_connectome.schema.yaml` |
| FR‑021 | T021 – compute SHA‑256 hashes of all derived artifacts and write them into `state/projects/PROJ-331-investigating-the-influence-of-network-m.yaml` (content hash map) |
| SC‑001 | T002 – manifest validation ensuring ≥ 95 % of target subjects processed |
| SC‑002 | T006 – wall‑clock guard aborts > 300 s, logs timeout warning, falls back to 3‑node‑only |
| SC‑003 | T007 – log contains p‑values for all 52 primary tests |
| SC‑004 | T008 – PDF generation timed ≤ 2 min, auto‑DPI reduction if size > 5 MB |
| SC‑005 | T010 – power‑analysis section present with minimum detectable r and Type II error statement |
| SC‑006 | T018 – results.json generation and contract validation |
| SC‑007 | T005b – `subject_metrics.csv` includes required columns |
| SC‑008 | T014 – contract schemas exercised by `tests/contract/test_schemas.py` |
| SC‑009 | T022 – analysis_results.json generation and validation |
| SC‑010 | T023 – structural_connectome.json validation |
| SC‑011 | T021 – content‑hash recording in project state YAML |

## Project Structure
```
specs/feature/motif-rsfc/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── analysis_results.schema.yaml
    ├── dataset.schema.yaml
    ├── motif_profile.schema.yaml
    ├── output.schema.yaml
    ├── results.schema.yaml
    └── structural_connectome.schema.yaml

code/
├── __init__.py
├── config.py                # constants, seed=42, paths
├── requirements.txt
├── data_loader.py           # streaming download, tractography (from pre‑computed streamlines), rsFC computation, parcellation
├── motif_analysis.py        # 3/4‑node counting, null model, timeout handling, parallelization
├── correlation_analysis.py # partial correlations, Bonferroni, permutation, VIF, power analysis
├── report_generator.py     # ReportLab PDF creation
├── utils.py                # logging, parameter validation, timeout helper, disclaimer check
└── main.py                 # orchestrates the pipeline

tests/
├── unit/
│   ├── test_motif.py
│   └── test_correlation.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schemas.py     # generic schema validation

data/
├── raw/            # streamed parquet shards (unchanged)
├── processed/
│   ├── <subject_id>/structural.npy
│   ├── <subject_id>/rsfc.npy
│   ├── <subject_id>/motif_profile.json
│   ├── <subject_id>/structural_connectome.json   # new metadata file
│   ├── subject_metrics.csv
│   ├── correlation_results.json
│   ├── results.json
│   ├── analysis_results.json
│   └── manifest.json
└── logs/
    └── pipeline.log

results/
└── results.pdf

state/
└── projects/PROJ-331-investigating-the-influence-of-network-m.yaml   # auto‑managed; stores content hashes
```

## Task List
| ID | Task | Deliverable | FR/SC |
|----|------|-------------|-------|
| T001 | Create required directory hierarchy (`code/`, `tests/`, `data/{raw,processed,logs}/`, `results/`, `state/`) and placeholder `README.md` files | Folder tree present in repo | FR‑001, FR‑008, FR‑011 |
| T002 | Stream‑download diffusion‑derived streamlines and rsFC parquet files for up to 50 subjects, compute SHA‑256 checksums, and write `manifest.json`. Log missing modalities and skip those subjects. | `data/raw/…`, `data/processed/manifest.json` | FR‑001, SC‑001 |
| T003 | Add linting configuration files: `.flake8`, `pyproject.toml` (Black settings), and a `.pre-commit-config.yaml` hook; ensure CI runs `flake8` and `black --check` | `.flake8`, `pyproject.toml`, `.pre-commit-config.yaml` | FR‑012 |
| T004 | Apply Schaefer‑100 parcellation to **pre‑computed streamlines**, produce binary undirected adjacency (`structural.npy`) per subject; generate accompanying `structural_connectome.json` metadata (see Task T023) | `data/processed/<sub>/structural.npy`, `structural_connectome.json` | FR‑002, FR‑004, T023 |
| T005 | Compute rsFC Pearson matrix (`rsfc.npy`) after **nuisance regression** (global signal & head‑motion), then compute mean strength & global efficiency (threshold |r| > 0.2). | `data/processed/<sub>/rsfc.npy` | FR‑003 |
| T005b | Aggregate per‑subject metrics (`subject_metrics.csv`) including mean rsFC strength, global efficiency, structural global degree, network density, and **optional covariates** (age, sex, head‑motion, scanner site). | `data/processed/subject_metrics.csv` | FR‑003, SC‑007 |
| T006 | Enumerate all 3‑node (4 classes) and 4‑node (9 classes) motifs, generate ≥ 1000 Maslov–Sneppen degree‑preserving random graphs (seed = 42). Compute z‑scores as `(N_obs − μ)/σ`. If σ = 0, set `z = 0`. Enforce **300 s timeout**; on timeout abort and fall back to **3‑node‑only** enumeration. Handle zero‑variance gracefully. | `data/processed/<sub>/motif_profile.json` | FR‑004, SC‑002 |
| T007 | Partial Pearson & Spearman correlations between each motif and each functional metric (strength, global efficiency), **optionally** controlling for structural global degree and any available covariates, Bonferroni correction across **52 primary tests** (α ≈ 0.00096), VIF ≥ 5 warning, pairwise \|r\| ≥ 0.9 warning, ≥ 1000 permutation tests; write `correlation_results.json` | `data/processed/correlation_results.json` | FR‑005, FR‑006, FR‑010, SC‑003, SC‑005 |
| T008 | Generate `results.pdf` with one page per motif: scatter plot + 95 % CI, partial Pearson & Spearman r, raw p, Bonferroni‑corrected p, empirical permutation p, VIF warning, flagged predictor pairs, zero‑variance notes; include power‑analysis section and mandatory disclaimer; auto‑reduce DPI if size > 5 MB. | `results/results.pdf` | FR‑007, FR‑009, SC‑004 |
| T009 | Write `specs/feature/motif-rsfc/data-model.md` defining entities and file formats | `data-model.md` | FR‑013 |
| T010 | Implement power‑analysis module (target = 0.80, α = 0.05/52), fallback for N < 30 with remedial suggestions | Section in `correlation_results.json` and PDF | FR‑010 |
| T011 | Implement `code/utils.py` containing (a) parameter validation (seed, Bonferroni α, permutation count ≥ 1000, VIF threshold = 5), (b) structured logger writing JSON lines to `pipeline.log`, (c) timeout helper for motif enumeration, (d) post‑run verification that disclaimer string exists in PDF | `utils.py`, `pipeline.log` | FR‑014, FR‑008 |
| T012 | Add placeholder `README.md` files in each top‑level folder (`code/`, `tests/`, `data/`, `results/`, `state/`) to satisfy FR‑011 | README files | FR‑011 |
| T013 | Generate `results.json` matching `contracts/results.schema.yaml` and validate via contract tests | `data/processed/results.json` | SC‑006 |
| T014 | Run the full pipeline on a fresh GitHub Actions runner, confirm that all acceptance criteria (SC‑001…SC‑005) are met; iterate if any fail | CI‑validated run | All FR/SC |
| T018 | Generate `results.json` (machine‑readable summary) and run validation against `contracts/results.schema.yaml` | `results.json` | SC‑006 |
| T022 | Generate `analysis_results.json` conforming to `contracts/analysis_results.schema.yaml` and validate via contract tests | `analysis_results.json` | SC‑009 |
| T023 | Validate `structural_connectome.json` against `contracts/structural_connectome.schema.yaml` | validation pass | SC‑010 |
| T021 | Compute SHA‑256 hashes of all derived artifacts and write them into `state/projects/PROJ-331-investigating-the-influence-of-network-m.yaml` (content hash map) | state YAML updated | Constitution Principle V |
| T020 | (Existing) generate `results.json` matching `contracts/results.schema.yaml` and validate via contract tests | `results.json` | SC‑006 |

## Complexity Tracking
All constitution principles are satisfied; no violations remain. Every FR and SC is covered by a concrete task. The plan respects the compute budget, uses only verified open datasets, and introduces no un‑specified constraints.
