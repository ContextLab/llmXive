# Implementation Plan: llmXive follow-up: extending "Blind-Spots-Bench"

**Branch**: `001-blind-spots-order-analysis` | **Date**: 2026-08-12 | **Spec**: `specs/001-blind-spots-order-analysis/spec.md`
**Input**: Feature specification from `specs/001-blind-spots-order-analysis/spec.md`

## Summary

This project extends the "Blind-Spots-Bench" evaluation by analyzing the temporal ordering of constraint mentions in Chain-of-Thought (CoT) traces. The technical approach involves downloading the specific "Abstract Reasoning" and "Object-Centric" subsets of the benchmark, generating deterministic CoT traces using a 4-bit quantized mid-sized LLM (Llama-3-8B or Mistral-7B) on a CPU runner, parsing traces for first/last constraint mentions (with semantic equivalence checks), and applying a rule-based classifier to distinguish Perceptual vs. Procedural errors. The analysis concludes with a Chi-squared or Fisher's exact test to determine if error distribution is task-dependent, explicitly framing results as associational.

**Critical Methodological Correction**: The outcome variable (Error/Correct) is defined by **independent ground truth** (final answer correctness against a gold label), NOT by the temporal pattern itself. The temporal pattern (First/Last mention) is the **predictor**. This avoids tautological definitions where the predictor defines the outcome.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets` (Hugging Face), `transformers` (CPU mode), `sentence-transformers` (semantic matching), `scikit-learn`, `pandas`, `numpy`, `statsmodels` (for Fisher's exact test).  
**Storage**: Local file system (`data/` for raw/filtered data, `code/` for scripts).  
**Testing**: `pytest` (unit tests for parser/classifier, integration tests for data flow).  
**Target Platform**: GitHub Actions CPU runner (2 cores, ~7 GB RAM).  
**Project Type**: Research pipeline / CLI tool.  
**Performance Goals**: End-to-end analysis < 6 hours; per-task inference < 10 minutes; peak RAM < 7 GB.  
**Constraints**: No local GPU; 4-bit quantization mandatory for LLM; deterministic generation (temp=0.0); strict data integrity checks on ingestion.  
**Scale/Scope**: Subset of Blind-Spots-Bench (Abstract Reasoning + Object-Centric); **Minimum Viable Sample Size (MVS)**: 40 tasks (20 per category). If the effective sample size falls below MVS after filtering/timeouts, the study halts and reports "Underpowered".

> **Memory & Compute Strategy**: Low-bit quantized Llama models (compact weights) leaves <1 GB for OS/Python/Context, creating high OOM risk.
> 1.  **Primary Path**: Run 4-bit model with `device_map="auto"` and offloading to CPU. If OOM, fallback to a smaller 7B model (e.g., Mistral-7B-Int4) or reduce context window.
> 2.  **GPU Escape Hatch**: If CPU execution fails repeatedly (OOM or timeout) or exceeds time limits, the execution stage will offload to a **fixed-seed** Kaggle GPU run. This is **not** an automatic variable dependency; the seed is pinned to ensure reproducibility regardless of hardware. The plan explicitly documents this fallback mechanism and trigger conditions. The same code path is executed on the GPU, ensuring that the result is reproducible if the hardware changes, provided the seed is fixed.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Plan mandates pinned seeds, explicit `requirements.txt`, and CI-based re-runs. GPU fallback uses fixed seeds. |
| **II. Verified Accuracy** | PASS | Plan restricts dataset sources to verified URLs only (no fabricated links). |
| **III. Data Hygiene** | PASS | Plan includes checksumming raw data and separating raw/filtered files. Parsing operates on **copies** of raw files. |
| **IV. Single Source of Truth** | PASS | `statistical_report.json` is explicitly designated as the SSoT for all statistical results. |
| **V. Versioning Discipline** | PASS | Task T024 ensures content hashes for `statistical_report.json` and `data/` are recorded in the project state file. |
| **VI. CoT Trace Integrity** | PASS | Raw traces are preserved in `data/traces/` unmodified; parsing operates on copies. |
| **VII. Rule-Based Classification** | PASS | Classifier is strictly rule-based and deterministic; no learned parameters. |

## Project Structure

### Documentation (this feature)

```text
specs/001-blind-spots-order-analysis/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── trace.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── acquire.py       # Download and filter Blind-Spots-Bench
│   ├── integrity.py     # Checksum and constraint validation
│   └── pilot.py         # Pilot study for threshold validation
├── inference/
│   ├── generate.py      # LLM CoT generation (CPU, 4-bit)
│   └── parse.py         # Constraint mention parser (exact + semantic)
├── analysis/
│   ├── classify.py      # Rule-based error classifier (outcome vs pattern)
│   └── stats.py         # Chi-squared/Fisher test + reporting
├── utils/
│   ├── config.py        # Path config and seed management
│   └── logging.py       # Structured logging
└── main.py              # Orchestration script

tests/
├── unit/
│   ├── test_parser.py
│   └── test_classifier.py
└── integration/
    └── test_pipeline.py

data/
├── raw/                 # Downloaded raw dataset
├── filtered/            # Abstract Reasoning + Object-Centric subset
├── traces/              # Generated CoT traces (RAW, unmodified)
├── parsed/              # Parsed traces (copies)
└── reports/             # Statistical reports
```

**Structure Decision**: Single project structure selected to minimize overhead for a research pipeline. `src/` is split by functional domain (data, inference, analysis) to enforce separation of concerns and facilitate parallel development of components (e.g., parsing logic while inference is running).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Semantic Equivalence Check** | Constraint paraphrasing is common in CoT; exact string matching yields high false-negative rates for "Perceptual Errors". | Simple string matching was rejected as it would fail to detect valid constraints rephrased by the model, violating the accuracy of the error classification. |
| **4-bit Quantization** | Full precision models exceed 7 GB RAM on CPU; 8-bit may still be risky for larger context windows. | Running on a GPU-only runner was rejected to ensure reproducibility on standard CI; CPU-only execution is mandatory per spec constraints. |
| **Fisher's Exact Fallback** | Sample sizes for specific sub-categories may be < 5, violating Chi-squared assumptions. | Relying solely on Chi-squared was rejected as it produces invalid p-values for small counts, risking statistical rigor. |
| **Pilot Study (Threshold Validation)** | Arbitrary similarity thresholds (0.85) risk construct validity. | No pilot study was rejected because it would leave the semantic matching logic unvalidated, potentially biasing results. |

## Implementation Phases & Tasks

### Phase 0: Data Acquisition & Integrity (US-1)
*   **T001**: Download raw dataset to `data/raw/`.
*   **T002**: Filter for "Abstract Reasoning" and "Object-Centric" to `data/filtered/`.
*   **T003**: **Dataset Integrity Check (FR-006)**: Scan `data/filtered/` for missing `constraint` fields. If any found, **HALT** execution, log missing IDs, and report `Dataset Integrity Error`.
*   **T004**: Calculate checksums and update project state.

### Phase 0.5: Pilot Study & Threshold Validation (Methodology Fix)
*   **T005**: Generate CoT traces for a small pilot set (N=10).
*   **T006**: **Human Validation**: Experts label the pilot set for "Task Outcome" (Correct/Incorrect) and "Constraint Mention" (Yes/No).
*   **T007**: **Threshold Tuning**: Iterate cosine similarity threshold (range) to maximize agreement between automated semantic match and human labels. Select optimal threshold.

### Phase 1: CoT Generation (US-2)
*   **T008**: Load filtered dataset.
*   **T009**: Run LLM inference (4-bit, temp=0.0) with a fixed timeout duration per task (a predefined interval).
*   **T010**: **Memory Guard**: If OOM, fallback to smaller model (Mistral-7B) or reduce context.
*   **T011**: Save raw traces to `data/traces/` (unmodified).
*   **T012**: **Stopping Rule Check**: If effective sample size < 40 (MVS), halt and report "Underpowered".

### Phase 2: Parsing & Classification (US-2, US-3)
*   **T013**: Load raw traces and task records.
*   **T014**: **Parsing**: Identify first/last constraint mentions. "First step" is defined as the first 256 tokens; "Last step" is the last 256 tokens.
*   **T015**: **Semantic Matching**: Apply tuned threshold from T007.
*   **T016**: **Classification (Non-Tautological)**:
    *   **Predictor**: Temporal Pattern (Present in First & Last, Present in First Only, etc.).
    *   **Outcome**: Task Outcome (Correct/Incorrect) derived from `ground_truth` field in dataset.
    *   **Label**: Map (Pattern, Outcome) to "Perceptual", "Procedural", or "Correct" based on the hypothesis.

### Phase 3: Statistical Analysis (US-3)
*   **T017**: **Test Selection**: Check expected cell counts. If < 5, select Fisher's Exact; else Chi-squared.
*   **T018**: **Multiple Comparison Correction**: Apply Bonferroni if >1 test is run (FR-008).
*   **T019**: Compute p-value and statistic.
*   **T020**: **Framing Injection**: Explicitly set `framing` field to "Associational" in the output (FR-007).
*   **T021**: Generate `statistical_report.json` (SSoT).

### Phase 4: Validation & Reporting
*   **T022**: **Human Validation (FR-010, SC-006)**: Sample a representative proportion of traces. Experts label the *Task Outcome* (Correct/Incorrect) independently. Compare automated labels to human labels. Report agreement rate (Target ≥ 85%).
*   **T023**: Generate final paper sections.
*   **T024**: **State Update (Principle V)**: Hash `statistical_report.json` and `data/` artifacts, write to project state YAML.

### Phase 5: Consistency Check
*   **T025**: **Deterministic Consistency Check**: Implement script to run deterministic consistency check on the final outputs to ensure reproducibility.
