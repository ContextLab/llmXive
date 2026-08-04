# Research: The Impact of Interoceptive Awareness on Emotional Regulation During Simulated Stress

## 1. Dataset Strategy

### Verified Datasets & Availability
The project relies on the following datasets. Per the verified sources list, we will use the specific Hugging Face links provided for raw BIDS data where available, or Zenodo DOIs.

| Dataset | Purpose | Verified Source / URL | Variable Fit Check |
|:--- |:--- |:--- |:--- |
| **WESAD** | Stress/ECG/PPG Data | **Primary**: Zenodo DOI `10.5281/zenodo.1292932` (Raw BIDS). **Fallback**: None (Zenodo is the canonical source for raw BIDS). | **Stress**: Contains TSST. **Interoception**: **Likely Missing**. WESAD contains resting, stress, and amusement, but standard documentation confirms it does not include a Schandry heartbeat counting task. This confirms the spec's assumption of a data gap. |
| **OpenNeuro** | Stress/Interoception Search | **Target**: OpenNeuro raw BIDS datasets with physiological data. Search via API for "TSST" and "interoception". | **Search**: Scanning raw BIDS `events.tsv` and `dataset_description.json`. If found, download full BIDS directory. If no raw BIDS dataset with both TSST and interoception exists, this path also yields a data gap. **Note**: Processed fMRI parquets (e.g., fslr64k) are rejected as they lack raw signals and BIDS metadata. |
| **PhysioNet MIT-BIH** | HRV Metric Validation | ` | **Validation**: Used in `00_validate_hrv.py` to verify `hrv-analysis` library correctness before processing study data. |

### Dataset Selection Rationale
* **WESAD** is selected as the primary source because it contains the necessary ECG/PPG signals for HRV calculation and includes a stress paradigm. It is downloaded as a **raw BIDS** dataset to ensure `events.tsv` files are present for the audit.
* **OpenNeuro** is searched for interoception tasks. The plan targets **raw BIDS** datasets to ensure the presence of `events.tsv` files. Processed fMRI parquets are rejected as they lack the required metadata structure.
* **Feasibility Conclusion**: Based on the spec's assumption and the nature of WESAD (which focuses on emotional states, not interoceptive accuracy tasks), the project anticipates a **negative feasibility result** (data gap). The pipeline will generate a "Feasibility Failure" report.

## 2. Methodological Rigor

### Statistical Approach
* **Primary Analysis (Conditional)**: Linear Regression (ANCOVA).
 * **Outcome**: Stress HRV (RMSSD).
 * **Predictor**: Interoceptive Accuracy (Schandry score).
 * **Covariate**: Baseline HRV (RMSSD).
 * **Rationale**: Controls for individual differences in autonomic tone (Constitution Principle VII).
 * **Statistical Justification**: We use raw Stress HRV as the outcome with Baseline HRV as a covariate (ANCOVA) rather than a difference score (Stress - Baseline). In small samples (N<20), difference scores can suffer from regression-to-the-mean artifacts if the correlation between baseline and stress is high. ANCOVA is statistically superior for isolating the unique variance of the predictor while controlling for baseline, provided the linearity assumption holds.
* **Fallback Analysis (Expected)**: **Feasibility Failure Report**.
 * **Context**: If the Schandry task is missing (as expected).
 * **Method**: The study **does not** calculate an Upper Bound of Detectable Effect (UBDE) or Minimum Detectable Effect Size (MDES). A power analysis requires a defined predictor variance, which is unknown/zero if the task is missing. Calculating a UBDE would imply the study *could* have worked with more data, which is false without the task.
 * **Output**: The report explicitly states: "Hypothesis Untestable: Predictor Variable (Interoceptive Accuracy) Missing from Dataset." It documents the specific data gap and the impossibility of the test.

### Statistical Rigor Checklist
* **Multiple Comparisons**: Not applicable for the primary single hypothesis test.
* **Power/Sample Size**: WESAD typically has N=15-20 subjects. This is a small sample. The plan acknowledges low power. If data exists, the report will include a post-hoc power analysis noting the limitation.
* **Causal Inference**: **Associational only**. The dataset is observational. Claims will be framed as "predictive association," not causal effects.
* **Measurement Validity**: Schandry task is the gold standard for behavioral interoception. If missing, no proxy (e.g., resting HRV) will be used, per Spec Assumption.
* **Collinearity**: Baseline HRV and Stress HRV are correlated. Using Baseline as a covariate (ANCOVA) is statistically preferred over difference scores.

## 3. Compute Feasibility

* **CPU-First**: All operations (download, CSV parsing, HRV calculation via `hrv-analysis`, linear regression via `scikit-learn`) are lightweight and run efficiently on a 2-core CPU.
* **Memory**: WESAD BIDS is small (<1GB). HRV calculation is streaming or batch-based, well within 7GB RAM.
* **GPU**: Not required. No deep learning or large language models are used.
* **Time**: Download ([deferred]), Audit ([deferred]), Preprocessing ([deferred]), Analysis ([deferred]). Total estimated time < 20 minutes.

## 4. Data Integrity & Hygiene

* **Checksums**: Every downloaded file will be checksummed (SHA-256) and logged.
* **Raw vs. Derived**: Raw data is immutable. HRV metrics are written to new files.
* **Missing Data**: Subjects with missing interoception data (if any) are excluded from regression but included in descriptive stats. Subjects with noisy ECG (<5% valid beats) are excluded from HRV calculation with logging.
* **Audit Robustness**: The audit script (`02_audit_metadata.py`) checks `events.tsv`, `dataset_description.json`, and `README` files to avoid false negatives from non-standard task labels.

## 5. Decision/Rationale

**Choice**: CPU-only pipeline using `hrv-analysis` and `pandas`.
**Rationale**: The hypothesis requires classical statistical analysis on a small dataset. GPU acceleration offers no benefit and introduces unnecessary complexity. The primary challenge is data availability, not compute power. The plan prioritizes a robust "Feasibility Failure" reporting mechanism over a forced, underpowered regression on incomplete data.