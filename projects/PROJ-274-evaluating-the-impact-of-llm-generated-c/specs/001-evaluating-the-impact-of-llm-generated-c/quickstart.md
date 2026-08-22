# Quickstart: Evaluating the Impact of LLM-Generated Code Documentation on Developer Onboarding

## Prerequisites

* Python 3.11+
* `git` installed and configured.
* Access to a HuggingFace token (for `phi` model fallback).
* (Optional) API key for primary LLM provider.

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd evaluating-llm-docs-impact
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

4. **Configure environment variables**:
 Create a `.env` file in the root directory:
 ```bash
 export HF_TOKEN="your_huggingface_token"
 export LLM_API_KEY="your_api_key_if_applicable"
 ```

## Running the Pipeline

### Step 1: Repository Selection & Metric Calculation
Calculate LOC and Cyclomatic Complexity for candidate repositories.
```bash
python code/scripts/repo_metrics.py --repos "repo1,repo2,repo3" --output data/raw/repo_metrics.json
```

### Step 2: Documentation Generation
Generate documentation for the selected repositories (with fallback).
```bash
python code/scripts/generate_docs.py --config config/generation_config.yaml --output data/raw/generated_docs/
```

### Step 3: Experiment Execution (Simulated)
Run a mock experiment with simulated participants to verify logging.
```bash
python code/scripts/run_experiment.py --mode mock --participants 3 --output data/raw/participant_logs.json
```
*Note: For real participants, run with `--mode real` and follow the moderator protocol.*

### Step 4: Data Anonymization
Strip PII from logs.
```bash
python code/scripts/anonymize.py --input data/raw/participant_logs.json --output data/processed/anonymized_logs.json
```

### Step 5: Statistical Analysis
Run the robust statistical analysis with resource monitoring.
```bash
python code/scripts/analyze.py --input data/processed/anonymized_logs.json --output data/processed/results.json
```
*This command will automatically verify CPU time and memory usage against FR-007 constraints via the integrated monitor.py context manager.*

### Step 6: Citation Validation
Verify all citations in the research documentation.
```bash
python code/scripts/validate_refs.py --doc specs/001-evaluating-the-impact-of-llm-generated-c/research.md
```

## Troubleshooting

* **Memory Error**: If the local `phi` model fails to load, ensure you are using the `int4` quantization flag and have at least 4GB free RAM.
* **API Rate Limit**: The system will automatically retry with exponential backoff. If it fails, it will fallback to the local model.
* **Constraint Violation**: If the analysis exceeds a predefined computational time or memory threshold, the `monitor.py` context manager will raise an error and log the violation.

