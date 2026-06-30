# Implementation Plan: Phenomenological AI: First-Person Experience Modeling

**Branch**: `592-phenomenological-ai-first-person-experie` | **Date**: 2026-06-24 | **Spec**: `spec.md`

## Summary

This project implements a computational pipeline to generate and evaluate first-person phenomenological reports from open-source LLMs. The system employs four distinct prompting strategies (Direct, Hypothetical, Comparative, Role-play) to generate a corpus of text using a CPU-tractable model. It then computes three quantitative validity metrics (Internal Consistency via NLI, Semantic Stability via embeddings, Marker Presence via keyword rules) and conducts human qualitative validation.

**Generation Strategy**: The pipeline targets the generation of **[deferred] raw samples** (80 samples × 4 strategies × 20 prompts) using `TinyLlama-1.1B` exclusively for the automated CI pipeline.
- **Primary Execution**: The automated pipeline uses `TinyLlama-1.1B` via `llama-cpp-python` (4-bit GGUF) to ensure feasibility on the GitHub Actions free-tier (2 CPU, ~7GB RAM).
- **Local Reproduction**: The specification's original target models (`Mistral-7B`, `Llama-7B`) are acknowledged as requiring >14GB RAM. They are **excluded** from the automated CI path to prevent OOM/Timeout failures. Users with local hardware (≥16GB RAM) may optionally run these models via a separate script (`code/generation/runner_local.py`), but results from these models are not required for the primary research validity.
- **Analysis Target**: The ANOVA is designed to run on a minimum of **[deferred] valid samples** (128 per condition) to ensure statistical power (80% at α=0.05, MDES f=0.25).

The implementation strictly adheres to CPU-only execution constraints, ensuring reproducibility on free-tier CI environments.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers` (CPU-optimized), `llama-cpp-python` (for GGUF 1.1B models), `sentence-transformers`, `scikit-learn`, `pandas`, `nltk`, `torch` (CPU wheels), `datasets`, `statsmodels`  
**Storage**: Local file system (`data/` for artifacts, `code/` for scripts), CSV/JSON formats  
**Testing**: `pytest` (unit tests for metric logic, integration tests for pipeline flow)  
**Target Platform**: Linux (Ubuntu 22.04) on GitHub Actions free-tier (2 CPU, ~7GB RAM)  
**Project Type**: Computational research pipeline / CLI  
**Performance Goals**: 
- **Target Volume**: [deferred] raw samples (FR-001).
- **Analysis Volume**: Minimum 1,024 valid samples (Power Target).
- **Runtime**: ≤ 6 hours (CI timeout).
- **Memory**: < 6GB per process (sequential model loading).  
**Constraints**: 
- NO GPU, NO CUDA.
- **Model Selection**: `TinyLlama-1.1B` is the **only** model used in the automated pipeline. Larger models are excluded from CI due to RAM constraints (memory requirements exceeding available capacity).
- **Sequential Execution**: NLI and Embedding models are loaded/unloaded sequentially to prevent OOM during analysis.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Justification / Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All seeds pinned in `code/`. Models fetched via HuggingFace IDs or GGUF. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | All citations (phenomenology literature, statistical methods) will be verified against primary sources before inclusion in final artifacts. |
| **III. Data Hygiene** | **PASS** | Raw generations stored in `data/raw/`. Derivations (metrics) in `data/processed/`. Checksums recorded in state file. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in `paper/` will trace to `data/processed/validity_scores.csv`. |
| **V. Versioning Discipline** | **PASS** | Content hashes tracked for all artifacts. State file updated on change. |
| **VI. Phenomenological Validity** | **PASS** | Metrics (NLI, Embeddings, Keywords) strictly follow the three defined criteria. Composite score formula implemented as weighted sum. *Note: Results are valid for the "Small Model Style" condition.* |
| **VII. Human Qualitative Auditing** | **PASS** | Protocol for blind rating and Cohen's κ calculation defined. Thresholds (≥0.6) enforced. |

## Project Structure

### Documentation (this feature)

```text
specs/592-phenomenological-ai-first-person-experie/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── generation_output.schema.yaml
│   ├── validity_scores.schema.yaml
│   └── qualitative_ratings.schema.yaml
└── tasks.md             # Phase 2 output (created later)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Configuration (seeds, paths, model IDs)
├── generation/
│   ├── __init__.py
│   ├── prompt_engineering.py  # Strategy templates
│   ├── runner.py              # Inference loop (CPU-safe, GGUF TinyLlama)
│   ├── runner_local.py        # Optional: 7B model runner for local hardware
│   └── control_corpus.py      # Task: generate_control
├── analysis/
│   ├── __init__.py
│   ├── consistency.py         # NLI pairwise check
│   ├── stability.py           # Embedding cosine similarity
│   ├── markers.py             # Keyword dictionary
│   ├── fdr_correction.py      # Task: Benjamini-Hochberg
│   ├── tukey_hsd.py           # Task: Tukey HSD
│   ├── sensitivity_kappa.py   # Task: Sensitivity analysis (FR-011)
│   ├── stratified_sampler.py  # Task: SC-002 sampling logic
│   └── stats.py               # Wrapper for statistical tasks
├── validation/
│   ├── __init__.py
│   └── human_rater.py         # Interface for qualitative data entry
├── utils/
│   ├── logging.py
│   └── io.py
├── main.py              # Orchestration script
└── requirements.txt     # Pinned dependencies

data/
├── raw/                 # Generated text, seeds, prompts, control corpus
├── processed/           # Validity scores, embeddings, stats
└── qualitative/         # Human ratings, κ values

tests/
├── unit/
│   ├── test_consistency.py
│   └── test_stability.py
└── integration/
    └── test_pipeline.py
```

**Structure Decision**: Single-project Python structure. Separation of concerns between `generation` (data creation), `analysis` (metric computation), and `validation` (human interface) ensures modularity and testability.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **CPU-only inference for TinyLlama (GGUF)** | Spec requires 7B models, but CI has 7GB RAM. 7B models are infeasible. | Using large language models in FP/FP32 is impossible (14-28GB RAM). `llama-cpp-python` with 4-bit GGUF for TinyLlama is the only CPU-safe method that fits the CI box. |
| **Four prompting strategies + 1 model** | Spec requires comparison of strategies. | Reducing strategies would invalidate the ANOVA design (independent variable manipulation). We compare strategies *within* the TinyLlama architecture to test the "Phenomenological Style" hypothesis. |
| **Three distinct validity metrics** | Constitution Principle VI requires all three. | Using a single metric would fail the "Phenomenological Validity" non-negotiable. |
| **Control Corpus Generation** | Required for discriminant validity (methodology-87fdb544). | Without a control, we cannot distinguish 'phenomenological style' from 'general text quality'. |
| **Sequential Model Loading** | Required to prevent OOM during analysis (data_resources-36182768). | Loading NLI and Embedding models simultaneously exceeds 7GB RAM. |

## Task List (High Level)

1. **generate**: Generate [deferred] samples using `TinyLlama-1.1B` (CI-safe).
2.  **generate_control**: Generate a representative set of control technical reports.
3.  **select_validation_sample**: Select 10 reports per condition for human rating (SC-002).
4.  **analyze**: Compute NLI, Stability, Markers.
5.  **run_statistical_tests**: Apply FDR, Tukey HSD, ANOVA (FR-005).
6.  **sensitivity_kappa**: Run sensitivity analysis on κ thresholds (FR-011).
7.  **validate_human**: Collect human ratings and compute Cohen's κ.
8.  **local_7b_run**: (Optional) Script for users with local hardware to run 7B models.
