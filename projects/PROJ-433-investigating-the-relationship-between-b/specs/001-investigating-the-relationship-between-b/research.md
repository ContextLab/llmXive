# Research: Investigating the Relationship Between Brain Network Dynamics and Subjective Time Perception

## Dataset Strategy

This study utilizes the Human Connectome Project (HCP) large-scale release. The specific data modalities required are:
1. **Resting-state fMRI**: High-resolution resting-state scans (NIfTI) or pre-extracted time-series for a standard set of parcels.
2. **Behavioral Data**: Specifically the Digit Symbol Substitution Test (DSST) scores.

**Verified Datasets & Sources**:
Per the project constraints, only the following verified sources are cited. **Critical Note**: The filenames of some verified URLs suggest they may not contain fMRI data. The pipeline includes a **content verification step** to ensure the downloaded files actually contain the required data types. If a file fails verification, it is skipped, and a "Data Gap" is reported.

| Dataset Component | Source URL | Loading Method | Verification Status |
|:--- |:--- |:--- |:--- |
| HCP Behavioral (CSV) | ` | `pandas.read_csv` | **Verified for Metadata**: Contains subject IDs and behavioral scores. |
| HCP Flat Data (Parquet) | ` | `pandas.read_parquet` | **Verified for Metadata**: Contains subject IDs. |
| DSST Scores (Zip) | ` | `zipfile` + `pandas` | **Verified for Metadata**: Contains DSST scores. |
| HCP fMRI (Parquet) | ` | `pandas.read_parquet` | **UNVERIFIED for fMRI**: Filename suggests image generation data. **Pipeline will skip this for fMRI analysis.** |

**Dataset-Variable Fit Assessment**:
* **Requirement**: The study needs **resting-state fMRI time-series** for 200 parcels (Schaefer atlas) and **DSST scores**.
* **Gap Analysis**:
 * The verified URLs for behavioral data (`train.csv`, `LC.zip`) appear to contain DSST scores and subject IDs.
 * The verified URL for fMRI data (`Lexica.art.parquet`) **does not appear to contain fMRI time-series** (based on filename).
 * **Conclusion**: There is currently **no verified source** in the provided list that contains the required fMRI time-series or NIfTI files.
* **Fallback Strategy**:
 * **Primary**: The pipeline will attempt to download the verified behavioral data.
 * **Secondary**: The pipeline will **fail gracefully** with a "Data Gap: fMRI time-series not found in verified sources" error.
 * **Tertiary (Unit Tests Only)**: Synthetic fMRI time-series will be generated **only** for unit testing the code logic (e.g., verifying that the Louvain algorithm runs, that the correlation function works). **Synthetic data will NOT be used for the primary hypothesis test.**
 * **Implication**: The primary research question (relationship between brain dynamics and behavior) **cannot be answered** with the current verified sources. The project will report this as a "Data Availability Block" in the final paper.

## Methodological Rigor

### Statistical Analysis Plan
1. **Correlation**: Spearman rank correlation ($\rho$) between Reconfigurability Metric (transitions count) and DSST score.
 * *Rationale*: Non-parametric test suitable for non-normal distributions common in neuroimaging metrics.
2. **Multiple Comparisons**: Bonferroni correction applied across all metric-behavior pairs.
 * *Correction Factor*: $k = (\text{number of metrics}) \times (\text{number of behavioral measures})$.
3. **Permutation Testing**: 1000 shuffles of the DSST scores relative to the connectivity metrics.
 * *Null Hypothesis*: No association between network dynamics and cognitive speed.
 * *Significance*: $p_{perm} = (\text{count of } |r_{perm}| \ge |r_{obs}| + 1) / (N_{perm} + 1)$.
4. **Effect Size**: Cohen's $r$ calculated from Spearman $\rho$ ($r \approx \rho$). Benchmarks: 0.1 (small), 0.3 (medium), 0.5 (large).

### Power & Sample Size
* **Assumption**: 100 subjects (after QC) provides [deferred] power to detect $r=0.3$ at $\alpha=0.05$ (Bonferroni adjusted).
* **Limitation**: The free-tier CI limits testing to a small subset of subjects (1-2) or synthetic data for logic. This subset is **statistically underpowered** to detect the effect size of interest. The CI run serves only as a **logic validation** (does the code run?), not a statistical inference. The final paper will rely on a full dataset (obtained via manual download/cluster) for the power-adequate analysis.
* **Note**: The current plan cannot produce a statistically valid inference on the CI runner due to sample size constraints.

### Measurement Validity & Construct Validity
* **DSST**: Validated proxy for **processing speed** (Wechsler Adult Intelligence Scale).
 * **Limitation**: DSST measures processing speed and attention, **not subjective time perception** (e.g., duration estimation). The hypothesis is framed as investigating the relationship between network dynamics and *cognitive processing speed* (as measured by DSST), with a clear acknowledgment in the paper that DSST is a proxy and not a direct measure of time perception.
* **Schaefer Atlas**: 200 parcels, 7-network parcellation, widely used for functional connectivity.
* **Louvain Algorithm**: Standard for community detection.
 * *Collinearity Note*: If multiple window sizes are tested, they are not independent. The plan will report them descriptively or apply a stricter correction (e.g., FDR) if multiple window sizes are included in the primary hypothesis test.

### Causal Inference
* **Observational Design**: HCP data is observational. No random assignment.
* **Framing**: All claims will be framed as **associational**. No causal claims (e.g., "reconfigurability causes faster processing") will be made.

### Data Gap Handling
* **If fMRI data is missing**: The pipeline will log "Data Gap: fMRI time-series not found" and skip the preprocessing, metric computation, and correlation analysis steps. The final output will be a report stating that the hypothesis could not be tested due to data unavailability.
* **If only behavioral data is found**: The pipeline will download and validate the behavioral data but halt before analysis.
* **No Simulation**: The pipeline will not generate synthetic fMRI data for the primary analysis to avoid invalidating the scientific claim.

## Decision Log

| Decision | Rationale |
|:--- |:--- |
| **No Synthetic Data for Hypothesis** | Synthetic data cannot validate the relationship between *actual* brain dynamics and behavior. It is only used for unit testing code logic. |
| **Explicit Data Gap Reporting** | Since verified URLs lack fMRI time-series, the plan must explicitly state this limitation rather than faking data. |
| **CPU-Only Implementation** | Mandatory for GitHub Actions free tier. No GPU training. |
| **Seed All RNGs** | Required by Constitution Principle I (Reproducibility). |
| **Bonferroni Correction** | Required by Spec FR-006 for multiple comparisons. |
| **DSST as Proxy for Processing Speed** | Acknowledged that DSST measures processing speed, not time perception. The hypothesis is reframed accordingly. |
| **CI as Logic Validation** | CI runs are for verifying code logic and reproducibility, not for statistical inference due to power constraints. |
| **Data Gap as Blocking Condition** | If real fMRI is not found, the study halts. This prevents invalid results. |