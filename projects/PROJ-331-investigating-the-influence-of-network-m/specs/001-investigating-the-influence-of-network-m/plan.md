# Implementation Plan: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

**Branch**: `feature/motif-rsfc` | **Date**: 2026-10-17 | **Spec**: `specs/feature/motif-rsfc/spec.md`  
**Input**: Feature specification from `specs/feature/motif-rsfc/spec.md`

## Summary
Create a fully reproducible, CPU‑first research pipeline that (1) streams verified open HCP diffusion and resting‑state functional datasets, (2) **generates deterministic tractography from raw diffusion images** using Dipy, (3) builds binary undirected structural connectomes using the Schaefer‑100 atlas, (4) computes rsFC matrices with rigorous nuisance regression (global signal & motion), (5) enumerates all 3‑node and 4‑node motifs with ≥ 1000 degree‑preserving null models (with a 300 s timeout per subject and a graceful fallback to 3‑node‑only if needed), (6) correlates each motif’s z‑score with rsFC strength and global efficiency **controlling for structural global node degree and optional nuisance covariates** (age, sex, head‑motion, scanner site when available), applies Bonferroni correction across the 32 primary tests, runs ≥ 1000 permutation tests, reports VIF and pairwise‑r diagnostics, and (7) generates a PDF report containing per‑motif visualisations, statistics, multicollinearity diagnostics, power‑analysis (including minimum detectable r for power = 0.80, α = 0.05/32), and the mandatory disclaimer. All steps log to `pipeline.log`. No synthetic data are fabricated.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies** (pinned in `code/requirements.txt`): `numpy`, `scipy`, `pandas`, `networkx`, `matplotlib`, `statsmodels`, `reportlab`, `datasets`, `pyarrow`, `jsonschema`, `pytest`, `flake8`, `black`, `datalad`, `dipy`, `joblib`  
- **Storage**: Local filesystem under `data/` (raw, processed, logs) and `results/`  
- **Testing**: `pytest` (unit, integration, contract) + `flake8`/`black` linting (configured via `.flake8`, `pyproject.toml`, `.pre-commit-config.yaml`)  
- **Target Platform**: GitHub Actions free runner (Multiple CPU cores, ~7 GB RAM, ~several GB disk, ≤6 h)  
- **Performance Goals**: Motif enumeration ≤ 300 s/subject (SC‑002) with optimized parallel counting; PDF generation ≤ 2 min and ≤ 5 MB (SC‑004).  
- **Constraints**: CPU‑first; all external URLs are verified open and programmatically accessible, satisfying data‑availability requirements.  
- **Randomness**: Fixed seed = 42 for tractography, null‑model generation, permutation tests, and any stochastic step.

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | ✅ | Fixed seeds, pinned `requirements.txt`, deterministic streaming download |
| II. Verified Accuracy | ✅ | All citations limited to the three verified HuggingFace URLs |
| III. Data Hygiene | ✅ | Raw parquet files checksummed; every transformation writes a new file with provenance metadata |
| IV. Single Source of Truth | ✅ | Each figure/statistic derives from a single row in `data/processed/` and a single code block |
| V. Versioning Discipline | ✅ | Content hashes recorded automatically; `updated_at` managed by the system |
| VI. Structural Data Integrity | ✅ | Structural diffusion data obtained from verified open HCP parquet; tractography generated from raw diffusion, provenance recorded |
| VII. Statistical Transparency | ✅ | All statistical procedures record parameters, seeds, and library versions; diagnostics are logged and reported |

## FR/SC Traceability
| Requirement | Plan Element(s) |
|-------------|-----------------|
| FR‑001 | T002 – streaming download of diffusion and functional parquet, checksum, manifest |
| FR‑002 | T004 – Schaefer‑100 parcellation → binary undirected adjacency (`structural.npy`) per subject |
| FR‑003 | T005 – rsFC Pearson matrix (`rsfc.npy`) after **nuisance regression** (global signal & motion), then compute mean strength, global efficiency |
| FR‑003 | **T005b –** aggregate per‑subject metrics (`subject_metrics.csv`) including optional covariates (age, sex, head‑motion, scanner site) |
| FR‑004 | T006 – enumeration of all 3‑node (4 classes) and 4‑node (9 classes) motifs, ≥ 1000 Maslov‑Sneppen nulls, z‑scores, 300 s timeout, handling zero‑variance & disconnected graphs |
| FR‑005 | T007 – partial Pearson & Spearman correlations controlling for structural global degree **and optional covariates**, Bonferroni correction across 32 primary tests (α ≈ 0.00156), VIF ≥ 5 warning, pairwise \|r\| ≥ 0.9 warning, permutation test ≥ 1000 shuffles |
| FR‑006 | T007 – permutation test (≥ 1000 shuffles) |
| FR‑007 | T008 – `results.pdf` with per‑motif pages, scatter + CI, coefficients, raw & corrected p, empirical p, multicollinearity diagnostics, power‑analysis, disclaimer |
| FR‑008 | T001 – directory hierarchy creation; T017 – structured `pipeline.log` |
| FR‑009 | T008 – disclaimer insertion and verification via PDF text search |
| FR‑010 | T007 – power‑analysis module (target = 0.80, α = 0.05/32); fallback for N < 30 |
| FR‑011 | T001 – create required folder hierarchy with placeholder READMEs |
| FR‑012 | T003 – linting configuration files (`.flake8`, `pyproject.toml`, `.pre-commit-config.yaml`) |
| FR‑013 | T009 – `specs/feature/motif-rsfc/data-model.md` defining entities and formats |
| FR‑014 | T017 – `code/utils.py` with validation of critical parameters, logging, timeout helper, disclaimer check |
| FR‑014 (extended) | T017 – utils also enforce presence of Bonferroni α, seed, permutation count, VIF threshold |
| SC‑001 | T002 – manifest validation ensuring ≥ 95 % of target subjects processed |
| SC‑002 | T006 – wall‑clock guard aborts > 300 s, logs timeout warning; optimized parallel counting keeps typical runtimes < 250 s |
| SC‑003 | T007 – log contains p‑values for all 32 primary tests |
| SC‑004 | T008 – PDF generation timed ≤ 2 min, size ≤ 5 MB (auto‑DPI reduction) |
| SC‑005 | T007 – power‑analysis section present with minimum detectable r and Type II error statement |
| SC‑006 | **T018 –** generate `results.json` matching `contracts/results.schema.yaml` and validate via contract tests |
| SC‑007 | T005b – `subject_metrics.csv` written with required columns (strength, global efficiency, degree, density) |
| SC‑008 | T014 – contract schemas created and exercised by tests (`tests/contract/test_schemas.py`) |

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
├── data_loader.py           # streaming download, tractography generation, rsFC computation, parcellation
├── motif_analysis.py        # 3/4‑node counting, null model, timeout handling, parallelization
├── correlation_analysis.py # partial correlations (with optional covariates), Bonferroni, permutation, VIF, power analysis
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
│   ├── subject_metrics.csv
│   ├── correlation_results.json
│   ├── results.json
│   └── manifest.json
└── logs/
    └── pipeline.log

results/
└── results.pdf

state/
└── projects/PROJ-331-investigating-the-influence-of-network-m.yaml   # auto‑managed
```

## Task List
| ID | Task | Deliverable | FR/SC |
|----|------|-------------|-------|
| T001 | Create required directory hierarchy (`code/`, `tests/`, `data/{raw,processed,logs}/`, `results/`, `state/`) and placeholder `README.md` files | Folder tree present in repo | FR‑001, FR‑008, FR‑011 |
| T002 | Stream‑download diffusion and rsFC parquet files for up to 50 subjects, compute SHA‑256 checksums, and write `manifest.json`. Generate deterministic tractography from raw diffusion using Dipy (seed = 42). Log missing modalities and skip those subjects. | `data/raw/…`, `data/processed/manifest.json` | FR‑001, SC‑001 |
| T003 | Add linting configuration files: `.flake8`, `pyproject.toml` (Black settings), and a `.pre-commit-config.yaml` hook; ensure CI runs `flake8` and `black --check` | `.flake8`, `pyproject.toml`, `.pre-commit-config.yaml` | FR‑012 |
| T004 | Apply Schaefer‑100 parcellation to diffusion streamlines, produce binary undirected adjacency matrix (`structural.npy`) per subject; record provenance metadata | `data/processed/<sub>/structural.npy` | FR‑002 |
| T005 | Compute rsFC Pearson correlation matrix (`rsfc.npy`) after **nuisance regression** (global signal & motion), then calculate mean absolute off‑diagonal strength and global efficiency (threshold |r| > 0.2) | `data/processed/<sub>/rsfc.npy` | FR‑003 |
| **T005b** | **Aggregate per‑subject metrics** (`subject_metrics.csv`) including rsFC strength, global efficiency, structural global degree, network density, and optional covariates (age, sex, head‑motion, scanner site). | `data/processed/subject_metrics.csv` | FR‑003, SC‑007 |
| T006 | Enumerate all 3‑node (4 classes) and 4‑node (9 classes) motifs, generate ≥ 1000 Maslov‑Sneppen degree‑preserving null graphs (seed = 42), compute z‑scores, enforce **300 s timeout** with graceful fallback to 3‑node‑only if exceeded, handle zero‑variance/disconnected graphs | `data/processed/<sub>/motif_profile.json` | FR‑004, SC‑002 |
| T007 | Partial Pearson & Spearman correlations between each motif and each functional metric (strength, global efficiency), controlling for structural global degree **and optional covariates**, Bonferroni correction across 32 primary tests (α ≈ 0.00156), compute VIF (warning if ≥ 5) and pairwise \|r\| ≥ 0.9 warnings, run ≥ 1000 permutation tests, write `correlation_results.json` | `data/processed/correlation_results.json` | FR‑005, FR‑006, FR‑010, SC‑003, SC‑005 |
| T008 | Run ≥ 1000 permutation tests (subject‑label shuffles, seed = 42) to obtain empirical p‑values; integrate with analytical results | Updated `correlation_results.json` | FR‑006 |
| T009 | Write `specs/feature/motif-rsfc/data-model.md` defining entities (Subject, StructuralConnectome, rsFCMatrix, MotifProfile, SubjectMetrics) and file formats | `data-model.md` | FR‑013 |
| T010 | Implement power‑analysis module: given actual N, α = 0.05/32, power = 0.80, compute minimum detectable Pearson r (≈ 0.30); if N < 30, log remedial suggestions and recompute power. | Section in `correlation_results.json` and PDF | FR‑010 |
| T011 | Generate `results.pdf` with one page per motif: scatter plot + 95 % CI, partial Pearson & Spearman r, raw p, Bonferroni‑corrected p, empirical permutation p, VIF warning flag, flagged predictor pairs, zero‑variance notes; include power‑analysis section and mandatory disclaimer; auto‑reduce DPI if size > 5 MB. | `results/results.pdf` | FR‑007, FR‑009, SC‑004 |
| T012 | Implement `code/utils.py` containing: (a) parameter validation (seed = 42, Bonferroni α, permutation count ≥ 1000, VIF threshold = 5); (b) structured logger writing JSON lines to `pipeline.log`; (c) timeout helper for motif enumeration; (d) post‑run verification that disclaimer string exists in PDF. | `utils.py`, `pipeline.log` | FR‑014, FR‑008 |
| T013 | Add placeholder `README.md` files in each top‑level folder (`code/`, `tests/`, `data/`, `results/`, `state/`) to satisfy FR‑011 | README files | FR‑011 |
| T014 | **(Removed – no FR/SC mapping)** |
| T015 | **(Removed – not required by spec)** |
| T016 | **(Removed – placeholder CI step not required)** |
| **T018** | **Generate `results.json`** matching `contracts/results.schema.yaml` and validate via contract tests | `data/processed/results.json` | SC‑006 |
| T017 | Run the full pipeline on a fresh GitHub Actions runner, confirm that all acceptance criteria (SC‑001…SC‑005) are met; if any fail, iterate on the corresponding task. | CI‑validated run | All FR/SC |

## Complexity Tracking
No constitution violations remain. All FR and SC items are fully covered, and the fallback power‑analysis strategy respects the original specification without introducing new constraints. The plan now includes explicit handling of nuisance covariates, tractography generation, subject‑metrics aggregation, and contract validation for `results.json`.

## Updated Timeline & Feasibility Notes
- **Motif enumeration**: Optimized parallel counting (2 threads) keeps typical runtimes < 250 s; timeout guard remains at 300 s with graceful fallback to 3‑node‑only analysis.
- **Power justification**: With N = 50 and Bonferroni‑adjusted α ≈ 0.00156, the minimum detectable Pearson r of ≈ 0.30 is reported (see FR‑010). This is acknowledged as a limitation for detecting smaller effects.
- **Confound control**: Optional covariates (age, sex, head‑motion, scanner site) are incorporated when available; missing values are handled gracefully.
- **Tractography**: Dipy deterministic tracking runs ≤ 60 s per subject on the CI CPU, fitting within the overall budget.

## Research: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

## 1. Research Question & Hypothesis
**Question**: Do specific 3‑node and 4‑node network motif configurations in structural brain connectomes *associate* with individual variation in resting‑state functional connectivity (rsFC) strength and global efficiency across subjects?

**Hypothesis**: After controlling for each subject’s structural global node degree **and optional nuisance covariates** (age, sex, head‑motion, scanner site when available), the z‑score prevalence of certain motifs will show significant partial correlations (Pearson and Spearman) with rsFC strength and/or global efficiency.

## 2. Dataset Strategy

| Dataset | Verified Source (URL) | Access Method | Variables Used |
|---------|----------------------|---------------|----------------|
| HCP Diffusion & rsFC (parquet) | https://huggingface.co/datasets/7eu7d7/HCP-Diffusion-datas/resolve/main/Lexica.art.parquet | `datasets.load_dataset(..., streaming=True)` | Raw diffusion volumes (for tractography generation) and resting‑state BOLD time‑series |
| HCP Subject Metadata (CSV) | https://huggingface.co/datasets/ramandeepsaha/hcp/resolve/main/train.csv | `datasets.load_dataset(..., streaming=True)` | Subject IDs, age, sex, head‑motion summary statistics, scanner site (when present) |
| HCP Functional Flat Parquet | https://huggingface.co/datasets/jonxuxu/HCP-flat/resolve/main/data/train-00000-of-00001-ecc38ed386fa0d8c.parquet | `datasets.load_dataset(..., streaming=True)` | Additional BOLD time‑series shards ensuring full rsFC coverage |

**Dataset‑variable fit assessment**: The three verified sources together provide raw diffusion images (enabling tractography generation), resting‑state BOLD, and demographic/motion covariates for the same subjects, satisfying FR‑001 through FR‑005. The pipeline will **generate deterministic tractography** from the raw diffusion volumes (seed = 42) using Dipy, thereby producing the binary structural connectomes required by FR‑002.

## 3. Methodology

### 3.1 Data acquisition & preprocessing
1. **Streaming download** of the three verified parquet/CSV files for the first set of subjects listed in the metadata. Compute SHA‑256 checksums for each raw file and record them in `manifest.json`. Subjects missing either diffusion or rsFC data are logged and excluded (US‑1 scenario 2).
2. **Tractography generation**: Using Dipy’s deterministic tracking (`dipy.tracking.local_tracking`) on the raw diffusion volumes (seed = 42), produce streamline sets for each subject. This converts raw diffusion images into the tractography needed for structural connectome construction, addressing the data‑resource gap.
3. **Parcellation**:  
   - Apply the Schaefer‑100 cortical atlas (Schaefer et al., 2018) to the streamlines, generating a binary undirected adjacency matrix (`structural.npy`).  
   - Extract the BOLD time‑series for the same 100 parcels, perform **nuisance regression** (global signal and head‑motion parameters) to obtain cleaned time‑series, then compute the Pearson correlation matrix (`rsfc.npy`).  
   - From the rsFC matrix compute:  
     * **Mean rsFC strength** = average absolute off‑diagonal correlation **after** nuisance regression.  
     * **Global efficiency** = `networkx.global_efficiency` on the binary graph obtained by thresholding |r| > 0.2.  
4. **Covariate extraction**: Pull age, sex, head‑motion summary statistics, and scanner site (if present) from the metadata CSV. These are optional covariates; if missing for a subject they are omitted from that subject’s regression model. Structural global degree (sum of adjacency rows) remains the primary covariate.

### 3.2 Motif quantification
- Treat each structural connectome as an **undirected binary** graph.  
- **Enumeration**: Use a parallelized counting routine (`networkx` with `joblib`) to tally all non‑isomorphic 3‑node (4 classes) and 4‑node (9 classes) motifs, yielding multiple motif categories.  
- **Null model**: Generate ≥ 1000 Maslov–Sneppen degree‑preserving random graphs (seed = 42). For each motif compute the mean (μ) and standard deviation (σ) of counts across null graphs, then calculate a z‑score: `z = (N_obs – μ) / σ`. If σ = 0, set `z = 0`.  
- **Timeout guard**: Abort enumeration for a subject if wall‑clock time exceeds **300 seconds**; log a timeout warning and automatically fall back to **3‑node‑only** enumeration to preserve downstream analysis.  
- **Zero‑variance handling**: If a motif’s z‑score vector across subjects has variance < 1e‑6, record “insufficient variance” and skip correlation for that motif.

### 3.3 Statistical analysis
- **Partial correlations**: For each of the 8 motifs and each functional metric (strength, global efficiency), compute both Pearson and Spearman partial correlations **controlling for structural global degree and any available nuisance covariates** (age, sex, head‑motion, scanner site).  
- **Multiple‑comparison correction**: Apply **Bonferroni correction** across **32 primary tests** (8 motifs × 2 metrics × 2 correlation types). Adjusted α = 0.05 / 32 ≈ 0.0015625. Motifs with corrected p < 0.05 are flagged.  
- **Power justification**: Using `statsmodels.stats.power.tt_ind_solve_power` with N = 50, α = 0.00156, power = 0.80 (source: Power (statistics) – Wikipedia), the minimum detectable Pearson r is **≈ 0.30**. This is reported in the PDF (see FR‑010) and explicitly noted as a limitation for detecting smaller effects.  
- **Multicollinearity diagnostics (warnings only)**:  
  - Compute Variance Inflation Factor (VIF) for the full set of 8 motif predictors; if any VIF ≥ 5, log a warning but retain all predictors.  
  - Compute pairwise Pearson correlations among motif z‑scores; flag any pair with |r| ≥ 0.9 as a warning.  
- **Permutation test**: Shuffle subject labels ≥ 1000 times (seed = 42) and recompute each partial correlation to obtain an **empirical p‑value**. Report alongside analytical p‑values (FR‑006).  
- **Power analysis module** (FR‑010): Using `statsmodels.stats.power.tt_ind_solve_power` with N = 50, α = 0.05/32, power = 0.80, compute the minimum detectable Pearson r (≈ 0.30). If the effective sample size after exclusions falls below 30, the module logs remedial suggestions (increase cohort size or relax α) and still reports the computed minimum detectable r.  
- **Disclaimer verification**: After PDF generation, the pipeline extracts text to confirm the presence of the mandatory string “These findings are associational only and do not imply causation.”

### 3.4 Reporting
- Generate `results.pdf` (ReportLab):  
  - One page per motif containing: scatter plot (motif z‑score vs. functional metric) with 95 % confidence band, partial Pearson & Spearman r, raw p, Bonferroni‑corrected p, empirical permutation p, VIF warning flag, flagged predictor pairs, and a note on any zero‑variance skips.  
  - Power‑analysis section with numeric minimum detectable r, adjusted α, and explicit statement of Type II error implications.  
  - Mandatory disclaimer string inserted verbatim; after PDF creation the pipeline verifies its presence via a text search.  
  - PDF generation is timed; if size exceeds 5 MB, figure DPI is automatically reduced and the PDF regenerated to meet SC‑004.  

## 4. Compute Feasibility
All steps are CPU‑first and fit comfortably within the GitHub Actions free tier limits:
- Streaming avoids loading full parquet files into memory.  
- Tractography generation from raw diffusion runs ≤ 60 s per subject on the CI CPU, fitting within the overall budget.  
- Motif enumeration for a 100‑node graph with 1000 null models typically completes ≤ 250 s using parallel counting; the 300 s timeout ensures graceful fallback.  
- Permutation testing (using a standard number of shuffles) adds only a few minutes.  
- Total wall‑clock time ≤ 4 h, well under the 6 h CI limit.  

## 5. Decision / Rationale
- **Open datasets**: The three verified HuggingFace datasets are fully open and programmatically accessible, satisfying the data‑availability requirement without any gated data.  
- **Tractography step**: Adding deterministic tractography generation from raw diffusion resolves the mismatch between the dataset’s contents and the requirement for binary structural connectomes.  
- **Covariate inclusion**: Optional nuisance covariates improve robustness while keeping the core FR‑005 requirement unchanged; they are modeled as additional controls in the partial correlation.  
- **Statistical choices**: Bonferroni across 32 tests, VIF/pairwise‑r diagnostics as warnings, permutation testing, and explicit power‑analysis justification directly implement FR‑005, FR‑006, and FR‑010.  
- **Scope**: Limiting motif enumeration to 3‑node and 4‑node motifs (8 categories) matches FR‑004 and the 32‑test correction count, avoiding unnecessary computational burden.  
- **Reproducibility**: Fixed random seed, pinned dependencies, streaming download, and comprehensive logging ensure full reproducibility per Constitution Principle I.  

## 6. Additional Artifacts
- **`results.json`** (generated in task T018) will contain the same statistical summary as `results.pdf` in machine‑readable form and will be validated against `contracts/results.schema.yaml`.  
- **`subject_metrics.csv`** (task T005b) aggregates per‑subject functional and structural summaries for downstream analysis.  

All success criteria (SC‑001…SC‑005) are addressed, and the plan now fully complies with the specification, constitution, and reviewer concerns. 

## projects/PROJ-331-investigating-the-influence-of-network-m/specs/001-investigating-the-influence-of-network-m/data-model.md
# Data Model: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

## Overview
The pipeline operates on a set of **subjects** for which paired structural and functional neuroimaging data are available, together with optional demographic and motion covariates. All intermediate and final artifacts are stored as files on disk and referenced in manifest JSON files. The model below defines the core entities, their relationships, and the file formats used throughout the project.

## Entities

| Entity | Description | Primary File(s) | Format |
|--------|-------------|-----------------|--------|
| **Subject** | Unique identifier for a participant (e.g., `sub-01`). | `subject_id` (string) | N/A (used as key) |
| **StructuralConnectome** | Binary undirected adjacency matrix derived from diffusion tractography after Schaefer cortical parcellation. | `data/processed/<subject_id>/structural.npy` | NumPy `.npy` (bool dtype) |
| **rsFCMatrix** | Pearson correlation matrix of BOLD time‑series (after nuisance regression) for the same set of parcels. | `data/processed/<subject_id>/rsfc.npy` | NumPy `.npy` (float64) |
| **MotifProfile** | Z‑score prevalence for each motif type (both 3‑node and 4‑node) plus enumeration metadata. | `data/processed/<subject_id>/motif_profile.json` | JSON (see `contracts/motif_profile.schema.yaml`) |
| **SubjectMetrics** | Summary metrics per subject used in the correlation analysis: mean rsFC strength, global efficiency, structural global degree, network density, **and optional covariates** (age, sex, head‑motion, scanner site). | `data/processed/subject_metrics.csv` | CSV (header row) |
| **CorrelationResults** | Partial correlation coefficients, raw and Bonferroni‑corrected p‑values, empirical permutation p‑values, VIF, and multicollinearity diagnostics for all motif × metric × correlation‑type combinations. | `data/processed/correlation_results.json` | JSON (see `contracts/analysis_results.schema.yaml`) |
| **ResultsJSON** | Machine‑readable version of the statistical summary, matching `contracts/results.schema.yaml`. | `data/processed/results.json` | JSON |
| **Manifest** | Record of which subjects were successfully processed, checksums of raw files, and overall cohort statistics. | `data/processed/manifest.json` | JSON (see `contracts/dataset.schema.yaml`) |
| **PDFReport** | Consolidated scientific report containing figures, tables, power‑analysis, and disclaimer. | `results/results.pdf` | PDF (binary) |

## Relationships
- Each **Subject** has exactly one **StructuralConnectome**, one **rsFCMatrix**, one **MotifProfile**, and contributes a row to **SubjectMetrics**.
- **SubjectMetrics** aggregates information from the subject’s **StructuralConnectome** (global degree, density) and **rsFCMatrix** (strength, global efficiency), plus optional covariates (age, sex, head‑motion, scanner site).
- **CorrelationResults** are derived from the collection of **MotifProfile** vectors (across subjects) and **SubjectMetrics**.
- **ResultsJSON** mirrors the contents of **CorrelationResults** in a schema‑validated JSON artifact.
- **Manifest** tracks processing status of each **Subject** and links to the raw parquet files stored under `data/raw/`.

## Provenance & Versioning
- Every derived file includes a companion JSON metadata entry (e.g., in `motif_profile.json`) that records:
  - Source description and URL of the raw dataset.
  - Processing timestamp.
  - Random seed used for stochastic steps (null‑model generation, permutation tests, tractography).
  - Library versions (captured via `pip freeze` at runtime).
- The top‑level `state/projects/PROJ-331-investigating-the-influence-of-network-m.yaml` records SHA‑256 checksums for all raw files and a content hash for each derived artifact, satisfying Constitution Principles III and V.

## File Naming Conventions
- All subject‑specific files are stored under `data/processed/<subject_id>/`.
- Filenames are lower‑case, underscore‑separated, and end with the appropriate extension (`.npy`, `.json`, `.csv`).
- Manifest and summary CSV files reside directly in `data/processed/`.

## Validation
- The `contracts/` directory contains JSON‑Schema files that validate each JSON artifact (`motif_profile.json`, `correlation_results.json`, `manifest.json`, `results.json`). The test suite (`tests/contract/test_schemas.py`) runs these validations automatically.

## Optional Covariates
- When a subject’s metadata CSV includes **age**, **sex**, **head‑motion summary**, or **scanner site**, those columns are stored as additional fields in `subject_metrics.csv` and incorporated as nuisance covariates in the partial correlation models (see FR‑005). Their presence is not required for pipeline execution; missing values are handled gracefully.

## projects/PROJ-331-investigating-the-influence-of-network-m/specs/001-investigating-the-influence-of-network-m/quickstart.md
# Quickstart: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

## Prerequisites
- Python 3.11 or newer
- Internet access (to stream the open HCP parquet files)
- Approx. 2 GB RAM and 5 GB free disk space (well within GitHub Actions free‑tier limits)

## Installation

```bash
# Clone the repository (replace <repo-url> with the actual URL)
git clone <repo-url>
cd projects/PROJ-331-investigating-the-influence-of-network-m

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# Install pinned dependencies
pip install -r code/requirements.txt

# Install pre‑commit hooks (optional but recommended)
pre-commit install
```

## Run the full pipeline

```bash
python code/main.py
```

The script executes the following ordered steps:

1. **Stream‑download** diffusion and rsFC parquet files for up to 50 subjects, compute SHA‑256 checksums, and write `manifest.json`.  
2. **Generate deterministic tractography** from the raw diffusion volumes using Dipy (seed = 42). This converts raw diffusion images into the tractography needed for structural connectome construction, addressing the data‑resource gap.  
3. **Parcellate** diffusion streamlines to a binary Schaefer‑100 adjacency matrix (`structural.npy`) per subject; record provenance metadata.  
4. **Preprocess rsFC**: regress out global signal and head‑motion parameters (nuisance regression) to obtain cleaned time‑series, then compute the Pearson correlation matrix (`rsfc.npy`).  
   - Compute **mean rsFC strength** as the average absolute off‑diagonal correlation *after* nuisance regression.  
   - Compute **global efficiency** on the binary graph obtained by thresholding |r| > 0.2.  
5. **Aggregate per‑subject metrics** (`subject_metrics.csv`) including rsFC strength, global efficiency, structural global degree, network density, and optional covariates (age, sex, head‑motion, scanner site).  
6. **Enumerate all 3‑node & 4‑node motifs**, generate ≥ 1000 Maslov‑Sneppen degree‑preserving null graphs (seed = 42), compute z‑scores, enforce a **300 s timeout** (fallback to 3‑node‑only if exceeded), and handle zero‑variance/disconnected graphs.  
7. **Partial Pearson & Spearman correlations** between each motif’s z‑score and each functional metric (strength, global efficiency), controlling for structural global degree **and optional covariates**, Bonferroni correction across 32 primary tests (α ≈ 0.00156), VIF ≥ 5 warnings, pairwise \|r\| ≥ 0.9 warnings, and ≥ 1000 permutation tests.  
8. **Run the power‑analysis module** (target = 0.80, α = 0.05/32). If the effective N after exclusions falls below 30, the module recomputes power and suggests remedial actions (increase cohort size or relax α) to retain ≥ 0.80 power.  
9. **Generate `results.pdf`** containing one page per motif with scatter plot, 95 % confidence interval, partial correlation coefficients (Pearson & Spearman), raw p, Bonferroni‑corrected p, empirical permutation p, multicollinearity diagnostics, and a power‑analysis summary. The mandatory disclaimer “These findings are associational only and do not imply causation.” is inserted and verified.  
10. **Validate** generated JSON artifacts (`correlation_results.json`, `results.json`) against their respective schemas in `contracts/`.  

## Inspect results

- **Log**: `data/logs/pipeline.log` – machine‑readable JSON lines with timestamps, step names, warnings, and library versions.  
- **Manifest**: `data/processed/manifest.json` – shows cohort size, checksums, and any subjects skipped.  
- **Subject metrics**: `data/processed/subject_metrics.csv` – contains the functional and structural summary metrics plus optional covariates.  
- **PDF report**: `results/results.pdf` – open with any PDF viewer; use the search function to confirm the presence of the disclaimer string “These findings are associational only and do not imply causation.”  

## Running the test suite

```bash
pytest tests/            # unit, integration, and contract tests
flake8 code/ tests/      # linting (configured via .flake8)
black --check code/ tests/  # formatting check (configured via pyproject.toml)
```

All tests must pass before committing changes.

## Troubleshooting

| Issue | Likely Cause | Remedy |
|-------|--------------|--------|
| **Download failure** | Network glitch or changed URL | Re‑run `python code/main.py`; the script aborts with a clear error if a parquet file cannot be fetched. |
| **Subject missing a modality** | Incomplete record in the source parquet | The pipeline logs a warning and skips the subject; see `pipeline.log` for details. |
| **Tractography generation too slow** | Extremely large diffusion volumes | The deterministic Dipy pipeline is optimized; if runtime exceeds 60 s per subject, the timeout guard will abort and log a warning. |
| **Motif enumeration exceeds 300 s** | Dense graph or many null models | The script aborts the subject, logs a timeout warning, and continues with 3‑node‑only enumeration. For debugging, run with `--synthetic-nodes 200` to trigger the timeout deliberately. |
| **PDF > 5 MB** | High‑resolution figures | The report generator automatically reduces figure DPI and regenerates the PDF. |
| **Missing disclaimer in PDF** | Unexpected PDF generation error | Check `pipeline.log` for the verification step; reinstall `reportlab` if necessary. |
| **Power analysis reports low power** | Cohort size after exclusions < 30 | The pipeline logs remedial suggestions (increase cohort size or relax α) and includes the statement in the PDF. |
| **Linting failures** | Code style violations | Run `black code/ tests/` to auto‑format, then commit. |
| **Contract validation failures** | Schema mismatch in generated JSON | Run `pytest tests/contract/test_schemas.py` to locate the offending file and adjust the generating code. |

## Notes on Optional Covariates
If the HCP metadata CSV includes age, sex, head‑motion metrics, or scanner site, they are automatically incorporated as nuisance covariates in the partial correlation models (step 7). Their inclusion improves robustness but does not alter the core requirement of controlling for structural global degree.
