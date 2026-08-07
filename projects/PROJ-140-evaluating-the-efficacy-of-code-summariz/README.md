# Evaluating the Efficacy of Code Summarization Techniques for Bug Localization

This project implements a rigorous scientific study to evaluate how different code summarization techniques (LLM-generated vs. Rule-based) impact bug localization accuracy and speed.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Usage](#usage)
 - [1. Data Preparation](#1-data-preparation)
 - [2. Human Subject Study Data Collection](#2-human-subject-study-data-collection)
 - [3. Statistical Analysis](#3-statistical-analysis)
 - [4. Reproducibility Package Generation](#4-reproducibility-package-generation)
- [Configuration](#configuration)
- [Testing](#testing)
- [License](#license)

## Prerequisites

- **Python**: 3.9 or higher
- **Package Manager**: `pip` (or `pipenv`/`poetry` if preferred)
- **System Libraries**:
 - `libxml2-dev` (required for `srcML` if using rule-based extraction)
 - `build-essential` (for compiling certain dependencies)
- **Disk Space**: At least 20GB for Defects4J dataset and intermediate files.
- **RAM**: Minimum 7GB recommended for analysis scripts.

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd PROJ-140-evaluating-the-efficacy-of-code-summariz
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 The project requires several scientific computing and web framework libraries.
 ```bash
 pip install --upgrade pip
 pip install -r requirements.txt
 ```

 *Note: `requirements.txt` includes:*
 - `pandas`, `numpy`, `scipy`, `statsmodels` (for statistical analysis)
 - `python-dotenv` (for configuration)
 - `flask` or `fastapi` (for backend API, if applicable)
 - `transformers`, `torch` (optional, for real LLM generation in non-CI environments)
 - `pytest` (for testing)

4. **Set up environment variables**:
 Copy the example environment file and configure paths/seeds:
 ```bash
 cp.env.example.env
 # Edit.env to set:
 # - DATA_ROOT: Path to data directory
 # - SEED: Random seed for reproducibility
 # - LOG_LEVEL: Logging verbosity
 ```

## Project Structure

```
.
├── code/
│ ├── analysis/ # Statistical analysis scripts (McNemar, LME)
│ ├── data_prep/ # Defects4J download, summary generation
│ ├── utils/ # Logging, hashing, configuration, anonymization
│ ├── backend/ # API for participant interaction
│ └── tests/ # Unit and integration tests
├── data/
│ ├── defects4j/ # Downloaded Defects4J dataset
│ ├── summaries/ # Generated code summaries (LLM-Sim, Rule-based)
│ ├── interaction_logs/ # Raw and anonymized participant logs
│ ├── analysis_results/ # Statistical test results
│ └── consent/ # Secure storage for consent forms (excluded from git)
├── state/
│ └── projects/PROJ-140... # Project state and artifact hashes
├── contracts/ # API contracts
├── tests/ # Project-level tests
├──.env.example # Environment template
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Usage

### 1. Data Preparation

Before running the study, you must download the Defects4J dataset and generate summaries.

```bash
# Download Defects4J and extract stratified buggy methods
python code/data_prep/download_defects4j.py

# Generate deterministic LLM-Sim summaries (for CI) and Rule-based summaries
python code/data_prep/generate_summaries.py
```

*Optional: For non-CI environments with GPU, generate real LLM summaries:*
```bash
python code/data_prep/generate_summaries_real_llm.py
```

### 2. Human Subject Study Data Collection

Run the backend server to collect participant interaction data.

```bash
# Start the backend API
python code/backend/src/main.py
```

*Note: Ensure the frontend is configured to connect to this backend. The latency calibrator will run at startup to verify timestamp precision.*

### 3. Statistical Analysis

Once data collection is complete, run the statistical analysis pipeline.

```bash
# Anonymize logs (if not done automatically)
python code/utils/anonymize_logs.py

# Run full statistical analysis (McNemar, LME, Bootstrapping, Sensitivity)
python code/analysis/run_statistics.py
```

*Outputs will be written to `data/analysis_results/`.*

### 4. Reproducibility Package Generation

Generate the reproducibility package for OSF publication.

```bash
# Generate baseline results for CI verification
python code/utils/generate_baseline_results.py

# Create the reproducibility package
python code/utils/generate_reproducibility_package.py
```

The package `data/reproducibility_package_v1.0.tar.gz` will contain all necessary scripts and anonymized data.

## Configuration

Configuration is managed via `code/utils/config_manager.py` and the `.env` file. Key settings include:

- `DATA_ROOT`: Root directory for all data artifacts.
- `SEED`: Global random seed for reproducibility.
- `LATENCY_THRESHOLD_MS`: Maximum allowed timestamp precision (default: 100ms).
- `MAX_MEMORY_GB`: Memory limit for CI runners (default: 7GB).

## Testing

Run the full test suite to verify implementation correctness and resource constraints.

```bash
# Run all tests
pytest code/tests/ -v

# Run specific test suites
pytest code/tests/test_statistics.py -v
pytest code/tests/test_reproducibility.py -v
```

*Note: The CI workflow (`.github/workflows/test_reproducibility.yml`) automatically runs these tests with resource monitoring.*

## License

This project is licensed under the MIT License. See `LICENSE` for details.

## Contributing

Please read `CONTRIBUTING.md` for details on our code of conduct and the process for submitting pull requests.