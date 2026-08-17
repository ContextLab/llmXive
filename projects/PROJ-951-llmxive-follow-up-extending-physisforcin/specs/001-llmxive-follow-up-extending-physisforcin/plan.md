# Implementation Plan: llmXive follow-up: extending "PhysisForcing: Physics Reinforced World Simulator for Robotic Manipula"

**Branch**: `001-llmxive-physs-filter` | **Date**: 2026-07-13 | **Spec**: `specs/001-llmxive-physs-filter/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-physs-filter/spec.md`

## Summary

This project implements a CPU-first pipeline to generate synthetic robotic manipulation videos, filter them using a PyBullet-based physics consistency score, and train a distilled diffusion model on the curated subset. The core hypothesis is that sample exclusion (discarding physically inconsistent videos based on a fixed absolute threshold) yields downstream policy performance comparable to training-time physics-informed optimization, without the computational cost of the latter. The plan strictly adheres to CPU-only constraints for generation and training, utilizing the GPU escape hatch only if the specific diffusion architecture requires CUDA kernels that cannot be emulated on CPU.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `torch` (CPU mode), `pybullet` (headless), `diffusers`, `transformers`, `scikit-learn`, `pandas`, `opencv-python`, `datasets` (streaming), `ruff`, `black`
**Storage**: Local filesystem (`data/` for raw/curated videos, `models/` for checkpoints)
**Testing**: `pytest`, `pytest-cov`
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7GB RAM, 14GB Disk)
**Project Type**: Research Pipeline / Data Curation Tool
**Performance Goals**: 
- Filtering: < 2 hours for 1000 videos (batched)
- Training: < 4 hours for 50M parameter model on curated subset
- Memory: < 6 GB RAM peak
**Constraints**: 
- NO GPU dependencies for generation/training unless explicitly offloaded to Kaggle (escape hatch).
- Strict adherence to fixed absolute threshold (score >= 60.0) for curation (Source: 2506.09162).
- All data must be streamable or sampleable to fit CI limits.
**Scale/Scope**: 
- Initial generation: videos (subset for validation)
- Curated dataset: a substantial majority of generated
- Final model: a large-scale parameter configuration

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence/Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, deterministic seeds (`src/utils/seeding.py`), and streaming data fetches from verified HuggingFace sources. |
| **II. Verified Accuracy** | **PASS** | All citations (Wan2.1, PyBullet, R-Bench) will be validated against the `# Verified datasets` block via the Reference-Validator Agent. The fixed threshold is cited from 2506.09162. |
| **III. Data Hygiene** | **PASS** | Raw data stored in `data/raw/` with checksums. Curated data in `data/curated/`. No in-place modifications. PII scan included in CI. |
| **IV. Single Source of Truth** | **PASS** | Metrics will be derived from `data/results/` CSVs, not hand-typed. Code logs will feed the final report. |
| **V. Versioning Discipline** | **PASS** | Artifacts (models, datasets) will carry content hashes. The `state/PROJ-951-llmxive-follow-up-extending-physisforcin.yaml` file is the Single Source of Truth for these hashes. The Advancement-Evaluator Agent will read/write this file on artifact change. |
| **VI. Physics-Consistency Verification** | **PASS** | Plan explicitly includes `src/filters/pybullet_filter.py` scoring trajectory continuity, contact conservation, and dynamic consistency, discarding videos with score < 60.0. |
| **VII. Benchmark Alignment** | **PASS** | Evaluation strictly uses R-Bench and PAI-Bench metrics as defined in `specs/001-llmxive-physs-filter/spec.md`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-physs-filter/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
```

### Source Code (repository root)

```text
projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/
├── data/
│   ├── raw/             # Downloaded/generated raw videos
│   ├── curated/         # Filtered videos (passing physics check)
│   ├── prompts/         # Text prompts (prompts.jsonl)
│   └── results/         # Evaluation metrics (JSON/CSV)
├── src/
│   ├── generation/
│   │   ├── wan2_generator.py   # FR-001: Video generation
│   │   └── prompts.py          # Prompt management
│   ├── filters/
│   │   ├── pybullet_filter.py  # FR-002: Physics scoring
│   │   ├── mujoco_validator.py # FR-008: Independent validation
│   │   └── reconstruction.py   # Video-to-Simulation reconstruction
│   ├── training/
│   │   ├── config.py           # FR-004: Training config
│   │   └── trainer.py          # Diffusion training loop
│   ├── augmentation/
│   │   └── augment.py          # FR-009: Data augmentation
│   ├── evaluation/
│   │   ├── r_bench.py          # FR-005: R-Bench metrics
│   │   ├── pai_bench.py        # FR-005: PAI-Bench metrics
│   │   ├── tost_test.py        # FR-006: TOST equivalence test
│   │   └── downstream_task.py  # New: Downstream policy success rate
│   ├── utils/
│   │   ├── logging.py          # T006: Logging setup
│   │   ├── verify_env.py       # T008: Env check
│   │   ├── seeding.py          # T009: Seed management
│   │   └── profile_memory.py   # T006b: Memory profiling
│   └── cli/
│       └── main.py             # Entry point
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── config.yaml             # T007b: Config schema
├── requirements.txt        # T002: Dependencies
├── pyproject.toml          # T003: Linting/Formatting config
├── .ruff.toml              # T003: Ruff config
└── README.md
```

**Structure Decision**: Selected Option 1 (Single Project) but modularized into `src/` subpackages to separate generation, filtering, training, augmentation, and evaluation logic. This ensures the `code/` directory is fully populated with the required `src/`, `tests/`, and `data/` subdirectories, satisfying T001 and T001b. `config.yaml` and `requirements.txt` are placed at the root of `code/` to satisfy T002 and T007b.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Complexity | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Dual Physics Engines** (PyBullet + MuJoCo) | Required by FR-008 to ensure filter scores are not circularly correlated with benchmark metrics. | Using only PyBullet for both filtering and validation would violate the independence requirement for scientific validity. |
| **Streaming Data Pipeline** | Required to handle video datasets within 7GB RAM limit. | Loading full datasets into memory would exceed CI constraints and cause OOM errors. |
| **TOST Equivalence Testing** | Required by FR-006 to statistically validate "comparability" rather than just "difference". | Standard t-tests only detect differences; they cannot confirm equivalence within a predefined margin. |
| **Video-to-Simulation Reconstruction** | Required to convert MP4 frames to PyBullet state vectors. | Direct video parsing by PyBullet is impossible; a CV pipeline is necessary for feasibility. |
| **Real-World Proxy Validation** | Required to break circularity between filter and validator. | Comparing two simulators only confirms consistency between them, not physical correctness. |

## Phased Implementation Plan

### Phase 0: Research & Validation (Constitution Gate)
1.  **Reference-Validator Run**: Execute the Reference-Validator Agent against all citations in `research.md`. Ensure `CITATION_TITLE_OVERLAP_THRESHOLD` is met.
2.  **Dataset Verification**: Confirm access to `RoboTIPS` (prompts) and `Wan2.1` (weights).
3.  **Calibration**: Run a pilot batch (n=20) to calibrate the fixed threshold (score >= 60.0) against ground-truth physics.

### Phase 1: Data Generation & Curation
1.  **Prompt Loading**: Load prompts from `data/prompts.jsonl`.
2.  **Video Generation**: Generate videos using Wan2.1 (CPU or Kaggle offload).
3.  **Reconstruction**: Convert videos to simulation states using `src/filters/reconstruction.py`.
4.  **Filtering**: Score videos using PyBullet. Discard if score < 60.0.
5.  **Curation**: Save passing videos to `data/curated/`.

### Phase 2: Power Analysis (Pilot)
1.  **Variance Estimation**: Run a small-scale training on the curated subset (n=30).
2.  **Power Calculation**: Estimate variance of R-Bench scores. Calculate required n for TOST (power >= 0.80).
3.  **Augmentation Trigger**: If n < required, trigger Phase 3 (Augmentation).

### Phase 3: Data Augmentation (FR-009)
1.  **Augment**: Apply physics-preserving augmentation (temporal cropping, color jitter) to reach target n.
2.  **Verify**: Ensure augmented samples maintain physics scores >= 60.0.

### Phase 4: Model Training
1.  **Baseline Training**: Train PhysisForcing baseline on *raw* (unfiltered) data with joint optimization.
2.  **Filtered Training**: Train distilled model on *curated* data.
3.  **Timing**: Record `training_duration` for both. Abort if > 4 hours.

### Phase 5: Evaluation & Statistics
1.  **Benchmarks**: Run R-Bench and PAI-Bench on both models.
2.  **Downstream Task**: Train a lightweight policy on each dataset; measure success rate on a separate task.
3.  **Correlation**: Compute Pearson correlation between PyBullet and MuJoCo scores (Target < 0.95).
4.  **TOST**: Perform TOST equivalence test (predefined equivalence margin).
5.  **Reporting**: Generate `benchmark_results.json` with all metrics.

## Dependencies

- **requirements.txt**: `torch`, `pybullet`, `diffusers`, `transformers`, `scikit-learn`, `pandas`, `opencv-python`, `datasets`, `pytest`, `ruff`, `black`
- **pyproject.toml**: Configures `ruff` and `black` for linting/formatting.
- **config.yaml**: Defines `filter_discard_percent` (set to 0, as we use fixed threshold), `training_epochs`, etc.

## Risk Mitigation

- **Data Scarcity**: If < 30 videos pass filtering, FR-009 (augmentation) is triggered.
- **Training Divergence**: NaN loss check included; retry with lower learning rate (max a limited number of attempts).
- **Simulation Crashes**: Robust error handling in PyBullet filter assigns score 0 and logs the failure.
- **Compute Limits**: If CPU fails, offload to Kaggle GPU with quantized model.