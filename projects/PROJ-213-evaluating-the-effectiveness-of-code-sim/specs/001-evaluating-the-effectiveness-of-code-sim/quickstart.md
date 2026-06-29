# Quickstart: Evaluating the Effectiveness of Code Simplification on LLM Performance

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI execution)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd projects/PROJ-213-evaluating-the-effectiveness-of-code-sim
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify environment**
   ```bash
   python -m pytest tests/unit/
   ```

## Running the Benchmark

### Step 1: Download Dataset
```bash
python code/download.py --output data/raw/humaneval.jsonl
```
*Note: If HumanEval is not available from verified source, this step will fail. Document the gap.*

### Step 2: Simplify Code
```bash
python code/simplify.py --input data/raw/humaneval.jsonl --output data/processed/simplified/
```
*Outputs: `data/processed/simplified/*.py`, `parse_failures.log`, `flagged_snippets.csv`*

### Step 3: Run Inference (Raw)
```bash
python code/inference.py --input data/raw/humaneval.jsonl --output data/processed/metrics_raw.csv --mode raw
```

### Step 4: Run Inference (Simplified)
```bash
python code/inference.py --input data/processed/simplified/ --output data/processed/metrics_simplified.csv --mode simplified
```

### Step 5: Analyze Results
```bash
python code/analyze.py --raw data/processed/metrics_raw.csv --simplified data/processed/metrics_simplified.csv --output analysis_report.pdf
```

## Expected Outputs

| File | Description |
|------|-------------|
| `data/raw/humaneval.jsonl` | Downloaded HumanEval benchmark |
| `data/processed/simplified/*.py` | AST-simplified code snippets |
| `data/processed/metrics_raw.csv` | Inference metrics for raw code |
| `data/processed/metrics_simplified.csv` | Inference metrics for simplified code |
| `parse_failures.log` | AST parsing failures |
| `flagged_snippets.csv` | Semantic change warnings |
| `analysis_report.pdf` | Statistical report with tests + figures |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| HumanEval download fails | Check verified source; document gap if unavailable |
| Out of memory | Reduce sample size; confirm 4-bit quantization |
| Inference timeout | Check model loading; reduce context window |
| AST parse failures | Log to `parse_failures.log`; exclude from analysis if >5% |
| Semantic changes | Log to `flagged_snippets.csv`; exclude from analysis if >5% |
