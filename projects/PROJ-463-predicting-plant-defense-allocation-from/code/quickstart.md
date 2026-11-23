# Quickstart Guide

## Prerequisites

Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
conda install -c bioconda -c conda-forge -y fastp hisat2 subread r-sva r-normqpcr r-phylolm r-ape
```

## Running the Pipeline

### Synthetic Mode (Validation)

This mode generates synthetic data to validate the pipeline structure without requiring real biological data.

1. **Generate Synthetic Data**:
 ```bash
 python code/scripts/run_synthetic_generator.py
 ```
 This creates:
 - `data/raw/SYNTH_TPM_matrix.csv` (synthetic TPM matrix)
 - `data/manifests/synthetic_manifest.json` (manifest)
 - `data/processed/metadata_verification_report.json` (verification report)

2. **Verify Metadata**:
 ```bash
 python code/scripts/run_verify_metadata.py --mode synthetic
 ```

3. **Run QC Pipeline**:
 ```bash
 python code/scripts/run_qc.py
 ```

4. **Run Full Pipeline**:
 ```bash
 python code/scripts/run_synthetic_generator.py
 python code/scripts/run_verify_metadata.py --mode synthetic
 python code/scripts/run_qc.py
 python code/scripts/run_batch_correction.py
 python code/scripts/run_traits_try.py
 python code/scripts/run_traits_fallback.py
 python code/scripts/run_trait_gate.py
 python code/scripts/run_phylogeny_fetcher.py
 python code/scripts/run_reproducibility.py
 ```

### Real Mode

Requires valid NCBI/SRA accessions and network access.

1. **Fetch Real Data**:
 ```bash
 python code/scripts/run_download.py --mode real
 ```

2. **Verify Metadata**:
 ```bash
 python code/scripts/run_verify_metadata.py --mode real
 ```

3. **Run Full Pipeline**:
 ```bash
 python code/scripts/run_download.py --mode real
 python code/scripts/run_verify_metadata.py --mode real
 python code/scripts/run_qc.py
 python code/scripts/run_batch_correction.py
 python code/scripts/run_traits_try.py
 python code/scripts/run_traits_fallback.py
 python code/scripts/run_trait_gate.py
 python code/scripts/run_phylogeny_fetcher.py
 python code/scripts/run_reproducibility.py
 ```

## Output Files

The pipeline produces the following key artifacts:

- `data/raw/*.csv`: Raw/processed count matrices
- `data/processed/metadata_verification_report.json`: Metadata verification results
- `data/processed/post_qc_species_list.json`: Species passing QC
- `data/manifests/batch_correction_report.json`: Batch correction metrics
- `data/processed/aggregated_features.csv`: Aggregated feature matrix
- `data/processed/final_aggregated_traits.json`: Compiled trait data
- `data/manifests/reproducibility_report.json`: Reproducibility metrics
