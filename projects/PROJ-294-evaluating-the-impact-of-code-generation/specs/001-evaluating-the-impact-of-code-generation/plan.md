# Implementation Plan: Evaluating the Impact of Code Generation Models on Code Testability

**Branch**: `001-evaluating-the-impact-of-code-generation` | **Date**: 2026-06-25 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-evaluating-the-impact-of-code-generation/spec.md`

## Summary

This project implements a paired analysis pipeline to evaluate the impact of code generation models (specifically `Salesforce/codegenM-mono` and `CodeLlama` variants) on code testability compared to human reference solutions from the HumanEval benchmark. The technical approach involves downloading a matched subset of HumanEval tasks (selected via stratified sampling), generating code via CPU-trainable models, executing static analysis (`radon`) and dynamic coverage (`pytest --cov`), and performing rigorous statistical hypothesis testing (Wilcoxon Signed-Rank, McNemar, and Permutation Tests for bounded data) with a priori and post-hoc power analysis. The entire pipeline is designed to run on GitHub Actions free-tier runners (CPU-only, constrained memory resources). and produces an automated Markdown report with visualizations and sensitivity analysis.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets`, `torch` (CPU-only), `radon`, `coverage`, `pytest`, `scipy`, `matplotlib`, `jinja2`, `transformers` (CPU-optimized), `requests`  
**Storage**: Local file system (`data/`, `state/`, `results/`)  
**Testing**: `pytest` (for pipeline logic and unit tests), `coverage.py` (for code coverage metrics)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Research CLI / Data Pipeline  
**Performance Goals**: Complete pipeline execution within 6 hours; memory usage < 7GB; no GPU dependency.  
**Constraints**: Must use CPU-only inference; Low-bit quantization for CodeLlamaB only if it fits in available RAM (fallback to CodeLlamaB); exact dataset pinning via SHA.  
**Scale/Scope**: HumanEval tasks; ~ valid paired samples required for statistical power.

### Sampling Strategy
To ensure the A representative set of tasks is selected. and to prevent selection bias (e.g., hard tasks failing more often), the subset is selected via **stratified sampling** based on the distribution of human pass-rates in the full HumanEval set. The HumanEval tasks are divided into quartiles by difficulty (based on historical pass-rates), and a representative subset of tasks is randomly selected from each quartile to form a balanced subset.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Reproducibility** | **PASS** | Plan mandates pinned random seeds, exact dataset commit hashing, and fully automated `code/` execution. `state/artifact_hashes.yaml` tracks artifact hashes. |
| **II. Verified Accuracy** | **PASS** | Plan includes FR-010: Reference-Validator Agent must verify all external URLs/citations **before** `download_data.py` and `generate_code.py` steps. |
| **III. Data Hygiene** | **PASS** | Plan mandates SHA256 checksumming of HumanEval and generated artifacts; raw data preserved; derivations saved as new files. |
| **IV. Single Source of Truth** | **PASS** | All metrics and figures in `results_report.md` will be generated programmatically from `data/analysis/metrics.json` (the designated Single Source of Truth). |
| **V. Versioning Discipline** | **PASS** | Plan requires updating `state/artifact_hashes.yaml` with content hashes for dataset and model artifacts upon completion. |
| **VI. Testability Evaluation** | **PASS** | Plan explicitly defines `radon` and `coverage.py` pipelines for all code samples, storing results in `data/analysis/`. |
| **VII. Benchmark Integrity** | **PASS** | Plan mandates downloading HumanEval directly from HuggingFace without alteration and recording the specific version. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-the-impact-of-code-generation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-294-evaluating-the-impact-of-code-generation/
├── code/
│   ├── __init__.py
│   ├── download_data.py          # HumanEval download + checksum
│   ├── generate_code.py          # LLM generation (CodeGen + CodeLlama)
│   ├── analyze_metrics.py        # Radon + Coverage execution
│   ├── statistical_tests.py      # Wilcoxon, McNemar, Permutation, Power Analysis
│   ├── report_generator.py       # Jinja2 report creation
│   ├── utils.py                  # Logging, retry logic, hashing
│   └── requirements.txt          # Pinned dependencies
├── data/
│   ├── raw/                      # Downloaded HumanEval parquet
│   ├── generated/                # LLM code samples
│   └── analysis/                 # Metrics (JSON/CSV)
├── state/
│   └── artifact_hashes.yaml      # SHA256 tracking
├── results/
│   └── figures/                  # PNGs for report
└── tests/
    ├── unit/
    └── integration/
```

**Structure Decision**: Single project structure (Option 1) is selected. The project is a research CLI pipeline, not a web service or mobile app. All logic is contained within `code/` to ensure reproducibility and ease of CI execution.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Dual Model Strategy (CodeGen + CodeLlama)** | Required by FR-009 for sensitivity analysis to evaluate robustness across model scales. | Using only one model would fail to address the sensitivity analysis requirement and limit the study's generalizability. |
| **Low-bit Quantization Fallback

When the target precision is insufficient, the system will employ a fallback mechanism using reduced-precision quantization to maintain model stability and inference capability, as discussed in related work on model compression (Author et al.,; DOI:.xxxx/xxxx). This approach ensures robustness across varying hardware constraints without compromising the core research question regarding model efficiency under resource limitations.** | Required to fit CodeLlamaB in constrained RAM on CPU

Research question: Can CodeLlamaB be executed within limited memory resources on standard CPU hardware?
Method: Model quantization and memory-efficient inference techniques.
References: [Preserve existing citations as per original document] (if API fails). | Running full precision CodeLlama models would exceed memory limits on the GitHub Actions free tier., causing job failure. |
| **Paired Statistical Design** | Required to control for task difficulty variance between human and LLM solutions. | Unpaired tests would introduce high variance due to task difficulty differences, reducing statistical power. |
| **Stratified Sampling** | Required to ensure the task subset is representative of the full HumanEval difficulty distribution. | Random sampling might over-represent easy or hard tasks, biasing the results if failure rates correlate with difficulty. |
| **Permutation Test for Coverage** | Required for bounded, skewed data (Branch Coverage %). | Wilcoxon Signed-Rank assumes symmetric differences, which is invalid for coverage data with floor/ceiling effects. |

## Pipeline Execution Order

1.  **Pre-Check**: Run Reference-Validator Agent on all citations (FR-010). Abort if any fail.
2.  **Data Download**: Download HumanEval, verify SHA256, store in `data/raw/`.
3.  **Sampling**: Select a representative subset of tasks via stratified sampling (by human pass-rate quartiles).
4.  **Generation (Primary)**: Generate code for a set of tasks using `Salesforce/codegen-350M-mono`.
5.  **Generation (Sensitivity)**: Select a set of disjoint tasks. Generate code using `CodeLlamaB` (via API) or `CodeLlamaB` (fallback).
6.  **Analysis**: Run `radon` and `pytest --cov` on all samples. Log errors.
7.  **Testing**: Run Wilcoxon (complexity/Halstead), Permutation (coverage), McNemar (pass-rate).
8.  **Reporting**: Generate `results_report.md` from `data/analysis/metrics.json`.
9.  **Versioning**: Update `state/artifact_hashes.yaml` with new hashes.

## Data Model Traceability

The plan explicitly maps operational strategies to the data model:
- **Primary Generation**: `source_type` = "codegen-350M"
- **Sensitivity Generation (7B)**: `source_type` = "codellama-7b"
- **Sensitivity Fallback (3B)**: `source_type` = "codellama-3b"
- **Human Reference**: `source_type` = "human"

If the fallback logic triggers (7B -> 3B), the `source_type` field in `data/analysis/metrics.json` will be updated to "codellama-3b" for the affected sensitivity tasks, ensuring the data model accurately reflects the actual model used.

<!-- FILE: plan.md -->