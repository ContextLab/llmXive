# Implementation Plan: Evaluating the Robustness of LLM-Generated Code to Input Perturbations

**Branch**: `001-evaluating-robustness-llm-code` | **Date**: 2026-07-03 | **Spec**: `specs/001-evaluating-robustness-llm-code/spec.md`
**Input**: Feature specification from `/specs/001-evaluating-robustness-llm-code/spec.md`

## Summary

This project evaluates the robustness of LLM-generated code (StarCoder2-3B) against semantically-preserving input perturbations (synonym substitution, typo injection, syntactic rephrasing) using the HumanEval dataset. The study generates perturbed prompts, validates semantic equivalence via `sentence-transformers/all-MiniLM-L6-v2` (threshold > 0.95), executes generated code in a sandboxed CPU environment, and performs rigorous statistical analysis (McNemar's test with Bonferroni correction, Mixed-Effects Logistic Regression) to quantify pass@1 degradation. The implementation is constrained to free-tier GitHub Actions resources (2 CPU, 7 GB RAM, 6h runtime), requiring 4-bit quantization and strict resource management.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers`, `bitsandbytes` (CPU-optimized build), `sentence-transformers`, `scikit-learn`, `statsmodels`, `pandas`, `numpy`, `datasets`, `timeout-decorator`, `pytest`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/results`), HuggingFace Hub (model/dataset caching)  
**Testing**: `pytest` (unit tests for perturbation logic, integration tests for sandbox execution)  
**Target Platform**: Linux (GitHub Actions Free Tier Runner)  
**Project Type**: Computational Research Pipeline / CLI Tool  
**Performance Goals**: < 6h total runtime, < 7 GB peak RAM, < 30s generation timeout, < 10s execution timeout  
**Constraints**: No GPU; 4-bit quantization required for StarCoder2-3B; strict semantic similarity threshold (0.95); deterministic perturbation application; sandboxed execution with network disabled.  
**Scale/Scope**: 164 HumanEval tasks; up to 3 perturbed variants per task; ~500-600 total inference runs; statistical analysis on binary pass/fail outcomes.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
|-----------|-------------------|-----------------------|
| I. Reproducibility | **PASS** | Random seeds pinned in `code/`; `requirements.txt` with exact versions; HumanEval fetched from canonical HF URL; model weights cached locally with checksum verification. |
| II. Verified Accuracy | **PASS** | All dataset/model URLs in `research.md` sourced exclusively from the "Verified datasets" block; citation validation via `Reference-Validator` agent logic. |
| III. Data Hygiene | **PASS** | Raw data (HumanEval) preserved unchanged; perturbations written to new files with derivation logs; checksums recorded in `state/` artifact map. |
| IV. Single Source of Truth | **PASS** | All figures/stats in final report trace to `data/results/analysis_results.csv`; no hand-typed numbers in paper generation scripts. |
| V. Versioning Discipline | **PASS** | Artifacts carry content hashes; `state/` updated on every run; `current_stage` managed by Advancement-Evaluator. |
| VI. Secure Execution | **PASS** | Sandbox execution via Docker subprocess with `--network none` and `--cap-drop ALL`; 10s timeout enforced per test case. |
| VII. Perturbation Traceability | **PASS** | Perturbation scripts versioned; every output log includes `perturbation_type`, `original_hash`, `similarity_score`, and `candidate_id`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-robustness-llm-code/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-090-evaluating-the-robustness-of-llm-generat/
├── code/
│   ├── __init__.py
│   ├── main.py                  # Entry point for pipeline orchestration
│   ├── data/
│   │   ├── download.py          # HumanEval ingestion
│   │   └── checksum.py          # Data verification
│   ├── perturb/
│   │   ├── generator.py         # Synonym, typo, rephrase logic
│   │   └── validator.py         # Semantic similarity scoring
│   ├── inference/
│   │   ├── model_loader.py      # StarCoder2-3B 4-bit CPU loader
│   │   └── runner.py            # Generation with timeout
│   ├── execution/
│   │   ├── sandbox.py           # Docker-based code execution
│   │   └── parser.py            # Pass/Fail extraction
│   ├── analysis/
│   │   ├── statistics.py        # McNemar, Bonferroni, Mixed-Effects
│   │   └── sensitivity.py       # Threshold sweep analysis
│   └── utils/
│       ├── logging.py           # Structured logging
│       └── config.py            # Hyperparameters & seeds
├── data/
│   ├── raw/                     # HumanEval parquet (immutable)
│   ├── processed/               # Perturbed prompts, similarity scores
│   └── results/                 # Inference logs, analysis outputs
├── tests/
│   ├── unit/                    # Perturbation logic, timeout handling
│   ├── integration/             # End-to-end sandbox execution
│   └── contract/                # Schema validation tests
├── requirements.txt             # Pinned dependencies
└── README.md                    # Quickstart guide
```

**Structure Decision**: Single project structure with modular subdirectories (`data`, `perturb`, `inference`, `execution`, `analysis`) to enforce separation of concerns and facilitate unit testing of individual pipeline stages. This aligns with the computational research nature and simplifies reproducibility.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*No violations detected. Complexity is justified by the rigorous statistical requirements (McNemar, Mixed-Effects) and the CPU-only constraint necessitating 4-bit quantization and careful memory management.*
