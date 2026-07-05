# Implementation Plan: Socratic Transformers: Dialogue-Based Self-Teaching Through Adversarial Questioning

**Branch**: `582-socratic-transformers-dialogue-based-sel` | **Date**: 2026-06-30 | **Spec**: `specs/582-socratic-transformers-dialogue-based-sel/spec.md`

## Summary

This project implements a comparative study of static QA training versus "Socratic" training, where a model generates its own adversarial dialogues (question, initial answer, critique, revised answer) to refine its reasoning. The core intervention is a negative selection mechanism where the model identifies logical contradictions in its own output, aligning with Turing's "child-machine" education via reward/punishment and Krakauer's "negative selection" on belief. The plan ensures strict adherence to free-tier CI constraints (CPU-only, ≤7GB RAM) by utilizing a B parameter model (Phi-1.5) with 4-bit quantization and LoRA.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers`, `peft`, `bitsandbytes` (CPU backend), `datasets`, `scikit-learn`, `pandas`, `pytest`  
**Storage**: Local filesystem (JSONL/Parquet), GitHub Actions ephemeral storage  
**Testing**: `pytest` (unit/contract), integration tests via CI workflow  
**Target Platform**: Linux (GitHub Actions free-tier, 2 vCPU, 7GB RAM)  
**Project Type**: Research/Experimental ML Pipeline  
**Performance Goals**: Complete 10-seed experiment (conditions) within 6h/job; OOM-free execution  
**Constraints**: No GPU; strict memory limits; 4-bit quantization mandatory for >1B models; multiple-comparison correction required  
**Scale/Scope**: A representative set of samples per seed (downsampled from GSM8K/MATH); Multiple training conditions (Static, Socratic, Ablation)

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Status | Action/Notes |
|-----------|-------------------|--------------|
| **I. Reproducibility** | **Compliant** | All random seeds pinned in `code/`; datasets fetched via canonical HuggingFace loaders; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **Compliant** | All citations in `research.md` map to the "Verified datasets" block or primary literature (Turing, Kahneman & Tversky /1974). No invented URLs. |
| **III. Data Hygiene** | **Compliant** | Raw data (GSM8K/MATH) downloaded once; derivations (dialogue tuples) written to new files with checksums recorded in `state/`. No in-place modification. |
| **IV. Single Source of Truth** | **Compliant** | All metrics in `paper/` will be derived programmatically from `data/` via `code/` scripts. No hand-typed stats. |
| **V. Versioning Discipline** | **Compliant** | Artifacts hashed on write; `state/` updated on change. |
| **VI. Evaluation Integrity** | **Compliant** | Test splits (GSM8K test, MMLU STEM) strictly separated from training generation loops. |
| **VII. Adversarial Dialogue Quality Gate** | **Compliant** | Enforced in `src/data/generate_dialogue.py` via `n-gram overlap > 0.9` check and `DEGENERATE_DIALOGUE_TRUNCATED` logging; trivial dialogues discarded. |

## Project Structure

### Documentation (this feature)

```text
specs/582-socratic-transformers-dialogue-based-sel/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── download.py          # Fetches GSM8K/MATH
│   │   ├── generate_dialogue.py # Creates Socratic tuples (FR-001, FR-002); includes degenerate check (Principle VII)
│   │   └── ablation.py          # Creates neutral reasoning traces (FR-007)
│   ├── train/
│   │   ├── lora_config.py       # LoRA params (FR-003)
│   │   └── train_loop.py        # CPU-safe training with 4-bit (FR-003, FR-008)
│   ├── eval/
│   │   └── benchmark.py         # GSM8K/MMLU evaluation (FR-004)
│   ├── analyze/
│   │   └── stats.py             # Welch's t-tests, Bonferroni (FR-006)
│   └── utils/
│       ├── logging.py           # Structured logs (Edge Cases)
│       └── metrics.py           # Prediction error proxy (Assumptions)
└── tests/
    ├── contract/
    │   └── test_schemas.py      # Validates JSONL against contracts/
    └── unit/
        └── test_generation.py   # Verifies dialogue structure
```

**Structure Decision**: Single project structure (`src/` submodules) to minimize overhead and simplify dependency management for the constrained CI environment. All scripts are runnable end-to-end.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **4-bit Quantization + LoRA** | 7GB RAM limit on free-tier; full 1.5B model FP16 exceeds memory. | FP16 training causes OOM; CPU-only 8-bit is not supported by `bitsandbytes` on CPU in all versions, 4-bit is the verified path. |
| **Ablation Condition** | Required to isolate the "critique" signal from mere "extra text". | Training on just "Question+Answer" doesn't prove the *adversarial* nature of the Socratic method; neutral reasoning trace controls for token count and process simulation. |
| **Multiple Seeds (10)** | Required for statistical power (FR-005) and robustness to initialization variance. | Single-seed results are anecdotal and fail reproducibility standards (Constitution I). |
| **Degenerate Dialogue Detection** | Prevents training on noise (repetitive loops) which degrades model performance. | Without detection, the model learns to repeat itself, violating the "negative selection" principle (Constitution Principle VII). |