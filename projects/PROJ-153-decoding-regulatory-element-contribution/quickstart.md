# Quickstart Guide: Decoding Regulatory Element Contributions

This guide outlines the steps to run the full pipeline for analyzing yeast CREs.
Ensure all dependencies (Conda environment, R packages, Python libraries) are installed
as per `environment.yml` and `requirements.txt`.

## Prerequisites

1. **Conda Environment**: Activate the environment.
 ```bash
 conda activate yeast_analysis
 ```
2. **Data**: Ensure `manifest.yaml` is populated with valid (or placeholder) accessions.
 Run `python code/00_verify_manifest.py` to validate.

## Pipeline Execution

The pipeline is executed in phases. Below are the individual commands.
You can run them sequentially or use the orchestration script `run_pipeline.sh` (if available).

### Phase 1: Setup & Validation

1. **Verify Research Accessions**:
 ```bash
 python code/00_validate_research_accessions.py
 ```
2. **Verify Manifest**:
 ```bash
 python code/00_verify_manifest.py
 ```

### Phase 2: Data Processing

3. **Download Data**:
 ```bash
 bash code/01_download_data.sh
 ```
4. **Preprocess ChIP-seq**:
 ```bash
 bash code/02_preprocess_chipseq.sh
 ```
5. **Call Peaks**:
 ```bash
 bash code/03_call_peaks.sh
 ```
6. **Extract Top CREs & Intersections**:
 ```bash
 Rscript code/03b1_extract_top_cres.R
 Rscript code/03b2_compute_intersections.R
 Rscript code/03b3_calculate_overlap_stats.R
 ```
7. **Run LMM Sweeps**:
 ```bash
 Rscript code/03c1_run_sweep_lmm_0.01.R
 Rscript code/03c2_run_sweep_lmm_0.10.R
 Rscript code/03c3_run_sweep_lmm_0.05.R
 ```
8. **Extract Peak Signals**:
 ```bash
 Rscript code/03c_extract_peak_signals.R
 ```
9. **Merge & Annotate Peaks**:
 ```bash
 bash code/04_merge_annotate.sh
 ```
10. **Load Hi-C Data**:
 ```bash
 bash code/04b_load_hic.sh
 ```
11. **Define Null Regions & Compute Signal**:
 ```bash
 bash code/06a_define_null_regions.sh
 bash code/06b_compute_null_signal.sh
 ```
12. **Compute Delta Signal** (Critical for downstream):
 ```bash
 python code/05b_compute_delta_signal.py
 ```
13. **Validate eQTL Schema**:
 ```bash
 python code/01b_validate_eqtl_schema.py
 ```
14. **Stream eQTL Data**:
 ```bash
 python code/01_stream_eqtl.py
 ```

### Phase 3: User Story 1 - CRE Ranking

15. **Validate Motifs**:
 ```bash
 python code/05a1_validate_motif.py
 ```
16. **Validate Hi-C Contacts**:
 ```bash
 python code/05a2_validate_hic.py
 ```
17. **Check Collinearity (VIF)**:
 ```bash
 python code/05b_check_collinearity.py
 ```
18. **Compute Weights**:
 ```bash
 python code/05c_compute_weights.py
 ```
19. **Fit LMM**:
 ```bash
 Rscript code/06_fit_lmm.R
 ```
20. **Generate Reports**:
 ```bash
 Rscript code/10_generate_reports.R
 ```
21. **Add Disclaimer**:
 ```bash
 python code/10_add_disclaimer.py
 ```

### Phase 4: User Story 2 - Statistical Evidence

22. **Permutation Test**:
 ```bash
 Rscript code/07_permutation_test.R
 ```
23. **Bias Sensitivity Analysis**:
 ```bash
 Rscript code/08_sensitivity_analysis.R
 ```

### Phase 5: User Story 3 - Visualization

24. **Create BigWig Tracks**:
 ```bash
 bash code/11_create_bigwig.sh
 ```
25. **Summit Match Analysis**:
 ```bash
 Rscript code/09_summit_match.R
 ```
26. **Generate Visualization Summary** (T061):
 ```bash
 python code/08_visualize.py
 ```
27. **Final Report Generation**:
 ```bash
 Rscript code/10_generate_reports_with_r2.py
 ```

### Phase N: Polish

28. **Generate Manifest**:
 ```bash
 Rscript code/12_generate_manifest.R
 ```
29. **Final Integrity Check**:
 ```bash
 bash code/13_final_integrity_check.sh
 ```

## Troubleshooting

- **Missing Data Files**: Ensure `data/raw/` contains the downloaded files. Check `logs/pipeline.log` for download errors.
- **R Package Errors**: Re-install R packages via `install_packages.R` if missing.
- **Python Import Errors**: Ensure the Conda environment is active and `requirements.txt` is installed.

## Output Artifacts

- `results/CRE_ranked_heatshock.md`: Ranked list of significant CREs.
- `results/Statistical_summary.pdf`: Comprehensive statistical report.
- `results/visualization_summary.png`: Diagnostic plots for CRE quality.
- `tracks/`: BigWig files for genome browser visualization.