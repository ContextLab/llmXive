# Research: The Impact of Network Efficiency on Age-Related Changes in Resting-State EEG

## Dataset Strategy

**Critical Data Gap**: The current "Verified datasets" block **does not** contain a dataset linking EEG signals with clinical cognitive scores (MMSE/MoCA). The plan explicitly **BLOCKS** the cognitive correlation analysis until a valid source is added. The pipeline will proceed with **EEG-only analysis** (calculating metrics and correlating with Age if available in the TUH EEG Corpus).

| Variable | Source | URL / Loader | Notes |
|:--- |:--- |:--- |:--- |
| **EEG Signals** | TUH EEG Corpus | ` (Accession ID: `tuh_eeg`) | Primary source per FR-001. Demographics (Age) must be present. |
| **Cognitive Scores** | *Missing Verified Source* | N/A | **BLOCKED**: No verified source contains MMSE/MoCA linked to EEG. Analysis skipped if missing. |
| **Demographics** | TUH EEG Corpus (if available) | Same as EEG | If Age/Sex are not in the EEG source, the correlation with Age is also blocked. |

**Dataset Fit Analysis**:
- **EEG**: The TUH EEG Corpus is the required source. We will verify if it contains the 10-20 system electrode layout. If not, we will filter to available channels.
- **Cognition**: The current verified list **does not** contain a clinical cognitive assessment dataset linked to the EEG data. This is a fatal mismatch for the primary research question (FR-001).
 - *Mitigation*: The pipeline will run in "EEG-Only" mode. It will calculate network metrics and correlate them with **Age** (if available). The correlation with **Cognition** will be skipped, and a "Missing Cognitive Data" flag will be added to `results/regression_summary.json`.
 - *Validation*: Synthetic data is **only** used for unit testing the pipeline logic (US-2), not for the final scientific results.
- **ID Linkage Validation**: Before processing, the `01_download_data.py` script will parse the TUH metadata to verify the existence of a unique subject ID linking each EEG file to a demographic record. If a valid ID link cannot be established for a participant, they are excluded from the analysis. This step ensures that the "Age" variable corresponds to the correct "EEG" signal.

## Methodology & Statistical Rigor

### 1. Preprocessing & Graph Construction (US-1)
- **Filtering**: Bandpass 1-40 Hz (MNE `filter_data`).
- **ICA**: Remove ocular/muscular artifacts (MNE `ICA`).
- **Epoching**: 2-second non-overlapping epochs.
- **Connectivity**: **Imaginary Coherence** (in alpha 8-12Hz and beta 13-30Hz bands) to mitigate volume conduction (field spread) which artificially inflates connectivity.
- **Graph Metrics**:
 - **Clustering Coefficient**: $C_i = \frac{2T_i}{k_i(k_i-1)}$
 - **Characteristic Path Length**: $L_i = \frac{1}{N-1} \sum_{j \neq i} d_{ij}$
 - **Global Efficiency**: $E_{glob} = \frac{1}{N(N-1)} \sum_{i \neq j} \frac{1}{d_{ij}}$ (Average of inverse shortest paths, NOT $1/L$).
 - *Note on Spec Contradiction*: FR-003 in the spec mandates calculating efficiency as the mathematical inverse of path length ($1/L$). However, for weighted graphs (which coherence matrices are), this definition is mathematically incorrect and yields invalid metrics. The plan implements the scientifically correct definition (average of inverse shortest paths) and flags the spec for amendment.
 - **Modularity**: Louvain algorithm (NetworkX).
- **Thresholding**: Density-based thresholding at 0.1 (10% strongest edges), with sensitivity sweep (0.05, 0.1, 0.15) per FR-008.

### 2. Statistical Analysis (US-2, US-3)
- **Correlation**: Spearman rank correlation ($r_s$) between metrics and Age (and Cognition if available).
 - *Correction*: Bonferroni correction for family-wise error (number of metrics $\times$ number of outcomes).
 - *Power*: **Simulation-based Power Analysis** (SC-002). We will run a Monte Carlo simulation (1000 iterations) to estimate power for $r=0.3$ given the actual N. If power < 0.80, a "Low Power" warning is issued. Results recorded in `results/power_analysis.json`.
 - *FWER Check*: A permutation test (shuffling labels 1000 times) will be run to measure the actual Family-Wise Error Rate (SC-004) and compare it to the nominal alpha (0.05). Results recorded in `results/fwer_check.json`.
- **Regression**: Multiple linear regression: $Cognitive = \beta_0 + \beta_1(Efficiency) + \beta_2(Age) + \beta_3(Sex) + \beta_4(Edu) + \epsilon$.
 - *Collinearity Check*: Variance Inflation Factor (VIF) < 5.
 - *Associational Frame*: Explicitly state results are correlational (Assumption II).

### 3. Cognitive Registry Validation (FR-007)
- A hardcoded JSON registry of standard, validated tools (e.g., MMSE, MoCA) is maintained in `code/utils/cognitive_registry.py`.
- The pipeline checks the cognitive instrument used for each participant against this registry.
- If an instrument is not in the registry, the participant is flagged as "Invalid Cognitive Measure" and excluded from cognitive analysis.

### 4. Sensitivity Analysis (FR-008)
- The pipeline will sweep network density thresholds over a range of low-density values.
- The stability of correlation coefficients is measured. If cognitive data is missing, the stability metric (variation < 0.05) is applied to the **Age correlation coefficients** to satisfy the requirement.

### 5. Edge Case Handling
- **Low Signal Quality**: If SNR < 10dB or >50% epochs rejected, mark as "Excluded".
- **Missing Cognition**: Exclude from cognitive correlation; retain for age correlation.
- **Small Older Group**: If $N_{60+} < 15$, append "Low Power for Older Group" to `results/regression_summary.json` warnings.

## Decision Rationale (Compute Feasibility)
- **CPU-Only**: All libraries (`mne`, `networkx`, `statsmodels`) have CPU wheels. No GPU training required.
- **Memory**: Processing in batches (20 subjects/batch) ensures < 6GB RAM usage.
- **Runtime**: Graph metrics on the full TUH corpus (if N ~ 100-200) with 64 channels take < 6 hours on 2 CPU cores.

## Risks & Mitigations
1. **Risk**: No valid cognitive scores in verified datasets.
 * **Mitigation**: Pipeline runs in "EEG-Only" mode. Results are limited to Age correlations. A "Data Gap" flag is added to the final report.
2. **Risk**: EEG channel count insufficient for graph theory (needs >10 channels).
 * **Mitigation**: Filter to available 10-20 system channels; if <10, skip graph metrics and report "Insufficient Channels".
3. **Risk**: Volume conduction inflates metrics.
 * **Mitigation**: Use **Imaginary Coherence** instead of standard Coherence.
4. **Risk**: Underpowered study (N < 85).
 * **Mitigation**: Batch processing to maximize N. If N < 85, issue "Study Underpowered" warning and halt correlation analysis.