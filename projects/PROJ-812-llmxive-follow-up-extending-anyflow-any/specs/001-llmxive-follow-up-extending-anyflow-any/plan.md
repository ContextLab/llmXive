# Implementation Plan: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

**Branch**: `001-llmxive-follow-up-extending-anyflow-any` | **Date**: 2026-08-22 | **Spec**: `specs/001-llmxive-follow-up-extending-anyflow-any/spec.md`

## Summary
This project extends the "AnyFlow" video diffusion model research by validating a "flow-map divergence" metric as a proxy for numerical instability in the presence of semantic temporal discontinuities (scene cuts). The plan executes a CPU-tractable pipeline: (1) curating a dataset of short video clips from UCF101 (continuous motion) and Kinetics-400 (scene cuts) reflecting the natural distribution via simple random sampling; (2) manually annotating continuity scores (ground truth) via a blinded protocol with an oversampling strategy to ensure N>=500 valid samples; (3) computing divergence metrics using a frozen AnyFlow model via ONNX Runtime on CPU; and (4) performing statistical correlation and sensitivity analysis using Inverse Probability Weighting (IPW) for class imbalance. The implementation strictly adheres to the 6-hour CI limit and 7GB RAM constraint by optimizing the Euler solver steps and sampling strategy.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU build), `onnxruntime`, `opencv-python`, `datasets`, `pandas`, `scikit-learn`, `scipy`, `numpy`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/annotations`)  
**Testing**: `pytest` (unit tests for metric logic, integration tests for pipeline flow)  
**Target Platform**: GitHub Actions `ubuntu-latest` (2-core vCPU, 7GB RAM, no GPU)  
**Project Type**: Research/Computational Experiment  
**Performance Goals**: Full pipeline (500 clips) ≤ 6 hours; Peak RAM ≤ 7GB; Divergence computation < 10s per clip.  
**Constraints**: CPU-only execution; No synthetic data; Real video data only; Natural distribution sampling.  
**Scale/Scope**: 500 video clips (16 frames each); 1 frozen model; 1 statistical analysis suite.

> **Empirical Specifics (Power Analysis)**: The sample size of N=500 is derived from a formal power analysis. For a two-tailed correlation test (Pearson/Spearman) with alpha=0.05 and power=0.80, N=500 provides sufficient power to detect a minimum effect size of r ≈ 0.12. If the observed correlation is < 0.12, the result will be reported as 'underpowered to detect weak effects' rather than a false negative. This ensures honest interpretation of null results.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/utils/seeding.py`. Dataset fetchers use canonical HF URLs. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` restricted to the "Verified datasets" block. No fabricated metrics; divergence computed via explicit Euler rollout on real data. |
| **III. Data Hygiene** | **PASS** | Raw downloads stored in `data/raw` with SHA256 checksums. Annotations stored in `data/annotations` as immutable CSVs. |
| **IV. Single Source of Truth** | **PASS** | Every figure/statistic in the final report traces back to exactly one row in `data/` AND one block in `code/`. **Mechanism**: The analysis script logs `source_code_hash` for every calculation in the output CSVs to ensure traceability. No hand-typed numbers are permitted in the final report. |
| **V. Versioning** | **PASS** | Artifacts tracked via content hashes in `state/`. `code/` scripts versioned with git. |
| **VI. Latent Trajectory Fidelity** | **PASS** | AnyFlow model weights loaded once and frozen. ONNX conversion settings documented. **Metric Definition**: Divergence computed as L2 distance between model prediction and N=500 (or N=200) Euler baseline. **Metric Validation**: The *validation* of this metric is against the *manual continuity scores*, not the baseline. **Stability Check**: Pearson r > 0.7 must remain stable within ±0.05 tolerance after quantization changes. Re-run required if tolerance exceeded. |
| **VII. Temporal Continuity Ground Truth** | **PASS** | Manual annotation script (human-in-the-loop) generates `continuity_scores.csv` *before* any model inference. **No model features used in scoring.** Ground truth derived solely from pixel-space inspection. **Blinding**: Annotators are blinded to source dataset and cut metadata. |

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, thresholds, N_max defaults
├── seeding.py           # Global seed management
├── data/
│   ├── download.py      # Fetch UCF101/Kinetics subsets
│   ├── annotate.py      # Interactive annotation tool (CLI/GUI stub)
│   └── validate.py      # Variance/Kappa checks
├── models/
│   ├── anyflow_loader.py # Load ONNX model, extract latents
│   └── divergence.py     # Euler rollout, L2 calculation
├── analysis/
│   ├── correlation.py    # Pearson/Spearman, Logistic Regression (IPW), t-test
│   ├── sensitivity.py    # Threshold sweeping
│   └── report.py         # Final report generation
└── main.py              # Pipeline orchestrator

tests/
├── unit/
│   ├── test_divergence.py
│   └── test_seeding.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schemas.py

data/
├── raw/
│   ├── ucf101_subset/
│   └── kinetics_subset/
├── annotations/
│   └── continuity_scores.csv
├── processed/
│   ├── divergence_metrics.csv
│   ├── correlation_results.csv
│   └── sensitivity_report.csv
└── checksums.json
```

**Structure Decision**: A modular monolithic structure (`code/`) is selected to simplify dependency management for the research pipeline. Separation of `data/`, `models/`, and `analysis/` ensures clear data lineage and reproducibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Manual Annotation Step** | Required by FR-002 to establish ground truth without model bias. | Automated scoring would violate the "pixel-space only" constraint and introduce circular logic. |
| **Euler Solver Baseline** | Required by FR-004 to define "numerical error". The baseline *only* defines numerical error; the *correlation* with manual scores distinguishes semantic error. | Using a pre-computed baseline would obscure the dependency on N (steps) and invalidate the sensitivity analysis. |
| **Natural Distribution Sampling** | Required by FR-001 to reflect real-world video streams (skewed towards continuous motion). | Artificial balancing (50/50) would distort prior probabilities and require complex weighting, introducing selection bias. |
| **Blinding Protocol** | Required to prevent confirmation bias. | Annotators must not know the source dataset or pre-computed cut labels (derived from frame variance). |
| **Power Analysis & Oversampling** | Required to justify N=500 and interpret null results. | Without oversampling (starting with 600), discarding ambiguous clips could drop N below the power threshold. |
| **Inverse Probability Weighting** | Required to correct for class imbalance in logistic regression when using natural distribution data. | Unweighted logistic regression on skewed data yields biased accuracy estimates. |

## Data Acquisition & Processing

1.  **Download**: `code/data/download.py` fetches the UCF101 and Kinetics-400 datasets from canonical Hugging Face sources (`ucf101`, `kinetics-400`).
2.  **Extraction**: Clips are extracted as sequences of frames at a standard frame rate..
3.  **Sampling**: A **simple random sample** is drawn **proportional to the natural distribution** of the source datasets (likely >90% continuous). This avoids the bias of artificial stratification.
4.  **Annotation**: A human annotator reviews clips using a Likert scale (converted to 0.0–1.0). **Blinding Protocol**: Annotators receive clips with randomized IDs and **NO metadata** regarding the source dataset or the pre-computed 'cut' label. This process is manual and pixel-space only (FR-002).
5.  **Disagreement Resolution**: If Cohen's Kappa < 0.81, the system halts. If individual clips disagree (diff > 1 point), they are marked "discarded". If the final valid count < 500, the system triggers a re-run to fetch and annotate replacements until N=500 valid samples are reached.
6.  **Oversampling**: The system initially processes **N=600 clips** to ensure a final valid N >= 500 after discards.

## Compute Feasibility (CPU-First)

*   **Model Format**: AnyFlow weights will be converted to ONNX format for CPU inference using `onnxruntime`.
*   **Euler Solver**: The baseline Euler rollout uses $N=500$ steps. If the pre-flight check (FR-009) indicates runtime > 5.5 hours, $N$ will be reduced to 200.
*   **Memory**: Streaming video frames and processing one clip at a time ensures RAM usage stays < 7GB.
*   **GPU Escape Hatch**: None required. The entire pipeline is designed for CPU execution. If the ONNX model fails to load on CPU (e.g., requires specific CUDA kernels), the project will halt with a "Feasibility Error" rather than fabricating a CPU approximation.
*   **Real Data Only**: All divergence scores are computed via real ONNX inference on real video frames. No synthetic or simulated metrics are used.

## Execution Order

1.  **Data Fetch**: Download UCF101/Kinetics.
2.  **Pre-flight**: Estimate runtime on a 10-clip sample. Adjust N (Euler steps) if needed.
3.  **Annotation**: Run annotation tool on N=600 clips. Validate Kappa. Discard ambiguous. Fetch replacements if N < 500.
4.  **Inference**: Compute divergence for all valid clips.
5.  **Analysis**: Run correlation (Pearson/Spearman), Logistic Regression (with IPW), and Sensitivity Analysis.
6.  **Report**: Generate final report with traceability hashes.