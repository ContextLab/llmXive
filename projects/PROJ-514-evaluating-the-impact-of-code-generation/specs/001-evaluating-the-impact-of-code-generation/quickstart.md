# Quickstart: Evaluating Code Generation Impact on Code Smell Frequency

## Prerequisites
- Python 3.11+
- Node.js (for PMD/SonarQube CLI if required, otherwise PMD Java)
- Git
- GitHub Personal Access Token (optional, for rate limit increase)
- HuggingFace API Token (optional, for LLM generation)

## Installation

1.  **Clone and Setup Environment**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-514-evaluating-the-impact-of-code-generation
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

3.  **Configure Environment Variables**:
    Create `.env` in the project root:
    ```bash
    GITHUB_TOKEN=your_token_here
    HF_API_KEY=your_hf_key_here
    RANDOM_SEED=42
    MAX_CONCURRENT_JOBS=20
    ```

## Running the Pipeline

The pipeline is orchestrated via `code/main.py`.

### Step 1: Data Collection
Fetches human samples and generates LLM samples.
```bash
python code/main.py --step collect
```
*Output*: `data/raw/human_samples/`, `data/raw/llm_samples/`, `data/raw/api_logs.json`

### Step 2: Static Analysis
Runs PMD/SonarQube on all samples.
```bash
python code/main.py --step analyze
```
*Output*: `data/intermediate/analysis_results.json`

### Step 3: Statistical Analysis
Performs tests and sensitivity analysis.
```bash
python code/main.py --step analyze_stats
```
*Output*: `data/processed/smell_metrics.csv`, `data/processed/stat_results.json`

### Step 4: Report Generation
Generates the final Markdown/PDF report.
```bash
python code/main.py --step report
```
*Output*: `docs/report.md`

## Testing

Run unit tests:
```bash
pytest tests/unit/ -v
```

Run contract tests (validate data against schemas):
```bash
pytest tests/contract/ -v
```

## Troubleshooting
- **API Rate Limits**: The system implements exponential backoff. If it fails after 3 retries, the sample is skipped and logged.
- **Memory Errors**: Ensure `MAX_CONCURRENT_JOBS` is set to 20 or lower.
- **Syntax Errors**: Invalid code samples are logged and excluded from analysis.
