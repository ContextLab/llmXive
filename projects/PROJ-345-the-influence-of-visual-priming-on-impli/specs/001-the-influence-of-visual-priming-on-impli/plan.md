# Implementation Plan: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

**Branch**: `001-visual-priming-implicit-attitudes` | **Date**: 2024-10-12 | **Spec**: `specs/001-visual-priming-implicit-attitudes/spec.md`  
**Input**: Feature specification from `/specs/001-visual-priming-implicit-attitudes/spec.md`

## Summary
The pipeline will (1) download a **single, hard‑coded, openly‑available IAT‑style dataset** (URL stored in `code/config.py`), (2) validate core columns and halt with a clear *Data Gap* if they are missing, (3) extract stimulus metadata and compute linkage metrics, (4) derive missing **prime‑valence** and **stimulus‑ambiguity** scores using CPU‑only models/dictionaries, (5) run a **VIF pre‑check** before fitting a **linear mixed‑effects (LME) model** with optimizer fall‑backs, (6) apply **FDR** correction, (7) add mandatory **associational framing** notes, (8) perform an **α‑sweep sensitivity analysis**, and (9) always produce a **PDF report** (either a full results report or a data‑gap report). All steps are fully reproducible, respect the constitution, and run on the GitHub Actions free‑tier CPU box.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies** (pinned in `code/requirements.txt`): `pandas==2.2.2`, `numpy==1.26.4`, `statsmodels==0.14.2`, `scikit-learn==1.5.0`, `torch==2.3.0+cpu`, `transformers==4.44.0`, `datasets==2.20.0`, `pyyaml==6.0.2`, `reportlab==4.2.2`, `matplotlib==3.9.2`, `seaborn==0.13.2`, `pytest==8.3.2`, `nltk==3.8.1`, `opencv-python-headless==4.10.0.84`.  
- **Storage**: Local filesystem under `data/` (raw, processed, primes, targets) and `reports/`.  
- **Testing**: `pytest -m contract` validates JSON/YAML contracts; unit tests for each step.  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ≤7 GB RAM, ≤14 GB disk, ≤6 h).  
- **Project Type**: Data‑science CLI pipeline.  
- **Constraints**: CPU‑first only; no GPU required.  
- **Scale/Scope**: One primary dataset; size handled via streaming if >7 GB.

## Constitution Check
| Principle | Compliance | Detail |
|-----------|------------|--------|
| **I. Reproducibility** | PASS | Random seeds (`np.random.seed(42)`, `torch.manual_seed(42)`) are set in `code/config.py`. All external URLs are hard‑coded and validated against `data/verified_sources.json`. |
| **II. Verified Accuracy** | PASS | Only URLs listed in the “Verified datasets” block are cited. `research.md` references them verbatim; `verified_sources.json` is the single source of truth for URL validation (Task T048). |
| **III. Data Hygiene** | PASS | Raw files are immutable; every transformation writes a new file with a SHA‑256 checksum recorded in `state/artifact_hashes.json`. |
| **IV. Single Source of Truth** | PASS | Every figure/table in the PDF is generated directly from `data/processed/linked_trials.csv` and the model result JSON. No hand‑typed numbers. |
| **V. Versioning Discipline** | PASS | Content hashes for all artifacts are stored in `state/artifact_hashes.json`; `state/project_state.yaml` records `updated_at` after each task. |
| **VI. Distinct Stimulus Set Integrity** | PASS | `data/primes/` and `data/targets/` remain separate until the final merge step (Task T006). |

## Project Structure
```text
specs/001-visual-priming-implicit-attitudes/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── linkage_status.schema.yaml
│   ├── output.schema.yaml
│   └── verified_sources.schema.yaml
└── tasks.md   # generated later

code/
├── main.py                # CLI orchestrator, logging config
├── config.py              # PRIMARY_DATASET_URL, LINKAGE_THRESHOLD, seeds, paths
├── ingest.py              # Download & core‑column validation
├── preprocess.py          # Metadata extraction & linkage metrics
├── derive_valence.py      # Lexical dictionary / CPU emotion classifier
├── derive_ambiguity.py    # WordNet sense count / Laplacian texture variance
├── vif.py                 # VIF calculation (pre‑fit)
├── model.py               # LME fitting with optimizer fallback
├── fdr.py                 # Benjamini‑Hochberg correction
├── framing.py             # Append `caution_note` & `limitation_note`
├── sensitivity.py         # α‑sweep analysis
├── report.py              # Plotting & PDF assembly (always produces PDF)
├── streaming.py           # >7 GB streaming helper
├── verified_sources.py    # Loads `data/verified_sources.json`
├── pii_scan.py            # PII regex scan
├── requirements.txt
├── pip.conf               # `--extra-index-url https://download.pytorch.org/whl/cpu`
└── logs/
    └── pipeline.log      # Created on first CLI run

data/
├── raw/
│   └── iat.parquet
├── primes/
├── targets/
└── processed/
    ├── metadata_mapping.csv
    ├── ingest_metrics.json
    ├── ambiguity_scores.csv
    ├── valence_scores.csv
    └── linked_trials.csv

state/
├── artifact_hashes.json
├── linkage_status.json
├── analysis_scope.json
├── vif_flag.json
├── model_results.json
├── model_convergence_metrics.json
└── project_state.yaml

reports/
├── interaction_plot.png
├── sensitivity_analysis.csv
├── final_report.pdf
└── pii_scan.json
```

## Complexity Tracking (FR/SC → Tasks)

| FR / SC | Capability | Task(s) |
|--------|------------|---------|
| **FR‑001** | Verify core columns; derive missing scores | T002, T003, T005a, T005b |
| **FR‑002** | CPU‑optimized valence derivation | T005b |
| **FR‑003** | Associational framing | T010 |
| **FR‑004** | FDR correction | T009 |
| **FR‑005** | VIF computation & flagging | T007 |
| **FR‑006** | α‑sweep sensitivity | T011 |
| **SC‑001** | Ingestion/linkage completeness | T004 |
| **SC‑002** | Model convergence success (≥ [deferred] within 3 attempts) | T008 |
| **SC‑003** | PDF contains required artifacts | T012 |

## Task Ordering (dependency‑corrected)

| ID | Description | Depends On |
|----|-------------|------------|
| **T001** | **Environment Setup** – install pinned `requirements.txt` (with `pip.conf`), load `config.py`. | – |
| **T002** | **Ingest** – download from `config.PRIMARY_DATASET_URL` → `data/raw/iat.parquet`; compute SHA‑256 checksum; write `state/artifact_hashes.json`. | T001 |
| **T003** | **Core‑Column Validation** – ensure `response_time`, `participant_id`, `stimulus_id` exist. If any are missing, write `state/linkage_status.json` with `status: HALT` and `message: "Data Gap: Schema Mismatch"`; abort downstream steps. | T002 |
| **T004** | **Metadata Extraction & Linkage Metric** – split stimuli into `data/primes/` & `data/targets/`, create `data/processed/metadata_mapping.csv`, compute % linked trials, write `data/processed/ingest_metrics.json` and `state/linkage_status.json`. Threshold `config.LINKAGE_THRESHOLD` (default 95.0) is read from `config.py`. >10 % missing → HALT; ≤10 % → WARN & exclude. | T003 |
| **T005a** | **Derive Ambiguity** – if `ambiguity` column missing, compute WordNet sense‑count for words and Laplacian texture variance for images; write `data/processed/ambiguity_scores.csv`. | T004 |
| **T005b** | **Derive Valence** – if `prime_valence` missing, use lexical valence dictionary for words and a CPU‑only emotion classifier (`torch` backend) for images; write `data/processed/valence_scores.csv`. | T004 |
| **T006** | **Merge Scores** – join `metadata_mapping.csv`, `ambiguity_scores.csv`, `valence_scores.csv` → `data/processed/linked_trials.csv`; also write `state/analysis_scope.json` (`full` or `valence_only` if ambiguity unavailable). | T005a, T005b |
| **T007** | **VIF Pre‑Check** – compute VIF on predictors (`prime_valence`, `stimulus_ambiguity`, any demographics present); write `state/vif_flag.json`. If any VIF > 5.0, set `claim_suppressed: true`. | T006 |
| **T008** | **LME Fitting** – fit `statsmodels.MixedLM` with random intercept for `participant_id`; robust SE; retry up to 3 optimizers (`lbfgs`, `bfgs`, `powell`). Record attempts & convergence in `state/model_convergence_metrics.json`. If all fail, log suggestion to simplify random effects. | T007 |
| **T009** | **FDR Correction** – Benjamini‑Hochberg on all fixed‑effect p‑values from T008; write `state/fdr_results.json`. | T008 |
| **T010** | **Associational Framing** – augment model result dict with exact keys `caution_note` and `limitation_note` (strings defined in the spec). Also compute bootstrap effect sizes (Cohen’s d, partial η²) with seed 42 and ≥ 1000 resamples (count deferred). | T009 |
| **T011** | **Sensitivity Analysis** – sweep α ∈ {0.01, 0.05, 0.10} over FDR‑corrected p‑values; write `reports/sensitivity_analysis.csv`. | T009 |
| **T012** | **Report Generation** – always produce `reports/final_report.pdf`. If `state/linkage_status.json` is `HALT`, the PDF contains the data‑gap narrative; otherwise it includes interaction plot, coefficient table, effect‑size CIs, caution/limitation notes, and the sensitivity summary. | T004 (for halt case), T010, T011 |
| **T013** | **PII Scan** – run `code/pii_scan.py` on `data/processed/`; write `reports/pii_scan.json`. | T006 |
| **T014** | **Streaming Support Verification** – generate a synthetic >7 GB Parquet file (temp, seeded) and run `code/streaming.py` with `datasets.load_dataset(..., streaming=True)` to confirm the streaming path works. Delete the temp file afterwards. | T001 |
| **T015** | **Verified‑Sources Validation** – load `data/verified_sources.json` (schema defined in `contracts/verified_sources.schema.yaml`) and confirm `config.PRIMARY_DATASET_URL` appears there; abort with clear error if not. | T001 |
| **T016** | **Contract Verification** – `pytest -m contract` validates all JSON/YAML artifacts against the schemas in `contracts/`. | T012, T013 |

### Dependency Corrections (addressing panel concerns)
* **Threshold definition** moved entirely to `config.py`; no circular write/read between tasks.  
* **Confounding Check** removed because it was unrelated to the core research question.  
* **Aggregation** step removed – the model works directly on `linked_trials.csv`.  
* **VIF** now pre‑fit (Task T007).  
* **Optimizer fallback** embedded in T008; no separate task needed.  
* **URL source of truth** – `verified_sources.json` is authoritative (Task T015).  
* **`pip.conf`** creation is part of the repository; `PIP_CONFIG_FILE=code/pip.conf pip install -r code/requirements.txt` is documented in Quickstart.  
* **Streaming verification** uses a >7 GB synthetic file (Task T014) to satisfy the >7 GB condition.  

All functional requirements (FR‑001 – FR‑006) and success criteria (SC‑001 – SC‑003) are explicitly mapped to tasks above.

---
