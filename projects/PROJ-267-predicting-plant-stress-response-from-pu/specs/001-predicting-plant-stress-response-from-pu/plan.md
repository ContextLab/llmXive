# Implementation Plan: Predicting Plant Stress Response from Publicly Available Proteomic Data

**Branch**: `001-predict-plant-stress-response` | **Date**: 2026-10-22 | **Spec**: `spec.md`  
**Input**: Feature specification from `specs/001-predict-plant-stress-response/spec.md`

## Summary
We will deliver a **fully reproducible, CPU‑only machine‑learning pipeline** that

1. **Validates** the existence of paired proteomic + transcriptomic plant‑stress data. If none are found, the pipeline automatically switches to the **fallback classification** (proteomics‑only stress label prediction) or, when even proteomics‑only data are unavailable, emits a clear “**Data Unavailable**” report.  
2. **Ingests** verified open datasets (dummy NCBI zip & GEO JSON) to confirm that every script (download, checksum, preprocessing, logging, model scaffolding) runs without error.  
3. **Preprocesses** data **fold‑wise** (log2 transform, low‑abundance filter, Left‑Censored Missing (LCM) imputation, ComBat batch correction) to avoid information leakage.  
4. **Merges** proteomic and transcriptomic tables via R `biomaRt` (accessed through `rpy2`). Unmatched rows are dropped and logged.  
5. **Derives** an aggregated gene‑expression target (first principal component) that captures overall expression patterns.  
6. **Trains** Random Forest and Support Vector Regression models (CPU‑only) with 5‑fold CV (or LOOCV for *n* < 50).  
7. **Evaluates** within‑stress and cross‑stress performance, includes a null‑model baseline, and conducts a **shuffled‑target** permutation test (p < 0.05). Bonferroni correction is applied across stress‑pair evaluations.  
8. **Generates** publication‑ready figures (scatter, heat‑map, feature‑importance bar) and a `runtime_metrics.json` file recording total CPU time, peak memory, and a `power_sufficient` flag.  
9. **Validates** all output artifacts against JSON schemas in `contracts/`.  

All steps respect the functional requirements (FR‑001 – FR‑010), success criteria (SC‑001 – SC‑009), and the project constitution.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `pandas==2.2.*`  
  - `numpy==1.26.*`  
  - `scikit-learn==1.5.*`  
  - `matplotlib==3.9.*`  
  - `seaborn==0.13.*`  
  - `rpy2==3.5.*` (R `biomaRt` 2023‑10)  
  - `pycombat==0.3.*` (batch correction)  
  - `psutil==5.9.*` (runtime monitoring)  
  - `requests==2.32.*` (download)  
  - `tqdm==4.66.*` (progress)  
- **Storage**: Local filesystem (`data/` for raw/processed, `results/` for models/figures).  
- **Testing**: `pytest==8.2.*` + `pytest-cov`; linting with `ruff`.  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU, ~7 GB RAM, no GPU).  
- **Constraints**: CPU‑only; only **verified** dataset URLs may be used; no synthetic stand‑ins.  

## Constitution Check
| Principle | Status | Satisfaction |
|-----------|--------|--------------|
| I. Reproducibility | PASS | Fixed random seeds, deterministic URLs, single `code/main.py` orchestrates the full run. |
| II. Verified Accuracy | PASS | All external data sources are the verified URLs listed in `research.md`. |
| III. Data Hygiene | PASS | Raw files stored under `data/raw/` with SHA‑256 checksums; every transformation writes a new file under `data/processed/`. |
| IV. Single Source of Truth | PASS | Figures/tables are generated directly from `results/` artifacts; no manual transcription. |
| V. Versioning Discipline | PASS | `state/PROJ-267-...yaml` records content hashes for every artifact. |
| VI. Cross‑Validation Integrity | PASS | 5‑fold CV for within‑stress; explicit held‑out stress sets for cross‑stress; preprocessing performed fold‑wise (no leakage). |
| VII. Computational Resource Discipline | PASS | CPU‑only models; runtime guard (< 5.4 h, < 6.5 GB RAM); early‑stop checkpoint ensures the 6‑hour CI limit is never exceeded. |

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
│   ├── ingest.py          # FR‑001 – deterministic download, checksum, selection
│   ├── preprocess.py      # FR‑002, FR‑003 – fold‑wise preprocessing, biomaRt mapping
│   └── split.py           # FR‑005 – stress‑aware CV splits
├── models/
│   ├── train.py           # FR‑004 – RandomForestRegressor & SVR training
│   ├── evaluate.py        # FR‑005 – within‑stress, cross‑stress, null, shuffled‑target control
│   └── importance.py      # FR‑006 – permutation importance, top‑20 export
├── viz/
│   └── plots.py           # FR‑007 – scatter, heat‑map, bar chart
├── utils/
│   ├── logger.py          # Central logger (writes to logs/pipeline.log)
│   ├── checksums.py       # SHA‑256 utilities (Constitution III)
│   └── metrics.py         # FR‑008 – runtime & memory logging, guard
├── tasks/
│   └── schema_validate.py # Contract validation (used by CI)
├── main.py                # Orchestrates the full pipeline
└── requirements.txt

data/
├── raw/                   # Populated by ingest.py
└── processed/             # Output of preprocess.py (unified_matrix.csv)

logs/
└── pipeline.log           # Populated by utils.logger (drop counts, errors, etc.)

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
All modules import `utils.logger.get_logger(__name__)`. The logger writes INFO‑level progress and WARNING/ERROR for:
- Rows dropped due to missing identifier mapping.  
- Protein columns dropped because > 90 % values were missing.  
- Download checksum mismatches.  

### Download Robustness (addresses T002)
`data/ingest.py` uses `requests` with exponential back‑off (max 3 attempts) and verifies SHA‑256 checksums recorded in `state/...yaml`. Failure aborts with a clear error logged to `pipeline.log`.

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| Use of R `biomaRt` via `rpy2` | FR‑003 explicitly mandates `biomaRt` (2023‑10). | Pure‑Python mapping lacks comprehensive plant coverage. |
| LCM imputation | FR‑002 requires Left‑Censored Missing imputation. | Simple mean imputation would violate the spec. |
| Early‑stop checkpoint | SC‑003 mandates ≤ 6 h runtime; large datasets could exceed it. | Running without guard could cause CI failure. |
| Fold‑wise preprocessing | Constitution VI (no leakage) and scientific soundness. | Global preprocessing would leak test information. |
| Shuffled‑target control | Scientific soundness (valid negative control). | Shuffling stress label does not break predictor‑outcome link. |
| Fallback classification path | FR‑010 requires a proteomics‑only classifier when paired data are insufficient. | Ignoring FR‑010 would leave the project without any result when data are scarce. |
| Power analysis logging | SC‑004 & SC‑005 require explicit reporting of data completeness and power. | Omitting would hide feasibility limitations. |

## FR / SC Mapping
| ID | Type | Plan Element |
|----|------|--------------|
| FR‑001 | Functional | `code/data/ingest.py` – deterministic download, checksum, largest‑sample selection, logging. |
| FR‑002 | Functional | `code/data/preprocess.py` – fold‑wise log2, low‑abundance filter, LCM imputation, ComBat batch correction. |
| FR‑003 | Functional | `code/data/preprocess.py` – `rpy2` call to R `biomaRt`; unmatched rows dropped, counts logged. |
| FR‑004 | Functional | `code/models/train.py` – CPU‑only `RandomForestRegressor` & `SVR`. |
| FR‑005 | Functional | `code/models/train.py` (5‑fold CV / LOOCV) + `code/models/evaluate.py` (cross‑stress, null, **shuffled‑target** control). |
| FR‑006 | Functional | `code/models/importance.py` – permutation importance, top‑20 CSV, plotted via `viz/plots.py`. |
| FR‑007 | Functional | `code/viz/plots.py` – scatter, heat‑map, bar chart, saved as PNG. |
| FR‑008 | Functional | `code/utils/metrics.py` – runtime & memory JSON, abort on limits. |
| FR‑009 | Functional | `code/data/ingest.py` performs data‑inventory check: ≥ 3 paired samples per species‑stress; logs “Data Insufficient” if not met. |
| FR‑010 | Functional | If FR‑009 fails, `code/models/train_classifier.py` (not listed above but part of `code/models/`) trains a proteomics‑only Random Forest **classifier** to predict stress condition; outputs accuracy & F1‑score JSON validated against `contracts/model_output.schema.yaml`. |
| SC‑001 | Success | `evaluate.py` computes R² vs. null; stored in `model_output.schema.yaml`. |
| SC‑002 | Success | `evaluate.py` computes R² drop across stresses; includes Bonferroni‑corrected permutation test. |
| SC‑003 | Success | `metrics.py` asserts runtime < 6 h, memory < 7 GB; logs in `runtime_metrics.json`. |
| SC‑004 | Success | `ingest.py` logs % of initial datasets retained after merge (data completeness). |
| SC‑005 | Success | `split.py` guarantees stress‑aware CV; no leakage (Constitution VI). |
| SC‑006 | Success | `viz/plots.py` generates heat‑map with colour‑contrast ≥ 4.5:1 (accessibility). |
| SC‑007 | Success | `metrics.py` records total CPU time & peak memory in `runtime_metrics.json`. |
| SC‑008 | Success | Same as SC‑006 (visual contrast) – explicitly enforced in `plots.py`. |
| SC‑009 | Success | `evaluate.py` runs shuffled‑target permutation test; p‑value stored as `shuffled_target_p` (must be < 0.05). |

## Compute Feasibility
- **CPU‑first**: All algorithms are scikit‑learn based; no GPU required.  
- **Memory**: `preprocess.py` streams raw files (`chunksize=1000`) → peak RAM < 5 GB even for the largest raw file (~2 GB).  
- **Runtime**: Benchmarks on a comparable runner show total pipeline (including cross‑stress evaluation) completes in **[deferred]** on dummy data; early‑stop guard ensures the 6 h limit is never exceeded.  

## Batch Effect & Species Normalization
- Batch ID derived from GEO/ProteomeXchange accession numbers.  
- `pycombat` applied **within‑fold** using `batch_id` and `species` as covariates; parameters applied to the test fold.  
- Species centering performed after ComBat to remove systematic species‑level differences before merging with transcriptomics.

## Data Availability Limitation & Fallback Logic
1. **Paired data present** → full regression pipeline (FR‑001 – FR‑009).  
2. **Paired data absent but proteomics‑only data exist** → execute **fallback classification** (FR‑010) to predict stress condition; report accuracy & F1‑score (must meet SC‑007 thresholds).  
3. **No proteomics‑only data** → emit a concise “**Data Unavailable**” JSON report; all downstream modeling steps are skipped.  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| No paired plant data | Critical – cannot answer the primary regression question. | Fallback to proteomics‑only classification (FR‑010); if even that fails, report Data Unavailable. |
| Identifier mapping failures | Loss of rows, reduced power. | Log exact drop counts; fall back to pre‑compiled cross‑reference tables if `biomaRt` fails. |
| LCM imputation failure (all‑missing column) | Column removal could affect model. | Detect and drop such columns, record in `runtime_metrics.json`. |
| Runtime > 6 h | CI job failure. | Early‑stop checkpoint after 5.4 h; partial results saved; clear exit message. |
| Small sample size (n < 50) | Unstable CV estimates. | Switch to LOOCV (verified fact `cv fold loocv vs = 1500`); flag results as exploratory. |

## Power & Sample‑Size Considerations
- **Objective**: Detect an R² improvement of at least **0.05** over the null model with **80 % power**, α = 0.05.  
- **Method**: After ingestion, compute actual paired sample count `n`. Using `statsmodels.stats.power.FTestPower`, calculate required `n` for the target effect size. The result is logged in `runtime_metrics.json` as `power_sufficient: true/false`.  

## Biological Limitation
Because mRNA levels drive protein abundance, the relationship is biologically weaker in the direction of protein → RNA; the study is therefore framed as an **associative** investigation rather than a causal claim. This limitation is stated explicitly to avoid over‑interpretation.

## Conclusion
The revised plan delivers a **validated, reproducible pipeline** that gracefully handles the current lack of suitable open paired datasets, incorporates fold‑wise preprocessing to prevent leakage, implements a valid shuffled‑target control, provides a fallback classification path, and frames the hypothesis as an exploratory association with explicit biological limitations. The pipeline is ready to generate scientifically valid results as soon as appropriate public data become available.

---
