# Implementation Plan: Socratic Transformers (PROJ-582)

**Branch**: `582-socratic-transformers` | **Date**: 2026-06-29 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/582-socratic-transformers/spec.md`

## Summary

This plan implements a research pipeline to test whether **negative selection on belief** (adversarial critique) improves reasoning in language models more than static training or neutral feedback. The system generates three data conditions (Static, Dialogue/Socratic, Ablation) from GSM8K and MATH datasets, fine-tunes a quantized base model using LoRA under strict CPU constraints, and performs statistical analysis comparing accuracy across conditions. The approach strictly adheres to the "selectionist" framing (Krakauer) rather than "self-teaching," treating the critique as an evolutionary pressure filter rather than a pedagogical instruction.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers`, `peft`, `bitsandbytes` (CPU fallback), `datasets`, `scikit-learn`, `pandas`, `pytest`, `ruff`, `pyyaml`.  
**Storage**: Local filesystem (`data/`, `artifacts/`); no external DB.  
**Testing**: `pytest` (unit, integration, contract).  
**Target Platform**: Linux (GitHub Actions Free Tier: limited vCPU, 7GB RAM, 14GB Disk).  
**Project Type**: Research pipeline / CLI.  
**Performance Goals**: Fit within 6h runtime per job; memory < 7GB (4-bit quantization); OOM fallback to smaller models or CPU-only inference.  
**Constraints**: No local GPU; strict reproducibility (random seeds); no gated data access.  
**Scale/Scope**: A range of generated dialogue tuples per condition; fine-tuning on a substantial corpus of examples (sampled if necessary).

## Constitution Check

*GATE: Must pass before initial research. Re-check after design.*

| Principle | Status | Evidence/Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `requirements.txt` pins versions. Random seeds are set in all generators. Datasets fetched via `datasets.load_dataset` from verified URLs. |
| **II. Verified Accuracy** | **PASS** | All dataset URLs in `research.md` are from the verified block. No external citations added without source. |
| **III. Data Hygiene** | **PASS** | `data/download.py` computes SHA-256 checksums. `data/` contains only raw (unchanged) and derived (versioned) files. **No manual data population** (Task T060 removed). All data derived programmatically. `pytest` validates schema compliance per Principle III. |
| **IV. Single Source of Truth** | **PASS** | All metrics in `paper/` trace to `data/results.csv` (validated against `evaluation_result.schema.yaml`). No hand-typed numbers. `ruff` enforces code style for reproducibility (Principle V). |
| **V. Versioning Discipline** | **PASS** | Artifacts hashed in `state/`. `updated_at` timestamps managed by runner. `ruff` enforces code style for reproducibility. |
| **VI. Evaluation Integrity** | **PASS** | Test sets (GSM8K test, MATH test) are strictly separated from training data generation via explicit filtering in `generate_dialogue.py`. No leakage. |
| **VII. Adversarial Quality** | **PASS** | `generate_dialogue.py` includes a validation step to discard trivial/non-adversarial tuples (Critique length < 20 tokens OR Semantic similarity > 0.85) before saving. |

## Project Structure

### Documentation (this feature)

```text
specs/582-socratic-transformers/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── data_tuple.schema.yaml       # SSoT for generated tuples (FR-001, FR-002)
    ├── dataset.schema.yaml          # SSoT for raw datasets (FR-001)
    ├── dialogue.schema.yaml         # SSoT for dialogue tuples (FR-002)
    ├── dialogue_schema.schema.yaml  # Legacy/Alternative (Deprecated)
    ├── dialogue_tuple.schema.yaml   # SSoT for dialogue tuples (Unified)
    ├── evaluation_metrics.schema.yaml # SSoT for aggregated metrics (FR-006)
    ├── evaluation_result.schema.yaml # SSoT for evaluation results (FR-006)
    ├── evaluation_schema.schema.yaml # Legacy/Alternative (Deprecated)
    ├── result.schema.yaml           # Deprecated (Removed in favor of evaluation_result)
    └── stats_schema.schema.yaml     # SSoT for statistical tests (FR-006)
```

### Source Code (repository root)

```text
projects/PROJ-582-socratic-transformers-dialogue-based-sel/
├── code/
│   ├── src/
│   │   ├── data/
│   │   │   ├── download.py          # Fetch & checksum GSM8K/MATH
│   │   │   ├── verify_datasets.py   # Validate checksums & schema (Principle III)
│   │   │   └── generate_dialogue.py # Create Static, Dialogue, Ablation tuples (FR-001, FR-002)
│   │   ├── utils/
│   │   │   ├── config.py            # Config keys (CRITIC_MODEL_ID, etc.)
│   │   │   ├── logging.py           # JSON line logging (Principle III)
│   │   │   ├── metrics.py           # Accuracy, loss, Brier score (FR-006)
│   │   │   └── model_loader.py      # 4-bit quantization loader
│   │   ├── train/
│   │   │   └── run_training.py      # LoRA fine-tuning for A, B, C conditions
│   │   └── eval/
│   │       └── evaluate.py          # Run benchmarks & statistical tests (FR-006)
│   ├── tests/
│   │   ├── contract/                # Schema validation tests (Principle III)
│   │   ├── unit/
│   │   │   ├── test_metrics.py
│   │   │   └── test_logging.py
│   │   └── integration/
│   │       └── test_pipeline.py
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── ruff.toml
├── data/
│   ├── raw/                         # Downloaded datasets (checksummed)
│   └── processed/                   # Generated tuples (Static, Dialogue, Ablation)
└── state/
    └── projects/PROJ-582-...yaml    # Artifact hashes & timestamps
```

**Structure Decision**: Single project structure (`code/`) to minimize overhead. `src/` follows standard modular separation (data, utils, train, eval). `tests/` mirrors `src/` for contract and unit testing.

## Schema Traceability

The following schemas map directly to Functional Requirements:

| Schema File | Functional Requirement(s) | Description |
| :--- | :--- | :--- |
| `data_tuple.schema.yaml` | FR-001, FR-002 | Unified SSoT for generated tuples (Static, Dialogue, Ablation). |
| `dataset.schema.yaml` | FR-001 | Raw dataset structure (GSM8K, MATH). |
| `dialogue_tuple.schema.yaml` | FR-001, FR-002 | **SSoT** for dialogue tuples (Unified). |
| `evaluation_result.schema.yaml` | FR-006 | SSoT for evaluation results (accuracy, runtime). |
| `stats_schema.schema.yaml` | FR-006 | SSoT for statistical test outputs (t-stat, p-value). |
| `evaluation_metrics.schema.yaml` | FR-006 | Aggregated metrics for reporting. |

## Complexity Tracking

> **No violations found.** The scope is strictly limited to FR-001 through FR-008. Tasks addressing external reviewer personas (Turing, Rockmore, Kahneman) that were not in the spec (specifically T064, T065, T066, T067, T068) have been **explicitly deferred** or removed from the immediate implementation plan to prevent scope creep. The plan focuses on the core mechanism: **Negative Selection vs. Static vs. Ablation**. Manual data population tasks (T060) have been removed in favor of programmatic derivation.

## FR-008 Implementation (OOM Fallback)

FR-008 is implemented in **Phase 2: Training** via `src/train/run_training.py`.
- **Mechanism**: The script attempts to load the model with 4-bit quantization. If an `OutOfMemoryError` occurs, it catches the exception, logs the event, and attempts to reload with a smaller model (e.g., `TinyLlama` instead of `Phi-3`) or reduces the batch size to 1.
- **Verification**: A unit test `test_oom_fallback` verifies that the fallback logic triggers and the script continues without crashing.
- **Reference**: See `src/train/run_training.py` -> `try/except` block around `load_model`.

## Data Separation Mechanism

To satisfy Constitution Principle VI (Evaluation Integrity), the `generate_dialogue.py` script enforces strict separation:
1.  **Input Filtering**: The script loads the full GSM8K/MATH datasets but immediately filters out any examples present in the `test` split IDs used for evaluation.
2.  **Generation Scope**: Dialogue generation is restricted to the `train` or `validation` splits only.
3.  **Verification**: A pre-training check (`verify_datasets.py`) confirms that no example IDs from the evaluation set appear in the generated `data/processed/` files.