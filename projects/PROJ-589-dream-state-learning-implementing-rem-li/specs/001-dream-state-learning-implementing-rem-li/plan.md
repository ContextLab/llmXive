# Implementation Plan: Dream-State Learning: Implementing REM-like Consolidation in Language Models

**Branch**: `001-dream-state-learning-rem-consolidation` | **Date**: 2026-06-30 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-dream-state-learning-rem-consolidation/spec.md`

## Summary

This project implements a bio-inspired training cycle for small language models (≤100M params) that alternates between "wake" phases (standard supervised fine-tuning on real data) and "dream" phases (generative replay with masked inputs). The primary goal is to test if this oscillatory protocol improves few-shot generalization compared to continuous training, while strictly adhering to GitHub Actions free-tier constraints (2 CPU, 7GB RAM, ≤6h). The implementation will utilize a Denoising Autoencoder (DAE) approach for the dream phase, where the model reconstructs masked tokens from its own generated pseudo-samples, avoiding the computational intractability of full synaptic pruning simulations.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers>=4.40.0`, `datasets>=2.18.0`, `torch>=2.2.0` (CPU build), `scipy>=1.12.0`, `pandas>=2.2.0`, `accelerate>=0.28.0`  
**Storage**: Local file system (`data/` for datasets, `artifacts/` for checkpoints/logs)  
**Testing**: `pytest` (unit), `pytest-cov` (coverage), custom integration scripts for training loops  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 vCPU, 7GB RAM)  
**Project Type**: Research CLI / Experimental Training Framework  
**Performance Goals**: Complete full experimental pipeline (5 seeds, wake/dream + baseline, temp sweep) within 5 hours on CPU; peak RSS < 6.0 GB.  
**Constraints**: No GPU usage for training (CPU-first); strict memory abort threshold; no access to gated datasets; must handle low-entropy generation collapse.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

### Token Exposure Control
To satisfy US-2 and FR-003, the baseline run consumes the **exact same number of real training tokens** as the Wake phases of the experimental run. The Dream phase tokens (generated) are excluded from the baseline's token count. Total steps are identical, but the data volume (real tokens) is strictly controlled to isolate the consolidation effect from data volume. The baseline sees the same number of real tokens as the experimental run's Wake phases; the Dream phase's generated tokens do not count as 'real' exposure.

### Semantic Mapping: Generative Replay vs. DAE
The Spec (FR-002) mandates "generative replay with masked inputs". The plan implements this as a **Denoising Autoencoder (DAE)** on model-generated pseudo-samples. This satisfies the computational constraints while maintaining the spirit of replay (using model-generated data to refine representations). The "replay" is the generation of pseudo-samples; the "consolidation" is the reconstruction of the original real input. This implementation explicitly satisfies FR-002's "generative replay" requirement by treating the generation as the replay and the reconstruction as the consolidation.

### Frozen Teacher Mechanism
To address circularity concerns (scientific soundness), the Dream phase uses a **frozen copy** of the model from the start of the cycle to generate pseudo-samples. The active model learns to reconstruct the **original real input** (from the Wake batch), not the generated pseudo-sample. The teacher model is updated **only at the start of each Training Cycle (every 5 steps)**, ensuring the 'dream' signal is grounded but not static, breaking immediate circularity while allowing slow evolution. This ensures the learning signal is grounded in reality and not purely self-reinforcing.

### Warm-up Protocol (FR-007)
The first **[deferred] of total steps** (or a minimum of 10 steps, whichever is greater) are Wake-only. The warm-up ends early if validation loss stabilizes (change < 1% over 5 steps). This ensures initial representation stability before enabling the Dream phase.

### Temperature Sweep (FR-006)
The sensitivity analysis sweeps temperatures across the range **[0.7, 0.9, 1.1, 1.3]**. The variance metric is the **standard deviation of accuracy across seeds for each temperature setting**, and the variance *across temperatures* is also reported to satisfy the sensitivity analysis.

### Checkpoint Save on Abort (FR-005)
If peak RSS exceeds the threshold, the system triggers a hard abort, saves the current model state and optimizer state to `artifacts/checkpoints/oom_abort/`, and logs the peak usage for audit. This is a distinct task/phase in the implementation.

### Scope Creep
Tasks T040 (Salience-Based Selection), T041 (Logical Depth), T042 (Error Reduction Rate), T043 (Low-Shot Generalization), and T044 (Metabolic Cost) are **out of scope** and not authorized by the Spec. The `tasks.md` file (Phase 2 output) will be generated without these tasks to prevent implementation drift.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Method |
| :--- | :--- | :--- |
| **I. Reproducibility** | **COMPLIANT** | `requirements.txt` pins versions; random seeds pinned in `code/`; datasets fetched via `datasets.load_dataset` with explicit revision. |
| **II. Verified Accuracy** | **COMPLIANT** | All citations in `research.md` and `plan.md` will be validated against the "Verified datasets" block in the user message before artifact write. This is a *process* requirement, not a current state verification. |
| **III. Data Hygiene** | **COMPLIANT** | Data files will be checksummed upon download; raw data preserved; transformations produce new files. PII scan integrated in CI. |
| **IV. Single Source of Truth** | **COMPLIANT** | All results in `paper/` will be generated programmatically from `data/` and `code/` outputs; no hand-typed numbers. |
| **V. Versioning Discipline** | **COMPLIANT** | Artifact hashes recorded in state YAML; `updated_at` timestamps managed by Advancement-Evaluator. |
| **VI. Oscillatory Training Protocol** | **COMPLIANT** | Plan explicitly defines 4:1 wake/dream ratio (Constitution Principle VI); dream phase uses masked reconstruction; deviations logged as ablation. |
| **VII. Few-Shot Generalization Validation** | **COMPLIANT** | Evaluation on GLUE/SuperGLUE subsets (≤1000 samples); statistical significance via paired t-test (α=0.05) across ≥5 seeds; effect sizes reported. |

**Note on Statistical Method**: The Specification (SC-002) mandates a **paired t-test** with α=0.05. The Plan will implement this as the primary acceptance metric. A secondary **Wilcoxon signed-rank test** will be computed and reported for robustness, acknowledging the small sample size (n=5) and potential non-normality, but the t-test result drives acceptance. This ensures compliance with the Spec (SSoT) while addressing methodological rigor concerns.

## Project Structure

### Documentation (this feature)

```text
specs/001-dream-state-learning-rem-consolidation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (Note: T040-T044 excluded)
```

### Source Code (repository root)

```text
projects/PROJ-589-dream-state-learning-implementing-rem-li/code/
├── __init__.py
├── requirements.txt
├── main.py                  # Entry point for training orchestration
├── config.py                # Hyperparameters and paths
├── models/
│   ├── __init__.py
│   ├── trainer.py           # Wake/Dream loop logic
│   ├── dream_scheduler.py   # Phase timing and warm-up logic (FR-007)
│   └── entropy_checker.py   # Low-entropy detection and retry (Edge Cases)
├── data/
│   ├── __init__.py
│   └── loaders.py           # Dataset fetching and streaming
├── evaluation/
│   ├── __init__.py
│   ├── few_shot.py          # GLUE/SuperGLUE evaluation logic
│   └── stats.py             # Statistical analysis (t-test, Wilcoxon)
├── utils/
│   ├── __init__.py
│   ├── memory_monitor.py    # RSS monitoring and abort logic
│   └── logging.py           # Phase transition and audit logging
└── tests/
    ├── unit/
    │   ├── test_entrance.py
    │   └── test_stats.py
    └── integration/
        └── test_training_loop.py
```

**Structure Decision**: Single project structure under `projects/PROJ-589-dream-state-learning-implementing-rem-li/code/` is selected to maintain tight coupling between the research logic, data handling, and evaluation, facilitating the "Single Source of Truth" principle. The `tests/` directory is nested within `code/` to ensure tests are versioned with the code they validate.

**File Mapping**:
- `models/dream_scheduler.py`: Explicitly implements the **warm-up protocol** (FR-007) and phase timing.
- `models/entropy_checker.py`: Explicitly implements the **low-entropy detection** and retry logic (Edge Cases).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Separate Baseline Run** | Required by US-2 and FR-003 to isolate the effect of consolidation. The baseline consumes the same number of *real* tokens as the Wake phases of the experimental run. | A single run with mixed data would conflate the consolidation effect with general training progress, violating the experimental control. |
| **Entropy Check & Retry** | Required by Edge Cases to prevent training on collapsed/garbage data. | Skipping this risks model collapse or training on nonsensical pseudo-samples, rendering results invalid. |
| **Memory Monitor & Abort** | Required by FR-005 and US-3 to ensure CI feasibility. | Without hard abort, OOM errors on CI would cause silent failures or infinite hangs, breaking reproducibility. |
| **Checkpoint Save on Abort** | Required by FR-005 to save model/optimizer state upon memory abort. | Without this, debugging OOM failures would be impossible, violating reproducibility. |
| **Temperature Sweep** | Required by FR-006 and SC-005 to isolate consolidation from regularization. | A single temperature setting cannot distinguish between "dreaming" benefits and generic noise injection. |

## Success Criteria

- **SC-001**: The relative improvement in few-shot accuracy of the Wake/Dream model over the Continuous Baseline is measured against the baseline accuracy.
- **SC-002**: The statistical significance of the improvement is measured against a **paired t-test** threshold of α=0.05 across 5 random seeds (Primary metric). A Wilcoxon signed-rank test is reported for robustness.
- **SC-003**: The peak memory consumption during training is measured against the predefined system limit of **6.0 GB** to verify CPU-only feasibility.
- **SC-004**: The total wall-clock execution time is measured against the standard time limit of **5 hours** per GitHub Actions job.
- **SC-005**: The variance in final accuracy across a temperature sweep (range [0.7, 0.9, 1.1, 1.3]) is measured as the **standard deviation** of accuracy across seeds for each temperature, linked to the Temperature Sweep implementation in Technical Context.

## Performance Goals
- Complete full experimental pipeline (5 seeds, wake/dream + baseline, temp sweep) within **5 hours** (SC-004).
- Peak RSS < **6.0 GB** (SC-003).