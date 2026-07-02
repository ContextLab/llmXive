# Research: Investigating the Relationship Between Brain Network Dynamics and Musical Genre Preference

## 1. Research Question & Hypotheses

**Primary Question**: Is there a statistically significant association between resting-state functional network dynamics (specifically global efficiency, modularity, and dynamic reconfiguration rates) and individual musical genre preference?

**Hypotheses**:
- **H1**: Individuals with higher preference for complex genres (e.g., classical, jazz) will exhibit higher global efficiency in the Default Mode Network (DMN) and Salience Network.
- **H2**: Dynamic reconfiguration rates (flexibility) in the Auditory Network will correlate with the breadth of musical genre preference.
- **H3**: These associations will survive Benjamini-Hochberg correction for multiple comparisons.

## 2. Dataset Strategy

### Verified Sources
The following datasets are verified for download and format compatibility. **Note**: The spec requires behavioral variables (Music Preference/STOMP-R) which are **NOT** present in the verified OpenNeuro fMRI data sources listed below (ds000030, ds000208). The pipeline will attempt to find these in the metadata; if absent, it will halt.

| Dataset Name | Verified URL | Content | Status |
|:--- |:--- |:--- |:--- |
| OpenNeuro fMRI (Parquet) | ` | Resting-state fMRI data (fsLR64k) | **Available** |
| OpenNeuro fMRI (JSON) | ` | Dataset dictionary/metadata | **Available** |
| BOLD (JSONL) | ` | BOLD embeddings (not fMRI time series) | **Irrelevant** |
| BOLD (Parquet) | ` | BOLD embeddings | **Irrelevant** |
| TRs (CSV) | ` | Text summarization choices | **Irrelevant** |

### Dataset-Variable Fit Analysis (CRITICAL)
- **Requirement**: The spec requires `musical_genre_preference` or `STOMP-R` (a proxy).
- **Verified Data**: The OpenNeuro sources listed above contain **fMRI imaging data**. They do **not** contain the specific behavioral questionnaires required for this study.
- **STOMP-R**: No verified source found in the input block for the primary datasets.
- **Action Plan**:
 1. **Proactive Search**: The `data/validate.py` module will first scan the BIDS `participants.tsv` and any JSON sidecars for keys matching `musical`, `genre`, `STOMP`, or `preference`.
 2. **Targeted Dataset Search**: If the primary datasets (ds000030, ds000208) fail, the pipeline will query OpenNeuro for datasets specifically tagged with "music" or "STOMP-R" (e.g., ds000262) as a fallback.
 3. **If Missing**: If no dataset with the required variables is found, the system will raise `ERR_DATA_MISSING` and log the specific missing field. It will **NOT** proceed to analysis.
 4. **Fallback**: If the primary variable is missing but `STOMP-R` is present in the metadata of a fallback dataset, switch to `STOMP-R`. If neither, halt.

### Data Collection Strategy (If Data Missing)
If the verified sources do not contain the required behavioral variables, the research question is **untestable** with the current data source. The plan mandates the following steps before proceeding:
- **Step 1**: Identify a specific OpenNeuro dataset known to contain STOMP-R or musical preference (e.g., via a targeted search).
- **Step 2**: If no such dataset exists, the project must be paused, and a protocol for **primary data collection** (recruiting subjects, administering STOMP-R, scanning) must be defined.
- **Step 3**: The pipeline will not run until a valid data source is confirmed.

## 3. Methodological Rigor

### Statistical Rigor
- **Multiple Comparisons (Family Definition)**: The "Family of Tests" is defined as the set of all (Metric × Genre) pairs. For example, the family size is determined by the product of the number of metrics and the number of genres. The Benjamini-Hochberg (BH) correction will be applied across this **entire family** to control the False Discovery Rate (FDR) at q < 0.05. This increases the stringency of the threshold and reduces power, reinforcing the need for N≥85.
- **Power Analysis**: Post-hoc power analysis (FR-009) will be performed using `statsmodels.stats.power`.
 - *Target*: Power ≥ 0.8 for effect size |r| ≥ 0.3.
 - *Requirement*: Minimum N ≥ 85. If N < 85, the study is flagged as "Underpowered" and the pipeline halts.
- **Causal Claims**: No causal claims will be made. The study is observational (resting-state). All results will be framed as "associations".
- **Collinearity Handling**: Metrics like global efficiency and modularity are derived from the same connectivity matrix. The plan will:
 1. Calculate the correlation matrix between all metrics.
 2. If high collinearity (r > 0.8) is detected, the plan will report them descriptively but will **not** claim them as independent predictors in a combined model.
 3. Consider partial correlations to disentangle effects if necessary.
- **Measurement Validity**: The Schaefer-400 atlas and Yeo-7 networks are standard, validated parcellations. STOMP-R is a validated instrument (if found), but its validity depends on the specific dataset's administration.

### Robustness & Sensitivity
- **Sliding Window Sensitivity (FR-011)**: Dynamic metrics will be computed with window sizes of, 30, and 40 TRs. Stability will be measured via Intraclass Correlation Coefficient (ICC). If ICC < 0.7, the metric is considered unstable and flagged.
- **Null Distribution (FR-010)**: A permutation test with **1,000+ iterations** will randomize behavioral labels to verify the false positive rate is ≤ 0.05.
 - *Note*: The spec (FR-010) states 100 permutations, which is statistically insufficient for stable p-value estimation (min p=0.01). This plan uses [deferred]+ to ensure robustness. A spec amendment is required to align FR-010 with this requirement.
- **Motion Control**: Dynamic FC metrics are highly sensitive to motion. The plan requires:
 1. Regressing out Framewise Displacement (FD) and DVARS from the time series **before** sliding-window analysis.
 2. Including mean FD as a covariate in the final correlation model.
 3. Excluding subjects with mean FD > 0.5mm.

## 4. Compute Feasibility (CPU-Only)

- **Environment**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
- **Strategy**:
 - **fMRIPrep**: Run in Docker. If memory errors occur, the pipeline will downsample spatial resolution or process subjects sequentially (not in parallel) to stay within 6GB RAM.
 - **Data Sampling**: **NO SAMPLING TO N=50**. The pipeline requires N≥85. If N < 85, it halts.
 - **Runtime Risk**: N=85 subjects may exceed the 6-hour limit. The pipeline will log a warning and may fail. This requires a spec amendment to increase compute resources or reduce the scope.
 - **Libraries**: `nilearn` and `networkx` are CPU-optimized. No GPU/CUDA code will be used.
 - **Precision**: Default float64. No 8-bit quantization.

## 5. Decision Rationale

- **Why Schaefer-400?** It provides a fine-grained parcellation suitable for detecting subtle network dynamics, aligning with FR-003.
- **Why Sliding Window?** It captures non-stationary dynamics (FR-005) which static connectivity misses.
- **Why BH Correction?** The number of tests (Metrics x Genres) is large; BH is less conservative than Bonferroni while controlling FDR, suitable for exploratory neuroscience (FR-007).
- **Why Halt on Missing Data?** Fabricating data or using a proxy not verified in the dataset violates Constitution Principle II (Verified Accuracy) and risks a fatal dataset-variable fit error.
- **Why 1,000+ Permutations?** A specified number of permutations yields a minimum p-value of 0.01 and high variance. [deferred]+ is required for robust estimation of the null distribution.