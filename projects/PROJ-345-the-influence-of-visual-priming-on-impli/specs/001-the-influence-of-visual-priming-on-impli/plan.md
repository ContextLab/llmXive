# Implementation Plan: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

**Branch**: `001-visual-priming-implicit-attitudes` | **Date**: 2024-10-12 | **Spec**: `specs/001-visual-priming-implicit-attitudes/spec.md`  
**Input**: Feature specification from `/specs/001-visual-priming-implicit-attitudes/spec.md`

## Summary
The pipeline will (1) download a **single, hard‑coded, openly‑available IAT‑style dataset** whose URL is stored in `code/config.py` and cross‑checked against `data/verified_sources.json`; (2) validate core columns and halt with a clear *Data Gap* if they are missing; (3) extract stimulus metadata and compute linkage metrics; (4) derive missing **prime‑valence** and **stimulus‑ambiguity** scores using CPU‑only models/dictionaries; (5) run a **VIF pre‑check** before fitting a **linear mixed‑effects (LME) model** with optimizer fall‑backs; (6) apply **FDR** correction; (7) add strict **associational framing** notes; (8) perform an **α‑sweep sensitivity analysis**; (9) always produce a **PDF report** (full analysis or a data‑gap narrative). All steps are fully reproducible, respect the constitution, and run on the GitHub Actions free‑tier CPU box.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies** (pinned in `code/requirements.txt`):  
  `pandas==2.2.2`, `numpy==1.26.4`, `statsmodels==0.14.2`, `scikit-learn==1.5.0`, `torch==2.3.0+cpu`, `transformers==4.44.0`, `datasets==2.20.0`, `pyyaml==6.0.2`, `reportlab==4.2.2`, `matplotlib==3.9.2`, `seaborn==0.13.2`, `pytest==8.3.2`, `nltk==3.8.1`, `opencv-python-headless==4.10.0.84`.  
- **Storage**: Local filesystem under `data/` (raw, processed, primes, targets) and `reports/`.  
- **Testing**: `pytest -m contract` validates JSON/YAML contracts; unit tests for each step.  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ≤7 GB RAM, ≤14 GB disk, ≤6 h).  
- **Project Type**: Data‑science CLI pipeline.  
- **Constraints**: CPU‑first only; no GPU required.  
- **Scale/Scope**: One primary dataset; streaming is used if the file exceeds ~7 GB.

## Constitution Check
| Principle | Compliance | Detail |
|-----------|------------|--------|
| **I. Reproducibility** | PASS | Random seeds are set in `code/config.py`. All external URLs are hard‑coded and validated against `data/verified_sources.json`. |
| **II. Verified Accuracy** | PASS | Only URLs listed in the “Verified datasets” block are cited. `research.md` references them verbatim; the authoritative list lives in `data/verified_sources.json`. |
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
│   ├── model_results.schema.yaml
│   ├── ingest_metrics.schema.yaml
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
├── fdr_results.json
├── sensitivity_analysis.json
├── pii_scan.json
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
| **FR‑003** | Associational framing | T029 |
| **FR‑004** | FDR correction | T028 |
| **FR‑005** | VIF computation & flagging | T027a |
| **FR‑006** | α‑sweep sensitivity | T027b |
| **SC‑001** | Ingestion/linkage completeness | T004 |
| **SC‑002** | Model convergence success (≥ [deferred] within 3 attempts) | T025 |
| **SC‑003** | PDF contains required artifacts | T036 |

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
| **T027a** | **VIF Pre‑Check** – compute VIF on predictors (`prime_valence`, `stimulus_ambiguity`, any demographics present); write `state/vif_flag.json`. If any VIF > 5.0, set `claim_suppressed: true`. | T006 |
| **T025** | **LME Fitting** – fit `statsmodels.MixedLM` with random intercept for `participant_id`; robust SE; retry up to 3 optimizers (`lbfgs`, `bfgs`, `powell`). Record attempts & convergence in `state/model_convergence_metrics.json`. If all fail, log suggestion to simplify random effects. | T027a |
| **T028** | **FDR Correction** – Benjamini‑Hochberg on all fixed‑effect p‑values from T025; write `state/fdr_results.json`. | T025 |
| **T029** | **Associational Framing** – augment `state/model_results.json` with keys `caution_note` and `limitation_note` (strings defined in the spec). Also compute bootstrap effect sizes (Cohen’s d, partial η²) with seed 42 and ≥ 1000 resamples (count deferred). | T028 |
| **T027b** | **Sensitivity Analysis** – sweep α ∈ {0.01, 0.05, 0.10} over FDR‑corrected p‑values; write `reports/sensitivity_analysis.csv`. | T028 |
| **T036** | **Report Generation** – always produce `reports/final_report.pdf`. If `state/linkage_status.json` is `HALT`, the PDF contains the data‑gap narrative; otherwise it includes interaction plot, coefficient table, effect‑size CIs, caution/limitation notes, and the sensitivity summary. | T004 (for halt case), T029, T027b |
| **T009** | **Logging Configuration & Execution Log** – `code/main.py` configures a `logging.FileHandler` writing to `code/logs/pipeline.log`. The first execution of any `--step` creates the file with timestamped entries. | T001 |
| **T014** | **Streaming Support Verification** – generate a synthetic >7 GB Parquet file (seeded) and run `code/streaming.py` with `datasets.load_dataset(..., streaming=True)` to confirm the streaming path works. Delete the temp file afterwards. | T001 |
| **T015** | **Verified‑Sources Validation** – load `data/verified_sources.json` (schema defined in `contracts/verified_sources.schema.yaml`) and confirm `config.PRIMARY_DATASET_URL` appears there; abort with clear error if not. | T001 |
| **T016** | **Contract Verification** – `pytest -m contract` validates all JSON/YAML artifacts against the schemas in `contracts/`. | T036, T009, T018a, T017, etc. |

### Dependency Clarifications (addressing previous panel concerns)
- **Threshold handling**: `LINKAGE_THRESHOLD` is defined **once** in `code/config.py`. No task writes it; all tasks read it, eliminating circular writes.
- **Confounding check**: No separate confounding‑check task remains; any needed diagnostics are folded into the VIF pre‑check (T027a).
- **Aggregation**: Not required for this analysis; the model operates directly on `linked_trials.csv`.
- **VIF placement**: VIF is computed **before** model fitting (T027a → T025).
- **Logging**: T009 now explicitly creates `code/logs/pipeline.log` on first step execution.
- **Ingest metrics**: T004 writes a fully populated `data/processed/ingest_metrics.json`; this satisfies the missing artifact concern (previous T018a).
- **Linked trials**: T006 creates a non‑empty `data/processed/linked_trials.csv`; this satisfies the previous T017 gap.
- **Report PDF**: T036 assembles the final PDF; this resolves the missing `final_report.pdf` (previous T036).

All functional requirements (FR‑001 – FR‑006) and success criteria (SC‑001 – SC‑003) are explicitly mapped to tasks above.

---
