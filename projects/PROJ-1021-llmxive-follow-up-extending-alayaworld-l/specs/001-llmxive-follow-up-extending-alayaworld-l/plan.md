# Implementation Plan: llmXive follow-up: extending "AlayaWorld: Long-Horizon and Playable Video World Generation"

**Branch**: `001-llmxive-alayaworld-extend` | **Date**: 2026-08-20 | **Spec**: `specs/001-llmxive-follow-up-extending-alayaworld-l/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-alayaworld-l/spec.md`

## Summary

This project implements a hybrid video generation pipeline that combines a frozen "AlayaWorld" autoregressive model with a lightweight, deterministic symbolic logic layer. The primary goal is to quantify and reduce "Semantic Drift" in long-horizon interactive video sequences. The technical approach involves generating baseline video sequences, running a parallel symbolic simulation of object states (HP, inventory), and calculating a drift score via classical computer vision (sparse optical flow, color histograms). A "correction token" mechanism will then inject state constraints into the generation loop to force visual consistency with the symbolic ground truth. The entire pipeline is designed to run on a CPU-only, multi-core, limited RAM environment.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only build, quantized), `opencv-python`, `scikit-learn`, `numpy`, `pandas`, `datasets` (streaming mode), `scipy` (for statistical tests), `jsonschema`  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `data/results/`, `data/annotations/`)  
**Testing**: `pytest` (unit tests for symbolic engine, integration tests for drift calculation)  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7GB RAM)  
**Project Type**: Research/Computational Experiment  
**Performance Goals**: ≤30 minutes wall-clock time per 60s sequence; ≤7GB peak RAM.  
**Constraints**: No GPU acceleration; strict adherence to 8-bit/quantized model inference; deterministic symbolic engine (with a fixed seed).  
**Scale/Scope**: 10 random seeds × 2 conditions (baseline/hybrid) × 10 action sequences = 200 total sequence evaluations.

> **Note on Dataset**: The "AlayaWorld" dataset has **no verified source** found in the project's verified block. The plan assumes the existence of a local or programmatic access point for the "AlayaWorld" model weights and sample sequences as a prerequisite. If no open download exists, the implementation will fail at the data ingestion step, and the plan will flag this as a blocking feasibility issue. The symbolic engine and CV pipeline will be tested against a synthetic "mock" video stream for *unit testing* only, but the primary research results depend on the availability of the AlayaWorld dataset. If the dataset is unavailable, the study will be limited to a "Methodological Validation" report.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **CONDITIONAL** | All random seeds pinned (, plus 10 seed variations). Dependencies pinned. **Caveat**: Reproducibility is contingent on the availability of the AlayaWorld dataset, which is currently unverified. If the dataset is unavailable, the primary experiment cannot be reproduced. |
| **II. Verified Accuracy** | **CONDITIONAL** | Citations limited to the "Verified datasets" block (currently empty for AlayaWorld). **Caveat**: The dataset citation is unverified; this principle is passed only if the dataset is provided locally or a verified source is found. |
| **III. Data Hygiene** | **PASS** | Checksums recorded for all downloaded/processed data. Raw data immutable. Annotations stored in `data/annotations/`. |
| **IV. Single Source of Truth** | **PASS** | All metrics derived from `data/results/` JSON logs. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes tracked in `state/` YAML. |
| **VI. Deterministic Symbolic Grounding** | **PASS** | Symbolic engine implemented in pure Python with fixed seed (42). No stochastic elements. |
| **VII. Edge-Device Inference Constraints** | **PASS** | Pipeline designed for CPU-only, quantized inference. Memory and time constraints explicitly monitored. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-alayaworld-extend/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 0/1 Output (Finalized set)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-1021-llmxive-follow-up-extending-alayaworld-l/
├── code/
│   ├── __init__.py
│   ├── symbolic_engine.py      # Deterministic logic layer (FR-002)
│   ├── cv_pipeline.py          # Sparse optical flow, color histograms (FR-003)
│   ├── generator.py            # AlayaWorld wrapper + correction tokens (FR-001, FR-004)
│   ├── metrics.py              # Drift score calculation (FR-003)
│   ├── stats.py                # Shapiro-Wilk, Wilcoxon tests (FR-006)
│   └── main.py                 # Orchestration script
├── data/
│   ├── raw/                    # Downloaded AlayaWorld sequences (if available)
│   ├── annotations/            # Ground truth annotations (T003b)
│   ├── processed/              # Frame extractions, symbolic logs, error series
│   └── results/                # resource_logs.json, drift_scores.json
├── tests/
│   ├── unit/
│   │   ├── test_symbolic.py
│   │   └── test_cv_pipeline.py
│   └── integration/
│       └── test_full_pipeline.py
├── requirements.txt
└── pyproject.toml
```

**Structure Decision**: Single project structure (`code/`) is selected. This is a research experiment, not a production service. A monolithic `code/` directory with clear module separation is sufficient for the scope (200 sequences) and simplifies dependency management on the CI runner.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Hybrid Correction Loop** | Required to test the core hypothesis (P2) that symbolic injection reduces drift. | A purely baseline comparison (US-1 only) would fail to address the "follow-up" research question regarding the *influence* of the symbolic layer. |
| **Sparse Optical Flow vs. Template Matching** | Required to handle semantic drift. | Template matching fails when object appearance changes (drift). Sparse optical flow tracks motion vectors even under visual changes, providing a robust signal. |
| **Statistical Rigor (Shapiro-Wilk + Variance Check)** | Required by FR-006 to ensure valid inference. | ADF test is invalid for bounded, discrete frame-level errors. Shapiro-Wilk on paired differences is the correct non-parametric check for Wilcoxon assumptions. |

## Tasks & Execution Order

### Phase 0: Data Preparation & Validation
- **T001**: Verify AlayaWorld dataset availability. If unavailable, generate mock data for *unit testing only*.
- **T002**: Create Ground Truth Annotation Set for `data/annotations/ground_truth.json`.
- **T003a**: Validate CV pipeline on annotated set (FR-007). If accuracy < 85%, flag as invalid.
- **T003b**: **Feasibility Gate**: If dataset unavailable OR CV accuracy < 85%, abort main experiment and output "Methodological Validation" report.

### Phase 1: Baseline Generation
- **T017a**: Run Baseline (Vanilla) Generation for multiple seeds.
- **T017b**: Extract Visual States (CV) for Baseline.
- **T017c**: Calculate Baseline Drift Scores.

### Phase 2: Hybrid Generation
- **T022a**: Run Hybrid (Corrected) Generation for a set of seeds.
- **T022b**: **Generate Correction Tokens**: Map symbolic discrepancies to prompt strings (FR-004).
- **T022c**: Extract Visual States (CV) for Hybrid.
- **T022d**: Calculate Hybrid Drift Scores.

### Phase 3: Statistical Analysis
- **T023a**: Generate Frame-Level Error Series.
- **T023b**: Perform Shapiro-Wilk test on paired differences (Baseline - Hybrid).
- **T023c**: Perform Wilcoxon Signed-Rank Test.
- **T023d**: Generate Final Report.

### Phase 4: Resource Verification
- **T030**: Log and verify resource usage (RAM, Time) against constraints.

**Dependencies & Execution Order**:
- T001 must precede T002.
- T003a must pass (accuracy ≥ 85%) before T017a and T022a.
- T003b (Feasibility Gate) must pass before T017a.
- T017a, T017b, T017c must complete before T022a (to ensure consistent seeds).
- T023b depends on T017c and T022d.
- T030 runs in parallel with T017/T022.

## Dataset Variable Fit & Feasibility

- **Required Variables**: Object states (HP, inventory, position), user actions.
- **Dataset Check**: The "AlayaWorld" dataset is **not verified**.
  - **Risk**: If the dataset does not contain the specific object states or actions required, the symbolic engine cannot be grounded.
  - **Mitigation**: The symbolic engine will be designed to be generic. If the dataset lacks *any* object state information, the project will be flagged as "Data Unavailable" and the research question reframed to "Methodological Validation".
- **Conclusion**: The plan proceeds assuming the dataset contains the necessary action/state pairs. If not, the implementation will fail at the data loading step, and the report will explicitly state "Dataset Variable Mismatch: Required variables not found in AlayaWorld."

## Statistical Methodology (Revised)

### Statistical Test Selection
- **Primary Test**: Wilcoxon Signed-Rank Test (paired, non-parametric).
- **Pre-check 1 (Normality)**: Shapiro-Wilk test on the *paired differences* (Baseline - Hybrid). If p > 0.05, data is non-normal, justifying Wilcoxon.
- **Pre-check 2 (Variance Stability)**: Calculate rolling variance of frame-level error series. If variance > threshold (e.g., 0.5), flag as "High Variance" but proceed (Wilcoxon is robust to variance).
- **Removed**: Augmented Dickey-Fuller (ADF) test. It is statistically invalid for bounded, discrete frame-level error series and is not required for the Wilcoxon test.

### Correction Token Mechanism (FR-004)
- **Input**: Symbolic State Discrepancy (e.g., Object X: HP=0, Visual: Alive).
- **Logic**: Map discrepancy to a prompt string (e.g., "Object X is DEAD and should be removed").
- **Output**: Correction Token injected into the generation prompt at the next frame.
- **Schema**: Defined in `contracts/correction_token.schema.yaml`.

### Validation Independence
- The "Semantic Drift Score" is calculated by comparing the **validated** visual state (from T003a) against the symbolic state. This ensures the metric measures model drift, not CV pipeline failure.

## Edge Cases & Handling

- **Rendering Failure**: If symbolic state cannot be rendered (e.g., teleportation), log `RENDER_FAILURE` and inject a "reset" token.
- **Phantom Objects**: If CV detects an object not in symbolic log, increment drift score (phantom count).
- **Occlusion/Low Confidence**: If optical flow fails (confidence < 0.85), flag frame as "low-confidence" and use previous state (persistence) to avoid false positives.
