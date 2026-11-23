# Project Specification: Quantifying the Impact of Data Compression on Gravitational Wave Event Reconstruction

## 1. Introduction
This project investigates the impact of data compression techniques on the reconstruction accuracy of gravitational wave (GW) events. The goal is to determine the maximum compression ratio achievable without significantly biasing parameter estimation (PE) results for compact binary coalescences (CBCs).

## 2. Functional Requirements (FR)

### FR-001: Data Acquisition
**Amended Text**: System MUST generate ≥15 synthetic CBC injections into real GW noise segments fetched from GWOSC, using `LALSimulation` with known ground truth parameters, replacing the requirement to download public injection campaigns.

### FR-002: Compression Methods
System MUST implement at least two lossless compression methods (e.g., gzip, LZ4) and two lossy methods (e.g., quantization, wavelet thresholding, JPEG2000 via 1D-to-2D folding).

### FR-003: JPEG2000 Implementation
**Amended Text**: JPEG2000 compression MUST be implemented via 1D-to-2D folding (Hilbert curve algorithm) to adapt 2D codecs to 1D strain data. The resulting artifacts are tagged as 'Transformation+Compression'.

### FR-004: Reconstruction Error Metrics
System MUST compute Mean Squared Error (MSE) and Signal-to-Noise Ratio (SNR) degradation for all compressed waveforms.

### FR-005: Parameter Estimation Engine
**Amended Text**: System MUST run Parameter Estimation using `Bilby` with `Dynesty` (Fast PE) on both original and compressed datasets for ≥12 events, replacing LALInference due to CI constraints. Constitution Principle VII is amended to allow this deviation for the pilot phase.

### FR-006: Bias Calculation
System MUST calculate `Delta_Bias` as the difference between the posterior mean of the compressed run and the true injected parameters, normalized against the baseline bias.

### FR-007: Statistical Significance
**Amended Text**: System MUST attempt hierarchical Bayesian shift tests. If convergence fails (ESS < 100), the system MUST fallback to Paired t-tests (alpha=0.05) with Benjamini-Hochberg correction. This deviation is authorized by Plan Complexity Tracking.

### FR-008: Spin Metadata
System MUST ensure all synthetic injections include complete spin metadata, specifically tilt angles.

### FR-009: Event Count
System MUST process a minimum of 12 valid events with complete metadata to ensure statistical power.

### FR-010: Baseline Establishment
**Amended Text**: System MUST execute injection recovery tests with known true parameters to establish an independent baseline for bias detection.

## 3. Success Criteria (SC)

### SC-001: Pipeline Execution
The full pipeline (Download -> Inject -> Compress -> PE -> Analyze) must complete within 6 hours on standard CI infrastructure.

### SC-002: Compression Impact
Lossy compression levels causing SNR degradation > 5% must be flagged as 'unacceptable' for PE.

### SC-003: Bias Measurement
**Amended Text**: Parameter estimation bias is measured against the external baseline (`Bias_Original`) using `Delta_Bias` (Posterior Mean - True Value).

## 4. Constitution Amendments

### Principle II (Verified Accuracy)
**Deviation**: Use of synthetic injections instead of public injection campaigns is authorized due to lack of public data. Mitigation includes using `LALSimulation` with known ground truth.

### Principle VII (Engineering Constraints)
**Amended Text**: The use of `Bilby/Dynesty` replaces `LALInference` for parameter estimation to meet CI time and resource constraints. This is a temporary deviation for the pilot phase.

## 5. Data Model
- **Raw**: GWOSC noise segments (HDF5/JSON)
- **Interim**: Compressed waveforms (various formats)
- **Processed**: Posterior samples (JSON/CSV)
- **External**: Baseline bias metrics (JSON)

## 6. Implementation Plan
The project is divided into phases:
1. **Phase 0.1**: Spec & Constitution Amendments
2. **Phase 1**: Setup
3. **Phase 2**: Foundational
4. **Phase 3**: User Story 1 (Data Acquisition)
5. **Phase 4.5**: Baseline Generation
6. **Phase 5**: User Story 2 (Compression)
7. **Phase 6**: User Story 3 (Parameter Estimation)
8. **Phase 7**: Polish & Reporting
