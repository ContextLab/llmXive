# Implementation Plan: Quantifying Hallucination in LLM-Generated API Documentation

**Branch**: `001-quantify-hallucination` | **Date**: 2026-06-22 | **Spec**: `specs/001-quantify-hallucination/spec.md`
**Input**: Feature specification from `/specs/001-quantify-hallucination/spec.md`

## Summary

This project implements a reproducible pipeline to quantify hallucination in LLM-generated API documentation. The system ingests the CodeSearchNet Python dataset, generates descriptions using `codegen-350M` and `starcoderbase-1b` on CPU, and computes a composite hallucination index based on entity-overlap F1 scores against source code ASTs. It performs statistical correlation analysis (Spearman, Mann-Whitney U, Multiple Linear Regression) between hallucination and code characteristics (length, naming, complexity), applies multiplicity corrections, and validates the automated metric against a manual human-annotated subset. The pipeline is designed to run within GitHub Actions free-tier constraints (2 CPU, ~7GB RAM, 6h limit).

**Key Methodological Corrections**:
1.  **Independence of Validation**: The manual rubric (FR-009) now scores "Behavioral Consistency" (logic, side effects) rather than "AST Matching", ensuring the human ground truth is independent of the automated AST-based metric.
2.  **Avoidance of Mathematical Coupling**: The regression model (FR-008) controls for `source_code_token_count` instead of `generated_description_token_count` to avoid coupling the covariate with the dependent variable.
3.  **Metric Decomposition**: The "Hallucination Index" is split into "Precision Hallucination" (invented entities) and "Recall Omission" (missing entities) to distinguish between distinct phenomena.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers`, `torch` (CPU-only), `datasets`, `spacy`, `radon`, `pandas`, `scikit-learn`, `numpy`, `seaborn`, `matplotlib`  
**Storage**: Local filesystem (CSV/JSON/Parquet) within `data/` and `results/` directories  
**Testing**: `pytest` with contract validation against YAML schemas  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data science research pipeline / CLI  
**Performance Goals**: Process 1000 functions within 6 hours; memory usage < 7GB  
**Constraints**: CPU-only execution for generation; no external API keys; strict random seed pinning for reproducibility  
**Scale/Scope**: A representative set of functions sampled from CodeSearchNet; % manual validation subset

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence/Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates `config.py` (T008a) AND explicit `torch.manual_seed`, `numpy.random.seed`, `random.seed` calls in `generate.py` and `analyze.py` (T008b). All data fetches use canonical Hugging Face URLs. |
| **II. Verified Accuracy** | **PASS** | All dataset citations restricted to the `# Verified datasets` block (CodeSearchNet parquet URLs). No fabricated URLs. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of downloaded parquet files before processing. Raw data preserved; derivations written to new files. |
| **IV. Single Source of Truth** | **PASS** | Final report (JSON/CSV) is the sole source for statistics. No hand-typed numbers in `paper.md` (future phase). |
| **V. Versioning Discipline** | **PASS** | `state/` artifact hashes updated upon data generation and analysis completion. |
| **VI. Metric Alignment** | **PASS** | Plan includes T030b (Interface), T030c (Human Annotation), and T032 (Correlation Check) to validate the entity-overlap F1 metric against an independent behavioral rubric (FR-009). |
| **VII. Code-Metric Isolation** | **PASS** | Plan mandates running the full pipeline for *both* models (`codegen-350M`, `starcoderbase-1b`) and comparing regression coefficients to isolate model-specific variance. |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantify-hallucination/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── analysis_result.schema.yaml
│   └── manual_score.schema.yaml
└── tasks.md             # Phase 2 output (not created by this command)
```

### Source Code (repository root)

```text
projects/PROJ-762-quantifying-hallucination-in-llm-generat/
├── code/
│   ├── __init__.py
│   ├── config.py              # Seeds, model paths, thresholds
│   ├── download.py            # Fetch CodeSearchNet parquet
│   ├── generate.py            # LLM generation + entity extraction
│   ├── analyze.py             # Stats, regression, sensitivity
│   ├── validate.py            # Manual validation interface logic
│   └── main.py                # Orchestration
├── data/
│   ├── raw/                   # Downloaded parquet files
│   ├── processed/             # Generated CSVs with metrics
│   └── manual/                # Manual validation CSVs
├── results/
│   ├── performance_log.json   # Memory/time metrics
│   └── final_report.json      # Correlation/regression results
├── tests/
│   ├── contract/              # Schema validation tests
│   └── integration/           # End-to-end pipeline tests
└── requirements.txt
```

**Structure Decision**: Single-project structure (Option 1) chosen as this is a linear data processing pipeline. Separation of `download`, `generate`, `analyze`, and `validate` ensures modularity and testability. `data/` is strictly for inputs/intermediates; `results/` for final outputs.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Two Model Runs** | Constitution Principle VII requires comparing `codegen-350M` and `starcoderbase-1b` to isolate model-specific variance. | Running a single model would conflate code characteristics with model bias, failing the isolation requirement. |
| **Manual Validation Step** | Constitution Principle VI and FR-009/SC-003 require human-in-the-loop verification of the entity-overlap metric against an independent behavioral ground truth. | Purely automated metrics (BLEU/ROUGE) are known to correlate poorly with factual accuracy in code; human scoring is mandatory for validity. |
| **CPU-Only Constraint** | Target platform is GitHub Actions free-tier (no GPU). | GPU-based models (e.g., Llama-2-7B) would exceed memory limits and fail the compute feasibility gate. |
| **Behavioral Rubric** | To avoid circular validation, the human rubric must measure "Behavioral Consistency" (logic, side effects) rather than "AST Matching". | A rubric based on AST matching would be tautological with the automated metric. |

## Tasks (Updated to Address Gaps)

*   **T008a**: Create `config.py` with model paths and seed values.
*   **T008b**: **Implement Seeding Logic** - Inject `torch.manual_seed`, `numpy.random.seed`, and `random.seed` calls into `generate.py` and `analyze.py` to ensure deterministic execution (Addresses Spec Coverage concerns).
* **T030a**: Implement sampling logic for the [deferred] validation subset.
*   **T030b**: **Generate Manual Annotation Interface** - Create the CSV template and simple CLI tool for human annotators to input scores based on the revised "Behavioral Consistency" rubric.
*   **T030c**: **Execute Human Annotation** - Produce the `manual_scores.csv` artifact with real human scores (or a flagged placeholder for CI testing that is replaced by real data for final results). This task is the producer of the ground truth data for T032.
*   **T032**: Implement correlation logic between automated F1 and manual scores, including the `r >= 0.7` flag.
*   **T039**: **Run Performance Validation** - Execute `quickstart.md` steps on a fresh environment, measure max RAM and total time for 1000 functions, and **assert** `max_memory_mb < 7168` and `total_time_sec < 21600`, recording metrics in `results/performance_log.json`.

## Data Flow

1.  **Raw Data**: `data/raw/*.parquet` (CodeSearchNet)
2.  **Processed Data**: `data/processed/records.csv` (FunctionRecord with F1 scores)
3.  **Manual Data**: `data/manual/scores.csv` (ManualScoreRecord) - Produced by T030c.
4.  **Final Report**: `results/final_report.json` (AnalysisResult)

## Constraints

- **Null Handling**: Missing docstrings are filtered out. Missing complexity metrics are set to `NaN` and excluded from regression.
- **Range**: `entity_f1` and `human_score_norm` are strictly in $[0.0, 1.0]$.
- **Uniqueness**: `id` must be unique across all records.
- **Reproducibility**: All random seeds are pinned in `generate.py` and `analyze.py` (T008b).
- **Independence**: The manual rubric (FR-009) is explicitly defined to measure behavioral consistency, independent of the AST-based automated metric.
- **No Coupling**: Regression covariates exclude `generated_description_token_count` to avoid mathematical coupling.