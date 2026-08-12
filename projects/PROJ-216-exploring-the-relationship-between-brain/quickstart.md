# Quickstart Guide: Brain Network Dynamics and Fluid Intelligence Pipeline

This guide provides step-by-step instructions to run the entire analysis pipeline end-to-end, from data ingestion to final report generation.

**Prerequisites**:
- Python 3.11+
- FSL >= 6.0 and AFNI >= 21.0 installed and in PATH
- Internet connection (for downloading OpenNeuro data)
- ~14 GB disk space for N=10 subjects

## 1. Environment Setup

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Verify Environment
Check that all required tools are available:
```bash
python code/verify_env.py
```
*Expected output*: All tools (fsl, afni, fslmaths) found. Exit code 0.

### Verify Directory Structure
Ensure the project directory structure is correct:
```bash
python code/setup_directories.py
```
*Expected output*: Directories created and verified. `data/.verify_structure.log` contains 'OK' for all paths.

## 2. Data Ingestion (User Story 1)

### Download OpenNeuro Data
The pipeline will download resting-state fMRI data from OpenNeuro ds000224 (primary) or ds000230 (fallback). [UNRESOLVED-CLAIM: c_6b7a347c — status=not_enough_info] It validates for the presence of **Fluid Intelligence** scores.
```bash
python code/download.py
```
*Output*: `data/processed/valid_subjects.json` containing N subjects with valid Fluid Intelligence scores.
*Note*: The script enforces the N=10 limit defined in `specs/amendment-001-fluid-intelligence-n10.md`.

### Validate Fluid Intelligence
Ensure the downloaded data contains valid Fluid Intelligence scores:
```bash
python code/validate_fluid_intelligence.py
```
*Output*: Logs any missing scores. The pipeline halts if no valid scores are found.

## 3. Preprocessing (User Story 1)

### Preprocess Subjects
Run motion correction, spatial normalization, and bandpass filtering using FSL/AFNI:
```bash
python code/run_preprocessing.py
```
*Output*: Preprocessed NIfTI files in `data/processed/` and `data/processed/preprocessing_stats.json`.

### Motion Artifact Detection
Detect and exclude subjects with excessive motion (Translation > 3mm OR Rotation > 2mm):
```bash
python code/motion_detection.py
```
*Output*: `data/processed/motion_exclusion_log.csv` listing excluded subjects.

### Resource Monitoring
Track RAM usage during preprocessing:
```bash
python code/execute_resource_monitor.py
```
*Output*: `data/processed/resource_profile.json` with peak RAM and runtime metrics.

## 4. Graph Metric Computation (User Story 2)

### Acquire Schaefer Atlas
Download the 200-ROI Schaefer atlas:
```bash
python code/graph_metrics.py --download-atlas
```
*Output*: Atlas files in `data/external/`.

### Compute Graph Metrics
Generate connectivity matrices and calculate global efficiency, clustering coefficient, and modularity:
```bash
python code/graph_metrics.py
```
*Output*: `data/processed/graph_metrics.csv` with metrics for each subject.

### Validate Metrics
Check for numerical anomalies:
```bash
python code/validate_graph_metrics.py
```
*Output*: `data/processed/graph_metric_validation.log` listing any anomalies.

### Aggregate Results
Consolidate all graph metrics into a single CSV:
```bash
python code/aggregate_graph_metrics.py
```
*Output*: Updated `data/processed/graph_metrics.csv`.

## 5. Statistical Analysis (User Story 3)

### Verify Data Alignment
Ensure graph metrics and Fluid Intelligence scores are available for all subjects:
```bash
python code/stats.py --validate
```
*Output*: `data/processed/us3_validation.json` with counts of valid pairs.

### Correlation Analysis
Perform Pearson/Spearman correlation between graph metrics and Fluid Intelligence:
```bash
python code/stats.py
```
*Output*: `data/processed/correlation_results.csv` with correlation coefficients, p-values, and Bonferroni-corrected p-values.

### Effect Size Calculation
Calculate Cohen's d and 95% confidence intervals:
```bash
python code/calculate_effect_sizes.py
```
*Output*: Appended effect sizes to `data/processed/correlation_results.csv`.

### Generate Visualizations
Create scatter plots of metrics vs. Fluid Intelligence:
```bash
python code/generate_scatter_plots.py
```
*Output*: `reports/scatter_metric_vs_fluid.png`.

### Generate Summary Report
Compile all results into a final PDF report:
```bash
python code/generate_summary_report.py
```
*Output*: `reports/summary.pdf`.

## 6. Final Verification

### Check Resource Profile
Review the analysis resource usage:
```bash
python code/generate_analysis_resource_profile.py
```
*Output*: `data/processed/analysis_resource_profile.json`.

### Run Integration Tests (Optional)
Verify the full pipeline with automated tests:
```bash
pytest tests/integration/test_pipeline.py
```

## Troubleshooting

- **Missing Fluid Intelligence Data**: Ensure you are using the correct OpenNeuro dataset (ds000224). If the primary dataset fails, the pipeline will attempt to fetch the fallback (ds000230).
- **FSL/AFNI Not Found**: Verify installation and add to PATH. Run `python code/verify_env.py` for details.
- **Motion Exclusion**: If too many subjects are excluded due to motion, check the `data/processed/motion_exclusion_log.csv` for details.
- **RAM Issues**: If the process exceeds memory limits, reduce the number of subjects or increase system RAM.

## Governance Notes

- This pipeline adheres to `specs/amendment-001-fluid-intelligence-n10.md`, which mandates:
 - Use of **Fluid Intelligence** scores (not Musical Creativity).
 - **Bonferroni** correction for multiple comparisons (not FDR).
 - N=10 sample limit for CI feasibility.
- All data is sourced from real OpenNeuro datasets. [UNRESOLVED-CLAIM: c_9e8cba3e — status=not_enough_info] No synthetic data is used.