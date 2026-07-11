# Implementation Plan: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

**Branch**: `001-gene-regulation` | **Date**: 2026-07-11 | **Spec**: `specs/001-llmxive-follow-up-extending-anyflow-any/spec.md`
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-anyflow-any/spec.md`

## Summary

This project implements a CPU-tractable validation pipeline for the "flow-map divergence" metric. The primary goal is to test the hypothesis that **model internal divergence (distillation error) correlates with external physical discontinuity (scene cuts)**.

**Technical Approach**:
1.  **Data Curation**: Fetch a representative set of clips from UCF101/Kinetics/DAVIS. Annotate with manual continuity scores [0.0, 1.0] (Ground Truth).
2.  **Metric Calculation**: Compute "Internal Divergence" (L2 distance between distilled model prediction and high-res Euler rollout) AND "External Flow Variance" (Optical Flow via RAFT).
3.  **Statistical Analysis**: Correlate Internal Divergence with External Flow Variance. Perform sensitivity analysis and power analysis.

**Critical Methodological Update**: The "ground truth" for the hypothesis is **External Optical Flow Variance**, not the model's own Euler rollout. The Euler rollout serves only as the *numerical baseline* for calculating the divergence metric. This breaks the circularity of validating a model against itself.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `onnxruntime`, `torch` (CPU-only), `scikit-learn`, `pandas`, `opencv-python-headless`, `datasets` (for Kinetics/DAVIS), `ucimlrepo` (for UCF101 fallback), `raft-torch` (CPU-opt for optical flow).  
**Storage**: Local file system (`data/raw`, `data/processed`), CSV files for annotations and metrics.  
**Testing**: `pytest` (unit tests for metric logic, integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Computational Research Pipeline / CLI  
**Performance Goals**: Complete full pipeline (500 clips) in ≤6 hours; peak RAM ≤7 GB.  
**Constraints**: No GPU/CUDA; no 8-bit/4-bit quantization requiring CUDA; strict memory limits; manual annotation required for ground truth.  
**Scale/Scope**: A set of video clips (a fixed number of frames each); 1 frozen model; 1 correlation analysis; 1 optical flow proxy calculation.

> **Dataset Note**: The spec assumes availability of UCF101, Kinetics, and DAVIS. The plan uses `ucimlrepo` for UCF101 (with manual download fallback) and `datasets.load_dataset` for Kinetics. DAVIS requires manual download due to licensing. **AnyFlow** has **NO verified source found**; the plan relies on user-provided weights with a 'Unverified Source' flag and mandatory architectural verification.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **I. Reproducibility**: The plan mandates pinned `requirements.txt` (including `ucimlrepo` and `datasets` versions), fixed random seeds in `code/`, and immutable raw data storage. Scripts will be designed to re-run from scratch on a fresh runner.
2.  **II. Verified Accuracy**: The plan admits **AnyFlow** has **NO verified source found**. A 'Provenance Declaration' artifact is introduced where the user declares the source. The 'Verified Accuracy Gate' is **failed** for the model source, and the final report must explicitly state this limitation. This satisfies the requirement to not bypass the gate but to document the failure.
3.  **III. Data Hygiene**: All raw downloads will be checksummed. Manual annotations will be stored in `data/raw/annotations.csv` (immutable). Derived metrics will be in `data/processed/divergence_metrics.csv`. No in-place modification.
4.  **IV. Single Source of Truth**: Correlation coefficients ($r$, $\rho$) will be computed by script and written to a JSON summary, which the paper will read. No manual entry of statistics.
5.  **V. Versioning Discipline**: All artifacts (code, data) will carry content hashes. The `updated_at` timestamp will be updated on artifact changes.
6.  **VI. Latent Trajectory Fidelity**: The plan includes a **Quantization Sensitivity Test**. A subset of clips is re-run with a different ONNX precision (float16 vs float32) to verify that the correlation $r$ remains stable within $\pm 0.05$. **This is mandatory.** If the test fails, the pipeline halts and flags the quantization as invalid.
7.  **VII. Temporal Continuity Ground Truth**: The plan enforces a strict separation: `data/raw/annotations.csv` is created *before* any inference script runs. The correlation analysis uses **external optical flow variance** as the physical ground truth proxy, breaking the circularity of using the model's own Euler rollout as truth.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-anyflow-any/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # INPUT ARTIFACTS (provided by planner)
│   ├── annotation.schema.yaml
│   ├── metric.schema.yaml
│   ├── result.schema.yaml
│   └── sensitivity.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── data_curation/
│   ├── download_clips.py      # Downloads from UCF101/Kinetics/DAVIS
│   ├── download_ucf101_manual.py # Fallback for UCF101 raw files
│   └── annotate.py            # Manual annotation helper (CLI/CSV output)
├── metric_calculation/
│   ├── load_model.py          # Loads frozen AnyFlow to ONNX + Integrity Check
│   ├── extract_latents.py     # Extracts latent trajectories
│   ├── compute_divergence.py  # Calculates L2 divergence vs Euler rollout
│   └── compute_optical_flow.py # Computes external flow variance (raft-small CPU)
├── analysis/
│   ├── correlation.py         # Pearson/Spearman calculation (Divergence vs Flow)
│   ├── sensitivity.py         # Threshold sweep (0.01, 0.05, 0.1)
│   ├── distribution.py        # Calculates score variance/distribution (SC-004)
│   └── report.py              # Generates final report with Runtime Env (SC-005)
├── main.py                    # Orchestrator script
├── requirements.txt           # Pinned dependencies
└── utils/
    └── logging.py             # Standardized logging
```

**Structure Decision**: Single `code/` directory with modular sub-packages. This minimizes overhead for the 6-hour CI limit and keeps the pipeline linear (Download -> Annotate -> Compute -> Analyze).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Manual Annotation Step | Required by FR-002 and US-1 for ground truth. | Automated metrics cannot replace human-verified "temporal continuity" as the ground truth for this specific hypothesis. |
| Optical Flow Proxy | Required to break circularity (Scientific Soundness). | Using the model's own Euler rollout as ground truth creates a circular validation that does not measure external discontinuity. |
| Quantization Sensitivity Test | Required by Constitution Principle VI. | Without verifying stability across quantization, the CPU-optimized metric may introduce artifacts. |
| Power Analysis | Required by Methodology Panel. | N=500 must be justified against minimum detectable effect size to avoid underpowered results. |
| Inter-Annotator Reliability | Required by Methodology Panel. | Single annotator introduces bias; double-annotation and Krippendorff's Alpha ensure consistency. |

## Phase Breakdown

### Phase 0: Data Curation & Ground Truth (FR-001, FR-002)
1.  **Download**: Fetch a set of video clips.
    - **UCF101**: Use `ucimlrepo` (with manual download fallback script `download_ucf101_manual.py`).
    - **Kinetics**: Use `datasets.load_dataset("kinetics-400")`.
    - **DAVIS**: Manual download (licensing) via script.
2. **Manual Annotation**: Annotate each clip with a score [0.0, 1.0]. **Double-annotate [deferred]** of clips. Calculate Krippendorff's Alpha; if < 0.6, halt and revise rubric.
3.  **Binarization**: Define binary labels for sensitivity analysis: Score < 0.4 = 'Continuous', Score > 0.6 = 'Discontinuous', 0.4-0.6 = 'Ambiguous' (excluded from binary metrics).

### Phase 1: Metric Calculation (FR-003, FR-004)
1.  **Model Integrity & Architecture Verification**: Load AnyFlow ONNX. Compute SHA-256 hash. **Verify layer count and input/output shapes match the 'On-Policy Flow Map Distil' architecture.** If mismatch, halt with error. Log 'Unverified Source' if no known-good hash exists.
2. **Quantization Check**: Run a subset with float16 vs float32. Verify correlation stability ($\Delta r < 0.05$). **If failed, halt.**
3.  **Internal Divergence**: Compute L2 distance between predicted and Euler rollout (N=1000) for each clip. (This is the metric).
4.  **External Proxy**: Compute optical flow variance (raft-small CPU) for each clip. (This is the Ground Truth for the hypothesis).

### Phase 2: Statistical Analysis (FR-005, FR-006, FR-007)
1.  **Distribution Analysis**: Calculate variance and histogram of manual scores (SC-004). **Explicitly report variance.**
2.  **Power Analysis**: Calculate Minimum Detectable Effect Size (MDES) for N=500, power=0.8, alpha=0.05. Report this as a limitation.
3.  **Correlation**: Calculate Pearson $r$ and Spearman $\rho$ between **Internal Divergence** and **External Optical Flow Variance**. Frame as associational.
4.  **Sensitivity**: Run threshold sweep {0.01, 0.05, 0.1} using the **Binarized** labels (SC-003).
5.  **Report Generation**: Generate final JSON report including **Runtime Environment** (SC-005) and **Provenance Declaration** (Constitution II). **Explicitly state "CPU-only" in the report.**

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **AnyFlow model unavailable or mismatched** | Fatal (cannot compute metric) | Plan requires user to provide weights. Architecture verification step halts if structure is wrong. |
| **Memory Overflow** | High (CI job killed) | Process in small batches; clear CPU memory after each clip. |
| **Annotation Bias** | Medium (Ground truth skewed) | Double-annotate 20%; Krippendorff's Alpha < 0.6 triggers halt. |
| **Runtime > 6h** | High (CI failure) | Optimize ONNX session; reduce N=1000 to N=500 if necessary (documented). |
| **Circular Metric** | High (Invalid hypothesis) | Use external optical flow variance as ground truth proxy; reframe hypothesis. |
| **Unverified Model Source** | Medium (Constitution II failure) | Log 'Unverified Source' flag; final report must explicitly state this limitation. |
| **Quantization Instability** | High (Invalid metric) | Mandatory Quantization Sensitivity Test. Halts if $\Delta r > 0.05$. |