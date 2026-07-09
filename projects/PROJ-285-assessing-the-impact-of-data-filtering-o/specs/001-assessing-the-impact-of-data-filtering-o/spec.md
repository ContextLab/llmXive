# Feature Specification: Assessing the Impact of Data Filtering on Gravitational Lens Detection Rates

**Feature Branch**: `001-assessing-filtering-impact`  
**Created**: 2026-06-26  
**Status**: Draft  
**Input**: User description: "Assessing the Impact of Data Filtering on Gravitational Lens Detection Rates physics"

## User Scenarios & Testing

### User Story 1 - Generate Detection Metrics Across Threshold Grid (Priority: P1)

The researcher needs to apply a systematic grid of Signal-to-Noise Ratio (SNR) and morphology score thresholds to the DES Year 3 Gold catalog to calculate detection counts for every combination.

**Why this priority**: This is the core data generation step. Without a complete matrix of detection counts across the defined parameter space, no analysis of bias or purity can occur. It establishes the raw data required for all subsequent validation.

**Independent Test**: Can be fully tested by running the filtering script on a small, synthetic subset of the catalog (regardless of input size) and verifying that the output CSV contains rows corresponding to the grid dimensions (SNR steps × 7 morphology steps) with non-negative integer counts.

**Acceptance Scenarios**:
1. **Given** a valid DES Year 3 Gold subset and defined grid ranges (SNR 5–20 in 1σ steps, Morph 0.3–0.9 in 0.1 steps), **When** the filtering script executes, **Then** it outputs a CSV where every row represents a unique threshold pair and contains a non-negative integer detection count, resulting in a set of data rows.
2. **Given** the same input, **When** the script encounters a row with missing SNR or morphology values, **Then** that row is excluded from the count for that specific threshold pair but does not cause the script to crash.

---

### User Story 2 - Validate Purity Against Independent Catalog (Priority: P2)

The researcher needs to cross-reference the detection candidates from each threshold combination against an independent validation catalog (simulated or visually confirmed) to calculate the True Positive (TP) and False Positive (FP) rates, deriving a purity metric.

**Why this priority**: Detection count alone is insufficient; understanding the *quality* (purity) of detections at different thresholds is the primary scientific goal. This step transforms raw counts into scientifically meaningful metrics.

**Independent Test**: Can be fully tested by providing a mock detection list and a mock validation catalog with known overlaps. The script must correctly identify overlaps (TP), non-overlaps in detection (FP), and report a purity score of `TP / (TP + FP)`.

**Acceptance Scenarios**:
1. **Given** a mock detection list of 10 items and a validation catalog with exactly 5 matching coordinates (within tolerance), **When** the validation logic runs, **Then** the The calculated purity is moderate..
2. **Given** a detection list of 5 items and a validation catalog with 0 overlapping coordinates, **When** the logic runs, **Then** the purity is negligible. and the script handles the division-by-zero case gracefully (or reports N/A).

---

### User Story 3 - Statistical Comparison and Visualization (Priority: P3)

The researcher needs to perform a Logistic Regression trend analysis and Bootstrap goodness-of-fit test to compare detection distributions across filtering regimes and generate plots showing detection rate and purity curves versus thresholds.

**Why this priority**: This synthesizes the raw metrics into the final scientific conclusions (hypothesis testing) and provides the visual evidence required for the project report. The new statistical methods correctly handle the nested nature of cumulative detection data.

**Independent Test**: Can be fully tested by feeding the script a pre-calculated CSV of metrics and verifying that it produces a `logistic_coefficient`, `bootstrap_p_value`, and generates two plot files (`.png`) without errors.

**Acceptance Scenarios**:
1. **Given** a CSV of purity values across thresholds, **When** the visualization module runs, **Then** it generates a line plot where the X-axis represents the threshold and the Y-axis represents purity, with no missing data points.
2. **Given** two distinct detection distributions from different threshold regimes, **When** the Logistic Regression/Bootstrap analysis is applied, **Then** the output includes a valid p-value and a conclusion string indicating whether the trends are statistically different.

### Edge Cases

- What happens when the DES Gold catalog subset is smaller than the required 12GB but contains no lens candidates? (System must report zero detections and handle empty validation gracefully).
- How does the system handle a validation catalog that uses a different coordinate system (e.g., RA/Dec vs. pixel coordinates)? (System must assume coordinates are pre-matched or raise a specific error if not, preventing silent data loss).
- What happens if the grid step size results in a threshold combination that filters out all data? (System must record a count of 0 and purity as undefined/0, not crash).

## Requirements

### Functional Requirements

- **FR-001**: System MUST load the DES Year 3 Gold catalog subset and filter it to lens candidate columns without loading the full 12GB+ dataset into memory at once, processing it in chunks or via lazy evaluation. (See US-1)
- **FR-002**: System MUST iterate through a defined grid of SNR thresholds (ranging from low to high significance levels) and morphology score cutoffs (0.3 to 0.9 in 0.1 steps) to generate a complete detection matrix. (See US-1)
- **FR-003**: System MUST calculate detection counts and purity metrics (TP / (TP + FP)) for each threshold combination by cross-referencing with an independent validation catalog using a coordinate matching tolerance ≤ 1.0 arcsec. (See US-2)
- **FR-004**: System MUST frame all findings as associational relationships between filtering thresholds and detection rates, avoiding causal language regarding lens formation, as the data is observational. (See US-2)
- **FR-005**: System MUST apply a multiple-comparison correction (e.g., Benjamini-Hochberg FDR) when interpreting the significance of Bootstrap/Likelihood Ratio tests across the threshold grid to control family-wise error. (See US-3)
- **FR-006**: System MUST perform a sensitivity analysis by sweeping the primary decision cutoff (e.g., SNR) over a small concrete set (e.g., ±0.5σ, ±1.0σ) and reporting how the false-positive rate varies. (See US-3)
- **FR-007**: System MUST generate summary plots (detection rate vs. threshold, purity curves) using `matplotlib` ensuring total output artifacts do not exceed runner disk limits. (See US-3)
- **FR-008**: System MUST validate the injection/recovery methodology of the independent catalog by confirming that the coordinate matching tolerance (≤ 1.0 arcsec) recovers ≥ 95% of simulated lenses injected at known positions. (See US-2)

### Key Entities

- **LensCandidate**: Represents a potential gravitational lens object from the DES catalog, containing attributes: `SNR`, `morphology_score`, `RA`, `Dec`.
- **ValidationEntry**: Represents a confirmed or simulated lens from the independent catalog, containing attributes: `RA`, `Dec`, `simulated_purity_label`.
- **ThresholdMetric**: Represents the result of applying a specific threshold pair, containing attributes: `snr_threshold`, `morph_threshold`, `detection_count`, `purity_score`, `logistic_p_value`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The detection rate variance across the threshold grid is measured against the independent validation catalog to quantify incompleteness corrections, and the system MUST output a CSV row where the variance metric is calculated for every threshold pair. (See US-2)
- **SC-002**: The false-positive rate variation is measured across the sensitivity sweep of the SNR cutoff (e.g., 5σ, 6σ, 7σ) to validate threshold robustness, and the system MUST report the rate change for each sweep step. (See US-3)
- **SC-003**: The statistical significance of detection distribution trends is measured using a Bootstrap goodness-of-fit test, and the system MUST output a p-value < 0.05 for at least one threshold pair to confirm a significant trend. (See US-3)
- **SC-004**: The total analysis runtime is measured against the CI runner time limit to ensure CPU feasibility without GPU acceleration. (See Assumptions)
- **SC-005**: The The memory footprint of the data processing pipeline is measured against the system's RAM capacity limit. to confirm chunking or sampling strategies are effective. (See Assumptions)

## Assumptions

- The DES Year 3 Gold catalog subset (≤12GB) contains the necessary columns (`SNR`, `morphology_score`, `RA`, `Dec`) and fits within the disk limit of the free-tier GitHub Actions runner when downloaded.
- An independent validation catalog (either `lsst-detect-lenses` simulation or Space Warps dataset) is publicly accessible and provides coordinate-matched entries to the DES subset for purity calculation.
- The analysis treats the relationship between filtering thresholds and detection rates as associational only; no causal claims about lens physics are made based on this observational data.
- Logistic Regression and Bootstrap goodness-of-fit tests are the appropriate statistical methods for comparing nested detection distributions across the defined threshold grid, as they correctly handle the cumulative nature of the data.
- The "sensitivity sweep" for threshold justification will use a fixed set of offsets (±0.5σ, ±1.0σ) as a community-standard default, as the idea did not specify a precise range.
- All required Python libraries (`astropy`, `pandas`, `scipy`, `matplotlib`) are available in the standard `ubuntu-latest` runner environment without requiring custom CUDA or GPU dependencies.
- The dataset does not contain significant missing values for `SNR` or `morphology_score` that would invalidate the grid analysis; rows with missing values are excluded from specific threshold counts.
- The coordinate matching tolerance of ≤ 1.0 arcsec is sufficient to establish ground truth for the validation catalog, recovering ≥ 95% of injected lenses.