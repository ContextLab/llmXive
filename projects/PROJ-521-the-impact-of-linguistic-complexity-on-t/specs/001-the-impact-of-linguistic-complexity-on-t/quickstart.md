# Quickstart: The Impact of Linguistic Complexity on Trust in AI-Generated Text

## Prerequisites

- Python 3.11+
- GitHub CLI (optional, for repo management)
- Prolific account (for survey deployment; simulated for CI)
- HuggingFace account (for dataset access; token required if private)

## Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/your-repo.git
   cd your-repo
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r projects/PROJ-521-the-impact-of-linguistic-complexity-on-t/code/requirements.txt
   ```

4. **Set environment variables** (optional for Prolific):
   ```bash
   export PROLIFIC_API_KEY="your-api-key"
   ```

## Running the Pipeline

### Step 1: Generate Text Samples
```bash
cd projects/PROJ-521-the-impact-of-linguistic-complexity-on-t/code/
python generate_text.py --num-samples 200 --seed 42
```
- Output: `data/raw/generated_text.csv`
- Verification: Check FK range (5.0–12.0) and variance.

### Step 2: Collect Trust Ratings (Simulation for CI)
```bash
python collect_trust.py --simulate --num-participants 100 --seed 42
```
- Output: `data/raw/trust_responses.csv`
- Note: For real deployment, replace `--simulate` with Prolific API calls.

### Step 3: Analyze Data
```bash
python analyze.py --input data/processed/analysis_inputs.csv --output data/outputs/
```
- Output: `data/outputs/regression_results.json`, `data/outputs/figures/`
- Verification: Check p-values for quadratic terms and plots.

## Testing

### Unit Tests
```bash
pytest tests/unit/
```

### Contract Tests (Schema Validation)
```bash
pytest tests/contract/
```

### Integration Test (End-to-End)
```bash
pytest tests/integration/test_pipeline.py
```

## CI/CD

The project is configured for GitHub Actions:
- **Workflow**: `.github/workflows/ci.yml`
- **Steps**:
  1. Install dependencies.
  2. Run unit tests.
  3. Run contract tests.
  4. Run integration test (generate → collect → analyze).
  5. Validate checksums.

## Troubleshooting

- **Gemma-2B OOM**: Reduce batch size or use smaller model (e.g., Gemma-1.1B).
- **FK Range Narrow**: Adjust prompts in `generate_text.py` to target more extreme complexity.
- **Model Non-Convergence**: Check for NaN/Inf in data; inspect `analysis_inputs.csv`.
- **Prolific API Error**: Use `--simulate` for CI; check API key for real runs.

## Next Steps

- Deploy survey on Prolific for real data collection.
- Expand sample size if N < 100.
- Write paper using `data/outputs/` results.
