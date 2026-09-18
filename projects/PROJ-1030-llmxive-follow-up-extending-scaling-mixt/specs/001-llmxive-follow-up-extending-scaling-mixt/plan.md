# Implementation Plan: llmXive follow-up: extending "Scaling Mixture-of-Experts Video Pretraining for Embodied Intelligence"

**Branch**: `001-llmxive-physical-validator` | **Date**: 2026-09-05 | **Spec**: `specs/001-llmxive-follow-up-extending-scaling-mixt/spec.md`
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-scaling-mixt/spec.md`

## Summary

This feature implements a rigorous validation pipeline to test the hypothesis that internal activation patterns in the LingBot-Video Mixture-of-Experts (MoE) model encode physical laws. The approach involves three sequential phases: (1) extracting latent vectors and expert masks from the pre-trained model on CPU using `torch.no_grad()` and memory chunking; (2) generating independent ground-truth labels ("valid"/"invalid") by reconstructing 3D states via monocular depth estimation, applying *known synthetic perturbations* to create the "invalid" class, and running a kinematic consistency check; and (3) training a lightweight CPU-based classifier (MLP or Random Forest) to predict physical validity from the extracted activations. The pipeline strictly adheres to CPU-only constraints, memory limits (7 GB RAM), and the requirement for associational (non-causal) claims. The plan explicitly acknowledges that monocular depth estimation is not a source of "true" ground truth but a tool to generate candidate trajectories for perturbation. The "ground truth" is the applied perturbation logic. The pipeline is designed to run end-to-end on a fresh GitHub Actions runner without manual intervention.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only build), `transformers`, `datasets`, `pybullet`, `opencv-python`, `monodepth2` (or similar CPU-compatible depth estimator), `scikit-learn`, `pandas`, `numpy`, `ruff`, `black`, `memory_profiler`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/external`), NumPy arrays (`.npy`), CSV/JSON for metadata.  
**Testing**: `pytest` (unit/integration), contract tests against YAML schemas.  
**Target Platform**: Linux (GitHub Actions free-tier: 2 vCPU, ~7 GB RAM, ~14 GB disk).  
**Project Type**: Research pipeline / Data processing library.  
**Performance Goals**: Feature extraction < 2 hours; Classifier training < 30 minutes; Total pipeline < 6 hours.  
**Constraints**: CPU-only execution; 7 GB RAM limit (requires chunking/streaming); No GPU offload for extraction/labeling (GPU escape hatch only if depth estimation fails on CPU, but plan assumes CPU-first); Strict separation of model inference and physics simulation.  
**Scale/Scope**: Subset of RoboNet/Ego4D dataset (streamed or sampled); [deferred]-5,000 clips initially for feasibility.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on constitution file*

- **Principle I (Reproducibility)**: Plan mandates pinned random seeds in `code/`, checksummed data in `data/`, and a `requirements.txt` for isolated execution. The pipeline is explicitly designed to run end-to-end on a fresh GitHub Actions runner without manual intervention.
- **Principle II (Verified Accuracy)**: All citations (LingBot model, RoboNet dataset) will be verified by the Reference-Validator Agent against the primary source with a title-overlap threshold of `CITATION_TITLE_OVERLAP_THRESHOLD = 0.7` before implementation. The agent will fail the pipeline if any citation fails.
- **Principle III (Data Hygiene)**: Plan includes checksums for raw data, immutable derivations (new filenames for processed data), and exclusion logs for filtered samples.
- **Principle IV (Single Source of Truth)**: All metrics (F1, precision) will be derived from `data/processed` artifacts and traced to code blocks in `code/`.
- **Principle V (Versioning)**: Content hashes for all artifacts will be recorded in `state/manifest.yaml`. The Advancement-Evaluator Agent will consume these hashes to invalidate stale review records if a mismatch is detected. A specific task 'Update Manifest Hashes' generates this file.
- **Principle VI (Latent-Space Grounding)**: Plan explicitly separates the LingBot-Video model (feature extractor) from the physics engine (label generator) to ensure label independence. The `prior_audit.py` script and `label_independence_score` metric provide the verification logic for this decoupling.
- **Principle VII (CPU-Tractable Efficiency)**: Plan prioritizes CPU-tractable methods (shallow MLP, chunked inference). The 'Verify Memory Chunking' task and `memory_log.json` artifact provide the verification logic for this requirement.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-physical-validator/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-1030-llmxive-follow-up-extending-scaling-mixt/
├── code/
│   ├── __init__.py
│   ├── config.py                  # Configuration and paths
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── data_loader.py         # Streaming dataset loading
│   │   ├── logging.py             # "FAIL LOUDLY" and progress logging
│   │   ├── prior_audit.py         # Audit for shared priors (Constitution VI)
│   │   └── validation.py          # Physics engine validation logic
│   ├── extraction/
│   │   ├── __init__.py
│   │   ├── lingbot_inference.py   # Feature extraction with torch.no_grad()
│   │   └── memory_chunker.py      # Frame subsampling/chunking logic
│   ├── labeling/
│   │   ├── __init__.py
│   │   ├── depth_reconstruction.py # Monocular depth estimation
│   │   ├── perturbation.py        # Synthetic perturbation logic
│   │   └── physics_sim.py         # PyBullet simulation for labels
│   ├── classification/
│   │   ├── __init__.py
│   │   ├── train_classifier.py    # MLP/RF training
│   │   └── evaluate.py            # Metrics and baseline calculation
│   └── cli/
│       └── run_pipeline.py        # Orchestration script
├── data/
│   ├── raw/                       # Downloaded datasets (checksummed)
│   ├── processed/                 # Extracted features, labels, logs
│   │   ├── features.npy           # Latent vectors and masks
│   │   ├── labels.csv             # Valid/Invalid labels (with null)
│   │   ├── excluded_samples.log   # Filtered samples
│   │   ├── memory_log.json        # Peak RAM usage log
│   │   ├── audit_report.json      # Prior audit results
│   │   ├── filtering_report.json  # Count of filtered vs retained samples
│   │   └── metadata.json          # Dataset statistics
│   └── external/                  # Pre-trained models (if not cached)
├── tests/
│   ├── unit/                      # Unit tests for utils, extraction, labeling
│   ├── integration/               # End-to-end pipeline tests
│   └── contract/                  # Schema validation tests
├── docs/
│   └── figures/                   # Generated plots
├── state/
│   └── manifest.yaml              # Artifact hashes and versioning
└── requirements.txt               # Pinned dependencies
```

**Structure Decision**: Single project structure with clear separation of concerns (extraction, labeling, classification) to ensure modularity and testability. This supports the "Reproducibility" and "Data Hygiene" principles.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Separate 3D Reconstruction & Physics Engine | Required by Constitution VI to ensure label independence from the foundation model. | Using the foundation model's internal states for labeling would create circularity and invalidate the hypothesis test. |
| Synthetic Perturbation for Labels | Required to break circularity with monocular depth estimation. The "ground truth" is the known perturbation, not the depth estimate. | Using depth estimate accuracy as the ground truth would be tautological and invalid. |
| Memory Chunking Strategy | Required by FR-006 to fit within 7 GB RAM on CI runners. | Processing full videos in memory would cause OOM crashes, violating compute feasibility. |
| Exclusion Logging (excluded_samples.log) | Required by Data Hygiene to track filtered samples and ensure transparency. | Simply dropping samples without logging would obscure data loss and violate reproducibility. |
| Baseline Calculation in Evaluation | Required by SC-001 to measure F1-score against random guessing (Majority Class Predictor). | Omitting this would make it impossible to verify if the classifier performs better than chance. |
| Prior Audit (label_independence_score) | Required by SC-005 to verify label independence. | Without this, the correlation between depth confidence and labels could invalidate the hypothesis. |
| Visual Fidelity Check | Required to ensure the input video has sufficient texture for depth estimation. | Processing videos where depth estimation is impossible would lead to noisy labels and invalid results. |
| Control Experiments | Required to rule out the classifier learning depth artifacts rather than physics. | Without shuffling or random depth controls, a high F1-score could be an artifact of the labeling pipeline. |

## Implementation Phases

### Phase 0: Validation & Setup
- **0.1 Reference-Validator**: Run Reference-Validator Agent on all citations. Fail if title-overlap < 0.7.
- **0.2 Visual Fidelity Check**: Filter dataset clips based on texture/variance score to ensure depth estimation feasibility. Clips failing this check are excluded *before* depth estimation.
- **0.3 Memory Chunking Verification**: Run a sample extraction with `memory_profiler` to verify peak RAM < 7 GB. Log to `memory_log.json`.

### Phase 1: Feature Extraction
- **1.1 Download Data**: Stream dataset from Hugging Face (RoboNet/Ego4D). Stratify sampling by **action type** (e.g., pick-and-place, push) to ensure diversity, not by physical validity (which does not exist yet).
- **1.2 Extract Features**: Extract latent vectors and expert masks using `torch.no_grad()` and memory chunking.
- **1.3 Save Features**: Save to `data/processed/features.npy`.

### Phase 2: Label Generation
- **2.1 Reconstruct 3D**: Run monocular depth estimation on filtered clips.
- **2.2 Kinematic Consistency Check**: Filter trajectories that are kinematically impossible (e.g., negative depth).
- **2.3 Generate Valid Labels**: Label original reconstructed trajectories as "valid".
- **2.4 Generate Invalid Labels**: Apply known synthetic perturbations (e.g., constant upward velocity) to a subset of trajectories to create "invalid" labels.
- **2.5 Generate Null Label Artifact**: For clips with low confidence (<0.9) or simulation failure, log to `excluded_samples.log` and assign "null" label in `labels.csv`. **Crucially, these samples are excluded from the final training/test CSV.**
- **2.6 Save Labels**: Save to `data/processed/labels.csv`.

### Phase 3: Prior Audit
- **3.1 Run Prior Audit**: Execute `prior_audit.py` to calculate `label_independence_score` (Pearson correlation between depth confidence and perturbation type). If correlation > 0.1, the audit fails.
- **3.2 Save Audit Report**: Save results to `data/processed/audit_report.json`. Fail if correlation is significant.

### Phase 4: Classification & Evaluation
- **4.1 Filter Data**: Remove "null" labels from training/test sets. Generate `filtering_report.json` logging the count of excluded vs. retained samples.
- **4.2 Train Classifier**: Train MLP/RF on filtered data.
- **4.3 Calculate Baseline**: Calculate **Majority Class Predictor** F1-score on the **filtered** held-out test set.
- **4.4 Evaluate Model**: Calculate F1, precision, recall.
- **4.5 Power Analysis**: Calculate MDE based on depth confidence variance.
- **4.6 Generate Associational Report**: Create `results_report.md` with mandatory "Associational Framing" section.

### Phase 5: Finalization
- **5.1 Update Manifest Hashes**: Generate `state/manifest.yaml` with content hashes.
- **5.2 Final Verification**: Run all contract tests and hygiene checks.