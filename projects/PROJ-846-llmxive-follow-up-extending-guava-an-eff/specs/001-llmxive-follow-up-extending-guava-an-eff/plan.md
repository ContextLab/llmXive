# Implementation Plan: llmXive follow-up: extending "Guava: An Effective and Universal Harness for Embodied Manipulation"

**Branch**: `001-symbolic-guava-perception` | **Date**: 2026-07-11 | **Spec**: `specs/001-symbolic-guava-perception/spec.md`

## Summary

This feature implements a research pipeline to test the "seeing-to-doing gap" hypothesis: whether replacing high-fidelity visual encoders with lightweight, symbolic perception modules preserves long-horizon task success in embodied manipulation. The approach involves: (1) ingesting Guava visual trajectories, (2) transforming them into a "Symbolic-Guava" dataset using a CPU-only OpenCV + ONNX YOLO-tiny perception module, (3) fine-tuning a 1.5B parameter LLM (Phi-3-mini) on these symbolic states, and (4) evaluating performance against an **Oracle-Symbolic** baseline via a Permutation Test. 

**Critical Methodological Shift**: To isolate the "reasoning" capability from "perception" noise, the baseline is **not** the original visual Guava agent. Instead, we compare the Symbolic-Guava LLM against an **Oracle-Symbolic** agent (which uses the same symbolic inputs but has access to ground-truth action sequences or a perfect policy). This ensures that any performance drop is attributed to the LLM's reasoning limitations, not the inherent superiority of visual encoders.

The implementation adheres to strict CPU-only constraints for the primary evaluation path.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `opencv-python`, `onnxruntime`, `datasets` (Hugging Face), `transformers`, `torch`, `scikit-learn`, `pandas`, `numpy`, `pytest`  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `artifacts/`), Hugging Face Hub (for model checkpoints)  
**Testing**: `pytest` (unit, integration, contract tests)  
**Target Platform**: Linux (GitHub Actions CPU runner: multiple cores, ~7 GB RAM)  
**Project Type**: Research Pipeline / Data Processing & ML Training  
**Performance Goals**: Perception latency ≤ 150ms/frame; Training convergence within 4h (CPU) or 9h (GPU escape); Total pipeline ≤ 6h on CPU.  
**Constraints**: CPU-only execution for evaluation; No PII in data; Reproducible seeds; Checksummed data.  
**Scale/Scope**: [deferred] trajectories (training), A set of tasks (evaluation).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned seeds, `requirements.txt`, and deterministic data fetching from verified sources. |
| **II. Verified Accuracy** | **PASS** | Citations restricted to verified dataset URLs; **Reference-Validator Agent** is invoked to block any artifact with unreachable citations. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of raw/derived data; no in-place modifications. |
| **IV. Single Source of Truth** | **PASS** | All metrics trace to `data/` rows and `code/` execution logs. |
| **V. Versioning Discipline** | **PASS** | `code/utils/state_manager.py` automatically updates `state/projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff.yaml` with content hashes and `updated_at` timestamps after every artifact generation. |
| **VI. Symbolic-Perception Fidelity** | **PASS** | Plan explicitly logs perception module version, parameters, and mapping to raw inputs; includes a dedicated validation phase. |
| **VII. Edge-Constraint Verification** | **PASS** | Evaluation enforced on CPU. If GPU escape hatch is triggered for training, the resulting model is valid for inference, but training metrics (time/convergence) are **not** reported as primary results. |

## Project Structure

### Documentation (this feature)

```text
specs/001-symbolic-guava-perception/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── symbolic_observation.schema.yaml
│   ├── trajectory.schema.yaml
│   ├── task_outcome.schema.yaml
│   └── perception_log.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data/
│   │   ├── __init__.py
│   │   ├── download_guava.py       # Fetches raw Guava data
│   │   ├── transform_symbolic.py   # FR-001, FR-002: YOLO-tiny + JSON conversion
│   │   ├── validate_perception.py  # NEW: Validates YOLO against GT
│   │   └── checksums.json          # Data hygiene
│   ├── models/
│   │   ├── __init__.py
│   │   ├── train_llm.py            # FR-003: Fine-tuning script
│   │   └── inference.py            # FR-004: Evaluation runner (Symbolic vs Oracle)
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── failure_categorizer.py  # FR-006, FR-007
│   │   └── stats_test.py           # FR-005: Permutation test (Symbolic vs Oracle)
│   ├── utils/
│   │   ├── logger.py               # Perception logging
│   │   ├── config.py               # Seeds, paths
│   │   └── state_manager.py        # NEW: Updates project state YAML
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── contract/
├── data/
│   ├── raw/                        # Raw Guava trajectories
│   ├── processed/                  # Symbolic-Guava JSON
│   └── artifacts/                  # Model checkpoints, logs
└── tests/
    ├── unit/
    ├── integration/
    └── contract/
```

**Structure Decision**: Single project structure (`code/`, `data/`, `tests/`) is selected to minimize overhead for a research pipeline. The separation of `data/` (raw vs. processed) and `code/` (modular scripts) ensures Data Hygiene and Reproducibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **GPU Escape Hatch** | Fine-tuning a 1.5B LLM on CPU may exceed 4h. | A purely CPU run risks timeout; the spec allows a scaled-down GPU run if CPU fails, ensuring feasibility without sacrificing the "seeing-to-doing" hypothesis test. |
| **Permutation Test** | Non-parametric comparison needed for small sample (N=50). | Standard t-tests assume normality which may not hold for binary success rates; Permutation Test is robust and explicitly required by FR-005. |
| **Oracle-Symbolic Baseline** | Comparing to a visual baseline conflates perception and reasoning. | A visual baseline (Baseline-Guava) would make the test tautological (visual > symbolic by definition). The Oracle-Symbolic baseline isolates the reasoning gap. |

## Phase Overview

### Phase 0: Data Acquisition & Validation
1. **Download**: Fetch Guava dataset. If unavailable, raise `DatasetUnavailableError`.
2. **Transform**: Convert raw frames to `SymbolicObservation` JSONs using YOLO-tiny.
3. **Validate**: Compute YOLO precision/recall against Guava ground truth. If recall < 90%, flag as "High Perception Risk" and halt or proceed with explicit warning.

### Phase 1: Model Training
1. **Fine-tune**: Train Phi-3-mini on Symbolic-Guava dataset using LoRA.
2. **GPU Escape**: If CPU training > 4h, trigger Kaggle GPU (8-bit quantization). *Note: Training time metrics are not reported as primary results if GPU is used.*

### Phase 2: Evaluation & Analysis
1. **Run Symbolic**: Evaluate LLM on a set of held-out tasks.
2. **Run Oracle**: Evaluate Oracle-Symbolic (perfect policy) on same 50 tasks.
3. **Statistical Test**: Permutation Test (iterations) comparing Symbolic vs. Oracle success rates.
4. **Failure Analysis**: Categorize failures (geometric, semantic, perception, latency).

### Phase 3: Reporting
1. **State Update**: `state_manager.py` updates project state file with hashes.
2. **Output**: Final metrics, p-values, and failure distribution.