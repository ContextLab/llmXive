# Research: Investigating the Impact of Network Topology on Neural Entrainment to Rhythmic Stimuli

## 1. Dataset Strategy

The analysis requires two distinct data sources:
1. **Resting-State fMRI Data**: To compute network topology (Schaefer 200, AAL, Power 264).
2. **Entrainment Metrics**: External Phase-Locking Values (PLV) to correlate with topology, **specifically derived from rhythmic stimuli**.

### Verified Datasets

Based on the "Verified datasets" block provided in the user message, the following sources are identified. **Critical Data Fit Assessment**:

| Dataset Name | Verified URL | Format | Fit Assessment |
|:--- |:--- |:--- |:--- |
| **HCP (Parquet)** | ` | Parquet | **MISMATCH**: Filename "Lexica.art" suggests image generation data, not fMRI. |
| **HCP (Parquet)** | ` | Parquet | **POTENTIAL**: "HCP-flat" suggests flattened HCP data. **Must verify** if it contains time-series or correlation matrices for 200+ regions. |
| **HCP (JSON)** | ` | JSON | **LOW FIT**: Metadata only. Unlikely to contain the raw connectivity matrices needed for topology calculation. |
| **EEG (CSV)** | ` | CSV | **MISMATCH**: "restingstate" implies **no external stimulus**. The hypothesis requires "rhythmic stimuli" (PLV). This dataset cannot measure entrainment to rhythmic stimuli. |
| **EEG (Parquet)** | ` | Parquet | **MISMATCH**: "seizure" data. Not suitable for rhythmic entrainment analysis of healthy subjects. |
| **MEG (JSONL)** | ` | JSONL | **MISMATCH**: "sycophancy-eval" suggests LLM evaluation, not neuroscience. |

### Critical Data Fit & Gap Analysis

**Fatal Risk Identified**: The spec explicitly requires **HCP S1200** fMRI data and **external entrainment metrics** (PLV to rhythmic stimuli).
- The provided "Verified datasets" block **does not contain a verified URL** for the specific HCP S1200 resting-state time-series or correlation matrices required for Schaefer/AAL parcellation.
- The provided "Verified datasets" block **does not contain a verified URL** for a dataset with "entrainment strength" or "phase-locking values" to **rhythmic stimuli**. The closest is `neurofusion/eeg-restingstate`, but "resting state" implies no external stimulus, which contradicts the "rhythmic stimuli" requirement.

**Plan Adjustment**:
1. The implementation will attempt to load the `jonxuxu/HCP-flat` parquet file to see if it contains the necessary connectivity matrices.
2. The implementation will attempt to load `neurofusion/eeg-restingstate/events.csv` to check for PLV columns.
3. **If these datasets do not contain the required variables** (Time-series/Correlation Matrix for HCP; PLV for Entrainment **with rhythmic stimulus metadata**), the pipeline **MUST** halt with a clear error: `Data Gap: Required variables (fMRI connectivity, Entrainment PLV from rhythmic stimuli) not found in verified datasets.`
4. **No Synthetic Scientific Results**: Synthetic data is **only** used in unit tests to verify the logic of the correlation and plotting code. It is **NOT** used to generate scientific results or claim hypothesis validation. If real data is missing, the study reports a "Data Gap" and halts.

## 2. Methodological Approach

### Network Topology Calculation
- **Input**: Correlation matrix (N x N) derived from fMRI time-series (or synthetic equivalent for unit tests).
- **Parcellation**:
 - Primary: Schaefer (100-1000 nodes).
 - Sensitivity: AAL (multiple nodes), Power (264 nodes).
- **Metric**:
 - **Clustering Coefficient ($C$)**: Average local clustering of the weighted graph.
 - **Characteristic Path Length ($L$)**: Average shortest path length.
- **Tool**: `networkx` (CPU-optimized).
- **Constraint**: For 200 nodes, $O(N^3)$ path length is trivial ($200^3 = 8,000,000$ ops), fitting within 6h/2-core.

### Statistical Analysis
- **Correlation**: Spearman's $\rho$ (non-parametric, robust to non-normality).
- **Multiple Comparisons**: Bonferroni correction for $N=2$ tests (Clustering, Path Length).
 - $p_{adj} = \min(p_{raw} \times 2, 1.0)$.
- **Collinearity**: Variance Inflation Factor (VIF) between $C$ and $L$.
 - If $VIF > 5$, flag "Collinearity Warning".
 - **Tautology Warning**: Acknowledge that $C$ and $L$ are mathematically coupled in many graph regimes. The analysis will report them as **descriptive topological properties** and **not** as independent predictors in a joint regression model, limiting the analysis to univariate correlations as per the spec.
- **Power**: If $N < 30$, flag "Power Warning: N < 30 (Exploratory)".

### Robustness (Sensitivity)
- Re-run with AAL and Power 264.
- Compare effect sizes (absolute difference in $r$).
- Visualize with bar chart.

### Data Validation Steps
1. **Check for Rhythmic Stimulus**: Verify that the entrainment dataset contains a `stimulus_type` or `rhythmic` flag, or that the PLV metric is explicitly derived from a rhythmic protocol. If only "resting-state" is found, halt with "Data Gap".
2. **Check for Connectivity**: Verify that the HCP dataset contains time-series or correlation matrices for the required regions.

## 3. Compute Feasibility

- **Memory**: 200x200 matrix $\approx$ 320KB. Even with 200 subjects, total RAM < 100MB.
- **CPU**: `networkx` calculations are fast. Python overhead is minimal.
- **Disk**: Parquet files for HCP (if available) are < 1GB. Processed CSVs are < 10MB.
- **Runtime**: < 30 minutes for full pipeline on 2 cores. If data is missing, the pipeline halts immediately (<5 mins).

## 4. Decision Rationale

- **Why No Synthetic Scientific Results?** The verified dataset list lacks the specific "Entrainment PLV" and "HCP S1200 Connectivity" variables required by the spec. Synthetic data cannot validate a hypothesis about real biological systems. The study must report a "Data Gap" if real data is unavailable.
- **Why Spearman?** Robust to outliers and non-normal distributions common in neuroscience metrics.
- **Why Bonferroni?** Spec requires it (US-2). Conservative but simple.
- **Why Tautology Warning?** Clustering Coefficient and Path Length are often mathematically coupled. Interpreting them as independent predictors could be tautological. The plan restricts interpretation to univariate correlations.

## 5. Data Gap Success Definition

To address the concern that SC-001 (scientific association) cannot be met if data is missing:
- **Pipeline Success**: Defined as the correct execution of the validation logic, detection of missing data, and halting with a structured error message and `data_gap_report.json`. This satisfies FR-007, FR-008, and SC-005.
- **Scientific Null**: The report will explicitly state that SC-001 is unmeasurable due to data absence. This is a valid scientific outcome (negative result due to data unavailability) and not a system failure.
- **Fallback Logic**: The pipeline will not attempt to use synthetic data to "fake" a result. Instead, it will document the gap and terminate, ensuring the integrity of the scientific process.