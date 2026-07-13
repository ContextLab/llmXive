# Implementation Plan: llmXive follow-up: extending "PhysisForcing: Physics Reinforced World Simulator for Robotic Manipula"

**Branch**: `001-llmxive-physs-filter` | **Date**: 2026-07-13 | **Spec**: `specs/001-llmxive-physs-filter/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-physs-filter/spec.md`

## Summary

This project investigates whether a lightweight, post-generation physics-consistency filter applied to synthetic robotic manipulation videos can yield physical consistency in downstream policy learning comparable to training-time physics-informed joint optimization. The technical approach involves generating synthetic videos using the Wan2.1 model, filtering them via a CPU-based PyBullet headless simulation to score trajectory continuity and contact conservation, discarding the bottom **[deferred]** of samples, and training a distilled diffusion model with a reduced parameter count on the curated dataset. The final model is evaluated against a **Physics-Informed Training Proxy** (mimicking the PhysisForcing baseline) and an unfiltered baseline on R-Bench and PAI-Bench, with statistical significance testing to determine if the performance gap is within 15%.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only), `pybullet` (headless), `diffusers`, `transformers`, `scikit-learn`, `pandas`, `numpy`, `opencv-python` (headless), `requests`, `sam2`, `zoe_depth`, `mujoco`  
**Storage**: Local file system (`data/raw`, `data/curated`, `data/eval`), JSON/Parquet for metadata  
**Testing**: `pytest` (unit/integration), custom validation scripts for physics consistency  
**Target Platform**: Linux (GitHub Actions free-tier: limited CPU resources, 7 GB RAM, 14 GB disk, no GPU)  
**Project Type**: Computational Research Pipeline  
**Performance Goals**: Training ≤ 4 hours on CPU; Filtering ≤ 2 hours; Memory < 6 GB peak; No CUDA dependencies  
**Constraints**: Strict CPU-only execution; No large model training from scratch; Dataset sampling required to fit RAM; Statistical power requirements (n ≥ 30)  
**Scale/Scope**: An initial batch of **~1000** generated videos will be produced. A curated set of **~600** videos (after a **[deferred]** discard rate) will be used for training. A model with a parameter count in the order of tens of millions will be trained.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence/Action |
|-----------|--------|-----------------|
| **I. Reproducibility** | PASS | Plan mandates pinned `requirements.txt`, fixed random seeds, and isolated virtualenv execution. All artifacts (videos, models, scores) will be stored with content hashes. |
| **II. Verified Accuracy** | PASS | Citations for datasets (Wan2.1, RobotBench) restricted to the provided verified URLs. No fabricated URLs. Baseline definitions (PhysisForcing Proxy) will be traced to primary sources in `research.md`. |
| **III. Data Hygiene** | PASS | Raw generated videos and filtered outputs will be checksummed. No in-place modification; derivations written to new files. PII scan included in CI. |
| **IV. Single Source of Truth** | PASS | All performance metrics (R-Bench, PAI-Bench) will be computed by code and stored in `data/eval/results.json`. Paper figures/statistics will reference these files. |
| **V. Versioning Discipline** | PASS | Content hashes for all data artifacts will be recorded in `state/projects/PROJ-951-llmxive-follow-up-extending-physisforcin.yaml`. |
| **VI. Physics-Consistency Verification** | PASS | The plan explicitly implements the CPU-based PyBullet filter for trajectory continuity and contact conservation, discarding the bottom **[deferred]** of videos as required by the Constitution. |
| **VII. Benchmark Alignment** | PASS | Evaluation strictly limited to R-Bench and PAI-Bench metrics as per the spec and constitution. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-physs-filter/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/
├── data/
│   ├── raw/                  # Raw generated videos (MP4)
│   ├── curated/              # Filtered videos + metadata (JSON/Parquet)
│   └── eval/                 # Evaluation results (JSON)
├── src/
│   ├── generation/
│   │   ├── wan21_generator.py    # Wan2.1 inference (CPU)
│   │   └── prompts.py            # Prompt management
│   ├── filtering/
│   │   ├── cv_pipeline.py        # SAM2/Depth extraction
│   │   ├── prompt_to_scene.py    # Prompt-to-Scene translation
│   │   ├── pybullet_filter.py    # Physics consistency scoring
│   │   └── score_utils.py        # Metric calculation
│   ├── training/
│   │   ├── diffusion_trainer.py  # 50M model training (CPU)
│   │   ├── augmentation.py       # Temporal jitter/flip logic
│   │   └── config.py             # Training hyperparameters
│   ├── evaluation/
│   │   ├── r_bench.py            # R-Bench scorer
│   │   ├── pai_bench.py          # PAI-Bench scorer
│   │   ├── mujoco_validator.py   # Independent validation (FR-008)
│   │   └── stats.py              # Statistical testing (LMM)
│   └── utils/
│       ├── io_utils.py           # File I/O, checksumming
│       └── logging.py            # Logging configuration
├── tests/
│   ├── unit/
│   │   ├── test_filter.py
│   │   └── test_stats.py
│   └── integration/
│       └── test_pipeline.py
└── requirements.txt
```

**Structure Decision**: The project follows a modular pipeline structure (`generation` → `filtering` → `training` → `evaluation`) to ensure clear separation of concerns and reproducibility. This aligns with the Constitution's requirement for traceability from code to data. The `data/` directory is split into `raw`, `curated`, and `eval` to enforce the "Data Hygiene" principle (no in-place modification).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Two-stage pipeline (Generate → Filter → Train)** | The hypothesis specifically tests if *post-generation filtering* is sufficient, necessitating a distinct filtering step before training. | A single-stage training with joint optimization (PhysisForcing) would test a different hypothesis (training-time physics vs. sample curation). |
| **CPU-only constraint** | The project must run on GitHub Actions free-tier (no GPU). | GPU-based methods are faster but violate the compute feasibility constraint and would make the project non-reproducible in the target environment. |
| **Statistical testing (LMM)** | Required to account for batch effects in multi-batch generation (n≥30 from 3 batches). | Simple t-tests would confound model performance with batch-specific generation artifacts. |
| **Independent Validation (MuJoCo)** | Required by FR-008 to avoid circularity in physics scoring. | Relying solely on PyBullet would validate the reconstruction, not the video's physical consistency. |
| **Prompt-to-Scene Translation** | Required to generate a ground truth trajectory from text prompts without a robotic manipulation dataset. | Using a generic dataset would not match the specific prompts; a symbolic parser is the only CPU-tractable option. |

## Implementation Phases

### Phase 0: Setup & Environment
1.  Initialize virtual environment with CPU-only `torch`.
2.  Install `pybullet`, `mujoco`, `sam2`, `zoe_depth`, `diffusers`.
3.  Verify environment with `python -c "import torch; import pybullet; import mujoco; print('OK')"`.

### Phase 1: Data Generation
1.  Load prompts from **RobotBench** (verified).
2.  Generate a substantial volume of videos using Wan2.1 (CPU-compatible subset or distilled version).
3.  Save raw videos to `data/raw/` with checksums.
4.  Generate multiple independent batches (A, B, C) to support statistical power.

### Phase 2: Physics Consistency Filtering
1.  **Prompt-to-Scene Translation**: Parse text prompts to select standard PyBullet assets (e.g., "grasp cup" -> cube object, plane surface) and define initial poses.
2.  **Canonical Simulation**: Run a deterministic PyBullet simulation to generate the "intended" trajectory (ground truth) for each prompt.
3.  **CV Pipeline**: Extract 3D trajectories from video frames using **SAM2** (segmentation) and **ZoeDepth** (depth estimation), followed by a Kalman Filter for smoothing. **Assumption**: Fixed camera intrinsics and static camera pose are used for 3D projection.
4.  **Scoring**: Compare extracted trajectory vs. canonical simulation using PyBullet to score continuity and contact conservation. **Note**: This is a *proxy* metric for physical consistency.
5. **Filtering**: Discard the bottom **[deferred]** of videos based on the score distribution.
6.  **Output**: Save curated dataset to `data/curated/`.

### Phase 2.5: Data Augmentation (FR-009)
1.  **Trigger**: If the curated set size < 30.
2.  **Action**: Apply **Temporal Jittering** (frame skipping/duplication) and **Geometric Flipping** to reach n ≥ 30.
3.  **Record**: Log augmentation parameters in metadata.

### Phase 3: Model Training
1.  Train a diffusion model with a moderate parameter count on the curated dataset.
2.  Monitor for NaN loss; abort and retry with adjusted learning rate if detected.
3.  Ensure training completes within 4 hours on CPU.

### Phase 4: Evaluation & Statistical Testing
1.  **Baseline Reproduction**: Re-train the **Physics-Informed Training Proxy** (standard diffusion + physics loss) on the *same* raw dataset to mimic the PhysisForcing baseline.
2.  **Evaluation Set**: Draw n=30 samples via stratified sampling from all batches (A, B, C).
3.  **Benchmarking**: Evaluate the filtered model and baseline on R-Bench and PAI-Bench.
4.  **Statistical Test**: Perform Linear Mixed Model (LMM) analysis with 'Batch' as a random effect.
5.  **Power Analysis**: Verify n=30 provides sufficient power (α=0.05, 1-β=0.8) for the 15% threshold. If power is insufficient, report as "inconclusive".

### Phase 5: Independent Validation (FR-008)
1.  **MuJoCo Re-scoring**: Run the curated videos through **MuJoCo** using the *same* CV-extracted trajectories and prompt-derived initial conditions.
2.  **Correlation Analysis (SC-006)**: Calculate the correlation coefficient between PyBullet scores and MuJoCo scores.
3.  **Independence Verification**: Verify that the correlation coefficient is < 0.95 to confirm that the two engines are not validating the exact same reconstruction artifact.

## Risk Mitigation

-   **Compute Feasibility**: If Wan2.1 is too large for CPU, switch to a distilled CPU-compatible video model and document the substitution.
-   **Dataset Size**: If n < 30 after filtering, trigger the defined augmentation (Temporal Jittering) immediately.
-   **Circularity**: Mitigated by using a prompt-derived canonical simulation as the independent ground truth for both PyBullet and MuJoCo, and by comparing engine-to-engine consistency.
-   **CV Reconstruction Error**: Acknowledged as a primary source of error. The physics score is treated as a proxy metric. A subset of videos will be manually reviewed to estimate reconstruction accuracy.
