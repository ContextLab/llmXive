# Specification: Quantifying the Impact of Data Compression on Gravitational Wave Event Reconstruction

## 1. Introduction

This document outlines the requirements for a system designed to quantify how data compression affects the reconstruction of gravitational wave (GW) events. The system will process real GW noise segments, inject synthetic CBC signals, apply various compression techniques, and perform Parameter Estimation (PE) to measure biases.

## 2. Functional Requirements

### 2.1 Data Acquisition and Injection (Amended FR-001)
**FR-001**: System MUST generate ≥15 synthetic CBC injections into real GW noise segments fetched from GWOSC, using `LALSimulation` with known ground truth parameters, replacing the requirement to download public injection campaigns.
*Note: This amendment is authorized by Plan Complexity Tracking due to the lack of public injection campaigns.*

### 2.2 Compression Techniques (Amended FR-003)
**FR-003**: JPEG2000 compression MUST be implemented via 1D-to-2D folding (Hilbert curve algorithm) to adapt 2D codecs to 1D strain data. The resulting artifacts are tagged as 'Transformation+Compression'.
*Note: This amendment is authorized by Constitution Principle VII (Modified) regarding the 1D-to-2D folding deviation.*

### 2.3 Parameter Estimation Engine (Amended FR-005)
**FR-005**: System MUST run Parameter Estimation using `Bilby` with `Dynesty` (Fast PE) on both original and compressed datasets for ≥12 events, replacing LALInference due to CI constraints.
*Note: Constitution Principle VII is amended to allow this deviation for the pilot phase.*

### 2.4 Statistical Testing (Amended FR-007)
**FR-007**: System MUST attempt hierarchical Bayesian shift tests. If convergence fails (ESS < 100), the system MUST fallback to Paired t-tests (alpha=0.05) with Benjamini-Hochberg correction. This deviation is authorized by Plan Complexity Tracking.

### 2.5 Bias Measurement (Amended FR-010 & SC-003)
**FR-010**: System MUST execute injection recovery tests with known true parameters to establish an independent baseline for bias detection.
**SC-003**: Parameter estimation bias is measured against this external baseline (`Bias_Original`) using `Delta_Bias` (Posterior Mean - True Value).

### 2.6 Event Selection Loop (Amended T015/T016)
The system MUST fetch noise segments and inject signals in batches until **≥12 valid events** with complete spin metadata are found.
* **Loop Condition**: `while valid_count < 12 and attempts < 20`.
* **Error Handling**: If `max_attempts` (20) is reached and `valid_count` is still < 12, the system MUST raise a critical error and halt execution.
* **Target**: The initial target for the pipeline is 15 events (per Amended FR-001), but the validation loop must strictly enforce the minimum of 12 valid events before proceeding.

## 3. Non-Functional Requirements

### 3.1 Performance
The full pipeline execution must complete within 6 hours on standard CI infrastructure (CPU-only).

### 3.2 Data Integrity
All synthetic injections must use `LALSimulation` with known ground truth parameters stored in metadata.

### 3.3 Reproducibility
Random seeds MUST be pinned via `src/utils/config.py`.

## 4. Data Model

### 4.1 Input
- Real GW strain data (H1, L1) from GWOSC.

### 4.2 Intermediate
- Injected strain data (`.h5` or `.npy`).
- Compressed artifacts (`.gz`, `.lz4`, `.jpg2000`, etc.).

### 4.3 Output
- Posterior samples (`.json` or `.h5`).
- Bias metrics (`Delta_Bias`).
- Final summary report.

## 5. Provenance and Deviations

- **Deviation Constitution Principle II**: Use of synthetic injections due to lack of public campaigns. See `code/provenance/deviation_constitution_principle_ii.md`.
- **Deviation JPEG2000 Folding**: Use of Hilbert curve for 1D-to-2D folding. See `code/provenance/deviation_JPEG2000_folding.md`.
- **Deviation PE Engine**: Use of Bilby/Dynesty instead of LALInference. Amended Constitution Principle VII.

## 6. Execution Flow

1. **Data Phase (US1)**: Fetch noise, inject signals, validate metadata (≥12 valid events).
2. **Compression Phase (US2)**: Apply lossless/lossy compression.
3. **PE Phase (US3)**: Run Bilby/Dynesty, compute biases.
4. **Analysis Phase**: Compare `Delta_Bias`, generate reports.

## 7. Appendix

- **Amended T015 Description**: "Implement logic to fetch additional noise segments in batches and inject/validate until **≥12 valid events** with complete spin metadata are found. *Note: Implements a loop to ensure the final analysis set meets FR-009. **MUST include max_attempts=20 and timeout=300s**. **Loop Condition:** `while valid_count < 12 and attempts < 20`. If max attempts reached and valid_count < 12, raise a critical error.*"
- **Amended T016 Description**: "Create `src/data/main.py` to orchestrate the **download-inject-validate** pipeline for **≥15 target events** (per **Amended FR-001**) and produce the validated dataset. The pipeline MUST enforce the stop condition of 12 valid events as defined in T015. *Note: Calls T015 logic.*"
