# Implementation Plan: llmXive Follow-up: Extending "JoyAI-VL-Interaction"

**Branch**: `001-llmxive-vl-intuition` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-vl-intuition/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-vl-intuition/spec.md`

## Summary

This feature implements a CPU-optimized research pipeline to validate the "latent intuition" hypothesis in the JoyAI-VL-Interaction model. The core objective is to determine if internal hidden states and attention maps (excluding final logits) contain sufficient signal to predict "optimal intervention" events (critical vs. silence) derived strictly from synthetic video ground truth. The pipeline consists of four phases: (1) Synthetic Data Generation with visual-only labeling (no VLM involvement) and noise injection, (2) Feature Extraction from VLM internal states, (3) Visual Baseline Implementation (Noisy Rule-Based Detector), and (4) Training/Evaluation of a M-parameter Transformer classifier on CPU-only hardware. Evaluation uses AUC-ROC, Cohen's Kappa, and Nested Model Comparison (Likelihood Ratio Tests) to verify unique predictive signal.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only), `transformers`, `datasets`, `scikit-learn`, `pandas`, `numpy`, `opencv-python`, `accelerate` (CPU mode)  
**Storage**: Local file system (`data/`), JSONL for intermediate features, YAML for schemas.  
**Testing**: `pytest` (unit tests for schema validation, integration tests for pipeline stages).  
**Target Platform**: Linux (GitHub Actions c6i.large equivalent: 2 vCPU, 7GB RAM, No GPU).  
**Project Type**: Computational Research / Data Pipeline  
**Performance Goals**: End-to-end pipeline execution ≤ 6 hours; Peak RAM ≤ 7GB; Inference latency < 200ms per frame (batched).  
**Constraints**: No CUDA/GPU operations; No 8-bit/4-bit quantization requiring specific CUDA kernels; Streaming/batching required for long videos; Ground truth must be decoupled from VLM outputs.  
**Scale/Scope**: Synthetic dataset target: hours of video (simulated); Model: A parameter count in the millions; Feature vectors: Hidden state dimension x Attention heads.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Compliance Strategy |
| :--- | :--- |
| **I. Reproducibility** | All random seeds pinned in `code/`. Synthetic data generation uses deterministic seeds. Dependencies pinned in `requirements.txt`. |
| **II. Verified Accuracy** | **Enforcement Step**: Before any artifact write, the pipeline invokes the `Reference-Validator Agent` to check citations against the `CITATION_TITLE_OVERLAP_THRESHOLD` (0.7). Citations are strictly limited to verified URLs. |
| **III. Data Hygiene** | Synthetic data checksums recorded. No in-place modification; derivations create new files. PII scan enforced (synthetic data is non-PII by design). |
| **IV. Single Source of Truth** | Metrics (Interruption Reduction, Safety Recall, AUC-ROC) calculated in `code/` and traced to `data/` artifacts. No hand-typed numbers in `paper/`. |
| **V. Versioning Discipline** | **Workflow**: Upon completion of each phase, the pipeline computes SHA-256 hashes for all `data/` and `code/` artifacts, updates `state/projects/PROJ-863-llmxive-follow-up-extending-joyai-vl-int.yaml` `artifact_hashes` map, and updates the `updated_at` timestamp. This is an automated step in `main.py`. |
| **VI. Latent-State Independence** | **Critical**: Labeling logic uses only visual events (object detection). VLM is only used for feature extraction *after* labels are fixed. Execution logs verify zero VLM calls during labeling. |
| **VII. Edge-Constraint Validation** | Pipeline explicitly designed for vCPU/7GB RAM. Batching/streaming implemented. Metrics for RAM/CPU tracked and reported. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-vl-intuition/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (Generated in next stage, not by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── data_synthesis/
│   ├── __init__.py
│   ├── generator.py       # Synthetic video generation (with noise injection)
│   └── visual_labeler.py  # Visual-only ground truth logic
├── feature_extraction/
│   ├── __init__.py
│   ├── extractor.py       # Hidden state/attention extraction
│   └── streaming.py       # Batching for memory limits
├── baseline/
│   ├── __init__.py
│   └── visual_detector.py # Noisy Rule-Based Visual Detector (Baseline)
├── scheduler/
│   ├── __init__.py
│   ├── model.py           # 15M Transformer classifier
│   ├── train.py           # CPU-optimized training loop
│   └── eval.py            # Metric calculation (Interruption/Safety/AUC)
├── utils/
│   ├── logging.py         # Execution log for FR-001.1
│   └── validation.py      # Schema validation
└── main.py                # Orchestration script (includes versioning workflow)

tests/
├── contract/
│   └── test_schemas.py
├── integration/
│   └── test_pipeline.py
└── unit/
    ├── test_visual_labeler.py
    └── test_feature_extractor.py

data/
├── raw/                   # Synthetic video frames (generated)
├── features/              # Extracted internal states
├── baseline/              # Visual baseline predictions
└── processed/             # Final training datasets
```

**Structure Decision**: Single Python project structure chosen to simplify dependency management and data flow for a research pipeline. Separation of `data_synthesis`, `feature_extraction`, `baseline`, and `scheduler` modules ensures modularity and adherence to the "Latent-State Independence" principle.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Streaming/Batching** | A substantial duration of video exceeds 7GB RAM if loaded fully. | Loading full video in memory would crash the CI runner, violating FR-003 and Constitution Principle VII. |
| **Visual-Only Labeling** | Required to ensure ground truth is not circular (model predicting its own output). | Using VLM outputs for labels would invalidate the "latent intuition" hypothesis test (Constitution Principle VI). |
| **M Parameter Model** | Balances capacity to learn complex patterns with CPU feasibility. | Larger models (e.g., BERT-large) would exceed 7GB RAM or 6h runtime on CPU; smaller models may fail to capture subtle internal state signals. |
| **Noise Injection** | Prevents the VLM from simply memorizing deterministic synthetic rules. | A deterministic synthetic generator would allow a rule-based detector to achieve perfect F1, making the "latent intuition" test trivial and invalid. |
| **Nested Model Comparison** | Required to prove unique signal beyond visual features. | Simple correlation is invalid; comparing model performance (AUC) between visual-only and visual+internal states is the statistically rigorous approach. |

## Implementation Phases

### Phase 0: Data Synthesis & Labeling
- **Task**: Generate synthetic video frames.
- **Task**: Apply visual-only labeling (critical/silence) based on object detection.
- **Task**: Inject temporal jitter and noise into labels/features to prevent deterministic memorization.
- **Task**: Generate execution log verifying zero VLM API calls.
- **Output**: `data/raw/`, `data/manifest.jsonl`, `data/execution_log.jsonl`.

### Phase 1: Feature Extraction
- **Task**: Load JoyAI-VL-Interaction model (CPU mode).
- **Task**: Extract hidden state embeddings and attention maps for each frame.
- **Task**: Stream data in batches. to respect RAM limits.
- **Output**: `data/features/*.jsonl`.

### Phase 2: Visual Baseline Implementation
- **Task**: Implement `visual_detector.py` (Noisy Rule-Based Detector).
- **Task**: Run detector on `data/raw/` to generate baseline predictions.
- **Task**: Calculate baseline F1, AUC, and Interruption Reduction.
- **Output**: `data/baseline/*.jsonl`.

### Phase 3: Scheduler Training & Evaluation
- **Task**: Train 15M Transformer on internal state features.
- **Task**: Evaluate scheduler using AUC-ROC, Cohen's Kappa, and Safety Recall.
- **Task**: Perform Nested Model Comparison (Likelihood Ratio Test) between visual-only and visual+internal states models.
- **Task**: Calculate Mutual Information between internal states and labels.
- **Task**: Compare scheduler F1 to Noisy Baseline F1 (SC-005).
- **Output**: `models/scheduler_checkpoint.pth`, `data/evaluation/results.jsonl`, `metrics_summary.json`.

### Phase 4: Versioning & Validation
- **Task**: Compute SHA-256 hashes for all artifacts.
- **Task**: Update `state/projects/PROJ-863-llmxive-follow-up-extending-joyai-vl-int.yaml`.
- **Task**: Run `Reference-Validator Agent` on citations.
- **Output**: Updated `state/` file, validation report.