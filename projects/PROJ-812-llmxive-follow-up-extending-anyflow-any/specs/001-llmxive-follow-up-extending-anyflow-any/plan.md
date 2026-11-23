# Implementation Plan: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

**Branch**: `001-llmxive-follow-up-extending-anyflow-any` | **Date**: 2026-08-22 | **Spec**: `specs/001-llmxive-follow-up-extending-anyflow-any/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-anyflow-any/spec.md`

## Summary

This project extends the AnyFlow video diffusion model by introducing a "flow-map divergence" metric to quantify model instability under temporal discontinuities (scene cuts). The study curates a stratified dataset of video clips (balanced between continuous motion and scene cuts), manually annotates them for continuity, and computes CPU-tractable divergence scores using an ONNX-optimized AnyFlow model. The core hypothesis is that numerical integration error (divergence) correlates with semantic discontinuity. The plan strictly adheres to CPU-only execution on GitHub Actions (a limited core configuration, constrained RAM).

The research question remains: [Insert Research Question]
The method remains: [Insert Method]
References: [Insert References], utilizing ONNX Runtime for inference and streaming/stratified sampling to manage data volume. Statistical analysis includes Spearman correlation (primary), Pearson (exploratory), logistic regression with Inverse-Probability Weighting (IPW), and sensitivity analysis on solver steps and classification thresholds.

**Critical Feasibility Note**: The plan requires a verified video dataset URL and a verified model source. If no verified URL is found in the "Verified datasets" block, the pipeline HALTS immediately with a "Data Availability Failure". No fallback to "assumed" sources is permitted.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `onnxruntime` (CPU), `opencv-python`, `pyscenedetect`, `pandas`, `scikit-learn`, `scipy`, `huggingface_hub`, `datasets`  
**Storage**: Local filesystem (`data/` for raw/processed clips, `code/` for scripts)  
**Testing**: `pytest` (unit tests for metric calculation, integration tests for pipeline flow)  
**Target Platform**: Linux (GitHub Actions ubuntu-latest runner, CPU-only)  
**Project Type**: Research/Data Pipeline  
**Performance Goals**: Full pipeline (500 clips) ≤ 6 hours; Peak RAM ≤ 7 GB  
**Constraints**: NO GPU; NO external API calls for data download; strict adherence to stratified sampling; manual annotation required for ground truth.  
**Scale/Scope**: A sufficient number of video clips (16 frames each @ 30 fps); A sufficient number of clips for control analysis.; A sufficient number of clips for the pilot..

> **Dataset & Model Gap**: The spec references UCF101, Kinetics, and DAVIS. The verified dataset block indicates **NO verified source** for UCF101, DAVIS, or a direct CPU-optimized AnyFlow model.
> - **Data**: The pipeline will attempt to load a verified video dataset via `datasets.load_dataset("kinetics-400")` (if available in the HF Hub with verified URL). **If no verified source is found, the pipeline HALTS with "Data Availability Failure"**. The 'verified_small_set' is ONLY for pipeline validation, not the main study.
> - **Model**: The pipeline requires the frozen AnyFlow weights in ONNX format. **If no verified source for the weights or conversion artifact is found, the pipeline HALTS with "Model Unavailable Failure"**.
> - **Action**: The implementation script `download_curation.py` and `inference_cpu.py` will check for these sources. If missing, they exit with code 1 and a clear error message. No synthetic data or assumed sources are used for the primary hypothesis test.

## Constitution Check

*Gates determined based on constitution file*

- **Principle I (Reproducibility)**: Plan mandates pinned `requirements.txt` and fixed random seeds in `code/`. All data downloads use `datasets.load_dataset(..., trust_remote_code=True)` with explicit commit hashes where possible.
- **Principle II (Verified Accuracy)**: Citations to AnyFlow and statistical methods will be validated against the primary sources. No unverified URLs for datasets or models will be used; if a source is missing from the verified block, the plan will halt or flag the gap.
- **Principle III (Data Hygiene)**: All data files under `data/` will be checksummed. Raw data is immutable; derived artifacts (divergence scores, annotations) are new files.
- **Principle IV (Single Source of Truth)**: `traceability_matrix.json` will map every statistic to a data row and code block.
- **Principle V (Versioning)**: Artifacts will carry content hashes.
- **Principle VI (Latent Trajectory Fidelity)**: The plan specifies using the *exact* frozen AnyFlow weights (via ONNX conversion) and documents any quantization changes. Correlation stability ($r > 0.7 \pm 0.05$) is a mandatory check. The plan includes a 'Stability Re-run Mechanism' to explicitly verify this.
- **Principle VII (Temporal Continuity Ground Truth)**: The plan enforces a strict separation: manual annotations (pixel-space only) are recorded *before* any model inference. No circular logic allowed.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-anyflow-any/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── video_clip.schema.yaml
│   ├── divergence_result.schema.yaml
│   ├── analysis_report.schema.yaml
│   ├── rubric_definition.md
│   ├── ipw_log.json
│   ├── dip_test_results.csv
│   ├── fisher_z_test_results.csv
│   ├── control_analysis.csv
│   ├── runtime_pilot_report.md
│   ├── power_analysis_report.md
│   ├── synthetic_validation_report.md
│   ├── variance_report.csv
│   ├── manual_calculation_expected.json
│   └── adjudication_log.csv
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-812-llmxive-follow-up-extending-anyflow-any/
├── data/
│   ├── raw/                 # Downloaded video clips (stratified)
│   ├── annotations/         # manual_continuity_scores.csv, adjudication_log.csv, rubric_definition.md
│   ├── processed/           # divergence_scores.csv, control_analysis.csv
│   └── synthetic/           # synthetic_validation_subset/
├── code/
│   ├── __init__.py
│   ├── download_curation.py # FR-001, FR-013, FR-025
│   ├── annotation_tool.py   # FR-002, FR-010, FR-014
│   ├── inference_cpu.py     # FR-003, FR-004, FR-009 (ONNX Runtime)
│   ├── analysis_stats.py    # FR-005, FR-006, FR-010, FR-011, FR-012
│   ├── validation.py        # FR-012, FR-028
│   └── utils/
│       ├── metrics.py       # Divergence calculation, IPW
│       └── plots.py         # Sensitivity reports
├── tests/
│   ├── contract/            # Schema validation tests
│   ├── unit/                # Metric calculation tests
│   └── integration/         # End-to-end pipeline test
├── artifacts/
│   ├── final_report_manifest.json
│   ├── traceability_matrix.json
│   └── power_analysis_report.md
└── requirements.txt
```

**Structure Decision**: Single project structure (Option 1) is selected. The research nature requires a linear pipeline (Download -> Annotate -> Inference -> Analysis) rather than a service architecture. All scripts are Python modules in `code/` for reproducibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Manual Annotation (Human-in-the-loop) | Ground truth for continuity cannot be algorithmically derived without circular logic (Principle VII). | Automated cut detection (PySceneDetect) only identifies cuts, not "continuity quality" or "stability" which requires semantic judgment. |
| ONNX Runtime (CPU) | GPU is unavailable on CI; model must run on 2-core vCPU. | Native PyTorch GPU inference is impossible; CPU fallback is mandatory. |
| Stratified Sampling + IPW | Dataset is artificially balanced for power, but natural prevalence is low. | Simple random sampling would yield too few cuts for statistical power; IPW corrects the bias. |
| Sensitivity Sweep (N=500, 200, 100) | Must prove robustness of the metric to solver discretization. | Single-step inference cannot distinguish model instability from numerical error. |

## Stability Re-run Mechanism (Principle VI)

To satisfy Principle VI (Latent Trajectory Fidelity), the plan includes a specific re-run mechanism:
1.  **Perturbation**: Apply Gaussian noise (sigma=0.01) to the latent vectors of the input clips.
2.  **Re-inference**: Re-run the divergence calculation on the perturbed data.
3.  **Re-correlation**: Recalculate the Pearson correlation between the perturbed divergence scores and the manual annotations.
4.  **Delta Calculation**: Compute $\Delta r = |r_{original} - r_{perturbed}|$.
5.  **Tolerance Check**: If $\Delta r > 0.05$, the system flags the result as "UNSTABLE" and logs the deviation in `stability_check.json`.
6.  **Output**: The `stability_check.json` file will contain `noise_level`, `delta_r`, and `stability_met` (boolean).

## Contract Mapping

| Plan Step | Output Artifact | Contract Schema |
|-----------|-----------------|-----------------|
| Data Curation | `data/raw/clip_metadata.csv` | `contracts/clip_metadata.schema.yaml` |
| Manual Annotation | `data/annotations/manual_continuity_scores.csv` | `contracts/continuity_scores.schema.yaml` |
| Manual Annotation | `data/annotations/adjudication_log.csv` | `contracts/adjudication_log.schema.yaml` |
| Rubric Definition | `data/annotations/rubric_definition.md` | `contracts/rubric_definition.md` (Text) |
| Divergence Calculation | `data/processed/divergence_scores.csv` | `contracts/divergence_result.schema.yaml` |
| IPW Weights | `data/processed/ipw_log.json` | `contracts/ipw_log.json` |
| Bimodality Test | `data/processed/dip_test_results.csv` | `contracts/dip_test_results.schema.yaml` |
| Fisher Z Test | `data/processed/fisher_z_test_results.csv` | `contracts/fisher_z_test_results.schema.yaml` |
| Control Analysis | `data/processed/control_analysis.csv` | `contracts/control_analysis.schema.yaml` |
| Pilot Report | `artifacts/runtime_pilot_report.md` | `contracts/runtime_pilot_report.schema.yaml` |
| Power Report | `artifacts/power_analysis_report.md` | `contracts/power_analysis_report.schema.yaml` |
| Synthetic Report | `artifacts/synthetic_validation_report.md` | `contracts/synthetic_validation_report.schema.yaml` |
| Variance Report | `data/processed/variance_report.csv` | `contracts/variance_report.schema.yaml` |
| Manual Calc Expected | `data/processed/manual_calculation_expected.json` | `contracts/manual_calculation_expected.schema.yaml` |
| Stability Check | `artifacts/stability_check.json` | `contracts/stability_check.schema.yaml` |