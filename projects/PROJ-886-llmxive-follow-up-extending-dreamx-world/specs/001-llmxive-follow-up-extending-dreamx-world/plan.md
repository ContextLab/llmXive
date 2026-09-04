# Implementation Plan: DreamX-Lite: Geometric Priors for 3D Consistency

**Branch**: `001-dreamx-lite-geometric-priors` | **Date**: 2026-09-03 | **Spec**: `specs/001-dreamx-lite-geometric-priors/spec.md`
**Input**: Feature specification from `/specs/001-dreamx-lite-geometric-priors/spec.md`

## Summary

This project implements a comparative study to determine if deterministic geometric constraints (fixed 4x4 camera projection) can replace learned positional encodings (E-PRoPE) in the DreamX-World 1.0 DiT backbone. The primary requirement is to swap the trainable module for a non-trainable linear projection, generate 10-second video rollouts on a CPU-only runner, recover trajectories via external SfM, and compute statistical significance (McNemar, Wilcoxon) of 3D consistency metrics. The technical approach involves a strict architectural ablation, decoupled metric evaluation, and sensitivity analysis across MAE thresholds.

**Critical Data Note**: The 'DreamX-World subset' and 'DreamX-World 1.0' weights have no verified public source. The implementation includes a strict **Data Fallback Protocol**: if the primary dataset/weights are unavailable, the pipeline aborts the primary claim generation and runs a 'Logic Verification' mode on a verified ScanNet subset, marking the primary results as 'Pending Data Access'. No synthetic data is used.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `torch` (CPU-only build), `transformers`, `datasets`, `colmap` (system binary), `scipy`, `pandas`, `numpy`, `opencv-python`, `scikit-learn`  
**Storage**: Temporary local storage for video frames and intermediate SfM outputs; `data/` for checksummed datasets.  
**Testing**: `pytest` (unit tests for metric independence, integration tests for pipeline execution).  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU cores, ~7 GB RAM).  
**Project Type**: Computational research / AI model evaluation  
**Performance Goals**: Complete 50-trajectory evaluation (including generation and SfM) within 6 hours on CPU.  
**Constraints**: No GPU libraries allowed in the primary runner; strict decoupling of metric calculation from model internals; fixed random seeds for reproducibility.  
**Scale/Scope**: Paired trajectories (Baseline vs. DreamX-Lite); -second rollouts per trajectory.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: The plan mandates pinned `requirements.txt`, fixed random seeds in `code/`, and re-fetching of canonical datasets (DreamX-World subset if available, or ScanNet fallback) on every run. All scripts are designed for end-to-end execution in an isolated virtualenv.
- **II. Verified Accuracy**: Citations for datasets and methods (McNemar, Wilcoxon) will be validated against primary sources. **Note**: The primary dataset (DreamX-World) has no verified source. The 'Verified Accuracy' gate will be passed conditionally: if the dataset is found, full verification; if not, the project proceeds with the fallback logic and the primary claim is marked as 'Unverified due to Data Access'.
- **III. Data Hygiene**: All downloaded data (HuggingFace datasets) will be checksummed. Raw data remains immutable; derived metrics (MAE, convergence flags) are written to new files in `data/derived/`.
- **IV. Single Source of Truth**: All figures and statistics in the final report will trace back to specific rows in `data/derived/metrics.csv` (SSoT) and specific blocks in `code/analysis/`. The `metrics.schema.yaml` is the SSoT; `evaluation_schema.yaml` is the runtime contract and will be extended to match.
- **V. Versioning Discipline**: Artifacts (code, data, config) will carry content hashes. The state file will be updated upon any artifact change.
- **VI. Geometric Prior Fidelity**: The plan strictly adheres to replacing E-PRoPE with a fixed 4x4 projection. No learned geometric embeddings or hybrid priors will be introduced. **Note**: The Constitution text mentions a 'paired t-test', but the Spec and Research docs correctly define 'Wilcoxon signed-rank test' and 'McNemar's test' due to non-Gaussian errors. The plan adheres to the Spec's methodological choice. **Conflict Resolution**: The Spec's choice (non-parametric) takes precedence over the Constitution's t-test requirement due to the non-Gaussian nature of geometric errors. The Constitution Principle VI is flagged for amendment to align with the Spec.
- **VII. Resource-Constrained Validation**: All performance metrics (latency, memory) will be measured exclusively on the defined CPU-only environment. GPU-based results are explicitly excluded from the primary claim validation.

## Project Structure

### Documentation (this feature)

```text
specs/001-dreamx-lite-geometric-priors/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/
├── data/
│   ├── raw/                  # Downloaded datasets (checksummed)
│   └── derived/              # Metrics, trajectories, logs
├── code/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── dreamx_base.py    # Original DiT loader
│   │   └── dreamx_lite.py    # Modified DiT with fixed projection
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── generate.py       # Inference & video generation
│   │   └── evaluate.py       # SfM recovery & metric computation
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── stats.py          # McNemar & Wilcoxon tests
│   │   └── sensitivity.py    # Threshold sweep
│   └── utils/
│       ├── __init__.py
│       └── io.py             # Data loading, checksumming
├── tests/
│   ├── unit/
│   │   └── test_metrics.py   # Independence checks
│   └── integration/
│       └── test_pipeline.py  # End-to-end run
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure (`projects/PROJ-886.../code/`) is selected to maintain tight coupling between model definition, generation, and analysis while ensuring all artifacts remain within the project root for versioning and checksumming. This aligns with the "Single Source of Truth" principle.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The project scope is tightly constrained by the spec and constitution. The CPU-only requirement and strict metric decoupling are essential for scientific validity and cannot be simplified without invalidating the results. | N/A |

## Phased Implementation Plan

### Phase 0: Data Verification & Fallback (Pre-Execution)
1. **Verify Data Sources**: Attempt to locate 'DreamX-World subset' and 'DreamX-World 1.0' weights via HuggingFace.
2. **Fallback Protocol**: If primary data is unavailable, abort primary claim generation. Switch to 'Logic Verification' mode using a verified ScanNet subset. Log the status as 'Pending Data Access'.
3. **Checksum**: Record checksums for any downloaded data.

### Phase 1: Model Abstraction & Configuration
1. **Load Baseline**: Load pre-trained DreamX-World 1.0 DiT.
2. **Implement DreamX-Lite**: Replace `E-PRoPE` with `nn.Linear(input_dim, embedding_dim)` (fixed, non-trainable).
3. **Configure Constraints**: Set identical resolution (256x256) and quantization (8-bit if needed) for *both* variants to isolate the geometric effect from resolution artifacts. **Resolution/Quantization Control**: Both Baseline and Lite variants will be run at the *exact same* resolution and quantization level. The plan explicitly states that results are valid only for this specific regime and that any performance gap is attributable to the geometric prior, not the resolution artifact.
4. **Verify**: Check parameter count reduction and deterministic output.

### Phase 2: Data Generation & SfM Recovery
1. **Baseline SfM Validation**: Run SfM on a subset of ground-truth renders to establish a baseline convergence rate (to distinguish 'metric failure' from 'model failure').
2. **Generate Rollouts**: Generate short videos for distinct camera prompts (identical for both models).
3. **Non-Triviality Check**: Verify that the generated video is not a trivial identity of the input prompt (e.g., by comparing pixel-wise similarity to a direct render of the input geometry).
4. **SfM Recovery**: Run COLMAP on generated frames.
5. **Metric Calculation**:
   - Perform **Procrustes Alignment** between recovered and ground-truth trajectories to resolve scale/rotation ambiguity. **Explicit Normalization**: MAE is computed on *aligned* trajectories to remove scale/rotation ambiguity.
   - Compute MAE (position, rotation) on aligned trajectories.
   - Compute **Scale Drift** (ratio of scales after alignment).
   - Record `convergence` (boolean) and `sfm_failure_reason` (string).
   - If SfM fails, set `mae_position` and `mae_rotation` to `null` (not sentinel -1.0).
   - If SfM fails but depth-consistency is available, mark `sfm_status` as 'censored'.

### Phase 3: Statistical Analysis (Hurdle Model)
1. **Convergence Test**: Run McNemar's test on binary `convergence` flags.
2. **Error Test**: Run Wilcoxon signed-rank test on MAE scores *only* for `convergence=true` trajectories. **No Sentinels**: Sentinel values are excluded from the Wilcoxon test.
3. **Censoring Analysis**: Calculate and report the 'Censoring Rate' for both models.
4. **Sensitivity Analysis**: Sweep thresholds {, 0.1} MAE and report success rates.

### Phase 4: Sensitivity Analysis (FR-006)
1. **Execute Sweep**: Run `code/analysis/sensitivity.py` with a range of thresholds.
2. **Report**: Generate a table showing success rates for both models at each threshold.
3. **Validate**: Ensure the output matches the requirements of FR-006.

### Phase 5: Reporting & Sufficiency Ratio (SC-005)
1. **Calculate Ratio**: Compute 'Information-Theoretic Sufficiency Ratio' = (DreamX-Lite Success Rate) / (Baseline Success Rate).
2. **Log Result**: Record this ratio in `data/derived/statistical_results.json`.
3. **Final Report**: Compile all metrics, p-values, and the sufficiency ratio into the final report.