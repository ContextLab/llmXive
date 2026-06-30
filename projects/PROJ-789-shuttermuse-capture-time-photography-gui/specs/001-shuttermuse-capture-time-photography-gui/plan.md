# Implementation Plan: ShutterMuse: Capture-Time Photography Guidance with MLLMs

**Branch**: `001-shutter-muse-guide` | **Date**: 2026-06-30 | **Spec**: `specs/001-shuttermuse-capture-time-photography-gui/spec.md`

## Summary
This feature implements a research pipeline to evaluate Multi‑Modal Large Language Models (MLLMs) on “capture‑time” photography guidance. The system ingests images from the AVA and COCO datasets, generates guidance using three distinct MLLMs (LLaVA, Qwen‑VL, GPT‑4V), and categorizes errors against ground‑truth composition tags. It further performs statistical bias analysis correlating error types with demographic and environmental metadata (inferred via FairFace) and compares architectural performance using counterfactual prompting as an **exploratory** hypothesis‑generation tool. All steps are designed for CPU‑only execution on GitHub Actions free‑tier runners.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies** (pinned in `requirements.txt`):
- `torch==2.2.2+cpu` (CPU‑only wheel)
- `transformers==4.40.2`
- `datasets==2.19.0`
- `pandas==2.2.2`
- `scikit-learn==1.5.0`
- `deepface==0.0.83` (provides FairFace weights; the only demographic inference library)
- `opencv-python==4.9.0.80`
- `pyyaml==6.0.1`
- `requests==2.32.2`
- `tqdm==4.66.4`

**Storage**: Local filesystem (`data/raw`, `data/processed`), CSV/Parquet for intermediate results.
**Testing**: `pytest` (unit tests for parsing, integration tests for a small subset).
**Target Platform**: Linux (GitHub Actions free‑tier runner, 2 CPU, ~7 GB RAM, ~14 GB disk).
**Performance Goals**: Complete analysis on a **sample of 30 images per model** (≈ 90 total inferences) within 6 h.
**Constraints**: No GPU, no large‑model fine‑tuning, all libraries CPU‑compatible. Models are run in 8‑bit quantized mode where supported.

## Constitution Check

| Principle | Status | Implementation Strategy |
|-----------|--------|-------------------------|
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`. External datasets fetched from canonical URLs or verified scripts. `requirements.txt` pins exact versions. |
| **II. Verified Accuracy** | **PASS** | Phase 0 runs `src/validate_refs.py`, a blocking step that invokes the Reference‑Validator Agent on all markdown artifacts before any review points are awarded. |
| **III. Data Hygiene** | **PASS** | Raw data downloaded to `data/raw/` with SHA‑256 checksums recorded in `state/project_state.yaml`. All transformations write new files under `data/processed/`. |
| **IV. Single Source of Truth** | **PASS** | All statistics in the paper are generated directly from `data/processed/` via the report script; no hand‑typed numbers. |
| **V. Versioning Discipline** | **PASS** | After each pipeline stage, `src/state_update.py` computes SHA‑256 hashes of newly created artifacts, updates `state/project_state.yaml`, and records an `updated_at` timestamp. |
| **VI. Visual Composition Grounding** | **PASS** | Error categorization strictly compares model output against AVA/COCO composition tags; no reliance on model confidence. |
| **VII. Failure Mode Attribution** | **PASS** | Errors are split into “Potential Reasoning Errors” (identified via counterfactual prompts) and “Data‑Driven Failures”. Limitations are explicitly documented (see research.md). |

## Project Structure

### Documentation (this feature)
```text
specs/001-shuttermuse-capture-time-photography-gui/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│ ├── analysis_result.schema.yaml
│ └── error_record.schema.yaml
└── tasks.md
```

### Source Code (repository root)
```text
projects/PROJ-789-shuttermuse-capture-time-photography-gui/code/
├── data/
│ ├── raw/
│ └── processed/
├── src/
│ ├── __init__.py
│ ├── download.py # Dataset fetching (FR‑001)
│ ├── face_detect.py # Primary face bounding‑box extraction
│ ├── demographics.py # FairFace inference (FR‑008)
│ ├── inference.py # MLLM prompting & retry (FR‑002, FR‑006)
│ ├── categorization.py # Error parsing & tagging (FR‑003)
│ ├── analysis.py # Statistical tests, Monte‑Carlo fallback (FR‑004)
│ ├── report.py # Comparative report generation (FR‑005)
│ ├── state_update.py # Artifact hashing & timestamp update
│ └── validate_contracts.py# JSON‑Schema validation of CSV/JSON outputs
├── tests/
│ ├── unit/
│ └── integration/
├── requirements.txt
└── main.py # Orchestration script
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| **Multiple MLLM Architectures** | Required by FR‑002 and US‑3 to explore reasoning vs. data failures. | A single model would not allow architectural comparison. |
| **External Demographic Inference** | Required by FR‑008; AVA/COCO lack demographics. | Hard‑coding demographics would violate Principle VI. |
| **Statistical Test Selection Logic** | Needed to handle sparse contingency tables on a CPU‑friendly sample size. | Using only chi‑square would produce invalid p‑values for low‑count cells. |
| **Counterfactual Prompting** | Required by FR‑009 to generate hypotheses about reasoning errors. | Omitting it would leave the research question unanswered. |
| **CPU Feasibility** | Large vision‑language models are GPU‑heavy. | Running full‑size models would exceed the 6 h limit. |

## Detailed Phase Plan

### Phase 0: Preparatory Steps
1. **Reference Validation** – Run `src/validate_refs.py` (CI step) to ensure all citations are verified before any review points are awarded (Constitution II).
2. **State Initialization** – Create `state/project_state.yaml` with an empty artifact hash map.

### Phase 1: Data Ingestion & Preprocessing (FR‑001, FR‑008)
1. **Download AVA & COCO** – `src/download.py` uses the official AVA script (`) and the HuggingFace COCO loader (`datasets.load_dataset("coco")`). Images are **sampled to 30 per model** (90 total) to respect RAM limits and CPU runtime.
2. **Face Detection** – `src/face_detect.py` runs a lightweight Haar cascade to locate the primary human subject; stores bounding box (`face_bbox`). Images without a detectable primary face are **excluded from bias analysis** but retained for general error logging (FR‑007).
3. **Demographic Inference** – `src/demographics.py` runs FairFace (via `deepface`) on the cropped face region. Records confidence; retains only records with `confidence ≥ 0.85` (FR‑008). Low‑confidence entries are flagged and excluded from bias analysis (FR‑007).
4. **Checksum & Logging** – SHA‑256 checksums of raw files written to `state/project_state.yaml`.

### Phase 2: MLLM Inference & Error Categorization (FR‑002, FR‑003, FR‑006)
1. **Prompt Library** – Two prompt types:
 - **Standard Prompt:** “Analyze this image for photography composition. Suggest capture‑time adjustments for lighting, angle, and rule of thirds.”
 - **Counterfactual Prompt:** “What if the lighting were *low‑light*? How would you change the composition?”
 Counterfactual prompts are **exploratory**; any inconsistency is recorded as **“Potential Reasoning Error (hypothesis)”** rather than a definitive reasoning failure.
2. **Retry / Rate‑Limit Handling** – Exponential backoff (max 3 retries). If cumulative wait > 5 min, the script pauses and logs a warning (Edge Case).
3. **Parsing & Categorization** – `src/categorization.py` maps model output to error categories:
 - “Hallucinated Object”
 - “Incorrect Rule Application”
 - “Missing Advice”
 - “Correct”
 - “Parsing Failure”
 - **“Potential Reasoning Error (hypothesis)”** – assigned only for counterfactual prompts where the response contradicts logical expectations while the visual input is unchanged.

### Phase 3 – Statistical Analysis (FR‑004, US‑2)
1. **Contingency Tables** – Build tables for `Error Type` vs. `Demographic Group` (gender, age, ethnicity) and `Error Type` vs. `Lighting Condition`. Include `image_quality` (average brightness) as a covariate to control for confounding.
2. **Test Selection Logic**:
 - Compute expected cell frequencies.
 - **If all expected ≥ 5** → **Chi‑square** (`scipy.stats.chi2_contingency`).
 - **If any expected < 5** **and** the table is **2×2** → **Fisher’s Exact**.
 - **If any expected < 5** **and** the table has **more than 2 dimensions** → **Monte‑Carlo chi‑square** (`scipy.stats.chi2_contingency(..., monte_carlo=True, n_iter=10000)`).
3. **Multiple‑Comparison Correction** – Apply **Bonferroni** correction across all tested variable pairs; record the method in the `correction_applied` field.
4. **Effect Size & Confidence** – Report **Cramér’s V** with **bootstrap 95 % confidence intervals** (10 000 resamples). Optionally provide a **Bayesian posterior** for the effect size in supplemental material.
5. **Bias Correlation Reporting** – For each demographic group, output error rates, test statistics, p‑values, and effect sizes. Non‑significant results are explicitly reported.

### Phase 4 – Architectural Comparison (US‑3)
1. **Aggregate Error Rates** – Compute per‑model error frequencies, separating “Potential Reasoning Errors (hypothesis)” from other categories.
2. **Counterfactual Insight** – Summarize each model’s consistency on counterfactual prompts; the model with the lowest proportion of hypothesis‑labeled errors is highlighted, **but** we note that this does not prove a causal reasoning advantage (Principle VII).
3. **Baseline Comparison** – Contrast model error rates with the deferred human‑expert baseline (SC‑003). Since the baseline is not directly comparable, we report relative differences only.
4. **Limitations & Future Work** – Emphasize that counterfactual prompts cannot definitively separate reasoning from data‑driven failures without a synthetic control dataset. Propose a future experiment with synthetic images where ground‑truth lighting changes are known.

### Phase 5 – Reporting & Validation
1. **Report Generation** – `src/report.py` creates `results/report.md` with tables, effect sizes, methodological notes, and explicit discussion of limitations.
2. **Contract Validation** – Run `src/validate_contracts.py` to ensure `error_records.csv` and `analysis_results.csv` conform to the schemas in `contracts/`.
3. **State Update** – Run `src/state_update.py` to compute SHA‑256 hashes of all newly created artifacts and update `updated_at` in `state/project_state.yaml`.
4. **Reproducibility Test** – The CI pipeline re‑runs the full pipeline on a **10‑image subset** to verify end‑to‑end reproducibility (Principle I).

## Compute Feasibility Summary
- **CPU‑only inference**: LLaVA and Qwen‑VL are loaded in 8‑bit quantized mode; inference ≈ 1–2 s per image per model.
- **FairFace**: Runs on cropped face (~0.5 s per image). Total inference time ≈ 2 h for 90 images across three models.
- **Statistical tests**: In‑memory, negligible runtime.
- **Total wall‑clock**: < 6 h on GitHub Actions free tier.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| FairFace CPU latency | Reduce sample size to a manageable number of images per model; parallelize across two CPU cores. |
| GPT‑4V rate limits | Exponential backoff + pause after 5 min of continuous failures. |
| Sparse tables | Monte‑Carlo chi‑square fallback; collapse rare error categories into “Other”. |
| Selection bias from confidence filtering | Include `image_quality` covariate; perform stratified sensitivity analysis. |
| Counterfactual interpretation | Frame as hypothesis generation; outline synthetic‑data future work. |

## projects/PROJ-789-shuttermuse-capture-time-photography-gui/specs/001-shuttermuse-capture-time-photography-gui/tasks.md
*(no changes required)*