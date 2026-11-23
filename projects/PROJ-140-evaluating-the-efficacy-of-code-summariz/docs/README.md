# Evaluating the Efficacy of Code Summarization Techniques for Bug Localization

This repository contains the implementation of a research pipeline to evaluate the efficacy of code summarization techniques (LLM-generated vs. rule-based) for bug localization.

## Project Overview

This project implements a deterministic simulation for CI testing and supports a "Real Study" path for final research output. It adheres to strict reproducibility and data integrity principles.

## Key Features

- **Defects4J Integration**: Automatically downloads and processes the Defects4J v2.0 dataset.
- **Summary Generation**: Supports both simulated (CI) and real (GPU) LLM summary generation.
- **Statistical Analysis**: Implements McNemar's tests for accuracy and Linear Mixed-Effects (LME) models for speed analysis.
- **Reproducibility**: Generates a reproducible research package compliant with GitHub Actions free-tier constraints (≤6h runtime, ≤7GB RAM).

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd <repository-name>
 ```

2. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

3. **Set up environment variables** (optional):
 Create a `.env` file in the root directory for custom paths or seeds:
 ```bash
 cp.env.example.env
 # Edit.env as needed
 ```

## Data Management

### Defects4J Dataset Handling

This pipeline strictly adheres to the **"Fail Loud"** and **"Streaming"** principles for data handling:

1. **Fail Loud Behavior**:
 - The data loader in `code/download/download_defects4j.py` is designed to **fail immediately** if the Defects4J dataset cannot be downloaded from the HuggingFace Hub or the specified mirror.
 - **No Synthetic Fallback**: The system **will not** generate synthetic or placeholder data if the download fails. This ensures that all results are based on real, verifiable data.
 - If the download fails, the script will raise an explicit error, and the pipeline execution will halt.

2. **Streaming Processing Strategy**:
 - To handle the large size of the Defects4J dataset within the CI memory constraints (≤7GB RAM), the pipeline uses **streaming**.
 - The dataset is loaded using `datasets.load_dataset(..., streaming=True)`, which allows processing the data in chunks without loading the entire dataset into memory.
 - **Chunk Size**: The streaming logic processes the dataset in chunks determined by performance tuning. Statistics are accumulated online to avoid holding the full dataset in RAM.
 - **Rationale**: This strategy ensures that the pipeline can handle the full Defects4J dataset without exceeding memory limits, maintaining reproducibility and data integrity.

3. **Data Directory Structure**:
 - `data/raw/defects4j/`: Contains the downloaded Defects4J data and ground truth.
 - `data/summaries/`: Contains generated LLM and rule-based summaries.
 - `data/interaction_logs/`: Contains participant interaction logs (raw and anonymized).
 - `data/analysis_results/`: Contains statistical analysis results and reports.
 - `data/consent/`: Contains consent forms (excluded from VCS).

## Execution

### Running the Pipeline

The main entry point for the pipeline is `code/main.py`.

```bash
python code/main.py
```

This command will:
1. Run startup checks (including latency calibration).
2. Download and process the Defects4J dataset.
3. Generate summaries (simulated for CI, real for GPU).
4. Simulate participant interactions.
5. Run statistical analysis.
6. Generate reports.

### Running Specific Tasks

You can also run specific tasks independently:

- **Download Defects4J**:
 ```bash
 python code/download/download_defects4j.py
 ```

- **Generate Summaries (Simulation)**:
 ```bash
 python code/generation/generate_summaries_offline.py
 ```

- **Run Statistical Analysis**:
 ```bash
 python code/analysis/run_statistics.py
 ```

### Sensitivity Analysis

To run the sensitivity analysis sweep:

```bash
python code/analysis/run_sensitivity.py
```

This will generate `data/analysis_results/sensitivity_analysis.csv` and `data/analysis_results/sensitivity_plot.png`.

## Reproducibility

### CI Workflow

The project includes a GitHub Actions workflow (`.github/workflows/test_reproducibility.yml`) that:
- Installs dependencies.
- Runs the full pipeline.
- Asserts runtime ≤6h and memory ≤7GB.
- Verifies numerical tolerance by re-running the analysis with the same seed.

### Reproducibility Package

A reproducibility package can be generated using:

```bash
python code/utils/package_reproducibility.py
```

This creates `data/reproducibility_package_v1.0.tar.gz`, which includes:
- All scripts (`code/`).
- Analysis results (`data/analysis_results/results.csv`).
- Anonymized logs (`data/interaction_logs/anonymized_logs.csv`).
- Documentation (`docs/`).
- Dependencies (`requirements.txt`).
- Artifact hashes (`state/`).

**Excluded**: `data/consent/`, `data/raw/defects4j/`, and `data/interaction_logs/raw_logs.csv`.

## Testing

Run the test suite:

```bash
python -m pytest code/tests/ -v
```

Key test modules include:
- `test_statistics.py`: Tests for McNemar's test and LME models.
- `test_bootstrap_utils.py`: Tests for bootstrapping functions.
- `test_reproducibility.py`: Tests for numerical tolerance.
- `test_defects4j_download.py`: Tests for dataset download integrity.

## Configuration

- **Sensitivity Analysis Cutoffs**: Defined in `code/analysis/config.py`. Default: `[0.01, 0.05, 0.10]`.
- **Random Seeds**: Controlled via `.env` or command-line arguments for reproducibility.

## Security & Privacy

- **PII Scrubbing**: The logging utility includes a regex-based PII scrubber to mask sensitive information.
- **Consent Storage**: Consent forms are stored in `data/consent/` with restricted permissions (`chmod 600`) and excluded from VCS.
- **Raw Logs**: `data/interaction_logs/raw_logs.csv` is excluded from VCS via `.gitignore`.

## License

[Insert License Information]

## Contributors

 [Insert Contributor Information]

## Acknowledgments

 [Insert Acknowledgments]