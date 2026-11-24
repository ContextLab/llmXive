# Implementation Plan: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

**Branch**: `001-visual-priming-implicit-attitudes` | **Date**: 2024-10-12 | **Spec**: `specs/001-visual-priming-implicit-attitudes/spec.md`  
**Input**: Feature specification from `/specs/001-visual-priming-implicit-attitudes/spec.md`

## Summary
The pipeline will (1) fetch a **single open‑source IAT dataset** whose URL is listed in `data/verified_sources.json`; (2) verify that the required trial‑level columns exist and abort with a clear *Data Gap* if they do not; (3) extract stimulus metadata, compute linkage metrics, and derive missing **prime‑valence** and **stimulus‑ambiguity** scores using CPU‑only models/dictionaries **and** validate those derived scores against external benchmarks; (4) perform a **VIF pre‑check** and a **power‑analysis checkpoint** before fitting a **linear mixed‑effects (LME) model** with random intercept **and random slope** for prime valence, including optimizer fall‑backs; (5) apply **FDR** correction, add associational framing notes, and run an **α‑sweep sensitivity analysis**; (6) always generate a **PDF report**—either a full scientific report or a data‑gap narrative—satisfying SC‑003; (7) compute **SHA‑256 checksums** for **all** artifacts and record them in `state/artifact_hashes.json`. All steps run on the GitHub Actions free‑tier CPU box (≤7 GB RAM, 2 CPU cores, ≤6 h). No GPU is required.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies** (pinned in `code/requirements.txt`):  
  `pandas==2.2.2`, `numpy==1.26.4`, `statsmodels==0.14.2`, `scikit-learn==1.5.0`, `torch==2.3.0+cpu`, `transformers==4.44.0`, `datasets==2.20.0`, `pyyaml==6.0.2`, `reportlab==4.2.2`, `matplotlib==3.9.2`, `seaborn==0.13.2`, `pytest==8.3.2`, `nltk==3.8.1`, `opencv-python-headless==4.10.0.84`.  
- **Storage**: Local filesystem under `data/` (raw, processed, primes, targets) and `reports/`.  
- **Testing**: `pytest -m contract` validates all JSON/YAML contracts; unit tests for each script.  
- **Target Platform**: Linux GitHub Actions runner (CPU‑only).  
- **Constraints**: CPU‑first; streaming path for >7 GB datasets; no GPU.  
- **Scale/Scope**: One primary dataset; streaming used if size >7 GB.

## Constitution Check
| Principle | Compliance | Detail |
|-----------|------------|--------|
| **I. Reproducibility** | PASS | Random seeds are defined in `code/config.py`. All external URLs are hard‑coded and validated against `data/verified_sources.json`. |
| **II. Verified Accuracy** | PASS | Only URLs from the “Verified datasets” block are cited; `research.md` references them verbatim. |
| **III. Data Hygiene** | PASS | Raw files are immutable; every transformation writes a new file with a SHA‑256 checksum recorded in `state/artifact_hashes.json`. |
| **IV. Single Source of Truth** | PASS | Every figure/table is generated directly from `data/processed/linked_trials.csv` and the model result JSON; no hand‑typed numbers. |
| **V. Versioning Discipline** | PASS | **All** artifacts (raw, processed, model outputs, reports) have SHA‑256 hashes stored in `state/artifact_hashes.json`. |
| **VI. Distinct Stimulus Set Integrity** | PASS | `data/primes/` and `data/targets/` remain separate until the final merge step (Task T009). |

## Project Structure
```text
specs/001-visual-priming-implicit-attitudes/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── ingest_metrics.schema.yaml
│   ├── linkage_status.schema.yaml
│   ├── model_results.schema.yaml
│   ├── output.schema.yaml
│   └── verified_sources.schema.yaml
└── tasks.md   # generated later

code/
├── main.py                # CLI orchestrator, logging config
├── config.py              # PRIMARY_DATASET_URL, LINKAGE_THRESHOLD, seeds, paths
├── ingest.py              # Download & core‑column validation
├── preprocess.py          # Metadata extraction, linkage metrics
├── derive_valence.py      # Lexical dictionary / CPU emotion classifier
├── derive_ambiguity.py    # WordNet sense‑count / texture variance
├── vif.py                 # VIF calculation (pre‑fit)
├── power_check.py         # A priori / post‑filter power analysis
├── confound_check.py      # Detect trial‑order, stimulus‑repetition confounds
├── validate_scores.py     # External validation of derived valence & ambiguity
├── model.py               # LME fitting with random intercept + slope, optimizer fallback
├── fdr.py                 # Benjamini‑Hochberg correction
├── framing.py             # Append `caution_note` & `limitation_note`
├── sensitivity.py         # α‑sweep analysis
├── report.py              # Plotting & PDF assembly (always produces PDF)
├── streaming.py           # >7 GB streaming helper
├── verified_sources.py    # Loads `data/verified_sources.json`
├── pip.conf               # `--extra-index-url https://download.pytorch.org/whl/cpu`
└── logs/
    └── pipeline.log      # Created on first CLI execution

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
    ├── linked_trials.csv

state/
├── artifact_hashes.json
├── linkage_status.json
├── analysis_scope.json
├── vif_flag.json
├── model_results.json
├── model_convergence_metrics.json
├── fdr_results.json
├── sensitivity_analysis.json
├── power_check.json
├── confound_check.json
├── score_validation.json
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
| **FR‑001** | Verify core columns; derive missing scores | T003, T004, T007, T008 |
| **FR‑002** | CPU‑optimized valence derivation | T008 |
| **FR‑003** | Associational framing | T013 |
| **FR‑004** | FDR correction | T012 |
| **FR‑005** | VIF computation & flagging | T010 |
| **FR‑006** | α‑sweep sensitivity | T014 |
| **FR‑007** *(new)* | External validation of derived scores | T020 |
| **FR‑008** *(new)* | Power‑analysis checkpoint | T021 |
| **FR‑009** *(new)* | Confounding diagnostics | T022 |
| **SC‑001** | Ingestion/linkage completeness | T005 |
| **SC‑002** | Model convergence success (≥ [deferred] within 3 attempts) | T011 |
| **SC‑003** | PDF contains required artifacts | T015 |
| **SC‑004** *(new)* | Artifact hashing for versioning | T023 |

All functional requirements and success criteria are explicitly covered, with the newly added tasks closing the previously identified gaps.

## Task Ordering (dependency‑corrected)

| ID | Description | Depends On |
|----|-------------|------------|
| **T001** | **Environment Setup** – create virtualenv, install pinned `requirements.txt` (uses `code/pip.conf`), ensure `code/logs/` exists. | – |
| **T002** | **Load Verified Sources** – read `data/verified_sources.json` (schema `verified_sources.schema.yaml`), select the first entry as `config.PRIMARY_DATASET_URL`. Abort if file missing or empty. | T001 |
| **T003** | **Ingest** – download dataset from `config.PRIMARY_DATASET_URL` → `data/raw/iat.parquet`; compute SHA‑256 checksum; write `state/artifact_hashes.json`. | T002 |
| **T004** | **Core‑Column Validation** – confirm presence of `response_time`, `participant_id`, `stimulus_id`. If any missing, write `state/linkage_status.json` with `status: HALT` and `message: "Data Gap: Schema Mismatch"`; abort downstream steps. | T003 |
| **T005** | **Metadata Extraction & Linkage Metric** – split stimuli into `data/primes/` & `data/targets/`; create `data/processed/metadata_mapping.csv`; compute % linked trials; write `data/processed/ingest_metrics.json` and update `state/linkage_status.json`. Threshold `config.LINKAGE_THRESHOLD` (default 95.0) is read from `code/config.py`. >10 % missing → HALT; ≤10 % → WARN & exclude. | T004 |
| **T006** | **Linkage Gate** – read `ingest_metrics.json` and `config.LINKAGE_THRESHOLD`; if `linkage_percentage < threshold` set `status: HALT` in `state/linkage_status.json`. | T005 |
| **T007** | **Derive Ambiguity** – if `ambiguity` column missing, compute WordNet sense‑count for words and Laplacian texture variance for images; write `data/processed/ambiguity_scores.csv`. | T005 |
| **T008** | **Derive Valence** – if `prime_valence` missing, use lexical valence dictionary for words and a CPU‑only emotion classifier (`torch` on CPU) for images; write `data/processed/valence_scores.csv`. | T005 |
| **T009** | **Merge Scores** – join `metadata_mapping.csv`, `ambiguity_scores.csv`, `valence_scores.csv` → `data/processed/linked_trials.csv`; also write `state/analysis_scope.json` (`full` or `valence_only` if ambiguity unavailable). | T007, T008 |
| **T010** | **VIF Pre‑Check** – compute VIF on predictors (`prime_valence`, `stimulus_ambiguity`, any demographics) using `linked_trials.csv`; write `state/vif_flag.json`. If any VIF > 5.0, set `claim_suppressed: true`. | T009 |
| **T020** | **Derived Scores Validation** – compare `prime_valence` against NRC VAD lexicon (words) and FER‑2013 benchmark (images); compare `stimulus_ambiguity` against established ambiguity corpora; store Pearson r and 95 % CI in `state/score_validation.json`. If r < 0.6, add a caution flag used later in reporting. | T009 |
| **T021** | **Power‑Analysis Check** – compute required N for target effect size f = 0.15, α = 0.05, power = 0.80; compare to `linked_trials.csv` row count; write `state/power_check.json`. If insufficient, set `status: HALT` in `state/linkage_status.json` with a “Power Limitation” message. | T009 |
| **T022** | **Confounding Check** – assess trial order autocorrelation, stimulus repetition frequency, and stimulus‑specific ICC; write `state/confound_check.json`. Severe confounds (e.g., ICC > 0.3) set `status: HALT` with explanatory message. | T009 |
| **T011** | **LME Fitting** – fit `statsmodels.MixedLM` with random intercept **and** random slope for `prime_valence` per `participant_id`; use robust SE; retry up to 3 optimizers (`lbfgs`, `bfgs`, `powell`). Record attempts & convergence in `state/model_convergence_metrics.json`. If all fail, log suggestion to simplify random effects. | T010, T020, T021, T022 |
| **T012** | **FDR Correction** – Benjamini‑Hochberg on all fixed‑effect raw p‑values from T011; write `state/fdr_results.json`. | T011 |
| **T013** | **Associational Framing** – augment `state/model_results.json` with `caution_note` and `limitation_note` (as defined in `contracts/model_results.schema.yaml`); compute bootstrap effect sizes (Cohen’s d, partial η²) with seed 42 and ≥ 1000 resamples (count deferred). | T012 |
| **T014** | **Sensitivity Analysis** – sweep α ∈ {0.01, 0.05, 0.10} over FDR‑corrected p‑values; write `reports/sensitivity_analysis.csv` and summary in `state/sensitivity_analysis.json`. | T012 |
| **T015** | **Report Generation** – always produce `reports/final_report.pdf`. If `state/linkage_status.json` is `HALT`, the PDF contains a data‑gap narrative; otherwise it includes interaction plot, coefficient table, effect‑size CIs, caution/limitation notes, and the sensitivity summary. Uses `code/report.py`. | T004 (for halt case), T013, T014 |
| **T016** | **Logging Configuration** – run a one‑off command that creates `code/logs/pipeline.log` with a timestamped entry. Subsequent steps append to this file. | T001 |
| **T017** | **Streaming Verification** – generate a synthetic >7 GB Parquet file (seeded), run `code/streaming.py` with `datasets.load_dataset(..., streaming=True)` to confirm streaming works, then delete the temp file. | T001 |
| **T018** | **Contract Verification** – execute `pytest -m contract` to validate all JSON/YAML artifacts against schemas in `contracts/`. | T015, T017, T016 |
| **T023** | **Artifact Hashing** – after each major output (raw download, processed CSV/JSON, model results, PDF), compute SHA‑256 checksum and append entry to `state/artifact_hashes.json`. Ensures full compliance with Principle V. | All tasks that produce files (T003, T005‑T015, T017) |

### Dependency Clarifications (addressing prior concerns)
- **No circular threshold definition**: `LINKAGE_THRESHOLD` is defined **once** in `code/config.py`; all tasks read the same static value.
- **VIF placed before modeling**: T010 now precedes T011, satisfying the methodological requirement.
- **Validation of derived scores**: T020 provides external construct‑validity evidence before any inferential claim.
- **Power check**: T021 enforces a minimum sample size prior to modeling.
- **Confounding diagnostics**: T022 explicitly assesses trial‑order and stimulus‑specific confounds.
- **Random slope inclusion**: T011 now fits a random slope for prime_valence.
- **Artifact hashing**: T023 guarantees every artifact is version‑hashed.
- **Logging artifact existence**: T016 guarantees `pipeline.log` is created before any other step writes to it.
- **Streaming verification uses >7 GB synthetic file**: T017 creates a 7.5 GB Parquet file, satisfying the requirement.

---

