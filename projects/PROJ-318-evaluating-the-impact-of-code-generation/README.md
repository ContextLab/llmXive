# Evaluating the Impact of Code Generation Models on Code Documentation Completeness

This project investigates how well LLM-generated docstrings cover function parameters compared to human-written documentation. It extracts method signatures and docstrings from real Python repositories, generates docstrings using a quantized CodeGen model, and performs statistical analysis on parameter coverage.

## Features

- **Data Extraction**: Automatically clones top Python repositories and extracts method signatures and existing docstrings using AST parsing.
- **Docstring Generation**: Uses `Salesforce/codegen-350M-mono` with 4-bit quantization (with fallback logic) to generate docstrings for extracted methods.
- **Coverage Analysis**: Calculates parameter coverage scores by matching AST-defined parameters against parsed docstring parameters.
- **Statistical Testing**: Performs Wilcoxon signed-rank tests to determine statistical significance of coverage differences.
- **Reproducibility**: Enforces deterministic random seeds and strict memory limits to ensure reproducible results.

## Prerequisites

- Python 3.9+
- Git (for repository cloning)
- 8GB+ RAM (recommended for model loading and data processing)
- Internet connection (for fetching repositories and downloading models)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

 The project requires the following key dependencies:
 - `transformers==4.35.0`
 - `torch==2.1.0`
 - `bitsandbytes==0.41.0` (for 4-bit quantization)
 - `sentence-transformers==2.2.2`
 - `docstring_parser==0.16`
 - `scipy==1.11.0`

## Project Structure

```
.
├── code/ # Main implementation scripts
│ ├── extract.py # Repository data extraction
│ ├── generate.py # Docstring generation
│ ├── analyze.py # Coverage analysis and statistics
│ ├── aggregate.py # Data consolidation
│ ├── config.py # Configuration management
│ └── utils/ # Utility modules
│ ├── ast_parser.py # AST parsing utilities
│ ├── coverage.py # Coverage calculation
│ ├── model_loader.py # Model loading with quantization
│ └──...
├── data/ # Data storage
│ ├── raw/ # Raw extracted data
│ │ └── repos/ # Repository clones and extracted JSON
│ └── processed/ # Processed results and analysis outputs
├── tests/ # Unit and integration tests
├── state/ # State tracking and checksums
├── logs/ # Execution logs
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Usage

### 1. Setup Project Structure

Ensure all required directories exist:

```bash
python -m code.setup_structure
```

### 2. Extract Repository Data

Clone repositories and extract method signatures with human docstrings:

```bash
python -m code.extract
```

This will:
- Fetch a frozen list of top Python repositories (up to 20)
- Clone each repository to `data/raw/repos/`
- Extract method signatures and docstrings
- Output JSON files to `data/raw/repos/`
- Record checksums in `state/projects/PROJ-318-evaluating-the-impact-of-code-generation.yaml`

### 3. Generate Docstrings

Generate docstrings using the CodeGen model with memory constraints:

```bash
python -m code.generate
```

This will:
- Load the `Salesforce/codegen-350M-mono` model (4-bit quantization with fallback)
- Process extracted methods in batches
- Monitor memory usage (abort if >7GB RAM)
- Handle empty/whitespace generated docstrings
- Save intermediate results to `data/processed/generation_batch_*.json`
- Aggregate results to `data/processed/results.json`

### 4. Analyze Coverage

Calculate parameter coverage scores and perform statistical analysis:

```bash
python -m code.analyze
```

This will:
- Calculate parameter coverage scores for each method
- Compute semantic similarity as an auxiliary metric
- Perform Wilcoxon signed-rank test for statistical significance
- Generate a final report to `data/processed/final_report.json`

### 5. Run Full Pipeline

Execute the complete pipeline from extraction to analysis:

```bash
python -m code.quickstart
```

### 6. Run Tests

Run unit and integration tests:

```bash
pytest tests/
```

## Configuration

Configuration is managed through `code/config.py`. Key settings include:

- **Model paths**: Default to `Salesforce/codegen-350M-mono`
- **Random seeds**: Fixed for reproducibility (Principle I)
- **Memory limits**: 7GB RAM threshold with automatic abort
- **Quantization**: 4-bit with 8-bit and full-precision fallback (Principle VII)
- **Rate limits**: Retry logic for API calls

To customize settings, modify `code/config.py` or use environment variables.

## Output Files

- `data/raw/repos/*.json`: Extracted method signatures and human docstrings
- `data/processed/generation_batch_*.json`: Intermediate generation results
- `data/processed/results.json`: Consolidated generation results
- `data/processed/results_with_scores.json`: Results with coverage and similarity scores
- `data/processed/final_report.json`: Final statistical analysis report
- `state/projects/PROJ-318-evaluating-the-impact-of-code-generation.yaml`: Artifact checksums and state tracking

## Error Handling

The pipeline includes robust error handling:

- **Memory Limit Exceeded**: Automatically aborts if RAM usage exceeds 7GB
- **Model Loading Failures**: Attempts 4-bit → 8-bit → full precision fallback
- **Syntax Errors**: Skips malformed Python files during extraction
- **Empty Docstrings**: Flags and handles empty/whitespace generated docstrings

## Reproducibility

This project enforces reproducibility through:

- Fixed random seeds for all stochastic operations
- Frozen repository list (deterministic selection)
- SHA-256 checksums for all data artifacts
- Deterministic model generation with fixed temperature

## Contributing

1. Create a feature branch
2. Implement your changes
3. Run tests to ensure nothing is broken
4. Submit a pull request

## License

This project is licensed under the MIT License.