# Evaluating the Effectiveness of LLMs for Detecting Code Smells

## Project Overview

This project evaluates the effectiveness of Large Language Models (LLMs) in detecting code smells compared to traditional static analysis tools. It implements a pipeline to:
1. Ingest a sampled subset of `codeparrot/github-code`
2. Compute structural metrics via `radon`
3. Generate baseline "smell labels" using Pylint
4. Compute semantic embeddings and generate "smell labels" via a CPU-quantized LLM
5. Perform comparative statistical analysis (McNemar's test, logistic regression, sensitivity analysis)

## Prerequisites

- Python 3.11+
- pip (Python package manager)
- System RAM ≥ 16GB (recommended for LLM inference)
- CPU with AVX support (for efficient `llama-cpp-python` inference)

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-271-evaluating-the-effectiveness-of-llms-for
 ```

2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Dependencies

The project requires the following Python packages (listed in `requirements.txt`):

- `datasets`: For streaming and sampling code from HuggingFace
- `pandas`: For data manipulation and analysis
- `radon`: For static code metric calculation (LOC, Cyclomatic Complexity, Nesting Depth)
- `pylint`: For static code smell detection
- `sentence-transformers`: For computing semantic embeddings
- `llama-cpp-python`: For running quantized LLMs on CPU
- `scikit-learn`: For logistic regression and statistical analysis
- `statsmodels`: For VIF calculation and statistical tests
- `numpy`: For numerical operations
- `psutil`: For system resource monitoring (RAM, CPU)

## Usage

### CLI Arguments

The main pipeline scripts support the following CLI arguments:

#### `code/data_pipeline.py`
```bash
python code/data_pipeline.py --sample-size 800 --seed 42 --output data/static_baseline.csv
```
- `--sample-size`: Number of functions to sample (default: 800)
- `--seed`: Random seed for reproducibility (default: 42)
- `--output`: Output path for the baseline CSV (default: `data/static_baseline.csv`)

#### `code/semantic_analysis.py`
```bash
python code/semantic_analysis.py --input data/static_baseline.csv --output data/processed/semantic_results.json --batch-size 10
```
- `--input`: Path to the static baseline CSV
- `--output`: Output path for semantic results JSON
- `--batch-size`: Batch size for LLM inference (default: 10)

#### `code/statistical_analysis.py`
```bash
python code/statistical_analysis.py --baseline data/static_baseline.csv --semantic data/processed/semantic_results.json --results-dir results/
```
- `--baseline`: Path to the static baseline CSV
- `--semantic`: Path to the semantic results JSON
- `--results-dir`: Directory to save statistical analysis results

### Usage Examples

1. **Run the full data pipeline** (Phase 1):
 ```bash
 python code/data_pipeline.py
 ```
 This will:
 - Sample 800 functions from `codeparrot/github-code`
 - Compute structural metrics using `radon`
 - Run Pylint analysis and normalize smell labels
 - Save results to `data/static_baseline.csv`

2. **Run semantic analysis** (Phase 2):
 ```bash
 python code/semantic_analysis.py
 ```
 This will:
 - Load the static baseline CSV
 - Compute semantic embeddings using `sentence-transformers`
 - Run LLM inference using `CodeLlama-7B-Instruct-GGUF` (4-bit quantized)
 - Save embeddings and LLM labels to `data/processed/semantic_results.json`

3. **Run statistical analysis** (Phase 3):
 ```bash
 python code/statistical_analysis.py
 ```
 This will:
 - Merge static and semantic datasets
 - Perform McNemar's test for each smell category
 - Calculate VIF and fit logistic regression
 - Run sensitivity analysis
 - Generate reports in the `results/` directory

4. **Run validation scripts**:
 ```bash
 # Validate the pipeline output
 python code/run_pipeline_validation.py

 # Run quickstart validation
 python code/run_quickstart_validation.py

 # Run dry-run with mock data
 python code/runtime_validator.py --dry-run
 ```

## Project Structure

```
PROJ-271-evaluating-the-effectiveness-of-llms-for/
├── code/ # Source code
│ ├── config.py # Configuration and paths
│ ├── data_pipeline.py # Data ingestion and static analysis
│ ├── semantic_analysis.py # Semantic embeddings and LLM inference
│ ├── statistical_analysis.py # Statistical analysis and reporting
│ ├── monitoring.py # Resource monitoring (RAM, CPU)
│ ├── helpers.py # Utility functions
│ ├── linting_config.py # Linting and formatting configuration
│ └──... # Other helper scripts
├── data/ # Data files
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Processed data (e.g., semantic_results.json)
│ └── static_baseline.csv # Static analysis baseline
├── results/ # Analysis results and reports
│ ├── resource_metrics.json # Resource usage metrics
│ ├── statistical_significance.json
│ ├── logistic_regression.json
│ ├── sensitivity_metrics.json
│ └── sensitivity_report.md
├── contracts/ # Contract definitions
│ ├── smell_mapping.json # Pylint code to smell name mapping
│ └── llm_prompt.txt # Standardized LLM prompt
├── tests/ # Test suites
│ ├── unit/ # Unit tests
│ └── contract/ # Contract tests
├── requirements.txt # Python dependencies
├── README.md # This file
└── quickstart.md # Step-by-step setup and run instructions
```

## Output Artifacts

After running the full pipeline, the following artifacts will be generated:

- `data/static_baseline.csv`: Static analysis baseline with structural metrics and smell labels
- `data/processed/semantic_results.json`: Semantic embeddings and LLM-generated smell labels
- `results/resource_metrics.json`: Resource usage metrics (RAM, CPU, inference time)
- `results/statistical_significance.json`: McNemar's test p-values
- `results/logistic_regression.json`: Logistic regression coefficients and VIF scores
- `results/sensitivity_metrics.json`: Sensitivity analysis results
- `results/sensitivity_report.md`: Human-readable sensitivity report

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## Support

For issues and questions, please open an issue on the GitHub repository.
