# Implementation Plan: Evaluating Prompting Strategies for Code Generation

**Branch**: `001-evaluate-prompting-strategies` | **Date**: 2024-05-21 | **Spec**: `specs/001-evaluate-prompting-strategies/spec.md`

## Summary

This project implements a reproducible evaluation pipeline to compare Zero-shot, Few-shot, and Chain-of-Thought (CoT) prompting strategies on the `Salesforce/codegen-350M-mono` model using the MBPP dataset. The system adheres to strict resource constraints (CPU-only, ≤7GB RAM, ≤6h runtime) by processing up to 500 tasks across 3 seeds, generating **k=10 samples per task for ALL strategies**, and enforcing execution timeouts. The output includes pass@k metrics (binary outcome: at least one of k samples passed), statistical significance testing (McNemar's test on paired pass@k outcomes), and resource utilization logs.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers` (CPU-only), `datasets`, `torch` (CPU), `scipy`, `pytest`  
**Storage**: HuggingFace Hub (MBPP), Local Cache (Model weights), JSON files (Results)  
**Testing**: `pytest` (Unit/Integration), Contract validation via YAML schemas  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7GB RAM)  
**Project Type**: CLI / Research Pipeline  
**Performance Goals**: Complete 500 tasks × 3 strategies × 3 seeds (k=10 for ALL) within 6 hours; Peak RAM < 7GB.  
**Constraints**: No GPU/CUDA; No 8-bit/4-bit quantization; Strict execution timeout per task; 500MB sandbox memory limit.  
**Scale/Scope**: ~500 MBPP test tasks; 3 independent seeds; 3 prompting strategies; **k=10 samples per task for Zero-shot, Few-shot, and CoT**.

> Dataset specifics (500 tasks), model precision (FP32 default, fallback FP16), and **uniform k=10 sampling** are derived directly from the Spec and Constitution, corrected to ensure valid statistical pairing.

## Constitution Check

This plan explicitly addresses every numbered principle in the project constitution:

1.  **I. Reproducibility**:
    *   **Implementation**: The pipeline will pin random seeds in `code/` (3 seeds per run).
    *   **Implementation**: MBPP dataset will be fetched via `datasets.load_dataset("google-research-datasets/mbpp")` ensuring canonical source consistency.
    *   **Implementation**: Model weights (`Salesforce/codegen-350M-mono`) will be cached locally; the script will check for existing cache before re-downloading.
2.  **II. Verified Accuracy**:
    *   **Implementation**: All citations in `research.md` and `plan.md` will be restricted to the "Verified datasets" block provided in the prompt. No external URLs will be guessed.
    *   **Implementation**: The `Reference-Validator` gate is integrated as a **blocking CI step** that runs automatically before the `research_accepted` transition. If citations are unreachable or mismatched, the advancement is blocked.
3.  **III. Data Hygiene**:
    *   **Implementation**: Raw MBPP data will be read directly from the HuggingFace cache; no in-place modifications.
    *   **Implementation**: **Checksumming**: Upon dataset download, a SHA-256 checksum will be computed and recorded in the project state YAML (`state/projects/PROJ-028...yaml`). The script verifies this hash before execution.
    *   **Implementation**: Derived results (JSON reports) will be written to new files with checksums recorded in the project state.
    *   **Implementation**: PII scan is assumed to pass as MBPP is a code generation dataset with synthetic problems.
4.  **IV. Single Source of Truth**:
    *   **Implementation**: All statistics (pass@10, p-values) in the final report will be generated programmatically from the JSON result files, not hand-typed.
    *   **Implementation**: Figures (if any) will be generated from the aggregated JSON data.
5.  **V. Versioning Discipline**:
    *   **Implementation**: The `requirements.txt` will pin exact versions of `transformers`, `torch`, etc.
    *   **Implementation**: **Artifact Hashing**: A dedicated utility script will compute SHA-256 hashes for input data and output JSONs post-run and write them to the `state/projects/...yaml` file, ensuring the Advancement-Evaluator can detect stale records.
6.  **VI. Resource Budget Compliance**:
    *   **Implementation**: The code will monitor RAM usage via `psutil` or `resource`. If >6.5GB, it will trigger FP16 fallback or garbage collection.
    *   **Implementation**: Runtime will be logged; a "Resource Constraint Warning" will be emitted if >6h, but execution continues.
    *   **Implementation**: **Structured Logging**: Resource logs (RAM, time) are written to a structured JSON file (`data/logs/resource_log.json`) and a text log (`data/logs/execution.log`) for **every run**, satisfying the "recorded for every run" mandate.
7.  **VII. Execution-Based Validation**:
    *   **Implementation**: Metrics will be calculated strictly via `pass@k` against unit tests in a subprocess sandbox.
    *   **Implementation**: No LLM-based self-evaluation will be used for final scoring.

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluate-prompting-strategies/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── mbpp_task.schema.yaml
│   └── evaluation_result.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
src/
├── cli/
│   └── main.py          # Entry point for running the pipeline
├── evaluation/
│   ├── runner.py        # Core loop: load task -> prompt -> generate -> execute
│   ├── prompts.py       # Templates for Zero-shot, Few-shot, CoT
│   ├── sandbox.py       # Execution wrapper with timeout/memory limits
│   └── metrics.py       # pass@k calculation and aggregation
├── analysis/
│   ├── stats.py         # McNemar's test implementation
│   └── report.py        # JSON to summary report generation
├── models/
│   └── loader.py        # Model loading with FP32/FP16 fallback logic
└── utils/
    └── logging.py       # Resource monitoring and structured logging

tests/
├── contract/
│   └── test_schemas.py  # Validates JSON output against YAML schemas
├── integration/
│   └── test_pipeline.py # End-to-end run on a small subset (e.g., 5 tasks)
└── unit/
    ├── test_prompts.py
    └── test_sandbox.py

requirements.txt
```

**Structure Decision**: A modular CLI structure is selected to separate concerns (prompting, execution, analysis) while keeping the entry point simple for CI. This aligns with the "CLI / Research Pipeline" project type and facilitates unit testing of the sandbox and prompt logic independently.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The scope (500 tasks, 3 strategies, k=10 for all) fits within the defined resource budget using the selected architecture. | N/A |