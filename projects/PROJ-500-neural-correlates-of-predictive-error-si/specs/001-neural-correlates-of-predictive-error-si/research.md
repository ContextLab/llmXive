# Research Plan: Neural Correlates of Predictive Error Signals

## Objective
To investigate the relationship between neural predictive error signals (MMN) and behavioral learning accuracy in a tactile discrimination task, utilizing a Gaussian Linear Mixed-Effects Model with Lagged Alignment.

## Methodology

### 1. Data Acquisition
- Source: OpenNeuro or similar public repositories.
- Criteria: Tactile, somatosensory, or odd-ball paradigms.
- Variables: `stimulus_type`, `response_correctness`.

### 2. Preprocessing
- Filtering: 1-40 Hz bandpass.
- Artifact Removal: ICA.
- Epoching: -200ms to 500ms.
- **Exclusion**: Subjects with <20 valid trials or insufficient cohort size are flagged as "underpowered" and excluded from primary analysis.

### 3. Feature Extraction
- **MMN Amplitude**: Calculated as the mean difference (Deviant - Standard) in the 150–250ms window at CP3, CP4, C3, C4.

### 4. Alignment Strategy (Methodological Correction)
- **Lagged Alignment**: Instead of direct trial-by-trial alignment, we employ a 50-trial moving window for MMN calculation (t-50 to t-10) which is then aligned to the subsequent behavioral accuracy block (t to t+n). This accounts for the latency of learning effects.
- **Pipeline Branching**: If behavioral logs are missing, the analysis defaults to "Stimulus-Driven" mode (using P=0.8 probability for simulation or standard deviation metrics).

### 5. Statistical Analysis (Methodological Correction)
- **Model**: Gaussian Linear Mixed-Effects Model (LME).
 - Formula: `MMN_Amplitude ~ Accuracy + Learning_Phase + (1 | Subject)`
- **Correction**: Benjamini-Hochberg (FDR) for multiple comparisons across electrodes.
- **Validation**: Permutation test (n=1000) to verify significance robustness.
- **Sensitivity**: Time window sweep (±10ms).

## Deviations from Original Spec
- **FR-006 Update**: Changed from generic LME to specific **Gaussian LME** to better fit the continuous nature of MMN amplitude data.
- **FR-005 Update**: Implemented **Lagged Alignment** (50-trial window) to better capture the temporal dynamics of learning, replacing immediate trial alignment.
- **Exclusion Criteria**: Explicitly defined and documented the exclusion of "underpowered" subjects (<20 subjects/trials) from the primary GLMM input, with data written to `data/excluded_subjects.csv`.

## Expected Outcomes
- A robust dataset (`data/aligned_data.csv`) linking lagged neural signals to behavioral accuracy.
- Statistically significant coefficients from the Gaussian LME model indicating the predictive power of MMN on learning.
- Validated results through permutation testing and sensitivity analysis.
