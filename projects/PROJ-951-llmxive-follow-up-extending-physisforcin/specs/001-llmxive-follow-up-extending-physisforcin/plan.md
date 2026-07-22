# Implementation Plan: llmXive follow-up: extending "PhysisForcing: Physics Reinforced World Simulator for Robotic Manipula"

**Branch**: `001-llmxive-physs-filter` | **Date**: 2026-07-13 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-llmxive-physs-filter/spec.md`

## Summary

This project implements a "Physics-First" curation pipeline for synthetic robotic manipulation videos. The core hypothesis is that a lightweight, post-generation physics filter (using PyBullet) can discard physically inconsistent samples to create a high-quality dataset. 

The experimental design is split into two distinct analyses to address methodological rigor:
1.  **Primary Analysis (Causal)**: Compares a model trained on the **Curated** dataset against a **Randomized Control** model (trained on a random subset of the same size). This isolates the effect of the *filter* (data quality) from the effect of *data reduction*. Both models use the same static training algorithm.
2.  **Secondary Analysis (Descriptive Benchmark)**: Compares the **Curated** model (static training) against the **PhysisForcing** baseline (joint optimization). This comparison is explicitly **not** a test of the "filtering alone" hypothesis, as it confounds data quality with training algorithm. Instead, it serves as a descriptive upper-bound benchmark to measure the absolute performance ceiling of static training on curated data versus state-of-the-art joint optimization. The "comparability" claim (≤15% gap) is defined as a measure of *generalization to unseen physical properties* (orthogonal to the filter's selection criteria), not a direct replication of the filter's score.

The entire pipeline is designed to run on CPU-only infrastructure (GitHub Actions free tier) for filtering/training/evaluation, with a scaled-down GPU offload for generation.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: 
- `torch` (installed with CUDA support for generation offload; explicitly run in CPU mode for filtering/training/evaluation)
- `diffusers`, `pybullet`, `mujoco` (for R-Bench/PAI-Bench re-implementation), `datasets`, `pandas`, `scikit-learn`, `ruff`, `black`  
**Storage**: Local filesystem (`data/raw`, `data/curated`, `data/eval`, `data/validation`), JSON/Parquet metadata  
**Testing**: `pytest` (unit/integration), `pytest-cov`  
**Target Platform**: Linux (GitHub Actions x64), CPU-first with optional Kaggle GPU offload for generation  
**Project Type**: Research pipeline / Data curation tool  
**Performance Goals**: 
- Filter throughput: >10 videos/hour (CPU)
- Training: <4 hours for 10 epochs on 50M model (CPU)
- Memory: <6GB RAM peak during filtering/training  
**Constraints**: 
- Core logic (filtering/training/evaluation) runs CPU-only.
- Generation uses GPU offload (Kaggle) with `device="cuda"`.
- R-Bench/PAI-Bench implemented using MuJoCo to ensure independence from PyBullet filter.
- No circular evaluation: Filter (PyBullet) vs. Final Score (MuJoCo) with orthogonality check.

> **Note on Dataset Variables**: The plan relies on generated synthetic data (Wan2.1) rather than pre-existing datasets for the training corpus. The "Verified datasets" list provides the *source* for prompts and initial seed videos, but the core "CuratedDataset" is a derived artifact of this pipeline. The plan strictly avoids inventing URLs for the generated videos.

## Constitution Check

**Status**: PASSED (with explicit methodological notes)

| Principle | Check | Notes |
|-----------|-------|-------|
| **I. Reproducibility** | ✅ | Random seeds pinned in `src/utils/seeding.py`. External datasets fetched via `datasets.load_dataset` with specific revisions. |
| **II. Verified Accuracy** | ✅ | All citations (R-Bench, PAI-Bench, PhysisForcing) map to verified sources or standard benchmarks. No title-token-overlap violations. |
| **III. Data Hygiene** | ✅ | Raw data (generated videos) preserved. Curated data written to new files. Checksums recorded in `state/`. No PII (synthetic data). |
| **IV. Single Source of Truth** | ✅ | Evaluation metrics derived strictly from `code/` outputs. No hand-typed stats in `plan.md`. |
| **V. Versioning Discipline** | ✅ | Artifacts will carry content hashes. `state.yaml` updated on artifact changes. |
| **VI. Physics-Consistency Verification** | ✅ | Explicitly implemented via PyBullet filter (US-1) with `continuity_score` and `contact_score` sub-metrics. Independent MuJoCo validation (FR-008) added with orthogonality check to ensure metrics are distinct (correlation < 0.95). |
| **VII. Benchmark Alignment** | ✅ | Evaluation strictly limited to R-Bench and PAI-Bench metrics, re-implemented in MuJoCo. The "comparability" claim is restricted to generalization metrics orthogonal to the filter. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-physs-filter/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── video_sample.schema.yaml
│   ├── curated_dataset.schema.yaml
│   ├── benchmark_result.schema.yaml
│   └── mujo_co_validation_result.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/
├── src/
│   ├── __init__.py
│   ├── generation/
│   │   ├── __init__.py
│   │   ├── wan21_generator.py      # Wan2.1 inference wrapper
│   │   └── prompts.py              # Prompt loading & management
│   ├── filtering/
│   │   ├── __init__.py
│   │   ├── pybullet_filter.py      # Physics scoring logic (continuity + contact)
│   │   └── scorer.py               # Trajectory continuity & contact metrics
│   ├── training/
│   │   ├── __init__.py
│   │   ├── config.py               # Training hyperparameters
│   │   └── trainer.py              # CPU-optimized diffusion training
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── r_bench.py              # R-Bench metric implementation (MuJoCo)
│   │   ├── pai_bench.py            # PAI-Bench metric implementation (MuJoCo)
│   │   ├── stats.py                # Statistical analysis (t-test, Mann-Whitney)
│   │   └── mujoco_validator.py     # Independent validation (PyBullet vs MuJoCo)
│   ├── augmentation/
│   │   ├── __init__.py
│   │   └── geometric_augmenter.py  # Data augmentation (FR-009)
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── io_utils.py             # File I/O, checksums
│   │   ├── logging.py              # Structured logging
│   │   ├── seeding.py              # Random seed management
│   │   ├── profile_memory.py       # Memory monitoring
│   │   └── verify_env.py           # Environment checks
│   └── cli/
│       └── main.py                 # Entry point
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_filtering.py
│   │   └── test_scoring.py
│   └── integration/
│       └── test_pipeline.py
├── data/
│   ├── raw/                        # Generated videos (immutable)
│   ├── curated/                    # Filtered videos
│   ├── control/                    # Randomized control subset
│   ├── eval/                       # Evaluation results
│   └── validation/                 # MuJoCo validation results
├── config.yaml                     # Global configuration
├── requirements.txt                # Dependencies
├── pyproject.toml                  # Project metadata & tooling config
└── README.md                       # Project overview
```

**Structure Decision**: Single-project structure selected to minimize overhead for a research pipeline. All logic is encapsulated in `src/` with clear separation of concerns (Generation, Filtering, Training, Evaluation, Augmentation). `data/` is strictly hierarchical to enforce the "Data Hygiene" principle.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Randomized Control Group** | Required to isolate the effect of the *filter* from *data reduction*. | Comparing Filtered vs. Unfiltered is confounded by subset dependency. Comparing Filtered vs. PhysisForcing confounds data quality with training algorithm. |
| **Independent Physics Validation (MuJoCo)** | Required by FR-008 and Constitution Principle VI to prevent circular evaluation. | Using only PyBullet for both filtering and final validation would violate the "Single Source of Truth" and "Verified Accuracy" principles. |
| **Dual-Benchmark Evaluation (R-Bench + PAI-Bench)** | Required by FR-005 and Constitution Principle VII for comprehensive physical consistency assessment. | Single-benchmark evaluation is insufficient to claim "comparable" performance to the PhysisForcing baseline across different physical domains. |
| **CPU-First Design with GPU Escape Hatch** | Required by compute feasibility constraints (GitHub Actions free tier). | A GPU-only design would be infeasible on the primary CI runner and would fail the "Compute Feasibility" gate. A fake CPU approximation of the generator is rejected as fabrication; the real scaled GPU run is planned for offload. |
| **MuJoCo Re-implementation of Benchmarks** | Required to break circularity between PyBullet filter and final score. | Using existing PyBullet-based benchmarks would make the evaluation circular (selection metric = evaluation metric). |
| **Orthogonality Check** | Required to ensure evaluation metrics are not trivially correlated with filter scores. | Without this, the "comparability" claim would be a tautology (selecting for X and measuring X). |

## Phase Ordering & Task Dependencies

### Phase 1: Foundation & Setup
- **T001**: Initialize Project Structure (Directories, `requirements.txt`, `pyproject.toml`).
- **T002**: Setup Python 3.11 Environment.
- **T003**: Configure Linting/Formatting (Ruff, Black).
- **T005-T010**: Implement Utility Modules (`io_utils`, `logging`, `seeding`, `verify_env`, `profile_memory`).
- **T012**: Load Verified Prompts (Static Asset) [P]
  - *Input*: Verified prompt sources.
  - *Output*: `data/prompts.jsonl`.

### Phase 2: Data Generation & Filtering
- **T013**: Generate Raw Videos (Wan2.1) [P]
  - *Depends*: T012 (Prompts ready).
  - *Output*: `data/raw/videos/`, `data/raw/metadata.jsonl`.
- **T014**: Apply PyBullet Physics Filter
  - *Output*: `data/curated/`, `data/curated/scores.parquet` (with `continuity_score`, `contact_score`).
- **T015**: Generate Randomized Control Subset
  - *Output*: `data/control/` (random subset of same size as curated).

### Phase 3: Validation (Pre-Training)
- **T018**: Run MuJoCo Validation & Orthogonality Check (SC-006)
  - *Input*: `data/curated/` videos.
  - *Output*: `data/validation/mujo_co_validation_result.json` (Correlation coefficient).
  - *Gate*: Proceed only if correlation < 0.95 (distinct metrics). If correlation ≥ 0.95, adjust evaluation metrics or abort.

### Phase 4: Training
- **T016**: Train Filtered Model (Curated Data)
- **T017**: Train Control Model (Random Data)
- **T019b**: Data Augmentation (if n < 50)
  - *Depends*: T014/T015 (if sample size insufficient).

### Phase 5: Benchmarking
- **T019**: Compute R-Bench/PAI-Bench Scores (MuJoCo)
  - *Input*: Trained Models (Filtered, Control).
  - *Output*: `data/eval/results.json` (with `evaluation_engine: "MuJoCo"`).
- **T020**: Perform Statistical Significance Testing
  - *Input*: Benchmark Scores.
  - *Output*: `data/eval/stats_report.json`.
- **T022**: Secondary Benchmark (PhysisForcing Comparison)
  - *Input*: Filtered Model Score vs. PhysisForcing Paper Report.
  - *Output*: `data/eval/secondary_benchmark.json`.
  - *Note*: This is a descriptive comparison, not a causal test of the filtering hypothesis.

### Phase 6: Verification
- **T011**: Integration Test (End-to-End Pipeline)
  - *Depends*: All previous phases.
  - *Output*: Test logs, pass/fail status.
  - *Note*: This test runs the full pipeline from T012 to T020 to verify end-to-end correctness.
