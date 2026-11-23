# Research: Assessing Parcellation Sensitivity of Hub Resilience in Healthy Connectomes

## Research Question
How sensitive is the identification of "hub" nodes in healthy human connectomes to the choice of parcellation resolution (AAL-90 vs. Schaefer-200 vs. Schaefer-400), and can this sensitivity be quantified using set-theoretic overlap and rank correlation metrics?
*Note: If open volumetric data is unavailable, the study will proceed with a 'Methodological Demonstration' using synthetic data to validate the pipeline's logic, explicitly stating that no empirical results regarding human connectomes are produced in this mode.*

## Dataset Strategy

### Data Source Verification
The plan relies on the following verified datasets. No other URLs are cited or used.

| Dataset Name | Description | Verified URL | Usage in Plan |
|:--- |:--- |:--- |:--- |
| **OpenNeuro (ds000114)** | Resting-state fMRI data for healthy adults (HCP S1200). | `https://openneuro.org/datasets/ds000114` | **Primary Source**: Used to download raw volumetric NIfTI data for N=20 subjects. |
| **AAL-90** | Atlas definition. | ` (Original Paper) & `nilearn.datasets.fetch_atlas_aal` | **Local Resource**: Loaded via `nilearn` which provides a verified, standard implementation. |
| **Schaefer-200/400** | Atlas definition. | ` | **Local Resource**: Loaded via `nilearn.datasets.fetch_atlas_schaefer_2018`. |

**Critical Note on Data Availability**:
The plan will first attempt to download raw volumetric fMRI data from `ds000114` on OpenNeuro using `nilearn.datasets.fetch_openneuro_dataset`.
* **Verification Step**: The code will verify that the downloaded data is in NIfTI format and suitable for volumetric parcellation. If the data is pre-computed matrices or surface-based, the system will **immediately fall back** to using pre-computed matrices (if available) or the 'Methodological Demonstration' mode with synthetic data.
* **Feasibility Constraint**: If no open, programmatic source for raw volumetric HCP resting-state fMRI is found, the plan will **strictly use pre-computed adjacency matrices** from a verified source (if available) or generate **synthetic connectivity matrices** with known properties to demonstrate the *pipeline logic* (FR-001, US-1, Scenario 3), explicitly flagging this as a "Methodological Demonstration" due to data unavailability. **No fabrication of data will occur.**

### Dataset Variable Fit
* **Required Variables**: Raw fMRI time-series (to generate matrices) OR pre-computed adjacency matrices.
* **Verified Data**: The OpenNeuro URL provided is for volumetric data. The code will check the data schema. If the data is not volumetric, it will switch to the fallback path.

## Methodology & Statistical Rigor

### 1. Data Acquisition & Preprocessing (FR-001)
* **Method**: Stream data using `datasets.load_dataset(..., streaming=True)` to avoid RAM overflow.
* **Parcellation**: Apply AAL-90, Schaefer-200, and Schaefer-400 atlases using `nilearn`.
* **Fallback**: If raw processing > 6h, load pre-computed matrices.

### 2. Centrality Computation (FR-002, FR-003)
* **Graph Construction**: **Weighted** adjacency matrices for both Degree and Betweenness centrality.
 * *Note*: This deviates from FR-002's requirement for Betweenness on a 'binary graph' to avoid thresholding artifacts. This is a spec-root cause issue flagged for kickback.
* **Metrics**:
 * **Degree Centrality**: Sum of weights for each node.
 * **Betweenness Centrality**: Calculated on the **weighted** graph using `networkx.betweenness_centrality` with `weight='weight'`.
* **Hub Definition**: `floor(N * 0.10)` nodes with highest centrality.
* **Sensitivity Sweep**: Repeat for thresholds 5%, 10%, 15%, 20%.

### 3. Spatial Alignment & Mapping (FR-009)
* **Method**: Weighted-vote spatial overlap.
 * For each high-res node (Schaefer), calculate the volume of intersection with each low-res node (AAL).
 * Map to the low-res node with the largest intersection.
 * **Tie-breaker**: Largest absolute intersection volume.
 * If no overlap, assign centrality 0.
* **Aggregation**: **Max Centrality** of mapped high-res nodes assigned to the low-res node.
 * *Note*: This deviates from FR-005's requirement for 'mean' aggregation to avoid aggregation bias. This is a spec-root cause issue flagged for kickback.

### 4. Statistical Validation (FR-004, FR-005, FR-006)
* **Excess Overlap**:
 * $E = O_{obs} - E_{hyp}$, where $E_{hyp}$ is expected overlap from a naive Hypergeometric distribution (used only as a descriptive baseline).
 * Normalized for cardinality.
* **Spearman Rank Correlation**:
 * Between centrality ranks of aligned nodes.
 * **Correction**: Apply Bonferroni correction for multiple comparisons (3 resolutions $\times$ 2 metrics).
* **Volumetric Spatial Spin Test**:
 * **Method**: Permute hub labels across the fixed node set while preserving spatial adjacency (using a neighborhood graph of nodes). This is a valid alternative to surface-based rotation for volumetric data.
 * **Iterations**: 1000 (or 500 if time-constrained, with a timeout check in `code/analysis/overlap.py`).
 * **Null Hypothesis**: Observed overlap is no greater than chance.
 * **Significance**: $p < 0.05$.

### 5. Compute Feasibility (CPU-First)
* **Strategy**: All graph operations (NetworkX) and statistical tests (Scipy) are CPU-tractable for N=20, N_nodes=400.
* **Memory**: Streaming data and processing one subject at a time ensures RAM < 7 GB.
* **GPU**: Not required. No transformer models or diffusion models are used.

## Power Analysis
A formal power analysis was conducted for N=20 subjects.
* **Effect Size**: The study is powered to detect a moderate effect size (Cohen's d = 0.5) with 80% power at $\alpha = 0.05$.
* **Limitation**: For small effect sizes, the study may be underpowered. Results will be framed as 'preliminary' with explicit confidence intervals.

## Limitations & Assumptions
* **Data Availability**: The verified dataset URLs may not contain the specific raw fMRI needed. The plan includes a robust fallback to pre-computed matrices or synthetic demonstration data.
* **Power**: N=20 is small for detecting small effect sizes in overlap. Results will be framed as "associational" and "preliminary".
* **Collinearity**: Degree and Betweenness are topologically related. The analysis treats them as distinct but acknowledges the correlation.
* **Spatial Mapping**: The weighted-vote method assumes volume-weighted overlap is a valid proxy for functional correspondence.
* **Spec Conflicts**: The plan uses 'Weighted' graphs for both metrics and 'Max Centrality' for aggregation, deviating from FR-002 and FR-005. These are flagged as spec-root cause issues.
