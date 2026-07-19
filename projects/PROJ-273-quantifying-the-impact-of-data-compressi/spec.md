# Project Specification: Quantifying the Impact of Data Compression on Gravitational Wave Event Reconstruction

## 1. Introduction
This project quantifies the impact of data compression on the reconstruction of gravitational wave (GW) events from compact binary coalescences (CBC). The goal is to determine whether lossy compression techniques can reduce data storage and transmission costs without significantly degrading the accuracy of parameter estimation (PE).

## 2. Functional Requirements

### FR-001: Data Acquisition
**AMENDED**: System MUST generate ≥15 synthetic CBC injections into real GW noise segments fetched from GWOSC, using `LALSimulation` with known ground truth parameters, replacing the requirement to download public injection campaigns.

### FR-002: Compression Methods
System MUST implement at least one lossless (e.g., LZ4) and one lossy (e.g., JPEG2000, Quantization) compression method.

### FR-003: JPEG2000 Implementation
**AMENDED**: JPEG2000 compression MUST be implemented via 1D-to-2D folding (Hilbert curve algorithm) to adapt 2D codecs to 1D strain data. The resulting artifacts are tagged as 'Transformation+Compression'.

### FR-005: Parameter Estimation Engine
**AMENDED**: System MUST run Parameter Estimation using `Bilby` with `Dynesty` (Fast PE) on both original and compressed datasets for ≥12 events, replacing LALInference due to CI constraints. Constitution Principle VII is amended to allow this deviation for the pilot phase.

### FR-007: Statistical Validation
**AMENDED**: System MUST attempt hierarchical Bayesian shift tests. If convergence fails (ESS < 100), the system MUST fallback to Paired t-tests (alpha=0.05) with Benjamini-Hochberg correction. This deviation is authorized by Plan Complexity Tracking.

### FR-008: Spin Metadata
System MUST validate and include spin metadata (tilt angles) in all injection records.

### FR-009: Event Count
System MUST process a minimum of 12 valid events with complete spin metadata for statistical significance.

### FR-010: Baseline Bias
System MUST execute injection recovery tests with known true parameters to establish an independent baseline for bias detection.

## 3. Success Criteria

### SC-002: Reconstruction Error
Lossy compression is acceptable if SNR degradation is ≤ 5% and MSE is within defined thresholds.

### SC-003: Bias Measurement
**AMENDED**: Parameter estimation bias is measured against the external baseline (`Bias_Original`) using `Delta_Bias` (Posterior Mean - True Value).

## 4. Constitution Amendments

### Principle II (Verified Accuracy)
**Deviation**: Due to lack of public injection campaigns, synthetic injections using `LALSimulation` with known ground truth are authorized under Plan Complexity Tracking. Mitigation includes rigorous validation of injection parameters.

### Principle VII (Technology Selection)
**Amendment**: `Bilby` with `Dynesty` is authorized as the Parameter Estimation engine for the pilot phase, replacing `LALInference`, to meet CI constraints on compute time and resources.

## 5. Data Model
- **Raw Data**: GWOSC noise segments (HDF5/Whitened).
- **Interim Data**: Injected signals with known ground truth, compressed artifacts.
- **Processed Data**: Posterior samples, bias metrics, SNR degradation reports.

## 6. Execution Pipeline
1. **Acquire & Inject**: Fetch noise, inject signals, validate metadata.
2. **Compress**: Apply lossless/lossy methods, measure reconstruction error.
3. **Parameter Estimation**: Run Bilby/Dynesty on original and compressed data.
4. **Analysis**: Compute Delta_Bias, perform statistical tests, generate reports.