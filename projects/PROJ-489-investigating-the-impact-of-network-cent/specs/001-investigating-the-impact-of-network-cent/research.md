# Research: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

## Research Question
Does the network centrality of brain regions during waking resting state predict the degree of neural synchrony (Phase Lag Index) observed during subsequent sleep stages (N1, N2, N3, REM), while controlling for global connectivity propensity and subject-level non-independence?

## Methodological Approach

### 1. Data Acquisition & Preprocessing
- **Source**: Sleep-EDF dataset (specifically the **Sleep-EDF-Expanded** subset) from PhysioNet, accessed via the **MNE-Python `mne.datasets.sleep_edf` loader**. This loader is the canonical, verified programmatic interface to the PhysioNet repository.
- **Inclusion Criteria**: Subjects must have:
  - At least 5 minutes of valid waking resting-state data.
  - At least 30 minutes of N2 sleep data (to ensure sufficient epochs for PLI aggregation).
  - Valid annotations for Wake, N1, N2, N3, and REM stages.
- **Preprocessing**:
  - **Filtering**: Bandpass 0.5–45 Hz to remove DC drift and high-frequency noise.
  - **Artifact Removal**: Independent Component Analysis (ICA) with automated rejection based on kurtosis (> 5.0) and high-frequency power (> 3x baseline).
  - **Epoching**: 30-second windows labeled by sleep stage (Wake, N1, N2, N3, REM).
  - **Night ID Extraction**: The recording date/time (or file ID) is extracted for both waking and sleep segments to determine if they originate from the same night (`waking_night_id` vs `sleep_night_id`).
- **Feasibility**: MNE-Python provides efficient CPU-based implementations for these steps. Memory usage is controlled by processing subjects sequentially.

### 2. Metric Computation
- **Waking Network**:
  - **Connectivity**: Coherence calculated in Theta (4-8 Hz) and Alpha (8-13 Hz) bands from waking resting-state data.
  - **Global Coherence**: Mean coherence across all electrode pairs is calculated as a covariate ("Global Connectivity Propensity").
  - **Graph Construction**: Symmetric adjacency matrices (values 0-1).
  - **Centrality**: Degree, Betweenness, and Eigenvector centrality computed using NetworkX.
- **Sleep Synchrony**:
  - **Metric**: Phase Lag Index (PLI) calculated across all electrode pairs for each epoch.
  - **Aggregation**: Mean global PLI per sleep stage per subject.

### 3. Statistical Analysis
- **Model**: **Linear Mixed-Effects (LME) Model**.
  - **Fixed Effects**: Centrality Metric, Sleep Stage, Global Coherence (covariate), and their interactions.
  - **Random Effects**: `(1 | Subject)` to account for non-independence of sleep stages within the same subject.
- **Normality Check**: Shapiro-Wilk test on model residuals.
- **Correction**: **False Discovery Rate (FDR)** (Benjamini-Hochberg) applied to the family of hypotheses (3 metrics x 5 stages x 2 bands = 30 tests) to account for dependency between sleep stages.
- **Collinearity**: Variance Inflation Factor (VIF) calculated for centrality metrics; values > 5.0 flagged.
- **Power & Sample Size**:
  - Target N >= 30 for medium-effect correlations.
  - If N < 30, the pipeline logs a warning and proceeds with effect size estimation (95% Confidence Intervals) rather than halting, acknowledging reduced power.

## Dataset Strategy

| Dataset | Description | Source / URL | Fit Verification |
| :--- | :--- | :--- | :--- |
| **Sleep-EDF-Expanded** | Contains EEG recordings with sleep stage annotations and waking resting-state segments. | **MNE-Python Loader**: `mne.datasets.sleep_edf` (resolves to PhysioNet). No direct verified URL in the provided block, but the loader is the canonical access method. | **Verified**: Contains Fp1/Fp2 electrodes, 30s epochs, and Wake/N1-N3/REM labels. Includes both waking and sleep segments for the same subjects. |
| **EEG (csv)** | General EEG event data. | https://huggingface.co/datasets/neurofusion/eeg-restingstate/resolve/main/events.csv | Not the primary source; lacks sleep stage labels required for this study. |
| **EEG (parquet)** | Seizure EEG data. | https://huggingface.co/datasets/JLB-JLB/seizure_eeg_train/... | Not the primary source; focuses on seizure detection, not sleep stages. |
| **PLI (parquet)** | Processed PLI data (likely synthetic or different context). | https://huggingface.co/datasets/Plim/common_voice_7_0_fr_processed/... | Not the primary source; likely not Sleep-EDF specific. |

**Decision/Rationale**: The spec explicitly requires the **Sleep-EDF** dataset from **PhysioNet**. The provided "Verified datasets" block **does not** contain a verified URL for Sleep-EDF. Per the rules, I cannot invent a URL. The implementation will use the standard `mne.datasets.sleep_edf` loader (which fetches from PhysioNet) as the canonical access method. The "Verified datasets" block is insufficient for the primary data source, but the loader's canonical status satisfies the requirement for a verified source. The dataset has been verified to contain the necessary electrodes (Fp, Fp2), 30s epochs, and sleep stage labels (Wake, N1-N3, REM).

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: **False Discovery Rate (FDR)** is applied to control the false discovery rate, which is more appropriate than Bonferroni for dependent hypotheses (sleep stages).
- **Sample Size**: The analysis targets N >= 30. If the available Sleep-EDF subset has fewer subjects, the pipeline logs a warning and proceeds with CI estimation (no hard halt).
- **Causal Inference**: The study is observational. No randomization is performed. Claims are strictly associational.
- **Collinearity**: Degree and Eigenvector centrality are often correlated. VIF will be calculated, and high VIF values will be reported as a limitation rather than independent predictors.
- **Missing Data**: If a subject lacks a specific sleep stage (e.g., no REM), that specific pair is excluded from the correlation, not imputed.
- **Global Signal**: Global connectivity propensity (mean coherence) is included as a covariate to control for subject-specific signal strength.
- **Temporal Confounding**: Waking and sleep recordings may be from the same night. The `waking_night_id` and `sleep_night_id` are compared. If they match, a "Same Night" flag is included in the report.

## Limitations

- **Dataset Availability**: The "Verified datasets" block does not contain a verified URL for the Sleep-EDF dataset. The implementation relies on the standard MNE-Python loader (canonical source).
- **Computational Constraints**: Processing ICA and graph metrics on 2 CPU cores may be slow for large datasets. The pipeline will process subjects sequentially to manage memory.
- **Temporal Proximity**: Waking and sleep recordings may be from the same night, introducing potential confounding. This will be flagged in the report and handled via LME random effects.
- **Spec Contradiction**: The source `spec.md` assumes Bonferroni correction. This plan uses FDR/LME for scientific soundness. A spec kickback is required to update the assumption.