# PROJ-076: Assessing the Validity of Modified Newtonian Dynamics

This project implements a rigorous scientific pipeline to evaluate Modified Newtonian Dynamics (MOND) against the standard NFW dark matter halo model using the SPARC galaxy rotation curve dataset.

## Project Structure

- `code/`: Core implementation modules (download, preprocessing, fitting, statistics).
- `data/`:
 - `raw/`: Original SPARC data files (after download).
 - `processed/`: Filtered galaxy data (`filtered_galaxies.csv`).
- `results/`: Output artifacts including fit summaries, sensitivity analysis, and statistical verdicts.
- `tests/`: Unit, integration, and contract tests.
- `docs/`: Documentation, including the research paper and API references.

## Quick Start

### Prerequisites
- Python 3.9+
- `pip install -r requirements.txt`

### Execution Pipeline

1. **Data Acquisition**:
 ```bash
 python code/download.py
 python code/checksum_verification.py
 ```
 *Outputs*: `data/raw/`, `data/metadata.yaml`

2. **Preprocessing**:
 ```bash
 python code/preprocess.py
 ```
 *Outputs*: `data/processed/filtered_galaxies.csv`

3. **Model Fitting**:
 ```bash
 python code/fit.py
 python code/generate_fit_summary.py
 ```
 *Outputs*: `results/fit_summary.csv`

4. **Sensitivity Analysis**:
 ```bash
 python code/sensitivity.py
 python code/generate_sensitivity_summary.py
 ```
 *Outputs*: `results/sensitivity_data.csv`, `results/sensitivity_summary.txt`

5. **Statistical Verification**:
 ```bash
 python code/generate_residual_stats.py
 python code/generate_verdict.py
 ```
 *Outputs*: `results/residual_stats.csv`, `results/analysis_verdict.md`

## Documentation

- **Research Paper**: See `docs/research_paper.md` for the full scientific analysis, methodology, and results.
- **Data Model**: `contracts/dataset.schema.yaml`
- **Fit Results Schema**: `contracts/fit_results.schema.yaml`

## License
Open Source (MIT)
