# Implementation Plan: Non-Neural Approximation of VLA Priors

**Branch**: `001-non-neural-vla-approximation` | **Date**: 2026-08-02 | **Spec**: `specs/001-non-neural-vla-approximation/spec.md`
**Input**: Feature specification from `/specs/001-non-neural-vla-approximation/spec.md`

## Summary

This project implements a CPU-only pipeline to approximate Vision-Language-Action (VLA) priors using non-neural models (Decision Trees, Gaussian Mixture Models). The approach ingests the Qwen-VLA dataset, clusters action sequences by kinematic features (engineered from time-series), trains lightweight models on frozen BERT embeddings, and evaluates trajectory fidelity in a PyBullet simulation. The plan strictly adheres to the "CPU-only" constraint, explicitly rejecting any GPU offloading logic.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only, pinned in `code/requirements.txt`), `transformers` (frozen BERT), `scikit-learn`, `pandas`, `pybullet`, `datasets`  
**Storage**: `data/` (raw parquet, derived csv/parquet), `code/` (scripts)  
**Testing**: `pytest` (unit, integration, simulation edge cases)  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, ample RAM)  
**Project Type**: Research Pipeline / CLI  
**Performance Goals**: Inference ≤ 2s/prompt; Total runtime ≤ 6h; Memory ≤ 7GB  
**Constraints**: No GPU usage; No synthetic data substitution; Strict reproducibility (seeds pinned).  
**Scale/Scope**: A variable number of clusters (adaptive) will be determined based on data characteristics., A representative set of test prompts per task type.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

**Single Source of Truth for Constraints**: The `code/requirements.txt` file is the **Single Source of Truth** for the CPU-only constraint. All dependency versions, specifically `torch` (CPU-only build), are pinned there to ensure Principle I (Reproducibility) and Principle VI (Simulation-Based Validation) are met.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`; `datasets.load_dataset` used for canonical fetch; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | All dataset URLs cited in `research.md` are from the verified list; no external citations invented. |
| **III. Data Hygiene** | **PASS** | Raw data checksummed; derivations written to new files; no in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All metrics trace to `data/` outputs; no hand-typed stats in `paper/`. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes tracked in state YAML; `updated_at` updated on change. |
| **VI. Simulation-Based Validation** | **PASS** | **Critical Fix:** All evaluation occurs in PyBullet on CPU. **Removed** Task T043 (GPU-Offload) as it contradicted this principle. |
| **VII. Distillation Fidelity Thresholds** | **PASS** | Evaluation explicitly reports fidelity gaps; claims require quantitative data. |

## Project Structure

### Documentation (this feature)

```text
specs/001-non-neural-vla-approximation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
code/
├── 01_ingest_cluster.py      # FR-001, FR-002, FR-002a
├── 02_train_models.py        # FR-003
├── 03_inference.py           # FR-004
├── 04_simulate_eval.py       # FR-005, FR-006
├── utils/
│   ├── data_loader.py        # Verified dataset fetching
│   ├── kinematics.py         # Feature extraction (Time-series to stats)
│   └── simulation.py         # PyBullet wrapper (CPU)
├── tests/
│   ├── test_ingest.py        # T040: Ingestion edge cases
│   ├── test_simulation.py    # T040: Simulation crash handling
│   └── test_ood.py           # T040: OOD prompt handling
├── requirements.txt          # Pinned dependencies (Source of truth for CPU constraint)
└── main.py                   # Entry point

data/
├── raw/                      # Downloaded parquet (checksummed)
├── processed/                # Clustered data, embeddings, engineered features
└── results/                  # Simulation CSVs, stats

contracts/
├── dataset.schema.yaml       # Input data validation
├── trajectory.schema.yaml    # Output trajectory validation
├── simulation_result.schema.yaml # Evaluation output validation
├── model.schema.yaml         # Model artifact validation
└── simulation.schema.yaml    # Simulation configuration validation
```

**Structure Decision**: Single project structure selected to minimize overhead on the CI runner. All logic is script-based to ensure reproducibility and easy debugging on CPU.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Task T043 (GPU-Offload)** | **REMOVED**. Proposed detecting CUDA errors and offloading to GPU. | **Resolved**. Directly contradicted Constitution Principle VI (CPU-only) and FR-004. Removed from plan. No GPU fallback implemented. |
| **None** | The plan strictly follows the spec's CPU constraint. | The rejected GPU-offload task (T043) was removed as it violated Constitution Principle VI. |

## Data Flow & Validation

1.  **Ingestion**: `file-000.parquet` -> `data/raw/vla_episodes.parquet` (Checksum verified).
2.  **Feature Engineering**: Raw action sequences -> Statistical features (Mean/Max/Variance of velocity, acceleration, joint angles) -> `data/processed/kinematic_features.csv`.
3.  **Clustering**: Features -> K-means (k=50, adaptive) -> `data/processed/cluster_assignments.csv`.
4.  **Validation**: Silhouette Score calculated. If < 0.25, k reduced (FR-002a).
5.  **Model Training**: BERT embeddings + Cluster Features -> Decision Tree/GMM -> `data/models/cluster_*.pkl`.
6.  **Inference**: New Prompt -> BERT -> Cluster -> Trajectory -> `data/processed/generated_trajectories.json`.
7.  **Simulation**: Trajectories -> PyBullet -> `data/results/simulation_results.csv`.
8.  **Evaluation**: Paired t-tests (Non-Neural vs. VLA Proxy vs. Random).

## Prompt Alignment Protocol

To ensure valid statistical comparison (paired t-tests), the following protocol is enforced:
1.  The **VLA Proxy** is a static artifact containing a set of `(prompt_id, prompt_text, trajectory)` pairs.
2.  The **Non-Neural Test Set** is derived *exclusively* from the `prompt_id` list in the VLA Proxy artifact.
3.  The simulation runs the non-neural model on these exact prompts.
4.  The "paired" nature is guaranteed because both models (Proxy and Non-Neural) are evaluated on the identical set of text instructions.

## Construct Validity Gate

Before model training (FR-003), a **Construct Validity Check** is performed:
1.  Compute Mutual Information or R² between BERT embeddings and kinematic features.
2.  **Threshold**: If R² < 0.1 (or MI < threshold), the hypothesis that "text determines kinematics" is considered to have failed.
3.  **Action**: If the threshold is not met, the pipeline **HALTS** model training, logs a "Hypothesis Failure" report, and proceeds directly to the negative result phase. This prevents wasted compute on a known-to-fail mapping.

## Manifold Robustness Mitigation

To address the risk of K-means failing on non-convex trajectory manifolds:
1.  **Primary**: K-means with adaptive $k$ (FR-002a).
2.  **Diagnostic**: Calculate Silhouette Score and Calinski-Harabasz Index.
3.  **Fallback**: If K-means diagnostics indicate poor fit (e.g., low silhouette despite high $k$), the pipeline switches to **Hierarchical Agglomerative Clustering (HAC)** with Ward linkage, which is better suited for complex manifolds and still feasible on CPU.
4.  **Validation**: The chosen clustering method must yield a valid cluster count (k > 1) or a single global model with a "degenerate" warning.
