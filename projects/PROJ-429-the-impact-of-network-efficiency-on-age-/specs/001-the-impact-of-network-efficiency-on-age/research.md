# Research: The Impact of Network Efficiency on Age-Related Changes in Resting-State EEG

## Executive Summary

This research plan outlines the methodology for analyzing the relationship between resting-state brain network efficiency and aging/cognitive decline. The study leverages preprocessed EEG data from the Temple University Hospital (TUH) EEG Corpus (accession ID: `tuh_eeg`), computes graph-theoretical metrics (using Area Under the Curve for robustness), and performs statistical analyses while adhering to strict computational constraints (CPU-only, <7GB RAM). Key challenges include ensuring dataset-variable fit, handling missing data, and maintaining statistical rigor through multiple-comparison correction and power analysis.

**Critical Limitation**: The study relies on a single dataset (TUH) containing both EEG and cognitive metadata. If the TUH Corpus lacks paired cognitive scores (MMSE/MoCA) for participants with EEG data, the study **cannot** test the hypothesis that "reduced network efficiency predicts cognitive performance." In this case, the analysis will be restricted to correlating network efficiency with **age only**, and the cognitive prediction aim will be explicitly flagged as untestable with the available data. No cross-dataset matching is attempted.

## Dataset Strategy

### Verified Datasets

The following datasets have been verified for reachability and format. Only these sources will be used:

| Dataset Name | Type | Verified URL | Relevance |
|--------------|------|--------------|-----------|
| TUH EEG Corpus (tuh_eeg) | Raw Signal (EDF/BDF) | | **Primary Source**. Contains resting-state EEG signals. Must be verified for presence of age/cognitive metadata. |

**Dataset-Variable Fit Assessment**:
- **Required Variables**: Age, cognitive score (MMSE/MoCA), EEG signal (resting-state epochs), sex, education.
- **Fit Check**:
 - The TUH EEG Corpus is the mandated source (FR-001). We will inspect the available metadata files (e.g., `events.csv`, `demographics.csv` if available within the corpus) to confirm the presence of cognitive scores.
 - **Critical Limitation**: If the TUH Corpus lacks paired cognitive scores (MMSE/MoCA) for the participants with EEG data, the study **cannot** test the hypothesis that "reduced network efficiency predicts cognitive performance." In this case, the analysis will be restricted to correlating network efficiency with **age only**, and the cognitive prediction aim will be explicitly flagged as untestable with the available data.
 - **No Cross-Dataset Matching**: We will **not** attempt to match participants with external datasets (e.g., MMS-e) as they lack shared unique identifiers, rendering such a join impossible.

**Data Loading**:
- Use `mne.io.read_raw_edf` or `read_raw_bdf` for TUH signal files.
- Use `pandas.read_csv` for any associated metadata files within the TUH repository.
- No `datasets.load_dataset` for HuggingFace datasets as the primary source is PhysioNet.

## Methodology

### Preprocessing Pipeline (FR-002)

1. **Bandpass Filtering**: 1-40 Hz using MNE-Python `filter_data` to remove slow drifts and high-frequency noise.
2. **Artifact Removal**: Independent Component Analysis (ICA) to identify and remove ocular/muscular artifacts. Components will be flagged based on automated criteria (e.g., EOG correlation).
3. **Epoching**:
 - **For Connectivity**: Segment data into **10-second epochs** (non-overlapping) to ensure sufficient frequency resolution (0.1 Hz) for reliable coherence estimation (addresses scientific soundness concern b12f8fb7).
 - **For QC**: Retain 2-second epochs for signal quality checks if needed, but use 10s for graph construction.
4. **Signal Quality Check**: Compute SNR; flag participants with SNR < 10dB as "Low Signal Quality" (FR-001, US-1).
5. **Artifact Rejection Sensitivity (SC-003)**: Perform a sensitivity sweep on the artifact rejection threshold (e.g., 30%, 40%, 50% of epochs rejected). The pipeline will re-run the correlation analysis for each threshold and report the variation in correlation coefficients. If variation > 0.05, the finding is flagged as unstable.

### Network Construction (FR-003)

1. **Connectivity Metric**: Coherence between 10-20 system electrodes in the alpha band (8-12 Hz) using 10s epochs or Welch's method with overlap.
2. **Thresholding Strategy (AUC)**:
 - **Primary Metric**: Compute graph metrics across a density range of 0.05 to 0.20 (step 0.01). The final metric for each participant is the **Area Under the Curve (AUC)** of the metric across this range. This avoids the arbitrariness of a single threshold (addresses concern 7db2650b).
 - **Sensitivity Check**: Also compute metrics at a fixed density of 0.1 for comparison, but AUC is the primary output.
3. **Graph Metrics** (Scientifically Correct Definitions):
 - **Characteristic Path Length**: Average shortest path length.
 - **Clustering Coefficient**: Local clustering.
 - **Global Efficiency**: **Average of the inverse shortest path lengths** ($1/d_{ij}$). *Note: This differs from the spec's FR-003 which incorrectly defines it as the inverse of the average path length. The implementation follows the scientifically correct definition to avoid tautological collinearity.*
 - **Local Efficiency**: Average of the inverse shortest path lengths in local neighborhoods.
 - **Modularity**: Community structure detection using Louvain algorithm.

### Statistical Analysis (FR-004, FR-006)

1. **Correlation**: Spearman rank correlation between each network metric and age.
 - **Multiple-Comparison Correction**: Apply Bonferroni correction (alpha / number of tests) or FDR (Benjamini-Hochberg) to control family-wise error rate (SC-004).
 - **Power Analysis (SC-002)**:
 - **Pre-Analysis Check**: Before running the main analysis, calculate the effective N for the cognitive subset (if available).
 - **Simulation**: Use `statsmodels.stats.power` to estimate power for detecting r=0.3 with the observed N and corrected alpha.
 - **Deliverable**: Output a `power_analysis_report.json` containing the calculated power. If Power < 0.80, flag "Low Power" and interpret results cautiously.
2. **Regression (FR-005)**:
 - **Model**: Multiple linear regression with **Cognitive Score as the outcome (Y)** and **Network Efficiency as the predictor (X)**, controlling for Age, Sex, and Education.
 - **Equation**: $Cognition = \beta_0 + \beta_1(Efficiency) + \beta_2(Age) + \beta_3(Sex) + \beta_4(Ed) + \epsilon$.
 - **Collinearity Check**: Compute VIF for predictors; if VIF > 5, report collinearity and interpret coefficients cautiously (Assumption about collinearity).
 - **Note**: Age is **not** modeled as an outcome of network metrics in the regression, as this is scientifically invalid for this cross-sectional design. Age correlations are handled via Spearman analysis.
3. **Sensitivity Analysis**: Report variation in correlation coefficients across artifact rejection thresholds (SC-003) and density thresholds (FR-008).

### Cognitive Instrument Registry (FR-007)

- **Registry**: A hardcoded JSON file `code/config/cognitive_registry.json` containing validated instruments (e.g., `{"MMSE": "Folstein et al. 1975", "MoCA": "Nasreddine et al. 2005"}`).
- **Validation**: The pipeline loads this registry. If a participant's cognitive instrument is not in the list, they are flagged as "Invalid Cognitive Measure" and excluded from cognitive analysis.

### Visualization (FR-008, US-3)

- Age-stratified bar plots with 95% CI for network metrics.
- Regression coefficient tables with standard errors and p-values.

## Statistical Rigor

### Multiple-Comparison Correction
- **Method**: Bonferroni (conservative) or FDR (less conservative); choice documented in research.md.
- **Rationale**: Testing 4 metrics against 2 outcomes (8 tests) requires correction to avoid false positives (FR-006).

### Power Analysis
- **Target**: Detect r=0.3 with 80% power at corrected alpha.
- **Limitation**: If sample size < 100 (or effective N < 85), power may be insufficient; report explicitly (SC-002).
- **Simulation**: Use `statsmodels.stats.power` to estimate required N; if actual N is lower, flag "Low Power".
- **Deliverable**: `power_analysis_report.json` containing the measured power value.

### Causal Inference
- **Observational Nature**: No randomization; all claims framed as associational (Assumption about methodology).
- **Confounding**: Controlled via regression (sex, education); residual confounding acknowledged.

### Measurement Validity
- **Instruments**: MMSE/MoCA must match hardcoded registry; invalid instruments trigger exclusion (FR-007).
- **EEG Metrics**: Graph metrics validated against community standards; coherence chosen for robustness in resting-state (with 10s epochs).

### Collinearity
- **Age vs. Cognition**: Expected correlation; VIF check ensures coefficients are interpretable (Assumption about collinearity).
- **Network Metrics**: Global/local efficiency are mathematically related but defined correctly to avoid tautology; reported as distinct but interpreted descriptively.

## Edge Cases & Mitigations

| Edge Case | Mitigation |
|-----------|------------|
| Missing cognitive scores | Exclude from cognitive analysis; retain for age correlation if age present. |
| Excessive artifact (>50% epochs rejected) | Flag as "Excluded"; remove from all analyses. |
| Small older group (N < 15) | Output "Low Power for Older Group" warning; adjust CI. |
| Dataset lacks cognitive scores | Restrict analysis to age correlation; document gap. |
| Invalid cognitive instrument | Exclude participant from cognitive analysis per FR-007. |

## Decision Log

| Decision | Rationale |
|----------|-----------|
| Use coherence over PLV | Coherence is more robust to volume conduction in resting-state EEG; community standard. |
| 10s Epochs for Coherence | 2s epochs yield noisy coherence; 10s provides sufficient frequency resolution (0.1 Hz). |
| AUC for Network Metrics | Single fixed threshold (0.1) is arbitrary; AUC across 0.05-0.20 is robust (addresses concern 7db2650b). |
| Bonferroni over FDR | Conservative approach preferred for exploratory analysis with small sample size. |
| CPU-only implementation | Required by compute feasibility constraints; no GPU available on GitHub Actions free tier. |
| Subset data to fit RAM | Full corpus may exceed 7GB; process in batches or sample to ensure runtime < 6h. |
| No Cross-Dataset Matching | TUH is the only verified source; matching with external datasets is impossible without shared IDs. |
| Global Efficiency Definition | Scientific definition (avg of 1/d) used instead of spec's flawed definition (1/avg d) to avoid tautology. |

## References

- **MNE-Python**: Gramfort et al. (2013). "MEG and EEG data analysis with MNE-Python." *Frontiers in Neuroscience*.
- **Graph Metrics**: Rubinov & Sporns (2010). "Complex network measures of brain connectivity." *NeuroImage*.
- **Sensitivity Analysis**: Van Wijk et al. (2010). "Comparing networks." *PLoS ONE*.
- **Power Analysis**: Cohen (1992). "A power primer." *Psychological Bulletin*.
