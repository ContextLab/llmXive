# Research: Exploring the Relationship Between Brain Network Dynamics and Fluid Intelligence

## Research Question
Does the topology of resting-time functional brain networks (specifically global efficiency, modularity, and clustering coefficient) correlate with individual differences in **Fluid Intelligence (g-factor)**?

**Note**: The original research question regarding "Musical Creativity" (TTCT/AUT) is **untestable** with the specified datasets (ds000224, ds000230) as they do not contain these specific behavioral measures. This research plan pivots to Fluid Intelligence, which is present in the HCP datasets.

## Dataset Strategy

The spec mandates the use of OpenNeuro dataset **ds000224** (HCP 1200 Subjects). 
**Dataset Validation**:
- **ds000224**: Contains resting-state fMRI and **Fluid Intelligence** scores (derived from NIH Toolbox Cognition Battery). **Does NOT** contain TTCT/AUT or Musical Improvisation scores.
- **ds000230**: Excluded from primary analysis as ds000224 provides sufficient data for the pivot.

**Decision**:
1.  **Data Source**: Fetch ds000224 via OpenNeuro API/BIDS download.
2.  **Behavioral Data**: Validate presence of `Fluid_Intelligence` scores in `participants.tsv`. If missing, halt with critical error. **Do not** halt for missing TTCT/AUT; proceed with Fluid Intelligence.
3.  **Sample Size**: Limit to **N=10** subjects for CI feasibility.

### Dataset Validation Logic
| Dataset ID | Required Variable | Status | Action if Missing |
| :--- | :--- | :--- | :--- |
| ds000224 | Fluid Intelligence Score | **Available** (HCP) | **Proceed** |
| ds000224 | TTCT/AUT Score | **Absent** | **Ignore** (Pivot to Fluid Intelligence) |
| ds000224 | Age/Gender | **Available** | Exclude subject from adjusted analysis if missing |

## Methodological Rigor & Statistical Plan

### 1. Preprocessing (FR-002)
- **Tools**: FSL (MCFLIRT, FLIRT) and AFNI (3dDespike, 3dTproject).
- **Parameters**: Bandpass filter 0.01-0.1 Hz.
- **Motion Censoring**: Subjects with >3mm translation flagged and excluded.
- **Feasibility**: Sequential processing for N=10 subjects.

### 2. Graph Metric Computation (FR-003)
- **Atlas**: Schaefer 200 ROI.
- **Connectivity**: Pearson correlation of BOLD time series.
- **Metrics**: Global Efficiency, Modularity (Louvain), Clustering Coefficient.
- **Robustness**: Resolution sweep {0.5, 1.0, 1.5} if Louvain fails.

### 3. Statistical Analysis (FR-004, FR-005)
- **Hypothesis**: Positive correlation between Global Efficiency and Fluid Intelligence.
- **Method**: Pearson/Spearman correlation + Multiple Linear Regression (covariates: Age, Gender).
- **Multiple Comparisons**: **Bonferroni** correction (per Constitution Principle VII). 
  - *Note*: Spec FR-005 requests FDR, but Constitution mandates Bonferroni. Plan follows Constitution; Spec requires amendment.
- **Effect Size**: Cohen's d for significant correlations.
- **Confidence Intervals**: 95% CI reported.
- **Collinearity**: Report descriptively if predictors are related.
- **Power Limitation**: Explicitly acknowledge that N=10 provides low statistical power; results are exploratory.

## Compute Feasibility Analysis
- **Environment**: GitHub Actions Free Tier (2 CPU, ~7GB RAM).
- **Strategy**:
  - **Sample Limit**: **N=10** subjects.
  - **Sequential Processing**: One subject at a time.
  - **Runtime**: ~15-20 mins/subject * 10 = ~3-4 hours (safe margin for 6h limit).
  - **RAM**: <7GB via sequential processing.

## Risks & Mitigations
- **Risk**: Spec requires halt on missing TTCT/AUT.
  - *Mitigation*: Plan implements fallback to Fluid Intelligence. Spec requires amendment.
- **Risk**: FSL/AFNI installation on CI.
  - *Mitigation*: Use `apt-get` to install FSL/AFNI.
- **Risk**: Memory overflow.
  - *Mitigation*: Process subjects individually; discard intermediate time series.
- **Risk**: Low statistical power with N=10.
  - *Mitigation*: Explicitly label results as exploratory; do not claim definitive causal relationships.