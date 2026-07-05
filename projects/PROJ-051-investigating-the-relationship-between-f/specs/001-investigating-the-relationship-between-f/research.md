# Research: Fractal Dimension and Energy Dissipation in Turbulent Flows

## Research Question
Does the fractal dimension ($D_f$) of vorticity iso-surfaces in isotropic turbulence correlate with the local energy dissipation rate ($\epsilon$), and does this relationship exhibit Reynolds number scaling?

## Hypotheses
- **H1**: There is a significant positive correlation between $D_f$ and $\log(\epsilon)$ in spatial subdomains, **significantly exceeding** the correlation observed in a null model (Phase-Shifted DNS).
- **H2**: The correlation coefficient $r$ is robust across different vorticity thresholding methods (Normalized RMS vs. Absolute).
- **H3**: $D_f$ is asymptotically constant or weakly dependent on $Re_\lambda$ in the range [200, 600] (Requires verified multi-Re data).

## Dataset Strategy

**Constraint**: The plan MUST use ONLY the verified datasets listed in the project's verified block. If a dataset required by the spec (JHTDB) is not in the verified block, the plan must explicitly state the mismatch and propose a fallback or flag the gap.

**Verified Datasets Available**:
The provided "Verified datasets" block contains only:
1. `DNSMOS-TTS` (CSV) - Audio/MOS data
2. `serial2023` (Parquet) - Serial data
3. `sn` (Parquet) - Serial data
4. `finance-financialmodelingprep` (Parquet) - Stock news
5. `eumetsat-rss` (Zarr) - Satellite RSS
6. `WIFI_RSSI_Indoor_Positioning` (CSV) - WiFi RSSI

**Critical Gap Identification**:
The Feature Specification (FR-001) explicitly requires: *"System MUST download DNS velocity field data from the Johns Hopkins Turbulence Database (https://turbulence.pha.jhu.edu/) for isotropic turbulence at Re_λ = 200, 400, 600"*.
The "Verified datasets" block **does not contain** the JHTDB datasets or any verified DNS velocity field data (3D vector fields).

**Action Plan**:
1. **Primary Path**: The code will attempt to fetch from JHTDB. If the URL is unreachable or the dataset is not in the verified block, the system logs a critical warning.
2. **Fallback Strategy (Null Model)**: To satisfy the *mechanical* requirement of running on the CI without fabricating URLs, and to provide a scientifically valid baseline:
   - **Phase-Shifted DNS**: The implementation will use a **Phase-Shifted DNS** generator. This method takes a verified real DNS snapshot (if available locally or via a verified HuggingFace mirror of JHTDB) and applies random phase shifts in Fourier space. This destroys spatial coherence (vortex structures) while preserving the energy spectrum ($k^{-5/3}$) and one-point statistics.
   - **Usage**: This dataset is used **only** for:
     - Algorithm validation (US-1, US-2).
     - Null model comparison (to distinguish physical correlation from mathematical coupling).
     - **NOT** for testing H3 (Reynolds number scaling), as synthetic data cannot validate physical scaling laws.
3. **Real Data Requirement**: If no verified real DNS data is available, H3 is marked as **Unverified**. H1 and H2 are tested on real data (if available) and compared against the null model.

**Dataset Selection for Validation**:
- **Synthetic Menger Sponge**: For validating the box-counting algorithm (Ground truth $D_f \approx 2.73$).
- **Synthetic Taylor-Green Vortex**: For validating the dissipation calculation (Analytical $\epsilon$).
- **Phase-Shifted DNS**: For null model validation and algorithm robustness.

## Methodological Approach

### 1. Fractal Dimension Computation (US-1)
- **Algorithm**: Box-counting method.
  - Divide the 3D domain into boxes of size $\epsilon$.
  - Count boxes $N(\epsilon)$ containing vorticity magnitude $|\omega| > \text{threshold}$.
  - Fit $N(\epsilon) \propto \epsilon^{-D_f}$ via linear regression on $\log$-$\log$ plot.
- **Thresholding Methods (FR-009)**:
  1. **Normalized RMS**: Thresholds at $2\times, 3\times, 4\times$ global vorticity RMS.
  2. **Absolute**: Thresholds at fixed values (e.g., $|\omega| > 5, 10, 15$ s⁻¹).
- **Validation**: Test on Menger sponge (target $D_f \in [2.68, 2.78]$).

### 2. Energy Dissipation Rate (US-2)
- **Formula**: $\epsilon = 2\nu S_{ij}S_{ij}$ where $S_{ij} = \frac{1}{2}(\frac{\partial u_i}{\partial x_j} + \frac{\partial u_j}{\partial x_i})$.
- **Derivatives**: Central finite differences (2nd order).
- **Validation**: Test on Taylor-Green vortex (target relative error $\le 1\%$).

### 3. Correlation Analysis (US-3)
- **Sampling Strategy**:
  - **Independence**: Subdomains must be separated by a distance significantly larger than the integral length scale $\lambda$.
  - **Multi-Snapshot Pooling**: Since a A single snapshot of limited resolution cannot provide 100 independent samples. (requires domain > 1000$\lambda$), the pipeline extracts subdomains from **multiple independent time snapshots** from the JHTDB time-series.
  - **Sample Size**: Aggregate a substantial number ($n \ge \text{threshold}$) of subdomains across all available snapshots.
- **Statistical Method**:
  - **Block Bootstrapping**: Instead of i.i.d. bootstrapping, resample by **snapshot** or **cluster of subdomains** to account for spatial autocorrelation within a snapshot.
  - **Regression**: Linear regression of $D_f$ vs $\log(\epsilon)$.
  - **Inference**: Pearson $r$, p-value, Confidence interval via block-bootstrap (1000 iterations).
  - **Correction**: Bonferroni or Benjamini-Hochberg for multiple thresholds/Reynolds numbers.
- **Null Model Comparison**:
  - Compute correlation on **Phase-Shifted DNS** data.
  - **H1 Validation**: The correlation in real data is only considered significant if $r_{real} > r_{null}$ with $p < 0.05$. This decouples geometric thresholding from energetic magnitude.

### 4. Reynolds Number Scaling (US-4)
- **Procedure**: Repeat analysis for real DNS datasets at $Re_\lambda = 200, 400, 600$.
- **Fallback**: If real multi-Re data is unavailable, **H3 is marked as Unverified**. Do not use synthetic data for this test.
- **Scaling Law**: Fit $D_f \sim Re_\lambda^\alpha$.
- **Outcome**: Estimate $\alpha$ and 95% CI (if data available).

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: FR-006 requires FWE correction. We will apply Bonferroni correction for the thresholds (RMS) and (Absolute) across the Reynolds numbers (max tests).
- **Power Analysis**: Spec assumes $n=100$ provides [deferred] power for $|r| \ge 0.3$. We will verify this assumption in the code if possible, or explicitly state it as a design assumption.
- **Causal Inference**: The study is observational (DNS data). Claims will be framed as **associational**, not causal. No randomization strategy is applicable.
- **Collinearity & Mathematical Coupling**: $D_f$ and $\epsilon$ are derived from the same velocity field. The **Null Model (Phase-Shifted DNS)** is used to establish a baseline for spurious correlation. If the real correlation is not significantly higher than the null model, the hypothesis is rejected.
- **Measurement Validity**: The Phase-Shifted DNS generator preserves the energy spectrum but destroys vortex structures, making it a valid null model for testing the specific $D_f$-$\epsilon$ relationship.

## Compute Feasibility Plan

- **Memory Management**:
  - 512³ float64 = 2 GB.
  - Velocity (multiple components) + Gradients (multiple components) + Vorticity (single component) + Dissipation (single component) = substantial memory footprint (too large).
  - **Solution**: Process in chunks (e.g., $^3$ or $128^3$ blocks). Compute gradients and dissipation on the fly for each block, aggregate statistics, then discard.
  - **Peak Memory**: Target < 4 GB to stay within 6 GB limit.
- **Runtime**:
  - Box-counting is $O(N)$ in number of boxes. For 512³, this is heavy.
  - **Solution**: Use optimized numpy operations and avoid Python loops. Limit the number of box sizes to a small set for speed.
  - **Job Segmentation**: Split the pipeline into:
    1. Data Download/Generation (30 min)
    2. Gradient/Dissipation Computation (30 min)
    3. Fractal Dimension Calculation (30 min)
    4. Statistical Analysis (30 min)
 - Total: [deferred] (well within 6 hours).

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **JHTDB Data Unavailable** | High | Use Phase-Shifted DNS for validation/Null Model only; mark H3 as Unverified. Document gap. |
| **Memory Overflow** | High | Implement chunked processing; monitor RSS; use `numpy.memmap` if necessary. |
| **Box-Counting Slow** | Medium | Limit box sizes; use vectorized numpy; parallelize over subdomains (if threads allowed). |
| **Bootstrap Non-Convergence** | Medium | Ensure $n \ge 100$; use block-bootstrapping to account for spatial correlation. |
| **Mathematical Coupling** | High | Use Phase-Shifted DNS null model to distinguish physical correlation from artifact. |

## Decision Log

- **Data Source**: JHTDB (Targeted) with Phase-Shifted DNS (Verified Fallback/Null Model).
- **Algorithm**: Box-counting (CPU-tractable) instead of Minkowski-Bouligand or other complex methods.
- **Correction**: Bonferroni chosen for simplicity and strict control of FWE.
- **Sampling**: Multi-snapshot pooling to achieve $n \ge 100$ independent samples.
- **Null Model**: Phase-Shifted DNS used to decouple geometric and energetic coupling.