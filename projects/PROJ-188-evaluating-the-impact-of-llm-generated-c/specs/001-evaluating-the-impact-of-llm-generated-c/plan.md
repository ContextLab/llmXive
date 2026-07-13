# Implementation Plan: Evaluating the Impact of LLM-Generated Code Explanations on Comprehension

**Branch**: `001-eval-llm-code-explanations` | **Date**: 2024-05-22 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-eval-llm-code-explanations/spec.md`

## Summary

This project implements a computational study to evaluate the impact of LLM-generated code explanations on programmer comprehension. The system ingests Python functions from the CodeSearchNet corpus, generates explanations using the CodeLlama model (quantized for CPU, with fallback to TinyLlama), constructs a three-arm experimental survey (Code Only, Code+LLM, Code+Docstring), collects response accuracy and latency data, and performs a Generalized Linear Mixed Model (GLMM) analysis with sensitivity checks on BLEU similarity. The implementation is constrained to run on a GitHub Actions CPU-only runner (limited cores, restricted RAM, 6h limit).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers`, `torch` (CPU), `scikit-learn`, `statsmodels`, `pandas`, `numpy`, `sacrebleu`, `datasets`, `pyyaml`  
**Storage**: Local JSON/CSV/Parquet files in `data/` directory  
**Testing**: `pytest` for unit tests; synthetic data validation for analysis scripts  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner)  
**Project Type**: Computational research pipeline (data generation, survey logic simulation, statistical analysis)  
**Performance Goals**: Complete inference and analysis within 6 hours; memory usage < 7GB; handle N=30 snippets and ~90 participants.  
**Constraints**: No GPU; no deep network training; strict token limits (constrained); CPU-only quantization for CodeLlama

The research question is to evaluate the effectiveness of open-source large language models in code generation tasks. The method involves fine-tuning and benchmarking against standard coding datasets. References: Rozière et al. (2023).; deterministic seeds.  
**Scale/Scope**: A set of code snippets; experimental conditions; A sample of participants (simulated/recruited data).

> **Model Fallback Strategy**: The spec requests CodeLlamaB (-bit). However, loading a large language model on a CPU runner with limited RAM is high-risk for OOM. This plan implements a fallback: if CodeLlama-7B fails to load or exceeds memory/time thresholds, the system will automatically switch to **TinyLlama

The research question is: How can parameter-efficient fine-tuning be optimized for small-scale language models? The method involves conducting a comparative analysis of fine-tuning strategies across various model architectures. References: Zhang et al. (2023).** (a verified CPU-tractable model) to ensure the job completes within the designated time limit. The fallback will be logged, and results will be interpreted with the caveat of the model change.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned.. External datasets fetched from canonical HuggingFace URLs. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | Dataset URLs cited only from the "Verified datasets" block. No fabricated URLs. |
| **III. Data Hygiene** | **PASS** | Raw data will be checksummed. Derivations (cleaning, analysis) produce new files. No in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All stats trace to `data/` files. No hand-typed numbers in reports. |
| **V. Versioning Discipline** | **PASS** | Artifacts will carry content hashes. State updated on change. |
| **VI. Human-Subject Data Integrity** | **PASS** | Participant data anonymized (IDs only). Cleaning rules (time-based filter) applied via scripts. |
| **VII. Controlled Explanation Generation** | **AMENDMENT_REQUIRED** | **Conflict**: The Constitution mandates **StarCoder-15B** (200 tokens). The active `spec.md` mandates **CodeLlama-7B** (150 tokens). The plan follows the `spec.md` (CodeLlama-7B, 150 tokens) as the immediate implementation target. This constitutes a violation of Principle VII until the Constitution is formally amended to align with the spec. **Action**: Flagged for kickback to update Constitution or Spec. |

## Project Structure

### Documentation (this feature)

```text
specs/001-eval-llm-code-explanations/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-188-evaluating-the-impact-of-llm-generated-c/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── 01_data_curation.py       # Ingest CodeSearchNet, generate explanations
│   ├── 02_survey_logic.py        # (Simulation) Randomization, condition assignment
│   ├── 03_analysis.py            # GLMM, Tukey, Sensitivity Sweep
│   └── utils/
│       ├── config.py             # Seeds, paths, constants
│       └── metrics.py            # BLEU calculation, latency parsing
├── data/
│   ├── raw/                      # Downloaded CodeSearchNet parquet
│   ├── intermediate/             # Generated explanations, survey logs
│   └── processed/                # Cleaned analysis dataset
└── tests/
    ├── test_curation.py
    └── test_analysis.py
```

**Structure Decision**: Single `code/` directory with modular scripts following the computational pipeline order (Data -> Survey -> Analysis) to ensure strict dependency ordering and reproducibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **CodeLlama-7B (with Fallback)** | Required by spec (FR-001) for high-quality code explanation. | Using a smaller model (e.g., TinyLlama) would violate the spec's "LLM-generated" quality requirement *unless* the 7B model fails on CPU. The fallback ensures completion. |
| **GLMM with SnippetID Random Effect** | Required for statistical rigor (addressing methodology concerns). The model must account for the non-independence of repeated measures on the same snippet. | A simple LMM with only ParticipantID random intercepts is statistically invalid for this design (confounds Snippet and Complexity effects). |
| **BLEU Sensitivity Sweep** | Required by spec (FR-006) to assess robustness. | Single-point evaluation ignores the instability of BLEU as a fidelity metric. |
