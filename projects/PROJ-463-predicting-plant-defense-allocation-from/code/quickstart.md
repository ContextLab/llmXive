# Quickstart Guide

This guide outlines the steps to run the full pipeline for predicting plant defense allocation.

## Prerequisites

- Python 3.9+
- Conda environment with all dependencies installed (see `requirements.txt` and `environment.yml`)
- Access to NCBI GEO/SRA (for real data mode)
- TRY API Key (optional, for real data mode)

## Installation

1. Clone the repository.
2. Create and activate the conda environment:
 ```bash
 conda env create -f environment.yml
 conda activate plant-defense-pipeline
 ```
3. Install Python dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

The pipeline can be run in two modes: `synthetic` (for validation) and `real` (for actual analysis).

### Synthetic Mode (Validation)

This mode generates synthetic data to validate the pipeline structure and logic without requiring external data access.

```bash
python code/scripts/setup_data_dirs.py
python code/scripts/run_synthetic_generator.py
python code/scripts/run_verify_metadata.py
python code/scripts/run_qc.py
python code/scripts/run_batch_correction.py
python code/scripts/run_traits_try.py
python code/scripts/run_traits_fallback.py
python code/scripts/run_traits.py
python code/scripts/run_trait_gate.py
```

### Real Mode (Full Analysis)

This mode fetches real data from NCBI and performs the full analysis.

```bash
# Set TRY API Key if available
export TRY_API_KEY="your_api_key_here"

python code/scripts/setup_data_dirs.py
python code/scripts/run_download.py --mode real --accession_ids GSE12345,GSE67890
python code/scripts/run_verify_metadata.py
python code/scripts/run_qc.py
python code/scripts/run_batch_correction.py
python code/scripts/run_traits_try.py
python code/scripts/run_traits_fallback.py
python code/scripts/run_traits.py
python code/scripts/run_trait_gate.py
```

## Output

The pipeline produces several output files in the `data/` directory:

- `data/processed/metadata_verification_report.json`
- `data/processed/post_qc_species_list.json`
- `data/processed/trait_fallback_summary.json`
- `data/processed/final_aggregated_traits.json`
- `data/manifests/human_input_needed.flag` (if gate fails)

## Troubleshooting

- If the trait gate fails, check `data/manifests/human_input_needed.flag` for details.
- Ensure all system tools (fastp, hisat2, featureCounts) are installed and in the PATH.
- Verify that the NCBI E-utilities API is accessible for metadata retrieval.
