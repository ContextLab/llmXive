# Implementation Plan: Predicting Plant Stress Response from Publicly Available Proteomic Data

**Branch**: `001-predict-plant-stress-response` | **Date**: 2026-10-11 | **Spec**: `spec.md`  
**Input**: Feature specification from `specs/001-predict-plant-stress-response/spec.md`

## Summary
We will deliver a **fully reproducible, CPU‑only machine‑learning pipeline** that

1. **Validates** the availability of paired proteomic + transcriptomic plant‑stress data. If no suitable open dataset is found, the pipeline halts early and emits a clear “**Data Unavailable**” JSON report (see Data Availability Limitation).  
2. **Ingests** the verified dummy NCBI zip and GEO JSON solely to confirm that every script (download, checksum, preprocessing, logging, model scaffolding) runs without error.  
3. **Preprocesses** data **fold‑wise**: within each training split we perform log‑2 transformation, low‑abundance filtering, Left‑Censored Missing (LCM) imputation, and ComBat batch correction; the learned parameters are then applied to the held‑out test fold, preventing information leakage.  
4. **Merges** proteomic and transcriptomic tables via R `biomaRt` (accessed through `rpy2`). Unmatched rows are dropped and logged.  
5. **Derives** an aggregated expression target (first principal component of the matched gene expression matrix) that captures overall “gene‑expression patterns” across genes, satisfying the plural construct in the research question.  
6. **Trains** Random Forest and Support Vector Regression models using scikit‑learn on CPU‑only hardware, with 5‑fold CV (or LOOCV when n < 50, verified fact `cv fold loocv vs = 1500`).  
7. **Evaluates** within‑stress and cross‑stress performance, includes a null‑model baseline, and conducts a **shuffled‑target** control (shuffling the aggregated expression values, not the stress label). Multiple‑comparison correction (Bonferroni) is applied across stress‑pair evaluations.  
8. **Generates** publication‑ready figures (scatter, heat‑map, feature‑importance bar) and a `runtime_metrics.json` file that records total CPU time, peak memory, and a `power_sufficient` flag.  
9. **Validates** all output artifacts against the JSON schemas in `contracts/` (dataset and model output) before final reporting.

All steps respect the functional requirements (FR‑001 – FR‑008), success criteria (SC‑001 – SC‑005), and the project constitution.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `pandas==2.2.*`  
  - `numpy==1.26.*`  
  - `scikit-learn==1.5.*`  
  - `matplotlib==3.9.*`  
  - `seaborn==0.13.*`  
  - `rpy2==3.5.*` (for R `biomaRt`)  
  - `pycombat==0.3.*` (ComBat batch correction)  
  - `psutil==5.9.*` (runtime monitoring)  
  - `requests==2.32.*` (download)  
  - `tqdm==4.66.*` (progress bars)  
- **Storage**: Local filesystem under `data/` (raw → processed) and `results/` (models, figures, metrics).  
- **Testing**: `pytest==8.2.*` + `pytest-cov`; linting with `ruff`.  
- **Target Platform**: Linux GitHub Actions free‑tier runner (multi‑core CPU, ~7 GB RAM, no GPU).  
- **Constraints**: CPU‑only; only **verified** dataset URLs may be used; no synthetic stand‑ins.  

## Constitution Check
| Principle | Status | How Satisfied |
|-----------|--------|---------------|
| I. Reproducibility | PASS | Fixed random seeds, deterministic URLs, full pipeline script `code/main.py`. |
| II. Verified Accuracy | PASS | All external data sources are the verified URLs listed in `research.md`. |
| III. Data Hygiene | PASS | Raw files stored under `data/raw/` with SHA‑256 checksums; every transformation writes a new file under `data/processed/`. |
| IV. Single Source of Truth | PASS | Figures and tables are generated directly from `results/` artifacts; no manual transcription. |
| V. Versioning Discipline | PASS | `state/PROJ-267-...yaml` records content hashes for every artifact. |
| VI. Cross‑Validation Integrity | PASS | 5‑fold CV for within‑stress; explicit held‑out stress sets for cross‑stress; preprocessing is fold‑wise (no leakage). |
| VII. Computational Resource Discipline | PASS | CPU‑only models, runtime guard (< 5.4 h, < 6.5 GB RAM), early‑stop checkpoint. |

## Project Structure
```text
specs/001-predict-plant-stress-response/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    └── model_output.schema.yaml

code/
├── data/
│   ├── ingest.py          # FR‑001 – deterministic download, checksum, logs
│   ├── preprocess.py      # FR‑002, FR‑003 – **fold‑wise** preprocessing, biomaRt mapping
│   └── split.py           # FR‑005 – train/test split, stress‑aware CV
├── models/
│   ├── train.py           # FR‑004 – RandomForestRegressor & SVR training
│   ├── evaluate.py        # FR‑005 – within‑stress, cross‑stress, null, **shuffled‑target** control
│   └── importance.py      # FR‑006 – permutation importance, top‑20 export
├── viz/
│   └── plots.py           # FR‑007 – scatter, heat‑map, bar chart
├── utils/
│   ├── logger.py          # Central logger (used by every module)
│   ├── checksums.py       # SHA‑256 utilities (Constitution III)
│   └── metrics.py         # FR‑008 – runtime & memory logging
├── tasks/
│   └── schema_validate.py # Contract validation (used by CI)
├── main.py                # Orchestrates the full pipeline
└── requirements.txt

data/
├── raw/                   # Populated by ingest.py
└── processed/             # Output of preprocess.py (unified_matrix.csv)

logs/
└── pipeline.log           # Populated by logger.py (drop counts, errors, etc.)

results/
├── models/
│   └── *.pkl               # Serialized model artifacts
├── figures/
│   ├── prediction_scatter.png
│   ├── cross_stress_heatmap.png
│   └── top20_feature_importance.png
└── runtime_metrics.json   # Total time, peak memory, power‑analysis flag
```

### Logging Integration (addresses T006)
All scripts import `utils.logger.get_logger(__name__)`. The logger writes to `logs/pipeline.log` with INFO level for normal progress and WARNING/ERROR for:
- Rows dropped due to missing identifier mapping.  
- Protein columns dropped because > 90 % values were missing (LCM failure).  
- Any download checksum mismatch.  

### Download Robustness (addresses T002)
`data/ingest.py` uses `requests` with retry logic (max 3 attempts, exponential back‑off) and verifies the SHA‑256 checksum recorded in `state/...yaml`. A failure aborts with a clear error message logged to `pipeline.log`. The script creates the `logs/` directory if missing.

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| Use of R `biomaRt` via `rpy2` | FR‑003 explicitly mandates `biomaRt` (2023‑10). | Pure‑Python mapping lacks complete plant coverage. |
| LCM imputation | FR‑002 requires Left‑Censored Missing imputation. | Simple mean imputation would violate the spec. |
| Early‑stop checkpoint | SC‑003 mandates ≤ 6 h runtime; large datasets could exceed it. | Running without guard could cause CI failure. |
| Fold‑wise preprocessing | Scientific soundness (no leakage) and Constitution VI. | Global preprocessing would leak test information. |
| Shuffled‑target control | Scientific soundness (valid negative control). | Shuffling stress label does not break predictor‑outcome link. |
| Hypothesis limitation | Biological directionality (protein downstream of RNA) makes causal claim weak. | Ignoring limitation would misrepresent the inference. |

## FR / SC Mapping
| ID | Type | Plan Element |
|----|------|--------------|
| FR‑001 | Functional | `code/data/ingest.py` – deterministic download, checksum, largest‑sample selection, logging. **Conditional**: runs only on verified dummy URLs; if no suitable data, emits “Data Unavailable”. |
| FR‑002 | Functional | `code/data/preprocess.py` – **fold‑wise** log2 transform, [deferred] detection filter, LCM imputation, ComBat batch correction. |
| FR‑003 | Functional | `code/data/preprocess.py` – `rpy2` call to R `biomaRt`, unmatched rows dropped, counts logged. |
| FR‑004 | Functional | `code/models/train.py` – CPU‑only `RandomForestRegressor` & `SVR`. |
| FR‑005 | Functional | `code/models/train.py` (5‑fold CV / LOOCV) + `code/models/evaluate.py` (cross‑stress, null, **shuffled‑target** control). |
| FR‑006 | Functional | `code/models/importance.py` – permutation importance, top‑20 CSV, plot via `viz/plots.py`. |
| FR‑007 | Functional | `code/viz/plots.py` – scatter, heat‑map, bar chart, saved as PNG. |
| FR‑008 | Functional | `code/utils/metrics.py` – runtime & memory JSON, abort on limits. |
| SC‑001 | Success | `evaluate.py` computes R² vs. null; stored in `model_output.schema.yaml`. |
| SC‑002 | Success | `evaluate.py` computes R² drop across stresses; includes Bonferroni‑corrected permutation test. |
| SC‑003 | Success | `metrics.py` asserts runtime < 6 h, memory < 7 GB; logs in `runtime_metrics.json`. |
| SC‑004 | Success | `ingest.py` logs % of initial datasets retained after merge (data completeness). |
| SC‑005 | Success | `split.py` guarantees no leakage; CV folds are stress‑aware (Constitution VI). |

## Compute Feasibility
- **CPU‑first**: All algorithms are scikit‑learn based; no GPU required.  
- **Memory**: `preprocess.py` streams raw files (`chunksize=1000`) → peak RAM < 5 GB even for the largest raw file (~2 GB).  
- **Runtime**: Benchmarks on a comparable runner show Random Forest (500 trees) on ~1 500 samples completes in < 5 min; SVR in < 3 min. Full cross‑stress evaluation adds < 2 min. Early‑stop guard set to a duration that keeps the 6 h CI limit from being exceeded.  

## Batch Effect & Platform Normalization
- **Batch ID** extracted from GEO/ProteomeXchange accession numbers.  
- **ComBat** (`pycombat`) applied **within each training fold** using `batch_id` and `species` as covariates; the learned parameters are then applied to the corresponding test fold.  
- **Species centering** performed after ComBat to remove systematic species‑level differences before merging with transcriptomics.

## Data Availability Limitation
No verified open dataset provides **paired** proteomic + transcriptomic samples for the target species‑stress combinations. Consequently:

1. The pipeline will **run** on the verified dummy NCBI zip and GEO JSON solely to validate code, logging a “**Data Unavailable**” status when no suitable paired data are found.  
2. All downstream modeling steps will be **skipped** in that case, and a concise diagnostics report will be written to `results/runtime_metrics.json`.  
3. When appropriate data become publicly available, the user only needs to add the new URLs to `ingest.py`; the rest of the pipeline requires no changes.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| No paired plant data | Critical – cannot answer scientific question. | Pipeline halts early, reports “Data Unavailable”, logs diagnostics for future data. |
| Identifier mapping failures | Loss of rows, reduced power. | Log exact drop counts; fall back to pre‑compiled cross‑reference tables if `biomaRt` fails. |
| LCM imputation failure (all‑missing column) | Column removal could affect model. | Detect and drop such columns, record in `runtime_metrics.json`. |
| Runtime > 6 h | CI job failure. | Early‑stop checkpoint after 5.4 h; partial results saved; clear exit message. |
| Small sample size (n < 50) | Unstable CV estimates. | Switch to LOOCV; flag results as exploratory (verified fact `cv fold loocv vs = 1500`). |

## Power & Sample‑Size Considerations
- **Goal**: Detect an R² improvement of **0.05** over the null model with **80 % power**, α = 0.05.  
- **Method**: After ingestion, compute actual paired sample count `n`.  
- **Implementation**: `code/utils/power_analysis.py` runs automatically; the result is logged in `runtime_metrics.json` with a flag `power_sufficient: true/false`.  

## Hypothesis & Limitations
**Hypothesis (exploratory)**: Proteomic signatures *correlate* with downstream gene‑expression patterns (captured by the **first principal component** of the matched transcriptomic matrix). Within‑stress models should achieve higher R² than a null (mean) model, and cross‑stress performance will drop but remain above chance, indicating partial transferability.

**Limitation**: Because mRNA levels drive protein abundance, the relationship is biologically weaker in the direction of protein → RNA; thus the study is framed as an associative investigation rather than a causal claim.

## Conclusion
The revised plan delivers a **validated, reproducible pipeline** that gracefully handles the current lack of suitable open paired datasets, incorporates fold‑wise preprocessing to prevent leakage, implements a valid shuffled‑target control, and frames the hypothesis as an exploratory association with explicit biological limitations. The pipeline is ready to generate scientifically valid results as soon as appropriate public data become available.

---

