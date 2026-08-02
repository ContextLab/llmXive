# Project Specification: Quantifying the Impact of Data Compression on Gravitational Wave Event Reconstruction

## 1. Introduction

This project investigates how data compression techniques affect the accuracy of gravitational wave (GW) event parameter estimation. The goal is to determine the maximum compression ratio achievable without significantly biasing the inferred physical parameters (masses, spins, distance, etc.) of compact binary coalescences.

## 2. Functional Requirements

### FR-001: Data Acquisition
System MUST generate ≥15 synthetic CBC injections into real GW noise segments fetched from GWOSC, using `LALSimulation` with known ground truth parameters, replacing the requirement to download public injection campaigns.
*Note: This requirement is amended to reflect the lack of public injection campaigns. See T004.0 for formal deviation record.*

### FR-002: Compression Implementation
System MUST implement at least three compression methods:
- Lossless: gzip, LZ4, bzip2 at multiple levels
- Lossy: Quantized floating-point, Wavelet Thresholding
- Transformation+Compression: JPEG2000 via 1D-to-2D folding (Hilbert curve)

### FR-003: JPEG2000 Folding
JPEG2000 compression MUST be implemented via 1D-to-2D folding (Hilbert curve algorithm) to adapt 2D codecs to 1D strain data. The resulting artifacts are tagged as 'Transformation+Compression'.
*Note: This requirement is amended per T007 and T006 (JPEG2000 deviation record).*

### FR-004: Error Metrics
System MUST compute Mean Squared Error (MSE) and Signal-to-Noise Ratio (SNR) degradation for all compression methods.

### FR-005: Parameter Estimation Engine
System MUST run Parameter Estimation using `Bilby` with `Dynesty` (Fast PE) on both original and compressed datasets for ≥12 events, replacing LALInference due to CI constraints.
*Note: This requirement is amended per T001#1 and Constitution Principle VII (Modified).*

### FR-006: Posterior Comparison
System MUST compute credible interval overlap between original and compressed posteriors.

### FR-007: Statistical Significance Testing
System MUST attempt hierarchical Bayesian shift tests. If convergence fails (ESS < 100), the system MUST fallback to Paired t-tests (alpha=0.05) with Benjamini-Hochberg correction. This deviation is authorized by Plan Complexity Tracking.
*Note: This requirement is amended per T012.0.*

### FR-008: Spin Metadata
System MUST include spin metadata (tilt angles) in all injection metadata.

### FR-009: Minimum Event Count
System MUST process ≥12 valid events with complete spin metadata for final analysis.

### FR-010: Baseline Bias Calculation
System MUST execute injection recovery tests with known true parameters to establish an independent baseline for bias detection. System MUST measure bias against this external baseline (`Bias_Original`) using `Delta_Bias` (Posterior Mean - True Value).
*Note: This requirement is amended per T027.0 to measure Delta_Bias against an external baseline.*

## 3. Success Criteria

### SC-001: Compression Threshold
Identify the maximum compression ratio where SNR degradation remains < 5%.

### SC-002: Reconstruction Validity
Ensure transformation artifacts (e.g., JPEG2000 folding) do not invalidate MSE/SNR comparisons.

### SC-003: Bias Measurement
Parameter estimation bias is measured against this external baseline (`Bias_Original`) using `Delta_Bias` (Posterior Mean - True Value).
*Note: This criterion is amended per T027.0.*

## 4. Constitution Amendments

### Principle VII (Modified)
The original requirement for LALInference is replaced by `Bilby` with `Dynesty` for the pilot phase due to CI constraints. This deviation is authorized under Plan Complexity Tracking.

## 5. Data Pipeline Overview

1. **Acquisition**: Fetch real GW noise from GWOSC.
2. **Injection**: Generate synthetic CBC signals with known ground truth using LALSimulation.
3. **Validation**: Ensure metadata completeness (mass, spin, distance) and SNR > 8.
4. **Compression**: Apply lossless/lossy methods to validated events.
5. **Parameter Estimation**: Run Bilby/Dynesty on original and compressed data.
6. **Analysis**: Compare posteriors, compute Delta_Bias, and determine compression thresholds.

## 6. Implementation Plan

The project is divided into phases:
- Phase 0.1: Spec & Constitution Amendments
- Phase 1: Setup
- Phase 2: Foundational
- Phase 3: User Story 1 (Acquire & Validate)
- Phase 4.5: Baseline Generation
- Phase 5: User Story 2 (Compression)
- Phase 6: User Story 3 (Parameter Estimation)
- Phase 7: Polish & Cross-Cutting Concerns

## 7. Task Reference

- **T015**: Implement logic to fetch additional noise segments in batches and inject/validate until ≥12 valid events with complete spin metadata are found. **MUST include max_attempts=20 and timeout=300s**. **Loop Condition:** `while valid_count < 12 and attempts < 20`. If max attempts reached and valid_count < 12, raise a critical error.
- **T016**: Create `src/data/main.py` to orchestrate the download-inject-validate pipeline for ≥15 target events (per Amended FR-001) and produce the validated dataset. *Note: Calls T015 logic.*