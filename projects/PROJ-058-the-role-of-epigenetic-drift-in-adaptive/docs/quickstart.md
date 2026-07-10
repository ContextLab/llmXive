# Quickstart Guide: Epigenetic Drift in Adaptive Landscape Exploration

## Prerequisites

- Python 3.11+
- pip
- Access to a UNIX-like environment (Linux/macOS)

## Installation

1. Clone the repository and navigate to the project root:
 ```bash
 git clone <repository-url>
 cd PROJ-058-the-role-of-epigenetic-drift-in-adaptive
 ```

2. Create a virtual environment and activate it:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Directory Structure

The project follows this structure:
- `code/`: Source code modules (discovery, preprocess, analysis, viz)
- `data/`: Raw and processed data files
- `output/`: Results, figures, and logs
- `tests/`: Unit and contract tests
- `docs/`: Documentation

## Running the Pipeline

The main orchestrator is `code/main.py`. It executes the following steps in order:

1. **Data Discovery**: Checks for valid multi-generational datasets.
2. **Preprocessing**: Normalizes RNA-seq and methylation data using LOGO jackknife.
3. **Correlation Analysis**: Computes Spearman correlations stratified by environment.
4. **Timescale Alignment**: Validates drift vs. environmental fluctuation timescales.
5. **Sensitivity Analysis**: Sweeps generation thresholds (3, 4, 5).
6. **Final Report**: Merges all results into `output/final_report.json`.

Execute the pipeline:
```bash
python code/main.py
```

**Note**: The pipeline will halt if fewer than 3 valid datasets are found during the discovery phase (see `output/discovery_status.json`).

## Output Files

- `output/discovery_results.json`: List of valid accession IDs.
- `output/discovery_status.json`: Contains `halt_signal` if data is insufficient.
- `data/processed/variance_matrix.csv`: Unified variance metrics.
- `output/correlation_results.json`: Spearman's rho, p-values, and flags.
- `output/timescale_alignment.json`: Alignment status and validation flags.
- `output/final_report.json`: Consolidated results.

## Hypothesis and Timescale Alignment

This study investigates whether epigenetic drift acts as a mechanism for adaptive landscape exploration or merely as noise. A critical component of this investigation is the **Timescale Alignment** requirement (Phase 6).

The hypothesis posits that for epigenetic drift to be a viable mechanism for adaptation, the rate of drift must align with the frequency of environmental fluctuations. The pipeline explicitly calculates:
- **Drift Timescale**: Derived from the slope of variance vs. generation count.
- **Environmental Timescale**: Extracted from metadata keys (`fluctuation_timescale`, `fluctuation_period`, or `env_period`).

The analysis flags cases where these timescales are "Aligned" (within 10%), "Mismatched", or "Insufficient". **Crucially, the pipeline does not assert causality**; it strictly reports the alignment status as a validation metric.

## Testing

Run the test suite:
```bash
pytest tests/
```

Specific test modules:
- `tests/unit/test_discovery.py`: Mocked GEO/ENCODE queries.
- `tests/unit/test_preprocess.py`: LOGO split and variance logic.
- `tests/unit/test_analysis.py`: Correlation math and permutation tests.
- `tests/unit/test_timescale_align.py`: Alignment logic validation.
- `tests/contract/test_schema.py`: Final report schema validation.

## Troubleshooting

- **Pipeline Halts**: Check `output/discovery_status.json` for `halt_signal`. This indicates insufficient data (<3 valid datasets).
- **Memory Error**: The pipeline is optimized for <2GB RAM. If errors occur, reduce batch sizes in `code/config.py`.
- **Convergence Warning**: If the permutation test in `correlation.py` hits the hard cap, `output/correlation_results.json` will contain a `convergence_warning` flag.

## Data Sources

All data is sourced from real, publicly available repositories:
- **GEO (Gene Expression Omnibus)**: Accessed via `requests` for metadata and accession validation.
- **ENCODE**: Used for cross-validation of methylation datasets.

No synthetic data is used in the final analysis.
