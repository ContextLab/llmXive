# Implementation Plan: llmXive Follow-up: Extending "Improved Large Language Diffusion Models"

**Branch**: `001-llmxive-overfitting-trajectory` | **Date**: 2026-08-07 | **Spec**: `specs/001-llmxive-follow-up-extending-improved-lar/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-improved-lar/spec.md`

## Summary

This project implements a comparative study to validate the "overfitting-as-a-feature" hypothesis: that bidirectional masked diffusion models (MDM) exhibit slower generalization gap widening than causal autoregressive (AR) transformers when trained on a constrained data regime. To ensure statistical validity and computational feasibility on the free-tier CI runner (CPU, 6h limit), the design has been revised to:
1. **Reduce Dataset Size**: Target **1M tokens** ([deferred] - [deferred]) instead of 10M. *Note: The spec's 10M requirement is flagged as a root-cause conflict with the 6-hour CPU budget. This plan implements the feasible 1M regime.*
2.  **Increase Statistical Power**: Train **5 independent seeds** per architecture (N=5 per group) to enable valid Mixed-Model ANOVA.
3.  **Validate Generalization**: Include a cross-domain validation step on a held-out dataset (WikiText).

The implementation constructs the strict "Micro-Corpus", trains A set of models (5 AR, 5 MDM) for A sufficient number of epochs. on CPU-optimized loops, and performs statistical analysis on the Generalization Gap trajectories.

## Technical Context

**Language/Version**: Python 3.x  
**Primary Dependencies**: `transformers` (v4.40+), `datasets` (v2.18+), `torch` (v2.2+ with `torch.compile`), `scikit-learn`, `scipy`, `pandas`, `pyyaml`, `huggingface_hub`  
**Storage**: Local ephemeral storage (GitHub Actions runner); `data/` directory for Micro-Corpus and logs.  
**Testing**: `pytest` for unit tests; integration tests verify data bounds and model output shapes.  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner).  
**Project Type**: Computational Research / Machine Learning Experiment.  
**Performance Goals**: Complete 100 epochs for 10 models (5 seeds x 2 arch) on 1M tokens within 6 hours wall-clock time; peak RAM < 7GB.  
**Constraints**: Strict token count (MM); no GPU available for training (CPU-first); no access-gated datasets.  
**Scale/Scope**: Two M-parameter models (multiple seeds each); M token dataset; multiple epochs; a single statistical analysis pipeline.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned seeds, explicit `requirements.txt`, and re-runnable scripts. Random seeds will be fixed in `code/`. |
| **II. Verified Accuracy** | **PASS** | Citations for "overfitting-as-a-feature" and MDM architectures will be validated against primary sources before writing paper artifacts. |
| **III. Data Hygiene** | **PASS** | Micro-Corpus will be checksummed. No in-place modification; truncation logs will be recorded. |
| **IV. Single Source of Truth** | **PASS** | All metrics (loss, gap, p-values) will be derived from `data/training_logs.csv` and `data/statistical_results.json`. |
| **V. Versioning Discipline** | **PASS** | **Mechanism**: A dedicated step in Phase 0 and Phase 4 will compute SHA-256 hashes of all artifacts and update `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/state/projects/PROJ-864-llmxive-follow-up-extending-improved-lar.yaml` `updated_at` and `artifact_hashes` fields. |
| **VI. Overfitting Trajectory Isolation** | **PASS** | Plan enforces identical embedding dims/heads for AR and MDM. Micro-Corpus strictly limited to 1M tokens. HumanEval excluded from training. |
| **VII. CPU-Feasibility Constraint** | **PASS** | Training loops designed for `torch.compile` on CPU. Model size (scaled to fit available RAM / time limit) and data size (scaled to fit available RAM / time limit) selected to fit available RAM / time limit. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-improved-lar/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/
    ├── dataset.schema.yaml
    ├── model_config.schema.yaml
    ├── training_log.schema.yaml
    ├── statistical_result.schema.yaml
    └── human_eval.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/
├── data/
│   ├── download_micro_corpus.py
│   ├── validate_corpus.py
│   └── split_data.py
├── models/
│   ├── __init__.py
│   ├── autoregressive.py
│   └── diffusion.py
├── training/
│   ├── train_loop.py
│   ├── callbacks.py
│   └── run_experiment.py
├── analysis/
│   ├── compute_metrics.py
│   └── statistical_test.py
├── utils/
│   ├── logging.py
│   └── config.py
├── tests/
│   ├── test_corpus_bounds.py
│   └── test_model_shapes.py
├── requirements.txt
└── main.py

projects/PROJ-864-llmxive-follow-up-extending-improved-lar/data/
├── raw/
│   └── [downloaded source files]
├── processed/
│   ├── micro_corpus_train.jsonl
│   └── micro_corpus_test.jsonl
├── artifacts/
│   ├── training_logs.csv
│   ├── statistical_results.json
│   ├── human_eval_results.json
│   └── corpus_validation.json
```

**Structure Decision**: Single project structure. All data processing, training, and analysis are contained within the `code/` directory to ensure end-to-end reproducibility on the CI runner. Data artifacts are stored in `data/` with strict separation between raw downloads and processed tokens.

## Complexity Tracking

No violations found. The single-project structure minimizes overhead and aligns with the "CPU-Feasibility" constraint by keeping the pipeline tight and avoiding distributed training complexity.

## Phased Implementation Plan

### Phase 0: Research & Feasibility Verification
**Goal**: Confirm dataset availability, statistical power, and state file mechanism.
1.  **FR-001 / SC-001**: Identify and verify open-source datasets (Project Gutenberg, The Stack) with programmatic access. Confirm token counts and domain balance.
2.  **FR-009 / SC-005**: Perform a priori power analysis. Calculate required sample size (seeds) to detect interaction effect with power ≥ 0.8. *Design: 5 seeds per group.*
3.  **FR-002 / SC-002**: Verify that a model architecture of the intended scale fits in available RAM (using `torch.compile` and mixed precision if necessary).
4.  **Constitution V**: Define the script to update `state` file with content hashes.
5.  **Deliverable**: `research.md` containing dataset strategy, power analysis, and architecture feasibility confirmation.

### Phase 1: Data Model & Contract Definition
**Goal**: Define strict schemas for data and outputs.
1.  **FR-001**: Define `micro_corpus` schema (token count, split ratio).
2.  **FR-003 / FR-004**: Define `training_log` schema (epoch, model_type, seed_id, train_loss, val_loss, gap, time, ram).
3.  **FR-005 / FR-010**: Define `statistical_result` schema (ANOVA table, p-values, correlation coefficients).
4.  **FR-006**: Define `human_eval` schema.
5.  **Deliverable**: `data-model.md` and `contracts/*.schema.yaml` files.

### Phase 2: Data Construction (Micro-Corpus)
**Goal**: Build the 1M token dataset.
1.  **FR-001**: Implement `download_micro_corpus.py` to fetch and concatenate sources.
2.  **FR-001**: Implement tokenization with `gpt2` tokenizer.
3.  **FR-001 / Edge Case**: Implement strict truncation logic to enforce token bounds. Log truncation events.
4.  **FR-001**: Split into train/test ensuring no overlap.
5.  **FR-007**: Verify disk usage < 14GB and RAM load < 7GB.
6.  **FR-006 / Data Hygiene**: **Verify HumanEval exclusion** from the corpus *before* training begins. Generate `corpus_validation.json` with pass/fail status and final token count.
7.  **Deliverable**: `data/processed/micro_corpus_train.jsonl`, `test.jsonl`, and `data/artifacts/corpus_validation.json`.

### Phase 3: Model Implementation & Training Loop
**Goal**: Train multiple models (multiple seeds AR, multiple seeds MDM) for a sufficient number of epochs.
1.  **FR-002**: Implement `autoregressive.py` (Causal LM) and `diffusion.py` (Bidirectional MDM) with identical embedding/attention params.
2.  **FR-003**: Implement `train_loop.py` using `torch.compile` on CPU.
3.  **FR-004**: Integrate callbacks to log loss and gap every epoch, including `seed_id`.
4.  **FR-007**: Integrate resource monitoring (RAM, time).
5.  **FR-003**: Execute a sufficient number of epochs for each of the 5 seeds per architecture to ensure model convergence. **Timeout Logic**: If the time limit is approached, log the current epoch, set status=TRUNCATED in the log, and halt gracefully. The analysis will use available data.
6.  **Deliverable**: `data/artifacts/training_logs.csv`.

### Phase 4: Statistical Analysis & Benchmarking
**Goal**: Analyze overfitting trajectories and validate against HumanEval.
1.  **FR-005**: Run Mixed-Model Repeated-Measures ANOVA on Generalization Gap (Model × Epoch) with Seeds as subjects.
2.  **FR-006**: Evaluate final checkpoints on HumanEval (using the verified-excluded data). Save results to `human_eval_results.json`.
3.  **FR-010**: Calculate Pearson correlation between gap slope and HumanEval score **per architecture** (points for AR, points for MDM).
4.  **FR-009**: Report power analysis results against observed effect size.
5.  **Cross-Domain Validation**: Evaluate models on WikiText-2 to test generalization beyond the Micro-Corpus.
6.  **Constitution V**: Update `state` file with hashes of all new artifacts.
7.  **Deliverable**: `data/artifacts/statistical_results.json`, `human_eval_results.json`, and `analysis/report.md`.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **OOM on CPU** | High | Use `torch.compile` with `mode="reduce-overhead"`. Monitor RAM; if >6GB, reduce batch size dynamically. |
| **Timeout (>6h)** | High | Monitor wall-clock time per epoch. If trend indicates timeout, abort and log partial results (status=TRUNCATED). |
| **Dataset Bias** | Medium | Verify text distribution (code vs. prose) in `research.md`. If skewed, rebalance sources before tokenization. |
| **Null Result** | Low | Plan explicitly handles null hypothesis (no interaction). A non-significant p-value is a valid scientific finding. |
| **Spec Conflict (10M vs 1M)** | High | The spec mandates a large token corpus, but this is computationally infeasible on a limited CPU budget. This plan implements the feasible 1M regime and flags the spec conflict for future revision. |

