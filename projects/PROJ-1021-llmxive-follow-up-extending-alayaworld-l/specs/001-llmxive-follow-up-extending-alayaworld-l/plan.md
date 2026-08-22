# Implementation Plan: llmXive follow-up: extending "AlayaWorld: Long-Horizon and Playable Video World Generation"

**Branch**: `001-llmxive-alayaworld-extend` | **Date**: 2026-07-18 | **Spec**: `specs/001-llmxive-alayaworld-extend/spec.md`

## Summary

This project extends the AlayaWorld video generation model by integrating a lightweight, CPU-tractable symbolic logic layer. The primary objective is to quantify and mitigate "Semantic Drift" in long-horizon (60-second) interactive video sequences. The approach involves: (1) establishing a baseline drift score by comparing vanilla model outputs against a deterministic symbolic simulation; (2) implementing a hybrid correction mechanism that injects "correction tokens" into the generation loop based on symbolic state discrepancies; and (3) validating the system under strict edge-device constraints (2-core CPU, 7GB RAM).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: PyTorch (CPU-only build), OpenCV (for optical flow/template matching), `datasets` (for streaming), `scikit-learn` (statistical testing), `pandas`.  
**Storage**: Local filesystem (`data/` for artifacts, `code/` for scripts). No external DB.  
**Testing**: `pytest` (unit tests for symbolic engine, integration tests for drift calculation).  
**Target Platform**: Linux (GitHub Actions free-tier: 2 vCPU, 7GB RAM, 14GB Disk).  
**Project Type**: Research/Computational Experiment.  
**Performance Goals**: Wall-clock time ≤ 30 mins per 60-sec sequence; Peak RAM ≤ 7 GB.  
**Constraints**: No GPU usage for inference; symbolic engine must be deterministic; CV accuracy ≥ 85% required for valid drift scores.  
**Scale/Scope**: 10 random seeds, 10 action sequences per seed (100 total sequences).

> **Note on Dataset**: The spec assumes the existence of "AlayaWorld" data with specific object interactions. As no verified public URL exists for the AlayaWorld dataset (per the verified datasets block), the implementation will rely on a **simulated synthetic generator** that mimics the AlayaWorld action/visual structure for the purpose of the symbolic logic test, OR the plan assumes a local artifact `data/alayaworld_simulated_interactions.json` is provided by the user/researcher. The plan explicitly addresses this gap in `research.md`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Check | Status |
|-----------|------------------|--------|
| **I. Reproducibility** | Plan mandates pinned seeds, checksummed data, and isolated `requirements.txt`. | ✅ Compliant |
| **II. Verified Accuracy** | No external URLs cited for AlayaWorld (as none verified). Internal validation logic (FR-007) is mandatory. | ✅ Compliant |
| **III. Data Hygiene** | Plan requires checksumming of generated synthetic data and annotated subsets. No in-place modification. | ✅ Compliant |
| **IV. Single Source of Truth** | All drift scores and stats trace to specific JSON/CSV outputs in `data/`. | ✅ Compliant |
| **V. Versioning Discipline** | Artifacts will carry content hashes; state file updated on change. | ✅ Compliant |
| **VI. Deterministic Symbolic Grounding** | Symbolic engine implemented in pure Python with no stochastic elements. | ✅ Compliant |
| **VII. Edge-Device Inference** | Explicit constraints (2-core, 7GB RAM) enforced in `quickstart.md` and resource logging. | ✅ Compliant |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-alayaworld-extend/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── symbolic_state.schema.yaml
    ├── visual_state.schema.yaml
    └── drift_result.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-1021-llmxive-follow-up-extending-alayaworld-l/
├── data/
│   ├── raw/                  # Downloaded/Simulated raw sequences
│   ├── processed/            # Symbolic logs, visual logs
│   ├── annotated/            # Ground truth subset (≥50 frames)
│   └── results/              # Final JSON/CSV reports
├── code/
│   ├── symbolic_engine.py    # Deterministic rule-based logic
│   ├── cv_pipeline.py        # Optical flow, template matching
│   ├── hybrid_controller.py  # Correction token injection logic
│   ├── drift_analyzer.py     # Score calculation & validation
│   ├── stats_runner.py       # T-test & aggregation
│   └── main.py               # Orchestration script
├── tests/
│   ├── test_symbolic.py
│   └── test_cv_accuracy.py
└── config/
    └── params.yaml           # Includes `error_injection_prob` (20%)
```

**Structure Decision**: Single-project structure is selected. The research nature requires tight coupling between the symbolic engine, CV pipeline, and statistical analysis. No separate frontend/backend is needed.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Hybrid Controller + Edge Case Handling** | T017 and T018 merged. Edge cases (teleportation, occlusion) are intrinsic to the control loop logic, not a separate module. | Separating them creates false dependencies and risks state desynchronization between the controller and error handler. |
| **Ground Truth Data Generation** | T012 split into "Logic Implementation" and "Data Generation" (if needed). | The task description previously conflated code logic with data existence. The plan now explicitly requires a `data/annotated/gt_subset_50.json` file (generated or provided) to run the validation. |
| **Configurable Error Injection** | T010 requires explicit config. | "e.g., [deferred]" is ambiguous. A `config/params.yaml` file is mandated to define `error_injection_prob: 0.20` for deterministic testing. |
| **Statistical Output Paths** | T021 requires explicit paths. | Input/Output files are named explicitly (`data/results/baseline_scores.json`, `data/results/hybrid_scores.json`, `data/results/stats_comparison.json`) to ensure self-contained execution. |
| **Final Report Naming** | T026 requires explicit filenames. | Output files are named `data/results/final_results.csv` and `data/results/experiment_log.json`. |
| **GT Sample Size** | T012 requires ≥50 frames. | The plan explicitly mandates `data/annotated/gt_subset_50.json` containing at least 50 frames to satisfy FR-007. |
