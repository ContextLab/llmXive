# Research: The Influence of Simulated Social Validation on Neural Responses to Novel Information

## Dataset Strategy

The project relies on publicly available EEG datasets. The spec requires a dataset with (a) social feedback (simulated vs. real) and (b) social anxiety measures.

**Verified Datasets (Source: User Message Block)**:
The following datasets are available via the verified URLs provided. **Critical Finding**: None of the verified URLs in the input block correspond to a dataset that explicitly contains *both* a social feedback manipulation (simulated vs. real) AND a validated social anxiety scale (e.g., LSAS, SPIN) in a single study design.

| Dataset Name | Verified URL | Contains Social Feedback? | Contains Anxiety Scale? | Status |
|:--- |:--- |:--- |:--- |:--- |
| **EEG Resting State** | ` | No (Resting state) | No | **Ineligible** |
| **Seizure EEG (Train/Eval)** | `https://huggingface.co/datasets/physionet/seizure_eeg_train/resolve/main/train.parquet` | No (Seizure focus) | No | **Ineligible** |
| **OpenNeuro FSLR64k** | `https://openneuro.org/datasets/ds000001/versions/1.0.0` | Unknown (Structural/fMRI focus) | No | **Ineligible** |
| **PhysioNet Preprocessed** | ` | No (General sleep/ECG) | No | **Ineligible** |
| **PhysioNet Sleep Data** | ` | No (Sleep) | No | **Ineligible** |
| **CIRCOR Digiscope** | ` | No (Cardiovascular) | No | **Ineligible** |
| **SPIN Data (Dev)** | ` | No (Text data, not EEG) | No (Text corpus) | **Ineligible** |

**Conclusion on Data Availability**:
Based strictly on the **Verified datasets** block provided, **no single dataset** exists that meets the dual criteria (Social Feedback + Anxiety Scale).
- **Action Plan**:
 1. Execute `code/search.py` to programmatically verify the metadata of the listed datasets.
 2. If the search confirms the absence of a suitable dataset (as predicted), the pipeline **MUST** trigger the **Negative Finding Protocol** (T015, T016b, T016c, T016d).
 3. The pipeline will **NOT** attempt to fabricate a dataset or use a dataset lacking the required variables (e.g., using seizure data for social validation is a fatal validity flaw).
 4. The pipeline will generate a "Negative Finding Report" detailing the search results and the specific gap (no dataset with both conditions).

**Alternative Strategy (If a new dataset is found outside the verified block)**:
*Note: Per the "Verified datasets" rule, we cannot cite a URL not in the block. If a new dataset is found, it must be added to the verified block first. For this plan, we assume the search confirms the gap.*

## Methodological Rigor

### Statistical Approach
- **Model**: Linear Mixed-Effects Model (LMM).
 - **Dependent Variable**: P300 Amplitude (µV).
 - **Fixed Effects**: `validation_type` (Simulated vs. Real), `social_anxiety_score`, `validation_type * social_anxiety_score`.
 - **Random Effects**: Random intercepts for `subject_id`.
 - **Correction**: Holm-Bonferroni for the set of fixed effects (3 tests).
 - **Justification**: LMM handles unbalanced data and within-subject correlations. Holm-Bonferroni controls family-wise error rate (FWER) for the small number of planned comparisons.
- **Sensitivity Analysis**:
 - Sweep artifact rejection thresholds: ±75 µV, ±100 µV, ±150 µV.
 - **Metric**: Stability of the interaction term's p-value and effect size.
 - **Rationale**: Ensures results are not driven by arbitrary noise thresholds (FR-006).

### Statistical Rigor Checklist
- **Multiple Comparisons**: Addressed via Holm-Bonferroni (FR-005).
- **Power Justification**:
 - *Constraint*: The dataset size is unknown until download.
 - *Plan*: If the dataset has < 20 participants, the study will be flagged as "Underpowered" in the report. No post-hoc power calculation will be used to justify non-significant results.
- **Causal Inference**:
 - **Assumption**: The study is **observational** (even if feedback is manipulated, the anxiety measure is a pre-existing trait).
 - **Claim**: Findings will be framed as **associational** (e.g., "Anxiety moderates the neural response to...") not causal. No randomization of anxiety exists.
- **Measurement Validity**:
 - **P300**: Defined as peak amplitude in 250-550ms at Pz/CPz (Polich, 2007).
 - **Anxiety**: If a dataset is found, it must use LSAS or SPIN. If not, the study aborts.
- **Collinearity**:
 - VIF will be computed. If VIF > 5, the model will be re-specified (e.g., centering variables) or the independence of effects will be qualified in the discussion.

## Compute Feasibility (CPU-First)

- **Environment**: GitHub Actions Free Tier (multiple CPU cores, 7GB RAM).
- **Method**:
 - **Preprocessing**: `mne-python` is CPU-tractable for standard EEG (filtering, ICA) on datasets of ~20-50 subjects.
 - **Model**: `statsmodels` LMM is CPU-tractable.
 - **GPU Escape Hatch**: **NOT REQUIRED**. The spec explicitly states "All analyses will be performed using classical statistical methods (no deep-learning or GPU-based methods)."
 - **Data Streaming**: If the dataset exceeds RAM, `datasets.load_dataset(..., streaming=True)` will be used to process epochs in batches.

## Risk Assessment

1. **Data Gap (High Risk)**: No dataset matches the criteria.
 - *Mitigation*: Trigger Negative Finding Report (T015).
2. **Low Trial Count (Medium Risk)**: < 30 trials/condition.
 - *Mitigation*: Exclude participant (Edge Case in spec).
3. **High Artifact Rate (Medium Risk)**: > 40% rejection.
 - *Mitigation*: Flag as "low-quality" and exclude.
