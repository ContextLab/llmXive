# Implementation Plan: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

**Branch**: `001-gene-regulation` | **Date**: 2026-07-11 | **Spec**: `specs/001-llmxive-follow-up-extending-anyflow-any/spec.md`

## Summary

This project implements a CPU-tractable pipeline to evaluate the "flow-map divergence" metric of the AnyFlow video diffusion model against a manually curated ground-truth dataset of temporal continuity. The system downloads stratified video clips (UCF, Kinetics, DAVIS), computes a numerical instability metric (L-norm distance between model prediction and high-resolution Euler rollout) using ONNX Runtime, and performs correlation analysis (Pearson/Spearman) to test the hypothesis that model instability correlates with semantic scene cuts. The entire pipeline is constrained to run within 6 hours on a GitHub Actions free-tier runner (2 CPU, 7GB RAM).

**Critical Methodological Note**: The study explicitly controls for confounding variables (motion complexity, texture density) to isolate the effect of "cuts" on divergence. The "flow-map divergence" metric is treated as a proxy for numerical integration error, and the hypothesis is tested by comparing the correlation slope between "cut" and "continuous" clips, controlling for motion magnitude.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `onnxruntime`, `torch` (CPU-only build), `numpy`, `pandas`, `scikit-learn`, `requests`, `opencv-python-headless`, `matplotlib`  
**Storage**: Local filesystem (`data/` for raw/processed data, `code/` for scripts)  
**Testing**: `pytest` (unit tests for data validation, integration tests for pipeline steps)  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`)  
**Project Type**: Computational Research Pipeline  
**Performance Goals**: Full pipeline (500 clips) ≤ 6 hours; Peak RAM ≤ 7GB; No GPU usage.  
**Constraints**: No CUDA; No 8-bit/4-bit quantization requiring GPU; Manual annotation step is external/human-in-the-loop (simulated via CSV input for automation); Strict stratified sampling (% cuts).  
**Scale/Scope**: 500 video clips (16 frames @ 30fps); 3 specific thresholds for sensitivity analysis.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **COMPLIANT** | Random seeds pinned in `code/`; `requirements.txt` pins dependencies; Data fetched from canonical sources (UCF/Kinetics/DAVIS) via scripts; No manual data modification in place. |
| **II. Verified Accuracy** | **COMPLIANT** | AnyFlow model cited as "NO verified source found" (per dataset block) -> **BLOCKED** until verified source found. Code will load a local/onnx-converted version *only if* a verified URL is provided. No external citations in `plan.md` violate the threshold. |
| **III. Data Hygiene** | **COMPLIANT** | Raw data (videos) stored in `data/raw/`; Derived data (divergence scores) in `data/processed/`; Checksums recorded in `state/...yaml`; No PII (public datasets). |
| **IV. Single Source of Truth** | **COMPLIANT** | Final report statistics derived strictly from `data/processed/correlation_results.csv`; No hand-typed numbers. |
| **V. Versioning Discipline** | **COMPLIANT** | Artifacts (CSVs, reports) will be content-hashed in `state/...yaml`; `updated_at` timestamps managed by Advancement-Evaluator. |
| **VI. Latent Trajectory Fidelity** | **COMPLIANT** | Metric defined as L2 distance between predicted state and N=500 Euler rollout (or N=200 if validated fallback); ONNX Runtime settings documented; Variance check (≥0.05) enforced before correlation. |
| **VII. Temporal Continuity Ground Truth** | **COMPLIANT** | Manual scores (normalized to a unit interval) stored in immutable `data/raw/continuity_scores.csv` prior to metric calculation; No model features used for ground truth. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-812-llmxive-follow-up-extending-anyflow-any/
├── data/
│   ├── raw/
│   │   ├── videos/          # Downloaded 16-frame clips
│   │   └── continuity_scores.csv # Manual ground truth
│   └── processed/
│       ├── divergence_scores.csv
│       ├── correlation_results.csv
│       ├── sensitivity_report.csv
│       └── variance_report.csv
├── code/
│   ├── __init__.py
│   ├── data_download.py     # FR-001: Download & Stratified Sampling
│   ├── annotation_interface.py # FR-002: Manual Annotation Interface
│   ├── model_inference.py   # FR-003, FR-004: ONNX Loading, Euler Baseline, Divergence Calc
│   ├── analysis.py          # FR-005, FR-006, FR-007: Correlation, Sensitivity
│   ├── report_generator.py  # FR-008, SC-005: Final Report Generation
│   ├── utils.py             # Logging, Error handling (Edge cases)
│   └── main_pipeline.py     # Orchestrator (FR-009, FR-010)
├── tests/
│   ├── unit/
│   │   ├── test_data_download.py
│   │   ├── test_annotation_interface.py
│   │   └── test_analysis.py
│   └── integration/
│       └── test_full_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected to maintain tight coupling between data processing and analysis, minimizing I/O overhead on the limited 7GB RAM runner. The `code/` directory contains modular scripts for each phase (Download, Annotation, Inference, Analysis, Report) to allow independent testing and debugging.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **N=500 Euler Steps** | Required by spec (FR-004) to define "Numerical Baseline" for high-precision integration error. | N=50 or N=100 would not provide a sufficiently stable baseline to detect subtle model instabilities, violating the "Latent Trajectory Fidelity" principle. *Fallback*: If preflight check (FR-009) exceeds 5.5h, reduce to N=200 *after* validating baseline stability. |
| **Manual Annotation Step** | Required by FR-002 to ensure ground truth is pixel-space only. | Automated annotation (e.g., using a separate cut-detection model) would introduce circular logic and bias, violating Principle VII. |
| **Motion Complexity Covariate** | Required to isolate "cut" effect from general motion magnitude (Scientific Soundness concern). | Omitting this would result in a spurious correlation where divergence simply measures motion, not "cuts". |

## Revised Phases & Tasks

### Phase 0: Data Curation & Baseline Validation (FR-001, FR-002, FR-009)
1.  **Download**: Fetch 16-frame clips (30fps) from UCF101, Kinetics, DAVIS (verified URLs) using `code/data_download.py`.
2. **Stratification**: Apply a *Pixel-Difference Heuristic* (frame-to-frame MSE > threshold) to identify "cuts". Ensure [deferred] of clips are labeled "cut".
3.  **Heuristic Orthogonality Check**: Run a pilot on a small set of clips to verify the heuristic does not correlate with model divergence *before* full annotation.
4.  **Baseline Validation**: Run a pilot on 10 clips comparing N=500 Euler vs. N=2000 Euler/RK4. If error > 5%, reduce N to 200 or halt.
5.  **Annotation**: Generate `continuity_scores.csv` using `code/annotation_interface.py`.
    - *Constraint*: No model features used for scoring.
    - *Validation*: Variance must be ≥ 0.05 (FR-010).

### Phase 1: CPU-Tractable Inference (FR-003, FR-004)
1.  **Model Loading**: Load AnyFlow weights converted to ONNX format for CPU inference (ONNX Runtime) via `code/model_inference.py`.
    - *Constraint*: No CUDA, no quantization requiring GPU.
2.  **Confounding Variable Measurement**: Compute "Motion Complexity" (optical flow magnitude) and "Texture Density" (gradient variance) for each clip.
3.  **Divergence Metric**: Compute L2 distance between the model's predicted intermediate state and the Euler baseline (N=500).
    - *Metric*: $Divergence = \frac{1}{T} \sum_{t=1}^{T} || \text{Model}(x_t) - \text{Euler}(x_t) ||_2$.
4.  **Preflight Check**: Run on first 5 clips to estimate runtime (FR-009). If > 5.5h projected, reduce $N$ to 200 (if validated) or halt.

### Phase 2: Correlation & Sensitivity (FR-005, FR-006, FR-007)
1.  **Variance Check**: Calculate variance of `continuity_scores`. If < 0.05, halt and report "Insufficient Variance".
2.  **Correlation**: Compute Pearson $r$ and Spearman $\rho$ between `continuity_scores` and `divergence_scores`.
3.  **Partial Correlation**: Compute partial correlation controlling for "Motion Complexity" and "Texture Density".
4.  **Sensitivity**: Analyze classification rates at thresholds {0.01, 0.05, 0.1}.
5.  **Framing**: Explicitly state "Relationship: Associational" (FR-007).
6.  **Output**: Generate `correlation_results.csv`, `sensitivity_report.csv`, and `variance_report.csv`.

### Phase 3: Report Generation (FR-008, SC-004, SC-005)
1.  **Report Generation**: Execute `code/report_generator.py`.
    - *Logic*: Read `correlation_results.csv`, `sensitivity_report.csv`, `variance_report.csv`.
    - *Mandatory Injection*: Insert FR-008 statement: "The 'flow-map divergence' metric is a proxy for model instability..."
    - *Mandatory Injection*: Insert SC-005 statement: "CPU-only mode (ONNX Runtime, no CUDA)".
    - *Mandatory Injection*: Insert FR-007 statement: "Relationship: Associational".
2.  **Final Output**: Generate `final_report.md`.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Only two primary correlation tests (Pearson, Spearman) are run. A Bonferroni correction is noted but likely not strictly necessary for the primary hypothesis test; however, the sensitivity analysis involves 3 thresholds, so the interpretation of "significant" changes must be cautious.
- **Sample Size/Power**: The target is a substantial collection of clips.. Power analysis for a binary "cut vs. continuous" comparison (Mann-Whitney U) with medium effect size (d=0.5) and alpha=0.05 confirms N=500 is sufficient.
- **Causal Inference**: The study is **observational**. The plan explicitly avoids causal claims (FR-007). The relationship is framed as "model instability correlates with semantic discontinuity," not "instability causes discontinuity."
- **Measurement Validity**: The manual annotation relies on human visual inspection. To mitigate bias, the annotation rubric (not included in code) must be strict: = perfect continuity, 1.0 = hard cut.
- **Collinearity**: The divergence metric is derived from the model's latent state, which is also used to generate the video. However, the ground truth is pixel-based. There is no definitional collinearity between the *score* (human) and the *metric* (model error), so independent effects are not claimed; rather, a correlation is tested.
- **Construct Validity**: The plan explicitly tests if the correlation is driven by "motion magnitude" by including it as a covariate. If the correlation disappears when controlling for motion, the hypothesis is rejected.

## Compute Feasibility

- **Environment**: GitHub Actions `ubuntu-latest` (2 CPU, 7GB RAM).
- **Memory**: ONNX Runtime is optimized for CPU. 16-frame clips are small. A substantial number of clips will fit in memory if processed sequentially or in small batches.
- **Runtime**: The Euler baseline ($N=500$) is computationally expensive. The preflight check (FR-009) is critical. If $N=500$ exceeds the 6-hour budget, the plan allows reducing $N$ to 200, though this may reduce the precision of the "Numerical Baseline."
- **No GPU**: All operations are CPU-bound. `torch` and `onnxruntime` will be installed in CPU-only modes.

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **ONNX Runtime for Inference** | Required for CPU-only execution (FR-003). PyTorch CPU inference is slower and less optimized for static graphs. |
| **N=500 Euler Steps** | Spec requirement (FR-004) for "high-resolution" baseline. *Fallback*: N=200 if validated. |
| **Manual Annotation** | Required by FR-002 to ensure ground truth is independent of model features. |
| **Associational Framing** | Required by FR-007 due to observational nature of the study. |
| **Stratified Sampling** | Required by FR-001 to ensure [deferred] of clips are cuts, preventing class imbalance. |
| **Pixel-Difference Heuristic** | Required to avoid manual selection bias and ensure orthogonality to model failure modes. |
| **Partial Correlation** | Required to isolate the "cut" effect from general motion complexity. |