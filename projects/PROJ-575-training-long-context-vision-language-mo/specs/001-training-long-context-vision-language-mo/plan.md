# Implementation Plan: Reproduce & Validate Long-Context VLM Training with MMLongBench

**Branch**: `575-reproduce-long-context-vlm` | **Date**: 2026-05-20 | **Spec**: `specs/575-reproduce-long-context-vlm/spec.md`
**Input**: Feature specification from `specs/575-reproduce-long-context-vlm/spec.md`

## Summary

This feature executes the vendored `MMLongBench` evaluation pipeline on a CPU-only GitHub Actions runner to validate the claims of the paper "Training Long-Context Vision-Language Models Effectively with Generalization Beyond 128K Context." The primary objective is to reproduce the evaluation metrics for long-document VQA and generalization beyond large-scale contexts, while adhering to strict resource constraints (limited CPU and RAM). 

**Critical Constraint Resolution**: Due to the 7 GB RAM limit, the plan mandates the use of a **4-bit quantized** version of the `Qwen2.5-VL-7B` model (e.g., via GGUF or `bitsandbytes` 4-bit on CPU) to fit within memory, replacing the originally proposed float16 loading which would exceed capacity. The scaling analysis is framed as a **Descriptive Trend Analysis** due to the limited sample size (n=10), acknowledging that statistical power for hypothesis testing is insufficient.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only wheel), `transformers`, `mmlongbench` (vendored submodule), `pandas`, `scikit-learn`, `datasets`, `llama-cpp-python` (for GGUF support if needed)  
**Storage**: Temporary local disk for model weights and dataset caching (within 14 GB limit)  
**Testing**: `pytest` for contract validation; integration tests via shell scripts  
**Target Platform**: GitHub Actions Free Tier (Linux, 2 vCPU, 7 GB RAM, no GPU)  
**Project Type**: Computational Research / Reproduction Pipeline  
**Performance Goals**: Complete `--sample-size=10` evaluation in < 60 minutes; Peak RAM < 7 GB  
**Constraints**: 
- No CUDA/GPU usage. 
- **Model Loading**: Must use 4-bit quantization (e.g., `load_in_4bit=True` or GGUF) to fit < 7 GB RAM. Float (14 GB) is explicitly disallowed.
- No model retraining from scratch.
- **Dataset**: Must use `test` or `validation` split of MMLongBench, not `train`.
**Scale/Scope**: Evaluation of multiple samples per context length; Multiple context lengths (K-512K); baseline model, target model.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file*

1.  **Reproducibility**: The plan explicitly orders phases to download data (Phase 0) before evaluation (Phase 1) and fits models before analysis (Phase 2), ensuring deterministic runs.
2.  **Resource Feasibility**: All proposed libraries (`torch` CPU, `llama-cpp-python` for 4-bit) are compatible with the 7 GB RAM / 2 CPU constraint. The plan explicitly avoids float16 loading in favor of 4-bit quantization.
3.  **Statistical Rigor**: The plan includes a specific **Phase 3: Scaling Analysis** (matching User Story 3) to fit regression models. However, it explicitly acknowledges that with n=10, statistical significance testing is underpowered. The analysis focuses on **Effect Size Estimation** and **Descriptive Trends** rather than hypothesis testing with p-values. No multiple-comparison correction (BH) is applied as a validity gate due to lack of power; this is documented as a limitation.
4.  **Dataset Verification**: The plan strictly uses only the verified dataset repository `yubo2333/MMLongBench-Doc` (referenced in `research.md` Section 2) and loads the `test` split to avoid data leakage. It explicitly handles the case where a required dataset lacks a verified source by failing fast.
5.  **No Unspecified Constraints**: The plan does not invent new performance thresholds; it adheres strictly to the limits defined in the spec (hours-scale CI, GB-scale RAM, 128K+ generalization). The 4-bit quantization is a necessary implementation detail to meet the 7GB RAM constraint, not a new requirement.

## Project Structure

### Documentation (this feature)

```text
specs/575-reproduce-long-context-vlm/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── evaluation_run.schema.yaml
│   └── benchmark_result.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── mmlongbench/         # Vendored submodule
├── eval/
│   ├── run_cpu_eval.py  # Entry point for CPU execution (4-bit loading)
│   ├── scaling_analysis.py # Regression and stats logic (Descriptive)
│   └── utils.py         # Memory and data loading helpers
├── data/                # Downloaded datasets (cached)
└── results/             # Output JSON/CSV artifacts

tests/
├── contract/            # Schema validation tests
├── integration/         # End-to-end CPU smoke tests
└── unit/                # Helper function tests
```

**Structure Decision**: The structure isolates the vendored `mmlongbench` code from the reproduction logic (`src/eval/`). This ensures the reproduction scripts can be modified for CPU constraints (4-bit loading) without altering the original paper's codebase. The `contracts/` directory holds the validation schemas for the generated artifacts.

## Execution Phases

### Phase 0: Data Preparation & Verification
- **Goal**: Download and verify the MMLongBench dataset (test split).
- **Action**: Use `datasets.load_dataset("yubo2333/MMLongBench-Doc", split="test")` to fetch data.
- **Validation**: Check that the dataset contains the required fields (`context_length`, `task_type`, `question`, `answer`). Fail fast if missing.
- **Output**: Local cache of the dataset.

### Phase 1: Evaluation Execution
- **Goal**: Run the evaluation pipeline on CPU with 4-bit quantization.
- **Action**: Execute `run_cpu_eval.py` with `--sample-size 10`.
- **Constraint**: Load model using `load_in_4bit=True` (or GGUF) to ensure RAM < 7 GB.
- **Output**: 
  1. `results/evaluation_run.json`: Metadata for the run (matches `EvaluationRun` schema).
  2. `results/sample_results.json`: List of `BenchmarkResult` objects.

### Phase 2: Scaling Analysis (Descriptive)
- **Goal**: Analyze performance trends across context lengths.
- **Action**: Fit a linear regression of `score` vs `log(context_length)`.
- **Constraint**: Explicitly state that n=5 (context lengths) and n=10 (samples) are insufficient for rigorous hypothesis testing.
- **Output**: `results/scaling_report.json` containing slope, R², and a "Descriptive Trend" classification (linear/sublinear) with a disclaimer on statistical power.

### Phase 3: Reporting & Validation
- **Goal**: Generate the final report comparing results to the paper's claims.
- **Action**: Calculate retention rates and effect sizes. Explicitly state that statistical significance cannot be claimed.
- **Output**: Final markdown report summarizing findings and limitations.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Constitution Check passed. | N/A |