# Research: Quantifying the Impact of Network Structure on Heat Transport in Disordered Alloys

## 1. Problem Statement & Hypothesis

**Research Question**: To what extent do topological descriptors of defect networks (clustering coefficient, degree distribution moments, percolation threshold) in disordered alloys correlate with their thermal conductivity?

**Hypothesis**: Higher disorder (lower clustering, lower percolation threshold) in the defect network will be associated with reduced thermal conductivity due to increased phonon scattering at mismatched interfaces.

**Statistical Framework**:
- **Null Hypothesis ($H_0$)**: Correlation coefficient $\rho = 0$ between network metrics and thermal conductivity.
- **Alternative Hypothesis ($H_1$)**: $\rho \neq 0$.
- **Significance Level**: $\alpha = 0.05$, adjusted via Bonferroni correction for multiple comparisons (number of metrics tested).
- **Causal Interpretation**: Observational study. Claims will be restricted to associational relationships; causal claims require randomization not present in MD snapshots.

**Mode Distinction**:
- **Synthetic Validation Mode**: A **Simulation Study** designed to validate the pipeline's ability to recover a known effect size (r=0.6). Results are for methodological validation only.
- **Real Data Mode**: An **Observational Study** to test the physical hypothesis. (Deferred until data is available).

## 2. Dataset Strategy

### Verified Datasets
The following datasets were verified for availability. **Crucially, no verified open-access source exists for the specific MD snapshots of Cu-Ni/Au-Ag alloys with thermal conductivity metadata required by the spec.**

- **OpenKim**: NO verified source found (do NOT cite a URL for it).
- **Materials Cloud**: NO verified source found (do NOT cite a URL for it).
- **Alternative Open Data**:
  - `nemdo/nemdo-data` (CSV): Contains demand data, not atomic snapshots.
  - `wnkh/vlm-project-with-images...`: VLM images, not physics data.
  - `KisanVaani/agriculture-qa...`: Agriculture QA, irrelevant.
  - `nhagar/onlysports_dataset_urls`: Sports data, irrelevant.

### Dataset Variable Fit Analysis
The study requires:
1.  **Atomic Species** (String/Enum)
2.  **3D Coordinates** (Float3D)
3.  **Thermal Conductivity** (Float)
4.  **Alloy Type** (Cu-Ni, Au-Ag)

**Gap Analysis**:
- **Real Data**: No verified URL provides all four variables simultaneously for the specified alloy systems. The "Verified datasets" block confirms no open source exists for the required MD snapshots.
- **Consequence**: A plan relying on downloading real data from OpenKim/Materials Cloud would fail at the execution stage (CI runner cannot authenticate or find the specific files).
- **Resolution**: The project will utilize a **Synthetic Data Generator** that creates atomic configurations adhering to the physical constraints of Cu-Ni and Au-Ag alloys (lattice constants, atomic radii, species distribution). This generator will produce the required variables (species, coordinates, synthetic thermal conductivity based on a known physical model or random noise for validation) to test the pipeline's correctness.

### Synthetic Data Strategy

**Generator**: `code/ingest.py` will include a `SyntheticDataGenerator` class.

**Physics Model**:
1.  **Lattice**: Atoms placed on an FCC lattice with random species assignment based on alloy composition ratios (e.g., 50/50 for Cu-Ni).
2.  **Short-Range Order (SRO)**: To ensure physical realism (addressing concern `methodology-1f3d6f6a`), a Warren-Cowley SRO parameter ($\alpha$) is applied to bias species assignment. This creates realistic clustering/anti-clustering patterns found in real disordered alloys, rather than pure randomness.
3.  **Thermal Conductivity (Ground Truth)**: To avoid circularity (addressing concern `scientific_soundness-f1c96bb5`), thermal conductivity is assigned via a **linear model based on defect density** (a proxy for disorder) with added Gaussian noise:
    $$ TC = (10.0 - 5.0 \times \text{defect\_density}) + \mathcal{N}(0, \sigma_{noise}) $$
    This establishes a **known ground truth correlation** of approximately **r=0.6**. The pipeline's success is measured by its ability to recover this r-value from the derived topological metrics, validating the statistical machinery.

**Sample Size**: $N=50$ snapshots (sufficient for exploratory analysis; power analysis will be reported).

## 3. Methodology & Statistical Rigor

### 3.1 Graph Construction
- **Method**: Voronoi tessellation (`scipy.spatial.Voronoi`) to identify nearest neighbors.
- **Edge Definition**: Edge $(u, v)$ exists if $u$ and $v$ are Voronoi neighbors AND species$(u) \neq$ species$(v)$.
- **Validation**: Compare edge counts against theoretical expectations for random alloys.

### 3.2 Metric Extraction
- **Clustering Coefficient ($C$)**: Global average.
- **Degree Distribution**: Mean ($\mu_k$), Variance ($\sigma_k^2$).
- **Percolation Threshold ($p_c$)**: Calculated on the largest connected component (LCC). If LCC is undefined (no edges), report NaN.

### 3.3 Statistical Analysis
- **Correlation**: Pearson ($r$) and Spearman ($\rho$) coefficients.
- **Multiple Testing**: Bonferroni correction: $p_{corrected} = p_{raw} \times m$ (where $m$ = number of metrics).
- **Power Analysis Justification**: For N=50, the Minimum Detectable Effect Size (MDES) for Pearson correlation at $\alpha=0.05$ (two-tailed) with 80% power is **r ≈ 0.44**. Since the synthetic ground truth is **r=0.6**, the study is sufficiently powered to detect the hypothesized effect. If real data is obtained later, the power analysis will be re-evaluated against the actual N.
- **Robustness**: Sensitivity analysis sweeping $\alpha \in \{0.01, 0.05, 0.10\}$.
- **Synthetic Mode Validation**: In Synthetic Mode, statistical tests (Bonferroni, Power Analysis) are used to verify that the *machinery* functions correctly (i.e., the corrected p-value should be < 0.05 for the known r=0.6).

### 3.4 Compute Feasibility
- **CPU-First**: All operations (Voronoi, NetworkX, Scipy stats) are CPU-tractable.
- **Memory**: Synthetic datasets are small (< 1MB); no streaming required.
- **Time**: $N=50$ snapshots will complete in < 1 hour on 2 CPU cores.
- **GPU**: Not required. No transformer/diffusion models used.

## 4. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **No Real Data** | High | Switch to Synthetic Mode; clearly document as "Methodological Validation". |
| **Small Sample Size (N<30)** | Medium | Report power analysis; qualify conclusions as "exploratory". |
| **Numerical Instability** | Medium | Use robust statistical functions; handle NaN/Inf explicitly. |
| **Voronoi Edge Definition** | High | Validate against known lattice structures; unit tests for edge logic. |

## 5. Decision Rationale

**Why Synthetic Data?**
The "Verified datasets" block explicitly states no open source exists for the required MD snapshots. Attempting to download from OpenKim/Materials Cloud without credentials would fail. A synthetic generator is the only viable path to execute the pipeline and validate the methodology without fabricating data or violating the "no un-spec'd constraints" rule (by not inventing a fake URL).

**Why Bonferroni?**
FR-006 mandates correction for multiple hypotheses to prevent false positives in high-dimensional topological analysis.

**Why CPU-First?**
The method (graph theory, classical stats) is inherently CPU-efficient. No GPU acceleration is needed, ensuring compatibility with GitHub Actions free-tier.