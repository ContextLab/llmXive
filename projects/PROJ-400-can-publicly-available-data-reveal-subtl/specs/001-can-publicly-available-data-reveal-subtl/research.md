# Research: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

## Executive Summary

This research explores the feasibility of extracting T-violation constraints (D-coefficient) from archival beta decay data using a novel cross-modal fusion method. By combining momentum spectra and polarization asymmetry coefficients from the NNDC ENSDF database, we aim to derive upper bounds without new experiments. The approach relies on rigorous permutation testing to establish statistical significance.

## Dataset Strategy

The project relies **exclusively** on the NNDC ENSDF database for experimental data. The 2024 Particle Data Group (PDG) Review serves as the benchmark for validation.

**Note on Verified Datasets**: The user-provided "Verified datasets" block contains only LLM training traces (cybersecurity/coding) and **does not** contain beta decay data. Therefore, this project **must** use the NNDC ENSDF database directly. No HuggingFace dataset URL exists for the specific raw momentum/polarization data required. The plan adapts to fetch data programmatically from the NNDC web interface or available API endpoints, as no pre-packaged parquet/CSV exists for this specific physics domain.

### Data Sources

| Dataset | Description | Access Method | Verified URL / Source |
| :--- | :--- | :--- | :--- |
| **NNDC ENSDF** | Evaluated Nuclear Structure Data File. Contains raw/semi-raw beta decay spectra and asymmetry coefficients. | Web scraping / API (if available) | `https://www.nndc.bnl.gov/ensdf/` (Official Source) |
| **PDG Review 2024** | World average limits and single-experiment sensitivities for D-coefficients. | Manual extraction / Web scraping | `https://pdg.lbl.gov/2024/` (Official Source) |

**Feasibility Check**:
- **NNDC ENSDF**: Publicly accessible. Data format is stable (ASCII, XML, or downloadable text files).
- **PDG 2024**: Publicly accessible.
- **Constraint**: The "Verified datasets" block provided in the prompt **does not** list a beta decay dataset. This is a **critical deviation** from the prompt's instruction to use *only* listed URLs. However, since no such dataset exists in the provided list (which contains only coding traces), and the spec *requires* beta decay data, the only viable path is to fetch from the official NNDC source. **Fabricating a URL for a non-existent dataset is prohibited.** The plan explicitly acknowledges that the data must be fetched from the primary source (NNDC) rather than a pre-packaged HuggingFace dataset.

## Methodology

### 1. Data Retrieval & Validation (FR-001, FR-004)
- **Target Nuclei**: 6He, 19Ne.
- **Action**: Parse ENSDF entries for "Beta Decay" sub-sections.
- **Extraction**:
  - Momentum/Energy spectra (binned or event-level).
  - Polarization asymmetry coefficients ($A$, $B$, $D$).
- **Validation**:
  - Check for event-level granularity. If only binned aggregates exist without covariance info, flag as "invalid for fusion" (FR-004).
  - Align data by nuclear state and source experiment.

### 2. Cross-Modal Fusion (FR-002)
- **Theory**: The D-coefficient represents a T-odd correlation $\vec{\sigma} \cdot (\vec{p}_e \times \vec{p}_\nu)$.
- **Implementation**:
  - Treat momentum distribution $P(E)$ and polarization asymmetry $A(\theta)$ as independent random variables.
  - Compute the cross-modal covariance matrix: $\Sigma_{cross} = \text{Cov}(P, A)$.
  - Derive $D_{est}$ from the off-diagonal terms of the covariance matrix, normalized by experimental geometry factors.

### 3. Permutation Testing (FR-003, SC-002)
- **Null Hypothesis ($H_0$)**: No T-violation ($D=0$); momentum and polarization are uncorrelated.
- **Procedure**:
  1. Calculate observed covariance $C_{obs}$.
  2. Randomly shuffle polarization values relative to momentum bins $N=10,000$ times.
  3. Recalculate covariance $C_{perm}$ for each shuffle.
  4. Generate null distribution of $C_{perm}$.
  5. Calculate p-value: $p = \frac{\text{count}(C_{perm} \ge C_{obs}) + 1}{N + 1}$.
- **Confidence Interval**: Upper bound $|D| < D_{95}$ derived from the 95th percentile of the null distribution.

### 4. Sensitivity & Benchmarking (FR-005, FR-006)
- **Sensitivity Limit**: Standard error of the weighted mean of measurements for the specific nucleus.
- **Benchmarking**: Compare $|D| < D_{95}$ against 2024 PDG limits.
- **Output**: Flag if derived bound is looser than world average.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: If testing multiple nuclei, apply Bonferroni correction or false discovery rate (FDR) control.
- **Power Analysis**: Acknowledge that archival data is limited. If $N_{shuffles}$ is high but $N_{data}$ (bins) is low, power is limited. Explicitly state this limitation.
- **Causal Inference**: This is an observational study of archival data. Claims are strictly associational ($D_{est} \neq 0$ implies potential T-violation, but systematic errors must be ruled out).
- **Collinearity**: Momentum and polarization are physically distinct; no definition-based collinearity exists.
- **Measurement Validity**: ENSDF data is evaluated by experts; uncertainty estimates are assumed valid per PDG standards.

## Compute Feasibility

- **CPU-First**:
  - Data parsing: Minimal CPU.
  - Permutation test: 10,000 shuffles of ~100 bins = ~1M operations. Trivial for Python/NumPy on 2-core CPU.
  - Memory: < 100 MB.
- **GPU Not Required**: No deep learning or large matrix inversions. The "GPU escape hatch" is not needed for this specific methodology.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **No Raw Data Available** | High | If ENSDF only has pre-calculated D-coefficients, the project flags "fusion impossible" and reports the limitation (US-1, SC-005). |
| **Data Format Inconsistency** | Medium | Robust parsing with fallback to manual review; log all failures. |
| **PDG API Unavailable** | Low | PDG data is static; fallback to manual entry of known 2024 limits in a local JSON (checksummed). |
| **Fabrication Concern** | Critical | **Strictly** no synthetic data. If data is missing, the result is "No Result," not a simulated one. |

## Decision Rationale

- **Why NNDC ENSDF?** It is the only public repository containing the specific raw/semi-raw momentum and polarization data required. No HuggingFace dataset exists for this niche.
- **Why Permutation Testing?** Analytic assumptions (Gaussianity) may not hold for small, binned archival data. Permutation testing is distribution-free and robust.
- **Why CPU?** The statistical load is low; GPU acceleration adds unnecessary complexity and cost.
