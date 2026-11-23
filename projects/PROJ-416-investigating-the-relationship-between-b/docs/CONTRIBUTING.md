# Contributing to PROJ-416: Investigating Brain Network Dynamics and VR Therapy Response

Thank you for your interest in contributing to this research pipeline. This document outlines the specific guidelines for extending the multi-source data aggregation, sensitivity analysis, and anxiety instrument whitelist, ensuring adherence to the project's strict data hygiene and methodological constraints.

## 1. Adding New Data Sources to Multi-Source Aggregation (FR-013)

The project enforces a "Dataset-Variable Fit" gate (T001a) that iterates through verified sources to find a longitudinal dataset with pre/post clinical scores and a validated anxiety instrument.

### Procedure
1. **Identify the Source**: Determine the new repository (e.g., OpenNeuro, HCP, a secondary repository) and the specific dataset ID.
2. **Verify Variables**: Ensure the dataset contains:
 - Resting-state fMRI (NIfTI format).
 - Paired `pre_treatment_score` and `post_treatment_score` in the metadata.
 - A validated anxiety instrument (see Section 3 for the whitelist).
3. **Update the Aggregation Logic**:
 - Open `code/data/download.py` or `code/data/validate.py` (depending on where the source list is defined, typically in a configuration or a hardcoded list in `code/data/download.py` as per T001a).
 - Add the new source to the `verified_sources` list or dictionary.
 - Ensure the source metadata includes the `dataset_id` and `source_name`.
4. **Update `data/verified_sources.json`**:
 - If the source is verified, add an entry to `data/verified_sources.json` with the schema:
 ```json
 {
 "source_name": "New Repository Name",
 "dataset_id": "dsXXXXX",
 "verified_date": "YYYY-MM-DD",
 "notes": "Contains longitudinal VR therapy data with GAD-7 scores.",
 "has_pre_post": true,
 "has_clinical_scores": true
 }
 ```
5. **Testing**:
 - Run the verification gate (T046) to ensure the new source is correctly identified and validated.
 - Ensure the pipeline does not halt with "Data Unavailable" if this source is the only valid one.

**Constraint**: The pipeline MUST halt with "Data Unavailable: No longitudinal dataset found" if no source in the list meets all criteria. Do not bypass this check.

## 2. Extending Sensitivity Analysis Parameters (T032, T044)

The sensitivity analysis (T032, T044) sweeps motion thresholds, p-values, and outcome definitions to satisfy SC-006.

### Procedure
1. **Locate the Analysis Script**: Open `code/analysis/stats.py`.
2. **Identify the Sweep Logic**: Find the `run_sensitivity_analysis` function.
3. **Add Parameters**:
 - **Motion Thresholds**: Add new values to the `motion_thresholds` list (e.g., `{2.0, 3.0, 4.0}`).
 - **P-values**: Add new values to the `p_values` list (e.g., `{0.01, 0.05, 0.1, 0.2}`).
 - **Outcome Definitions**: Add new outcome types to the `outcome_definitions` list (e.g., `{"Change Score", "Residual", "Raw Post", "Normalized Post"}`).
4. **Update Output Schema**:
 - Ensure `reports/sensitivity_analysis.md` is updated to include the new combinations.
 - The report must contain columns: `threshold_type`, `threshold_value`, `significant_count`, `effect_size`, `ci_lower`, `ci_upper`.
5. **Validation**:
 - Run the full pipeline to ensure the sensitivity analysis completes without errors.
 - Verify that the report accurately reflects the new parameter combinations.

**Constraint**: Do not reduce the scope of the sweep (e.g., do not remove outcome definitions) unless explicitly justified by a data limitation.

## 3. Updating the Anxiety Instrument Whitelist (T052)

The project strictly enforces the use of validated anxiety instruments (GAD-7, HAM-A, BAI).

### Procedure
1. **Locate the Validation Logic**: Open `code/data/validate.py`.
2. **Identify the Whitelist**: Find the `ANXIETY_INSTRUMENT_WHITELIST` constant or similar.
3. **Add New Instrument**:
 - Add the new instrument name (e.g., "STAI") to the whitelist.
 - **Crucial**: Ensure the instrument is a **validated** anxiety scale with citable documentation.
4. **Update Documentation**:
 - Update this `CONTRIBUTING.md` file to list the new instrument.
 - Update `reports/limitations.md` if the addition of a new instrument introduces any new methodological considerations.
5. **Testing**:
 - Run `tests/unit/test_validate_instrument.py` (T052) to ensure the new instrument is accepted.
 - Ensure the pipeline halts with a `FatalError` if an instrument *not* in the whitelist is encountered.

**Constraint**: Do not add unvalidated or "best guess" instruments. The pipeline MUST raise a `FatalError` for any instrument not in the whitelist.

## General Guidelines

- **No Synthetic Data**: Never fabricate data or use synthetic fallbacks. If a real data source is unavailable, the pipeline must fail loudly.
- **Real Results**: All statistical outputs must be derived from real measurements. Do not hard-code results or use random values.
- **Documentation**: Keep `docs/quickstart.md`, `README.md`, and this `CONTRIBUTING.md` up to date with any changes to the pipeline.
- **Testing**: Ensure all new features are covered by unit and integration tests (e.g., `tests/integration/test_halt_conditions.py`).

## Reporting Issues

If you encounter a `FatalError` or a pipeline halt, check the logs in `logs/` for the specific error message. Common issues include:
- Missing `data/verified_sources.json`.
- Missing required variables (pre/post scores).
- Invalid anxiety instrument.
- Insufficient power (N < 5).
- Collinearity unresolvable.

For further assistance, refer to the `docs/quickstart.md` troubleshooting section.