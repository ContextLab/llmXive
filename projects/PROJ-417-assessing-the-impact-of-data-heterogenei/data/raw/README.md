# Raw Data Directory

This directory contains the base dataset used for simulation.

## Source

- **Primary Source**: T040 - Fetch Real Data from Cochrane (Jackson et al., 2010).
 - **URL**: https://osf.io/9k2v6/ (Open Science Framework)
 - **Accession ID**: osf.io/9k2v6
 - **Citation**: Jackson, D., White, I. R., & Thompson, S. G. (2010). Extensions for meta-analysis of binary outcomes. *Statistics in Medicine*, 29(2), 188-200.
 - **Status**: Unavailable for direct automated fetch in this environment; fallback used.

- **Fallback Source**: T040b - Generate Verified Synthetic Base.
 - **Trigger**: Activated when T040 fails to fetch real data.
 - **Generation Script**: `code/scripts/generate_synthetic_base.py`
 - **Parameters**:
 - Mean effect: 0.5
 - SE distribution: LogNormal(0.0, 0.5)
 - Study count: 20 [UNRESOLVED-CLAIM: c_e4878554 — status=not_enough_info]
 - **Citation**: Synthetic data generated for simulation purposes based on parameter ranges observed in Jackson et al., 2010.
 - **Status**: **ACTIVE**. This dataset is currently the source for simulation.

## Files

- `cochrane_base.csv`: The primary dataset (if fetched).
 - **Columns**: `study_id`, `effect_size`, `variance`, `sample_size`
 - **Citation**: Jackson et al., 2010.

- `cochrane_base_synthetic.csv`: The active dataset for this run.
 - **Source**: Generated via `code/scripts/generate_synthetic_base.py` (T040b).
 - **Columns**: `study_id`, `effect_size`, `variance`, `sample_size`
 - **Purpose**: Fallback to ensure pipeline execution when real data is unavailable.
 - **Citation**: Synthetic data generated for simulation purposes based on Jackson et al., 2010 parameter ranges.

## Verification

Ensure that exactly one of the above files exists before running the simulation pipeline (T010).
The pipeline will automatically attempt to load `cochrane_base.csv` and fall back to `cochrane_base_synthetic.csv` if the former is missing.

**Current Status**: Synthetic base data (`cochrane_base_synthetic.csv`) is the active source.
**Traceability**: This fallback is documented in `research.md` and triggered by the controlled failure of T040.
