# Implementation Plan: Socratic Transformers (PROJ-582)

**Branch**: `582-socratic-transformers` | **Date**: 2026-06-29 | **Spec**: [link]
**Input**: Feature specification from `specs/582-socratic-transformers/spec.md`

## Summary

This project implements a selectionist framework for improving LLM reasoning, replacing "self-teaching" with **negative selection on belief**. The system generates reasoning traces, applies an adversarial critique to identify logical errors (simulating thymic selection), and fine-tunes a base model using LoRA to reject these "failed" belief states. We compare three conditions: **Selection** (adversarial critique), **Ablation** (syntactic distractor matched for complexity), and **Static** (no critique). The implementation strictly adheres to free-tier CPU constraints (4-bit quantization, streaming data) and rigorous statistical analysis (Bonferroni-corrected independent t-tests) to isolate the effect of the selection signal.

## Technical Context

**Language/Version**: Python  
**Primary Dependencies**: `transformers`, `peft`, `bitsandbytes`, `datasets`, `scikit-learn`, `pandas`, `pytest`, `ruff`, `black`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/results`); no external DB.  
**Testing**: `pytest` (unit tests for data pipelines, integration tests for training loops).  
**Target Platform**: Linux (GitHub Actions free-tier: multiple CPUs, sufficient RAM).  
**Project Type**: Research CLI / Data Processing Pipeline  
**Performance Goals**: Complete end-to-end pipeline (download -> generate -> train -> eval) within 6 hours on CPU; memory footprint < 7GB.  
**Constraints**: 
- **CPU-First**: All training must use low-bit quantization (`bitsandbytes`) and LoRA to fit in constrained memory environments.
- **No GPU Dependency**: If a step fails on CPU due to OOM, the execution stage auto-offloads to a Kaggle GPU (scaled down: fewer epochs, smaller batch size). The plan does not assume auto-offload; it relies on the execution stage's error handling.
- **Data Integrity**: All datasets streamed or sampled to fit memory; no full dataset loading if >7GB.
- **Reproducibility**: Fixed seeds, checksummed data.
- **Hard Timeouts**: All training tasks enforce a bounded max runtime via signal handlers.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

- **I. Reproducibility**: 
  - `requirements.txt` pins all dependencies.
  - `random.seed(42)` and `numpy.random.seed(42)` enforced in `src/utils/config.py`.
  - Data checksums recorded in `state/` manifest.
- **II. Verified Accuracy**: 
  - All dataset URLs sourced strictly from the `# Verified datasets` block (GSMK: `openai/gsm8k`, MATH: `hendrycks/math`).
  - Citations in `research.md` validated against primary sources.
  - **Implementation**: Phase 0 includes a `verify_datasets.py` script (T010) that fetches checksums from the verified block and validates raw files before processing.
- **III. Data Hygiene**: 
  - `data/raw/` immutable; `data/processed/` contains derived artifacts with new filenames.
  - PII scan enforced via pre-commit hook (conceptual; implementation in `code/`).
- **IV. Single Source of Truth**: 
  - Evaluation results written to `data/results/metrics.json`; paper figures generated directly from this file.
- **V. Versioning**: 
  - Content hashes tracked in `state/` YAML.
- **VI. Evaluation Integrity**: 
  - Test sets (GSM8K test, MMLU STEM) are strictly separated from training generation loops.
- **VII. Adversarial Dialogue Quality Gate**: 
  - **Criteria**: `src/data/generate_dialogue.py` enforces:
    1. Critique length > 20 tokens.
    2. Critique must contain logical keywords (e.g., "contradiction", "error", "incorrect").
    3. Critic Model confidence score > 0.6.
  - Dialogues failing these criteria are discarded and regenerated.

## Project Structure

### Documentation (this feature)

```text
specs/582-socratic-transformers/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Schema definitions)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-582-socratic-transformers-dialogue-based-sel/
├── code/
│   ├── requirements.txt
│   ├── pyproject.toml   # Black/Ruff config
│   ├── ruff.toml
│   ├── src/
│   │   ├── __init__.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── config.py        # Seeds, paths, global constants
│   │   │   ├── logging.py       # Structured logging
│   │   │   └── model_loader.py  # 4-bit model loading logic
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   ├── download.py      # GSM8K/MATH streaming/download
│   │   │   ├── static_extractor.py # Static QA tuple generation
│   │   │   ├── generate_dialogue.py # Adversarial critique generation
│   │   │   └── ablation.py      # Syntactic distractor generation
│   │   └── train/
│   │       ├── __init__.py
│   │       ├── lora_config.py   # LoRA hyperparameters
│   │       └── train_loop.py    # Training loop with OOM fallback & timeouts
│   └── tests/
│       ├── __init__.py
│       ├── contract/            # Schema validation tests
│       ├── integration/         # Pipeline end-to-end tests
│       └── unit/                # Utility function tests
├── data/
│   ├── raw/                     # Downloaded datasets (checksummed)
│   ├── processed/               # Generated tuples (static, dialogue, ablation)
│   └── results/                 # Evaluation metrics, logs
└── state/
    └── projects/PROJ-582-.../
        └── artifact_hashes.yaml # Checksums and versioning
```

**Structure Decision**: Single project structure chosen for tight coupling of data generation and training. `src/` encapsulates logic; `data/` is strictly for artifacts; `tests/` validates contracts.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Three-Condition Design** | Required by FR-006 and FR-007 to isolate the effect of *content* vs. *token count*. | A two-condition design (Selection vs. Static) would fail to distinguish between "adversarial signal" and "mere presence of extra tokens," violating the ablation requirement. |
| **4-bit Quantization + LoRA** | Required by FR-003 to fit on 7GB RAM CPU. | Full fine-tuning or 16-bit quantization would exceed RAM limits on free-tier runners, causing OOM failures. |
| **Streaming Data** | Required to handle large datasets (MATH) without exceeding 14GB disk/RAM. | Loading full datasets into memory is infeasible; streaming ensures we can process the real data or sample it cleanly. |
| **Independent T-Test** | Required by statistical rigor (samples are independent across conditions). | Paired t-tests are invalid as the models and training sets are distinct. |

## Phase Plan

### Phase 0: Setup & Verification
- **T001**: Create `src/__init__.py`, `tests/__init__.py`, `requirements.txt`.
- **T003**: Create `pyproject.toml` and `ruff.toml` for linting/formatting.
- **T004**: Create `data/raw/`, `data/processed/`, `data/results/` with `.gitkeep`.
- **T005**: Create `src/utils/logging.py`.
- **T006**: Create `src/utils/config.py` (seeds, paths).
- **T007**: Create `src/utils/model_loader.py` (4-bit loading).
- **T008**: Create `src/utils/metrics.py`.
- **T010**: `verify_datasets.py`: Fetch checksums from verified block (GSM8K: `openai/gsm8k`, MATH: `hendrycks/math`), validate raw data.

### Phase 1: Data Generation
- **T012**: Create `src/data/download.py` (streaming GSM8K, MATH).
- **T013**: Create `src/data/static_extractor.py`.
- **T014**: Create `src/data/generate_dialogue.py` (Adversarial Critique via frozen Critic Model).
  - **Logic**: Prompt frozen model to identify logical contradictions.
  - **Quality Gate**: Discard if length < 20 tokens, no keywords, or confidence < 0.6.
- **T015**: Create `src/data/ablation.py` (Syntactic Distractor generation).
  - **Logic**: Generate distractor text matching *syntactic complexity* of the critique.

### Phase 2: Training Infrastructure
- **T020**: Create `src/train/lora_config.py`.
- **T021**: Create `src/train/train_loop.py` (with Hard Timeouts & OOM fallback).
  - **Timeout**: 5 hours per condition using `signal.signal(signal.SIGALRM, timeout_handler)`.
 - **Validation**: [deferred] of training data held out for Early Stopping.

### Phase 3: Evaluation
- **T030**: Create `src/eval/evaluate.py` (Accuracy on held-out test sets).

### Phase 4: Statistical Analysis (FR-006)
- **T033**: Create `src/utils/stats_analysis.py`:
  - Perform **Independent Samples t-tests** (Selection vs. Ablation, Selection vs. Static).
  - Apply Bonferroni correction ($\alpha = 0.025$).
  - Calculate MDES and report effect sizes.
  - **Stop-Rule**: If effect size < MDES, report "Inconclusive due to power".

### Phase 5: Reporting
- **T040**: Generate `data/results/analysis_report.md`.

## Compute Feasibility & Escape Hatch

### CPU-First Strategy
- **Model**: Large language models with billions of parameters in -bit quantization occupy a moderate amount of RAM..
- **Overhead**: Data loading, tokenization, and LoRA overhead add a measurable but moderate memory footprint.
- **Total**: Fits within 7GB limit.
- **Strategy**: Use `datasets` streaming to avoid memory spikes.

### GPU Escape Hatch
If the training loop fails with OOM on CPU:
- **Action**: The execution stage detects the OOM error and re-runs the same run-book on a Kaggle GPU.
- **Scaling**: The fallback script sets `CUDA_VISIBLE_DEVICES=0`, reduces batch size to a minimal unit, and increases gradient accumulation to compensate.
- **No Fabrication**: We do not simulate GPU training on CPU; we plan for the real scaled-down GPU run if necessary.

### Hard Timeouts (FR-008)
- **Implementation**: `train_loop.py` uses `signal.signal(signal.SIGALRM, timeout_handler)` and `timeout` decorators.
- **Limit**: 5 hours per condition.
- **Behavior**: On timeout, the script exits with a non-zero error code., logs the last checkpoint, and reports "TIMEOUT" in metrics.

## Data Availability & Verification

- **GSM8K**: `openai/gsm8k` (Verified: Contains reasoning steps in train split).
- **MATH**: `hendrycks/math` (Verified: Standard benchmark, programmatic download).
- **Verification**: `verify_datasets.py` (Phase 0) ensures checksums match the verified block before any processing.

## Decision Rationale

| Decision | Rationale |
|----------|-----------|
| **Independent T-Test** | Samples are independent across conditions (different models, different training sets). Paired tests are statistically invalid. |
| **Syntactic Distractor** | Controls for context window complexity and token count, isolating the *logical content* of the critique. |
| **Frozen Critic Model** | Ensures the selection pressure is external to the model being trained, avoiding circularity. |
| **Hard Timeouts** | Satisfies FR-008 by preventing hanging processes on free-tier runners. |
| **Power Analysis** | Acknowledges limitations of small N; uses MDES to interpret null results correctly. |