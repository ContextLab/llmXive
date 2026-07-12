# Quickstart Guide - llmXive ALE Extension

## Prerequisites

- Python 3.9+
- pip package manager
- 8GB+ RAM (for model loading)
- 20GB+ disk space

## Installation

1. **Clone the repository**
 ```bash
 git clone <repository-url>
 cd PROJ-840-llmxive-follow-up-extending-agents-last
 ```

2. **Create virtual environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**
 ```bash
 pip install -r requirements.txt
 ```

4. **Verify installation**
 ```bash
 python code/validate_quickstart.py
 ```

## Project Structure

```
.
├── code/
│ ├── analysis/ # Statistical analysis (T026-T029)
│ ├── classification/ # Failure classification (T010-T016)
│ ├── data/ # Data generation (T015)
│ ├── intervention/ # Context checkpointing (T019-T023)
│ ├── utils/ # Utilities (T004-T005, T007)
│ └── validate_quickstart.py # Validation script (T035)
├── data/
│ ├── raw/ # Raw generated data
│ └── processed/ # Processed results
├── docs/
│ ├── specs/ # Specification documents
│ └── quickstart.md # This file
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── requirements.txt # Python dependencies
├── pyproject.toml # Project configuration
└── README.md # Project overview
```

## Running the Pipeline

### Step 1: Generate Synthetic Data (T015)

```bash
python code/data/generator.py --output data/raw/golden_subset.json --n-traces 10
```

### Step 2: Classify Failures (T010-T016)

```bash
python code/classification/parser.py --input data/raw/golden_subset.json
python code/classification/heuristics.py --input data/raw/golden_subset.json
python code/classification/state_validator.py --input data/raw/golden_subset.json
python code/classification/semantic_classifier.py --input data/raw/golden_subset.json
```

### Step 3: Run Intervention (T019-T023)

```bash
python code/intervention/runner.py --baseline --output data/processed/baseline_results.json
python code/intervention/runner.py --intervention --output data/processed/intervention_results.json
```

### Step 4: Statistical Analysis (T026-T029)

```bash
python code/analysis/stats.py --baseline data/processed/baseline_results.json \
 --intervention data/processed/intervention_results.json
python code/analysis/sensitivity.py --n-values 1,3,5
python code/analysis/report_generator.py --output docs/report.md
```

## Validation

Run the quickstart validation to ensure everything is working:

```bash
python code/validate_quickstart.py
```

This script will:
1. Verify directory structure
2. Check requirements.txt
3. Validate pyproject.toml configuration
4. Test seed utilities
5. Test configuration loading
6. Verify module imports
7. Test data generation flow

## Troubleshooting

### Common Issues

- **Import errors**: Ensure you're in the project root and virtual environment is activated
- **Model loading failures**: Verify model path in `code/utils/config_schema.yaml`
- **Memory errors**: Reduce batch size or use smaller model quantization

### Getting Help

- Check `docs/specs/001-llmxive-ale-extension/plan.md` for detailed architecture
- Review task descriptions in `tasks.md`
- Run tests: `pytest tests/`
