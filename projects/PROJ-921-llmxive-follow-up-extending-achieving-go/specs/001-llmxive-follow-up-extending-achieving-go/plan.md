# Implementation Plan: llmXive follow-up: extending "Achieving Gold-Medal-Level Olympiad Reasoning via Simple and Unified S"

**Branch**: `001-llmxive-followup` | **Date**: 2026-07-14 | **Spec**: `specs/001-llmxive-followup/spec.md`
**Input**: Feature specification from `specs/001-llmxive-followup/spec.md`

## Summary

This project investigates whether the "reverse-perplexity" curriculum used to train the SU-01 model for Olympiad-level reasoning inadvertently encodes rigid heuristics that degrade performance on open-ended, ill-structured scientific problems. The technical approach involves a comparative inference pipeline running the SU-01 model and a baseline model on two distinct datasets: a deterministic Math Olympiad benchmark (IMO) and a curated "OpenSci-Reason" dataset (derived from ScienceQA). Responses are scored by a frozen, quantized LLM proxy (Llama-8B-INT4) on dimensions of Novelty, Feasibility, and Consistency. The analysis uses a Linear Mixed Effects (LME) model to isolate the interaction between model type and domain performance, and performs a dimension independence check to validate the scoring proxy. The pipeline is constrained to CPU-only execution on GitHub Actions free-tier runners.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers` (v4.40+), `torch` (CPU-only build), `datasets` (v2.19+), `pandas`, `scipy`, `statsmodels`, `pyyaml`, `huggingface_hub`  
**Storage**: Local file system (JSONL/Parquet), GitHub Actions ephemeral storage (~14 GB)  
**Testing**: `pytest` (unit tests for data parsing, scoring logic, statistical functions)  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner, CPU-only)  
**Project Type**: Research pipeline / CLI  
**Performance Goals**: Complete full inference and analysis within 6 hours; peak RAM usage < 7 GB; no CUDA dependencies.  
**Constraints**: CPU-only inference; strict token limits to prevent timeouts; quantized models (INT4) for scoring to fit RAM; no proprietary data access.  
**Scale/Scope**: ~500 OpenSci prompts (ScienceQA derived), full IMO test set (subset if necessary), N=50 gold standard validation set.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **I. Reproducibility (NON-NEGOTIABLE)**: **PASS**. The plan mandates pinned random seeds in `code/`, canonical dataset sources (verified URLs), and a `requirements.txt` to ensure re-runs on fresh runners yield identical results.
2.  **II. Verified Accuracy**: **PASS**. All dataset citations in `research.md` are restricted to the "Verified datasets" block provided in the prompt. No fabricated URLs will be used. The proxy model validation (FR-008) ensures the scoring mechanism is verified against human gold standards.
3.  **III. Data Hygiene**: **PASS**. The plan includes a checksumming step for all downloaded datasets. Raw data is preserved; derivations (e.g., scored responses) are written to new files with documented hashes.
4.  **IV. Single Source of Truth**: **PASS**. The statistical analysis script will read directly from the generated JSONL files. No manual data entry will occur in the final report.
5.  **V. Versioning Discipline**: **PASS**. The implementation will generate content hashes for all artifacts (datasets, model outputs, analysis results) and update the project state YAML.
6.  **VI. Evaluation of Ambiguity and Creativity**: **PASS**. The scoring pipeline (FR-004, FR-007) explicitly preserves raw semantic outputs (`score.raw_output`, `score.rationale`) and flags low-confidence responses (variance > 1.5, entropy > 2.0) to prevent loss of context regarding "false certainty."
7.  **VII. Inference Constraints and Thermal Stability**: **PASS**. The plan enforces `batch_size=1`, `temperature=0.7`, and explicitly logs `generation_params` (seed, temperature) per-generation in the inference output artifacts to validate thermal stability.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-followup/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-921-llmxive-follow-up-extending-achieving-go/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── download.py           # Handles dataset ingestion from verified URLs
│   │   ├── preprocess.py         # Unified JSONL formatting + ScienceQA prompt conversion
│   │   └── gold_standard.py      # Loader for N=50 human-rated set
│   ├── inference/
│   │   ├── runner.py             # CPU-only inference loop (SU-01 & Baseline)
│   │   └── config.py             # Token limits, seeds, temperature
│   ├── scoring/
│   │   ├── proxy_model.py        # Llama-3-8B-INT4 scoring logic
│   │   └── validator.py          # Correlation check against gold standard
│   ├── analysis/
│   │   ├── stats.py              # LME model, dimension independence, power analysis
│   │   └── report.py             # Generates summary tables/plots
│   └── utils/
│       ├── logging.py            # Audit log for failures/truncations
│       └── checksum.py           # Data hygiene utilities
├── data/
│   ├── raw/                      # Downloaded datasets (checksummed)
│   ├── processed/                # Unified JSONL, scored results
│   └── gold/                     # N=50 human-rated set
├── tests/
│   ├── unit/
│   │   ├── test_preprocess.py
│   │   └── test_stats.py
│   └── integration/
│       └── test_full_pipeline.py
├── requirements.txt
└── pyproject.toml
```

**Structure Decision**: A modular CLI-style structure is selected to separate data ingestion, inference, scoring, and analysis. This aligns with the research pipeline nature of the project, allowing independent testing of each stage (e.g., verifying the scoring model without re-running inference). The `data/` directory strictly separates raw downloads from processed artifacts to satisfy Constitution Principle III.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Dual-dataset approach** | Required to test the specific hypothesis (Olympiad vs. OpenSci). | A single dataset cannot distinguish between "rigid" and "creative" reasoning modes as the hypothesis posits a trade-off. |
| **Proxy LLM Scoring** | Human evaluation is infeasible for CI; automated scoring is required for reproducibility. | Simple keyword matching or binary classification fails to capture the nuance of "Novelty" and "Feasibility" in ill-structured problems. |
| **Quantized Model (INT4)** | Required to fit Llama-3-8B into 7GB RAM on CPU-only runner. | Running a full precision model would cause OOM errors, failing the compute feasibility constraint. |
| **Gold Standard Validation** | Required to ensure the proxy model is not hallucinating scores (FR-008). | Using the proxy model without validation risks measuring model bias rather than actual creativity. |
| **Linear Mixed Effects (LME)** | Required to handle nested data structure (responses within prompts) and test interaction effects. | Simple correlation or t-test fails to account for prompt difficulty variance and circularity of same-model metrics. |


## projects/PROJ-921-llmxive-follow-up-extending-achieving-go/specs/001-llmxive-follow-up-extending-achieving-go/research.md