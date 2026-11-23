# PROJ-416: Investigating the Relationship Between Brain Network Dynamics and VR Therapy Response

This project implements an automated science pipeline to analyze the relationship between functional brain network metrics (modularity, efficiency) and clinical outcomes in Virtual Reality (VR) therapy for anxiety.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the full pipeline (N=10 subset for CI)
python code/main.py --stage download
python code/main.py --stage preprocess
python code/main.py --stage compute
python code/main.py --stage analyze
python code/main.py --stage report
```

See `docs/quickstart.md` for detailed instructions and troubleshooting.

## Project Structure

- `code/`: Source code for the pipeline
 - `data/`: Download, validation, and preprocessing scripts
 - `analysis/`: Network metric computation and statistical analysis
 - `utils/`: Logging and configuration utilities
- `data/`: Input and output data
 - `raw/`: Original downloaded datasets
 - `processed/`: Preprocessed NIfTI files
 - `metrics/`: QC metrics, network metrics, and statistical results
- `reports/`: Final analysis reports and visualizations
- `tests/`: Unit and integration tests
- `docs/`: Documentation

## Known Limitations

This section documents critical methodological constraints and known limitations of the analysis pipeline, as mandated by the project specification (SC-004, FR-008).

### 1. Power Analysis and "Underpowered" Warning (SC-004)

The pipeline performs a formal power analysis using `statsmodels.stats.power.FTestPower` with a fixed effect size of `f2=0.15` (Cohen's medium).
- **HALT Condition**: If the number of included subjects (N) is less than 5, the pipeline halts immediately with the error: `"Insufficient Power: N < 5"`.
- **Underpowered Warning**: If 5 ≤ N < `min_N_required` (calculated for 80% power at α=0.05), the pipeline proceeds but flags the results as **"Exploratory Mode"**. In this mode:
 - Effect sizes are reported.
 - **No p-value claims** are made for hypothesis testing.
 - The report explicitly states: `"WARNING: Underpowered for hypothesis testing (Power < 0.8)"`.
- Users should interpret findings from small samples (N < 20) with caution, acknowledging the reduced statistical power.

### 2. Associational Framing Constraint (FR-008, SC-005)

The pipeline strictly adheres to an associational framing unless the dataset is explicitly randomized.
- **Logic**: The final report checks `metadata.study_design` (string 'randomized') and `metadata.randomized` (boolean true).
- **Default Behavior**: If neither field exists, or if the values do not explicitly confirm randomization, the report **defaults to ASSOCIATIONAL framing**.
- **Output**: The `reports/results.md` will contain the explicit statement: `"Findings are framed as ASSOCIATIONAL"`.
- **Implication**: Causal claims (e.g., "VR therapy causes changes in network X") are **not** supported by this analysis unless the input metadata confirms a randomized controlled trial design.

### 3. Collinearity Handling (FR-005, FR-012)

- **Primary Path**: Univariate OLS regression is the primary analysis path.
- **Collinearity Threshold**: If Variance Inflation Factor (VIF) > 5, the pipeline attempts to compute Principal Components (PCA) for visualization only.
- **HALT Condition**: If PCA fails or fewer than 2 components explain >90% variance, the pipeline halts with `"Collinearity Unresolvable"`.
- **Exploratory Mode**: If PCA succeeds but <90% variance is explained, the pipeline switches to "Exploratory Mode" (visualization only, no primary model replacement).
- **Constraint**: PCA components are **never** used to replace the primary univariate predictors in the main ANCOVA model.

### 4. Data Availability and "Data Unavailable" Halt

The pipeline enforces a strict "Real Data Only" policy.
- **Multi-Source Aggregation**: The pipeline attempts to verify a longitudinal VR therapy dataset across OpenNeuro, HCP, and secondary repositories.
- **Halt Condition**: If no dataset meeting the criteria (pre/post fMRI + clinical scores + validated anxiety instrument) is found, the pipeline halts immediately with: `"Data Unavailable: No longitudinal dataset found"`.
- **No Synthetic Fallback**: The pipeline does **not** generate synthetic data or fall back to placeholder datasets. A failure to find real data is a terminal error.

### 5. Sensitivity Analysis Scope

The sensitivity analysis (T032, T044) sweeps:
- Motion thresholds: {2.0, 3.0} mm
- P-values: {0.01, 0.05, 0.1}
- Outcome definitions: {Change Score, Residual, Raw Post}

Results are summarized in `reports/sensitivity_analysis.md`. Variations in significance counts and effect sizes across these thresholds should be interpreted as the stability of the findings.

## Dependencies

- Python >= 3.10
- See `requirements.txt` for the full list of dependencies (including `nilearn`, `networkx`, `bctpy`, `statsmodels`, `pandas`, `numpy`, `scikit-learn`).

## Contributing

See `docs/CONTRIBUTING.md` for guidelines on adding data sources, extending sensitivity analysis, and updating the anxiety instrument whitelist.

## License

[Project License]