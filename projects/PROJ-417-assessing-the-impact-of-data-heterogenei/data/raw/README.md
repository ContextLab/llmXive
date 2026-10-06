# Raw Data Directory

This directory contains the base dataset used for simulation in the "Assessing the Impact of Data Heterogeneity on Meta-Analysis Results" project.

## Active Data Source

The project currently utilizes a **Synthetic Base Dataset** generated via `code/scripts/generate_synthetic_base.py` (Task T040b-gen). This fallback was activated because the primary real-data fetch (Task T040) could not be completed in this environment.

### Synthetic Base Details
- **File**: `cochrane_base_synthetic.csv`
- **Generation Script**: `code/scripts/generate_synthetic_base.py`
- **Parameters**:
 - Mean effect ($\mu$): 0.0
 - Standard deviation ($\sigma$): 1.0
 - Study count ($N_{studies}$): 20
 - Effect Size Metric: Log Odds Ratio
- **Citation**: "Jackson et al. (2010)" - Jackson, D., White, I. R., & Thompson, S. G. (2010). Extensions for meta-analysis of binary outcomes. *Statistics in Medicine*, 29(2), 188-200.
- **Status**: **ACTIVE**. This dataset is the verified source for all simulation runs.
- **Checksum**: See `state/checksums/synthetic_base.sha256` for integrity verification.

## Primary Data Source (Unfetched)

The project is designed to fetch real data from the Cochrane Meta-Analysis Data Repository if available.

- **Primary Source**: T040 - Fetch Real Data from Cochrane.
- **Target URL**: https://osf.io/9k2v6/ (Open Science Framework)
- **Target Accession ID**: osf.io/9k2v6
- **Target Citation**: Jackson, D., White, I. R., & Thompson, S. G. (2010). Extensions for meta-analysis of binary outcomes. *Statistics in Medicine*, 29(2), 188-200.
- **Status**: Unavailable for direct automated fetch in this environment. The pipeline automatically falls back to the synthetic base defined above.

## Files

- `cochrane_base.csv`: The primary dataset (if fetched).
 - **Columns**: `study_id`, `effect_size`, `variance`, `sample_size`
 - **Citation**: Jackson et al., 2010.
 - **Current Status**: Not present.

- `cochrane_base_synthetic.csv`: The active dataset for this run.
 - **Source**: Generated via `code/scripts/generate_synthetic_base.py` (T040b-gen).
 - **Columns**: `study_id`, `effect_size`, `variance`, `sample_size`
 - **Purpose**: Verified fallback to ensure pipeline execution and reproducibility when real data is unavailable.
 - **Citation**: Synthetic data generated for simulation purposes based on parameter ranges observed in Jackson et al., 2010.

## Verification & Traceability

1. **Data Availability**: The pipeline (`code/simulation/generator.py`) checks for `cochrane_base.csv` first. If missing, it loads `cochrane_base_synthetic.csv`.
2. **Parameter Consistency**: The synthetic parameters ($\mu=0.0, \sigma=1.0, N=20$) are explicitly defined in `research.md` and `code/config.yaml`.
3. **Integrity**: The SHA256 checksum of the active synthetic file is recorded in `state/artifact_hashes.yaml` and `state/checksums/synthetic_base.sha256`.
4. **Documentation**: This README, `research.md`, and `code/config.yaml` are kept in sync regarding the active data source.

**Current Status**: Synthetic base data (`cochrane_base_synthetic.csv`) is the active source.
**Traceability**: This fallback is documented in `research.md` and triggered by the controlled failure of T040, satisfying Constitution II requirements for data provenance.
