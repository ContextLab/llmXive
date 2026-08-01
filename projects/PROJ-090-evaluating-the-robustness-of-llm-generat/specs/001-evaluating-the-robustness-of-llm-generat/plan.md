# Implementation Plan: Evaluating the Robustness of LLM-Generated Code to Input Perturbations

**Branch**: `001-evaluating-robustness-llm-code` | **Date**: 2026-07-03 | **Spec**: `specs/001-evaluating-the-robustness-of-llm-generat/spec.md`
**Input**: Feature specification from `specs/001-evaluating-the-robustness-of-llm-generat/spec.md`

## Summary

This project evaluates the robustness of LLM-generated code (specifically StarCoder2-1.5B for CPU feasibility, with StarCoder2-3B as a GPU fallback) against semantically-preserving input perturbations. The technical approach involves: (1) downloading the HumanEval dataset, (2) generating perturbed prompts via synonym substitution, typo injection, and syntactic rephrasing, (3) filtering perturbations using a high-fidelity semantic similarity threshold (>0.95) validated by `sentence-transformers/all-MiniLM-L6-v2`, (4) executing model inference on CPU with 4-bit quantization, (5) running generated code in a sandboxed environment, and (6) performing rigorous statistical analysis (McNemar's test with Bonferroni correction, Mixed-Effects Logistic Regression) to quantify performance degradation. The primary analysis will use the *entire candidate pool* with similarity scores as covariates to mitigate selection bias.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets`, `transformers`, `bitsandbytes`, `sentence-transformers`, `scikit-learn`, `statsmodels`, `pandas`, `numpy`, `timeout-decorator`  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`)  
**Testing**: `pytest` (unit tests for perturbation logic, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Research CLI / Data Pipeline  
**Performance Goals**: Total runtime < 6 hours on CPU (primary); < 9 hours on GPU (fallback). Memory usage < 7 GB during inference.  
**Constraints**: No CUDA available for primary run; strict generation timeout; s execution timeout; Low-bit quantization mandatory.  
**Scale/Scope**: A set of HumanEval tasks; up to 3 perturbations per task; total samples: a representative cohort sufficient for statistical power.

> **Note on Compute**: The primary run targets **StarCoder2-1.5B** with 4-bit quantization on CPU to ensure the 6-hour budget is met. StarCoder2-3B is reserved for the GPU escape hatch only. If CPU inference fails (OOM or timeout), the execution stage will auto-offload to a reproducible GPU environment (Kaggle or local GPU with pinned versions) as per the project's compute feasibility strategy.

### Verified datasets

- **HumanEval**: `openai/openai_humaneval` (HuggingFace Datasets). URL: `https://huggingface.co/datasets/openai/openai_humaneval`. Verified accessible.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/config.py`. `requirements.txt` pins versions. HumanEval fetched from canonical HF source on every run. GPU offload environment is pinned via Docker/requirements.txt. |
| **II. Verified Accuracy** | **PASS** | All dataset citations (HumanEval) verified against the `# Verified datasets` block. No hallucinated URLs. |
| **III. Data Hygiene** | **PASS** | Raw data (HumanEval parquet) checksummed before processing. Perturbation logs written to immutable JSON files. No in-place edits. |
| **IV. Single Source of Truth** | **PASS** | All statistics in the final report will be derived programmatically from `data/processed/inference_logs.json` and `data/processed/results.csv`. |
| **V. Versioning Discipline** | **PASS** | Artifacts will carry content hashes in `state/`. `updated_at` timestamps managed by the agent workflow. GPU environment versions pinned. |
| **VI. Secure Execution** | **PASS** | Code execution runs in a subprocess with `timeout` decorator and network disabled (via sandboxing logic). |
| **VII. Perturbation Traceability** | **PASS** | Every perturbation logged with `perturbation_type`, `similarity_score`, `seed`, and `execution_environment` (CPU/GPU) in the raw JSON. |

## Spec Defects & Assumptions

- **SC-003 (Spec Defect - RESOLVED)**: The spec text originally stated "Total job runtime is measured against the -hour GitHub Actions free-tier limit." **Action**: The spec has been corrected to "6-hour". Plan assumes 6 hours for internal logic.
- **US-2 Acceptance Scenario 1 (Spec Defect - RESOLVED)**: The text "within the A memory limit is imposed..." was corrupted. **Action**: The spec has been corrected to "within the constrained RAM limit and a bounded timeout".
- **US-3 Acceptance Scenario 3 (Spec Defect - RESOLVED)**: The text "for a a stratified random sample" contained a typo. **Action**: The spec has been corrected to "for a stratified random sample".
- **FR-011 (Undefined Cap)**: "Sufficient number" is undefined. **Action**: Plan defines cap as **656 samples** (A substantial number of original items will be included. + A set of perturbed samples will be generated.) to fit the 6-hour window.

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-robustness-llm-generat/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-090-evaluating-the-robustness-of-llm-generat/
├── code/
│   ├── __init__.py
│   ├── config.py              # Seeds, thresholds, model paths (StarCoder2-1.5B default)
│   ├── data/
│   │   ├── download.py        # HumanEval loader
│   │   ├── perturbation.py    # Synonym, typo, rephrase generators
│   │   ├── validator.py       # Semantic similarity scorer
│   │   └── filter.py          # Threshold filtering logic
│   ├── model/
│   │   ├── loader.py          # StarCoder2-1.5B/3B 4-bit quantization setup
│   │   └── inference.py       # Generation loop with timeout
│   ├── sandbox/
│   │   └── executor.py        # Code execution with timeout
│   └── analysis/
│       ├── stats.py           # McNemar, Bonferroni, Mixed-Effects
│       └── sensitivity.py     # Threshold sweep analysis
├── data/
│   ├── raw/                   # Downloaded parquet files
│   └── processed/             # Perturbation candidates, inference logs, results
├── tests/
│   ├── unit/
│   │   └── test_perturbation.py
│   └── integration/
│       └── test_pipeline.py
└── requirements.txt
```

**Structure Decision**: Single-project structure selected to minimize overhead. The pipeline is linear (Download -> Perturb -> Filter -> Inference -> Analyze), making a monolithic `code/` directory with modular sub-packages efficient.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Mixed-Effects Model** | Required by FR-012 to account for clustering of perturbations within tasks (Entity 1: Task in `data-model.md`). | Simple logistic regression would ignore the non-independence of multiple perturbations per task, violating statistical assumptions. |
| **4-bit Quantization** | Required by FR-004 to fit StarCoder2-1.5B/3B in ~7GB RAM on CPU. | Full precision (16-bit) would exceed memory limits on the CI runner. |
| **Semantic Similarity Filter** | Required by FR-003 to ensure "high-fidelity" perturbations. | Random noise generation would fail to isolate the effect of *semantic-preserving* surface changes. |
| **Full Pool Analysis** | Required to mitigate selection bias (scientific soundness concern). | Filtering to >0.95 only and analyzing that subset introduces survivorship bias; the plan uses the full pool with similarity as a covariate. |

## Task Ordering & Dependencies

- **Phase 1 (Data)**: T013 (Synonym), T014 (Typo), T015 (Rephrase) are [P] (parallel).
- **Phase 2 (Validation)**: T016 (Validator) must complete before T017. **T016 is NOT [P]** (it is a prerequisite).
- **Phase 3 (Generation)**: T017 (Generation Pipeline) depends on T013-T016.
- **Phase 4 (Inference)**: T021 (Inference) depends on T017.
- **Phase 5 (Analysis)**:
  - T032 (McNemar), T033 (Mixed-Effects), T034 (Sensitivity), T035 (Error Class) are [P] (parallel) after T021.
  - **T037 (ECE)** is [P] (parallel) with T032-T035.
  - T036 (Final Report) depends on T032-T037.
- **Verification Note**: T034 verification will check for *available* thresholds, not a hard `len(df)==4`, to handle empty candidate pools gracefully.

## File Outputs by Task

- **T016**: Writes `code/data/semantic_validator.py` (logic) and `data/processed/perturbation_candidates_raw.json` (output).
- **T017**: Generates `data/processed/perturbation_candidates_raw.json` (if not already present) and calls T016 logic.
- **T018**: Writes `data/processed/perturbation_candidates.json` (filtered dataset).
- **T021**: Writes `data/processed/inference_logs.json` (model outputs and execution results).
- **T033**: Writes `data/processed/mixed_effects_results.json` (variance components and coefficients).