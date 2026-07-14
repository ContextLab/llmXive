# Implementation Plan: Evaluating the Impact of LLM-Generated Code on Code Coverage

**Branch**: `[001-evaluating-llm-code-coverage]` | **Date**: 2026-06-25 | **Spec**: `spec.md`

## Summary

This feature implements a reproducible pipeline to evaluate the code coverage differences between LLM-generated solutions and human-written baselines for equivalent programming tasks. The system ingests tasks from MBPP and HumanEval, generates code using a configurable LLM (with a CPU-tractable -bit quantized fallback), executes test suites via `pytest-cov`, and performs advanced statistical analysis using Linear Mixed-Effects Models (LMM) or Generalized Linear Mixed Models (GLMM) to account for benchmark clustering and discrete data distributions. The implementation strictly adheres to the GitHub Actions free-tier constraints (Limited CPU resources, 7GB RAM, no GPU).

## Technical Context

**Language/Version**: Python +  
**Primary Dependencies**: `pytest`, `pytest-cov` (v4.0+), `scikit-learn`, `scipy`, `pandas`, `matplotlib`, `seaborn`, `transformers` (CPU-only), `datasets`, `openai` (optional), `huggingface_hub`, `statsmodels`, `bitsandbytes` (for -bit quantization).  
**Storage**: Local file system (`data/`, `generated/`, `coverage_reports/`, `outputs/`).  
**Testing**: `pytest` (unit tests for pipeline logic; integration tests for coverage execution).  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Data Science Pipeline / CLI Tool.  
**Performance Goals**: Process ≥100 tasks within ≤6 hours wall-clock time; memory usage <7GB.  
**Constraints**: No GPU/CUDA; strict rate-limit handling; deterministic random seeds; Low-bit quantization for CPU inference.  
**Scale/Scope**: A set of paired tasks (MBPP + HumanEval); A set of generated code files will be produced for analysis.; A substantial number of coverage reports.

> **Dataset Fit Note**: The spec requires MBPP and HumanEval. The "Verified datasets" block provided in the prompt **does not** list verified URLs for MBPP or HumanEval. Per the Constitution (Principle II & VII), the system will attempt to load these via standard programmatic loaders (`datasets.load_dataset("mbpp")` and `datasets.load_dataset("google-research-datasets/human_eval")`). **Crucially**, the plan acknowledges that if these sources are not verified by the Reference-Validator Agent, the project is in a **GATE BLOCKED** state for "research_accepted" status. The pipeline will proceed in "sandbox mode" to generate data, but no research conclusions can be officially accepted until verification is complete.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`; `requirements.txt` pins all versions; CI re-fetches canonical datasets. |
| **II. Verified Accuracy** | **FAIL (GATE BLOCKED)** | Citations in `research.md` restricted to the "Verified datasets" block. MBPP/HumanEval URLs are currently **unverified** in the provided block. **Action**: The pipeline runs in sandbox mode, but the project cannot advance to `research_accepted` until the Reference-Validator Agent confirms the source URLs. |
| **III. Data Hygiene** | **PASS** | All raw data in `data/` is checksummed; derived data (coverage reports) gets new filenames; no in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All statistics in `paper` trace to `data/coverage_pairs.csv`; figures trace to `outputs/`. |
| **V. Versioning Discipline** | **PASS** | Artifacts under `data/` tracked with content hashes in `state/`. |
| **VI. Coverage Measurement** | **PASS** | `pytest-cov` v4.0+ used consistently; config pinned; reports saved verbatim. |
| **VII. Benchmark Dataset Integrity** | **FAIL (GATE BLOCKED)** | MBPP/HumanEval are loaded via loaders, but the specific versions are not verified against canonical repositories in the provided block. **Action**: Same as Principle II; project is blocked from research acceptance until verification. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-llm-code-coverage/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── task_catalog.schema.yaml
│   ├── generated_solution.schema.yaml
│   └── coverage_record.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
data/
├── benchmarks/          # MBPP, HumanEval raw data
├── benchmarks/processed/ # Transformed executable test files
├── generated/           # LLM-generated Python files
├── coverage_reports/    # JSON/XML coverage outputs
└── processed/           # coverage_pairs.csv, stats_summary.csv

code/
├── __init__.py
├── main.py              # CLI entry point
├── config.py            # Config loading, seeds
├── dataset_loader.py    # MBPP/HumanEval ingestion
├── test_transformer.py  # Converts string tests to .py files
├── llm_generator.py     # LLM invocation, fallback logic (4-bit)
├── coverage_runner.py   # pytest execution, parsing
├── analyzer.py          # Stats (LMM, GLMM, Bootstrap)
├── visualizer.py        # Stratified plots
└── utils.py             # Retry logic, logging

tests/
├── unit/
│   ├── test_analyzer.py
│   └── test_llm_generator.py
└── integration/
    └── test_pipeline.py

requirements.txt
```

**Structure Decision**: Single-project structure (Option 1) is selected. The pipeline is a cohesive data science workflow requiring tight coupling between generation, execution, and analysis. Separating into microservices would add unnecessary overhead for a CI job with a duration of several hours

The research question, method, and references remain as originally stated in the planning document, with the specific temporal magnitude generalized to a qualitative description appropriate for the planning phase..

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **LMM/GLMM Strategy** | Required to handle benchmark clustering (MBPP vs HumanEval) and discrete coverage distributions. | Simple t-tests violate independence assumptions and are invalid for discrete data. |
| **4-bit Quantization** | Required to fit small-scale models in 7GB RAM on CPU. | FP32/FP16 models exceed RAM limits on free-tier runners. |
| **Test Suite Transformation** | MBPP/HumanEval provide test strings, not files. | `pytest-cov` requires executable files; raw strings cannot be measured. |
| **Bootstrap Sensitivity** | Required to assess robustness of effect size, not just sign flips. | Sign flips are a weak metric; bootstrap CI provides statistical stability. |
