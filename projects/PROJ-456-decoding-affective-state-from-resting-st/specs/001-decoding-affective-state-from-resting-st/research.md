# Research: Decoding Affective State from Resting-State EEG Microstates

## 1. Problem Statement & Hypotheses

**Research Question**: Do temporal dynamics of canonical resting-state EEG microstates (Classes A-D) correlate with self-reported affective dimensions (Valence, Arousal)?

**Hypotheses**:
- H1: Microstate Class C (associated with salience/anterior cingulate) duration/occurrence correlates with Arousal.
- H2: Microstate Class D (associated with visual/parietal) coverage correlates with Valence.
- H3: Microstate transition probabilities show significant associations with affective instability.

**Observational Nature**: This study is purely observational. No causal claims will be made. All results are framed as **associational correlations** (FR-007).

## 2. Dataset Strategy

The project relies on the following verified datasets. **CRITICAL WARNING**: The verified HuggingFace sources for PANAS and SAM appear to be text-based datasets (e.g., 'samsum' is a dialogue summarization dataset, 'cerita_panas' is a story sentiment dataset) and do NOT contain linked affective scores for the EEG subjects in the target datasets.

| Dataset Name | Verified Source URL | Content | Variable Fit Status |
|:--- |:--- |:--- |:--- |
| **EEG Resting State** | ` | Resting-state EEG events | **Check Required**: Verify presence of raw EEG data and subject IDs. |
| **OpenNeuro FSLR64k** | ` | Parquet subset of OpenNeuro | **Check Required**: Verify if this specific subset contains ds003501/ds004137 raw EEG and associated questionnaires. |
| **PANAS** | ` | Text/Sentiment dataset (Invalid) | **INVALID**: This is a text dataset, not PANAS questionnaire scores. **Action**: Skip join. |
| **SAM** | ` | Dialogue summarization dataset (Invalid) | **INVALID**: This is an NLP dataset, not Self-Assessment Manikin scores. **Action**: Skip join. |

**Dataset-Variable Fit Warning**:
The spec requires **both** resting-state EEG (≥128 Hz) **and** self-report affective scores (PANAS/SAM) for the *same subjects*.
- The verified sources for PANAS and SAM are **text-based** and do not contain the required structured affective scores linked to EEG subjects.
- **Action**: The implementation MUST check for the presence of `valence_score` and `arousal_score` fields in the EEG dataset metadata. If missing, the correlation analysis phase is **HALTED** with a "No Linked Data" error.
- **Fallback**: If verified sources lack the specific linked data, the project logs a critical gap, halts the correlation phase, and proceeds only to EEG preprocessing if raw data is present.

## 3. Methodology

### 3.1 Preprocessing (FR-002) & Data Validation (FR-012)
1. **Bandpass Filter**: 1-40 Hz (Butterworth, 4th order).
2. **ICA**: Run FastICA (scikit-learn) or MNE-ICA.
 - Remove components identified as ocular/muscle (using automated heuristics).
 - Retain ≥85% signal variance.
3. **Re-referencing**: Average reference.
4. **Validation**: Check questionnaire completion rate. Exclude subjects with <80% completion.

### 3.2 Microstate Segmentation (FR-003, FR-014)
1. **Template Approach**: Use a **pre-defined 4-class microstate template** from the literature (e.g., standard A-D atlas) to satisfy FR-014 (prevent data leakage) without splitting the small sample.
 - *Rationale*: Splitting data for template derivation reduces effective sample size and biases results in small N studies.
2. **Application**: Apply the pre-defined maps to the full dataset to assign labels at each timepoint.
3. **Validation**: Global Explained Variance (GEV) must be ≥75%.

### 3.3 Feature Extraction (FR-004)
Extract for each of the 4 classes:
- Mean Duration (ms)
- Occurrence Rate (per sec)
- Coverage (%)
- Transition Probabilities (4x4 matrix)

### 3.4 Statistical Analysis (FR-005, FR-006, FR-013, FR-015)
1. **Correlation**: Compute Pearson/Spearman correlations between 16 microstate features and 2 affective dimensions (Valence, Arousal). Total tests = 32.
2. **Correction Strategy**:
 - **Primary**: **Holm-Bonferroni** (controls Family-Wise Error Rate while being more powerful than Bonferroni under dependency).
 - **Secondary**: **Benjamini-Hochberg (FDR)** (controls False Discovery Rate).
 - *Note*: VIF is **not** used as a decision metric for correction type, as it is methodologically incoherent for bivariate correlations. The choice of Holm-Bonferroni addresses the dependency structure of the 32 tests directly (per FR-015 spirit).
3. **Effect Size**: Compute Cohen's d and 95% CI for significant correlations.
4. **Stability**: Bootstrap resampling (1000 iterations) if N ≥ 10.
 - If N < 20: Flag results as "Unstable (N < 20)" and rely on analytical p-values.
5. **Replication**: If multiple datasets are available, compute I²/Q-test heterogeneity statistics.

### 3.5 Sensitivity Analysis (FR-010)
Sweep significance thresholds over a range of standard values and report stability metrics (mean, std, range) across the sweep.

## 4. Compute Feasibility & Constraints

- **Hardware**: 2 CPU cores, 7 GB RAM, 14 GB disk.
- **Strategy**:
 - Data loaded in chunks or sampled if full dataset exceeds RAM.
 - No GPU usage.
 - Template-based segmentation and statistical tests are CPU-optimized.
 - **Runtime Limit**: 6 hours. If preprocessing of a full dataset exceeds a reasonable time threshold, the pipeline will process a random sample of subjects to ensure completion.
- **Libraries**: `mne`, `scikit-learn`, `numpy`, `pandas`, `statsmodels` (all CPU-compatible).

## 5. Risks & Mitigations

| Risk | Mitigation |
|:--- |:--- |
| **Dataset Mismatch** | Verified sources for PANAS/SAM are text-based. **Mitigation**: Explicit check for linked data; if fail, log "No Linked Data" and halt correlation phase. |
| **Collinearity/Dependency** | Microstate features are mathematically dependent. **Mitigation**: Use Holm-Bonferroni (primary) which is robust to dependency; no VIF calculation. |
| **Power Limitation** | N < 10 subjects. **Mitigation**: Skip bootstrap; report power limitation. If 10 ≤ N < 20, run bootstrap but flag as unstable. |
| **Memory Overflow** | EEG data is large. **Mitigation**: Stream processing; downsample if necessary; sample subjects. |
