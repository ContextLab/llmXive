# Implementation Plan: Evaluating the Impact of LLM-Generated Code on Memory Usage

**Branch**: `001-eval-llm-memory-impact` | **Date**: 2024-01-15 | **Spec**: `spec.md`

## Summary

This feature implements a computational pipeline to evaluate whether LLM-generated code exhibits systematically different memory consumption patterns compared to human-written equivalents. The approach involves downloading the HumanEval or MBPP benchmark, generating LLM solutions using CPU-tractable models (TinyLlama-1.1B as primary, with 8-bit quantization attempted if available), profiling memory usage via `memory_profiler` and `tracemalloc`, and performing statistical analysis (Kaplan-Meier estimator for censored data, Wilcoxon for uncensored) with multiple-comparison corrections. The entire pipeline is constrained to run on a GitHub Actions free-tier runner (2 CPU, 7 GB RAM, no GPU) within 6 hours.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers`, `datasets`, `memory-profiler`, `tracemalloc` (stdlib), `scikit-learn`, `statsmodels`, `lifelines` (for Kaplan-Meier), `networkx` (for cyclomatic complexity), `pandas`, `numpy`  
**Storage**: Local filesystem (`data/`, `outputs/`)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: CLI / Research Pipeline  
**Performance Goals**: < 6 hours total runtime; < 7 GB RAM peak; < 30s per code execution  
**Constraints**: No GPU; 8-bit quantization attempted if available; censored data handling for timeouts/failures  
**Scale/Scope**: N=50 paired observations (LLM vs Human), with fallback to MBPP if HumanEval yields <50 pairs.

## Constitution Check

This plan adheres to the following principles from `constitution.md`:

1.  **I. Reproducibility**: Random seeds will be pinned in `code/config.py`. Datasets will be fetched from specific HuggingFace version tags. `requirements.txt` will pin all versions.
2.  **II. Verified Accuracy**: All citations to datasets (HumanEval/MBPP) will reference the verified HuggingFace repository paths. No external URLs will be fabricated.
3.  **III. Data Hygiene**: Raw datasets will be downloaded to `data/raw/` with checksums. Derived data (memory logs, feature extractions) will be saved to `data/processed/` without modifying raw files.
4.  **IV. Single Source of Truth**: All statistics in the final report will be generated programmatically from `data/processed/` CSVs. No hand-typed numbers.
5.  **V. Versioning Discipline**: **Every artifact** (raw datasets, generated code, analysis scripts, and output files) will be hashed (sha256). These hashes will be recorded in the project's `state/...yaml` file to ensure the entire artifact set is versioned.
6.  **VI. Controlled Profiling Environment**: The `code/profiling_env.yaml` will record the runner OS, CPU model, and Python version. All runs will occur in this isolated environment.
7.  **VII. Benchmark Dataset Versioning**: The exact `dataset_id` and `revision` for HumanEval/MBPP will be recorded in `data/dataset_manifest.yaml`.

## Project Structure

### Documentation (this feature)

```text
specs/001-eval-llm-memory-impact/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-395-evaluating-the-impact-of-llm-generated-c/
├── data/
│   ├── raw/                 # Downloaded datasets (HumanEval/MBPP)
│   ├── processed/           # Memory logs, feature extractions, statistical results
│   └── dataset_manifest.yaml
├── code/
│   ├── __init__.py
│   ├── config.py            # Random seeds, model params, timeouts
│   ├── download.py          # Dataset fetching
│   ├── generate.py          # LLM inference (CPU-tractable)
│   ├── profile.py           # Memory profiling harness (tracemalloc/memory_profiler)
│   ├── features.py          # Static code analysis (LOC, complexity, imports)
│   ├── analyze.py           # Statistical tests (KM, Wilcoxon, VIF, corrections)
│   └── utils.py             # Error handling, retry logic, CSV I/O
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── requirements.txt
└── profiling_env.yaml
```

**Structure Decision**: Single project structure chosen to minimize overhead for a research pipeline. All scripts are CLI-driven and sequential to ensure reproducibility and fit within CI time limits.

## Plan Completeness & Methodological Rigor

### Functional Requirement Mapping

| FR-ID | Requirement | Plan Phase/Step | Implementation Detail |
| :--- | :--- | :--- | :--- |
| **FR-001** | Download HumanEval/MBPP | Phase 1: Data Acquisition | `code/download.py` uses `datasets.load_dataset("openai_humaneval")` or `mbpp` with specific version pinning. |
| **FR-002** | Generate LLM solutions (CPU, 8-bit) | Phase 2: Code Generation | `code/generate.py` **attempts** `load_in_8bit=True` first. If unavailable (CPU backend failure), it falls back to float16 on `TinyLlama-1.1B`. Timeout enforced at a fixed duration per sample. |
| **FR-003** | Profile memory (peak/steady) | Phase 3: Profiling | `code/profile.py` runs `tracemalloc` for steady-state (defined as median of final [deferred] of steps) and `memory_profiler` for peak. Multiple runs per solution, median recorded. |
| **FR-004** | Tobit or Kaplan-Meier (censored) | Phase 4: Primary Analysis | `code/analyze.py` uses **Kaplan-Meier estimator** as the primary method for handling censored data (timeouts/OOMs). Wilcoxon is used for the uncensored subset. Zero-diffs excluded. |
| **FR-005** | Multiple-comparison correction | Phase 4: Primary Analysis | `code/analyze.py` applies Holm-Bonferroni if ≥3 tests run. Reports raw and corrected p-values. |
| **FR-006** | Extract 3 features + efficiency | Phase 3: Feature Extraction | `code/features.py` calculates LOC, Cyclomatic Complexity (via `networkx`), Import Count. `memory_per_loc` is calculated **only as a descriptive metric** and excluded from regression. |
| **FR-007** | VIF calculation | Phase 5: Regression Diagnostics | `code/analyze.py` computes VIF for regression predictors (LOC, Complexity, Imports). Flags VIF > 5. |
| **FR-008** | Record CSV (ID, source, memory) | Phase 3: Data Storage | `code/utils.py` writes `memory_measurements.csv` with strict schema. |
| **FR-009** | N=50 in 6 hours | Phase 0: Feasibility Check | Plan limits N to a moderate sample size. If HumanEval yields <50 valid pairs, **MBPP is used as fallback**. Sequential execution with 30s timeout per run ensures total time < 6h. |
| **FR-010** | Handle syntax errors | Phase 3: Profiling | `code/profile.py` catches `SyntaxError`, logs "N/A", continues. |

### Statistical Rigor & Dataset Fit

-   **Dataset-Variable Fit**: HumanEval/MBPP provides code and test inputs. Memory usage is derived via execution. No external variables (e.g., personality) are needed. **Fit confirmed.**
-   **Multiple Comparisons**: Plan explicitly applies Holm-Bonferroni for any set of ≥3 tests (Peak, Steady, Efficiency).
-   **Power Limitation**: N=50 is the target. If fewer valid pairs exist in HumanEval, the pipeline switches to MBPP. If N < 50 even after switching, the report records `N_actual` and flags power limitation.
-   **Causal Inference**: The study is observational. The plan explicitly frames findings as **associational** (A-005). No causal claims.
-   **Collinearity & Size Control**: To isolate the "LLM effect" from code size, the plan uses a **two-stage residualization** approach: Peak Memory is first regressed on LOC (and Complexity/Imports if needed) to extract residuals, which are then compared between LLM and Human groups. VIF > 5 is flagged (FR-007).
- **Measurement Validity**: `tracemalloc` and `memory_profiler` are standard Python tools (A-002). **Steady-state** is defined as the median memory of the final [deferred] of execution steps to ensure reproducibility.
-   **Stability Check**: Instead of a simple CV threshold, the plan uses the **Interquartile Range (IQR)** of the 3 runs. If IQR > 15% of the median, the sample is re-run or excluded.

### Compute Feasibility (GitHub Actions Free Tier)

-   **Hardware**: 2 CPU, 7 GB RAM.
-   **Model Strategy**:
    -   **Primary**: `TinyLlama-1.1B` (1.1B parameters) in float16 (~2.2 GB RAM).
    -   **Rationale**: Fits comfortably within 7 GB RAM, leaving ~4.8 GB for OS, Python, and execution sandbox. Phi is too large for safe CPU inference on this hardware.
    -   **Quantization**: `load_in_8bit=True` is attempted first per FR-002. If `bitsandbytes` fails on CPU, the system falls back to float16.
-   **Memory Budget**: Data processing is streaming. No large matrices loaded at once.
- **Runtime**: A set of samples * (Generation [deferred] + Profiling [deferred] * 3 runs) [deferred]. Well within 6h limit.

### Constitution Check (Detailed)

-   **Principle V (Versioning Discipline)**: The implementation will compute SHA-256 hashes for:
    1.  Raw dataset files (in `data/raw/`).
    2.  Generated code artifacts (in `data/processed/llm_solutions.csv`).
    3.  Analysis scripts (`code/*.py`).
    4.  Final output files (CSVs, JSONs).
    All hashes will be recorded in `state/PROJ-395-...yaml` under `artifact_hashes`.