# Research: Predicting Plant Biomass from Publicly Available Hyperspectral Imagery

## Dataset Strategy

| Dataset | Verified Source | Load Method | Notes |
|---------|-----------------|-------------|-------|
| NEON (jsonl) | https://huggingface.co/datasets/EarthnDusk/NeonIsometric/resolve/main/Neon_Isometric.zip | `hf_hub_download` or direct URL | Contains spectral data and metadata; ground-truth biomass must be verified in metadata schema. |
| HyBiomass | **Attempt Download** | `datasets.load_dataset` (canonical source) | **Action**: Attempt to download from canonical source. If unavailable, log failure as a distinct error and proceed with NEON only. Findings are scoped to NEON. |
| LIDAR (structural) | NEON LiDAR (embedded in metadata) | `h5py` / `laspy` | Used for structural proxies (canopy height). **Constraint**: Must be physically independent of spectral data (not derived from spectral indices). |

**Dataset Fit & Variable Verification**:
- **Required Variables**: Spectral bands (hundreds), biomass labels (ground-truth), structural proxies (e.g., canopy height).
- **NEON Verification**: The NEON dataset (via `NeonIsometric`) contains hyperspectral reflectance. Ground-truth biomass is expected in metadata. **Validation Step**: Pipeline will fail fast if `biomass` field is missing or if it is a deterministic function of the spectral predictor.
- **HyBiomass Gap**: No verified URL found in initial search. The plan will attempt the download from the canonical source. If it fails, the ablation study for "atmospheric correction impact" on *HyBiomass* is infeasible. The study will proceed with NEON data only, explicitly noting this limitation.
- **Atmospheric Correction**: LEDAPS/FLAASH algorithms are not directly downloadable as datasets but as libraries. The plan assumes `pysptools` or `atmcorr` libraries are available in `requirements.txt`. **Verification**: A dependency check step will confirm installation feasibility on the CI runner.

## Methodological Rigor

### Statistical Plan
1.  **Multiple-Comparison Correction**: FR-008 mandates Bonferroni or FDR correction for ablation study hypotheses.
    -   *Method*: Apply Bonferroni correction to the set of p-values from ablation comparisons (e.g., corrected vs. uncorrected, with vs. without structural features).
    -   *Rationale*: Controls family-wise error rate when testing multiple hypotheses.
2.  **Sample Size / Power**:
    -   *Method*: Pre-analysis power estimation. Calculate the Minimum Detectable Effect Size (MDES) for R² delta based on the available N (determined after download).
    -   *Action*: If N is insufficient to detect a meaningful effect (e.g., power < 0.8 for expected delta), the plan will report the power limitation explicitly and interpret results as "exploratory" rather than definitive.
3.  **Causal Inference**:
    -   *Status*: **Observational**. The study is correlational.
    -   *Framing*: Claims will be framed as "predictive contribution" or "marginal utility" of features, **not** causal effects. The ablation study isolates *predictive signal*, not causal mechanism. Confounding variables (phenology, soil moisture) are acknowledged as uncontrolled limitations.
4.  **Measurement Validity**:
    -   *Biomass Labels*: Ground-truth values from NEON must be derived from field measurements or independent LiDAR allometric equations. **Constraint**: If biomass is calculated from the same spectral data used for prediction, the study is invalid (tautology).
    -   *Spectral Data*: NEON hyperspectral data is a standard remote sensing product.
    -   *Collinearity*: Spectral bands are highly correlated. The plan will use Random Forest (which handles collinearity) and TabPFN. **Mitigation**: Calculate Variance Inflation Factors (VIF) for structural vs. spectral features. If VIF > 5, the structural proxy will be orthogonalized or the combined effect reported without claiming independence.

### Computational Feasibility
-   **CPU-First**:
    -   **Data Loading**: Streaming (`datasets.load_dataset(..., streaming=True)`) or chunked loading to stay within 7GB RAM.
    -   **Models**: Random Forest (`scikit-learn`) is CPU-tractable. TabPFN (`torch` CPU) is attempted but may be slow; fallback to RF is mandated (FR-009).
    -   **Atmospheric Correction**: `pysptools` or `atmcorr` are CPU-based. **Verification**: Dependency check to ensure installation does not exceed a reasonable runtime threshold.
-   **GPU Escape Hatch**:
    -   **Status**: Not required for this plan. If TabPFN fails or is too slow on CPU, the fallback RF is used. No transformer fine-tuning is planned.
    -   **Rationale**: The spec prioritizes CPU feasibility. TabPFN is a small model but may still be heavy; the fallback ensures completion.

### Data Pipeline Design

1.  **Download**:
    -   Fetch NEON data from verified Hugging Face URL.
    -   **Attempt** HyBiomass download from canonical source; log failure if unavailable.
    -   Verify checksums (SHA-256).
2.  **Preprocessing**:
    -   Apply atmospheric correction (LEDAPS/FLAASH) to raw cubes.
    -   Validate reflectance range [0, 1].
    -   Log exclusion rate for failed scenes (cloud cover).
3.  **Label Extraction**:
    -   Extract biomass values from metadata.
    -   **Hard Stop**: If exclusion rate > 5%, halt execution and trigger 'Data Quality Alert'.
    -   Verify biomass provenance (not derived from spectral input).
4.  **Modeling**:
    -   Split data (5-fold CV).
    -   Train RF and TabPFN (if successful).
    -   Evaluate against null baseline (mean predictor) using **Nadeau & Bengio corrected t-test**.
5.  **Ablation & Sensitivity**:
    -   Run ablation (with/without correction, with/without structural features).
    -   Sweep feature importance thresholds across a range of low, moderate, and high sensitivity levels..
    -   Apply multiple-comparison correction.
6.  **Runtime Measurement**:
    -   Wrap entire pipeline in a timer.
    -   Log total runtime to `results/runtime_metrics.json`.
    -   Flag failure if > 6 hours.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| HyBiomass data unavailable | Log failure as distinct error; proceed with NEON only; scope findings to NEON. |
| Atmospheric correction fails | Log scene exclusion; proceed with remaining scenes. |
| TabPFN exceeds 6h CPU limit | Automatic fallback to Random Forest (FR-009). |
| Memory overflow (7GB) | Chunked loading, streaming, or subsampling. |
| Missing structural proxies | Proceed with available data; note limitation in analysis. |
| Tautological validation (biomass derived from spectra) | Fail fast if biomass provenance check fails. |
| Standard t-test on CV folds | Use Nadeau & Bengio corrected t-test. |
| High collinearity (VIF > 5) | Orthogonalize features or report combined effect. |