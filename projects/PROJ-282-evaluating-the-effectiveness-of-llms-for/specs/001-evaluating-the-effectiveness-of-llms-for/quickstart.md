# Quickstart: Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities

## Prerequisites
- Python 3.11+
- `git`
- 14 GB disk space (for datasets and cache)
- 7 GB+ RAM (recommended)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-282-evaluating-the-effectiveness-of-llms-for
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins `transformers`, `scikit-learn`, `pandas`, `tree-sitter`, `torch` (CPU version), and `bitsandbytes` (CPU path).*

## Running the Pipeline

The pipeline is executed via the CLI entry point.

### Step 1: Download & Validate Data
```bash
python -m src.cli.main download --dataset vuldeepecker
```
*This fetches data from the verified URLs, validates them against `research.md`, and stores it in `data/raw/` with checksums.*

### Step 2: Extract Features
```bash
python -m src.cli.main extract --input data/raw/vuldeepecker.parquet --output data/processed/features.csv
```
*Computes AST, complexity, and embedding features. Handles malformed code gracefully.*

### Step 3: Run Inference (LLM & Baseline)
```bash
python -m src.cli.main infer --features data/processed/features.csv --batch-size 10
```
*Runs zero-shot LLM inference (CPU, 4-bit quantization) and static analyzers (Bandit/cppcheck). Outputs `data/processed/predictions.csv`. Logs truncation events.*

### Step 4: Statistical Analysis
```bash
python -m src.cli.main analyze --predictions data/processed/predictions.csv --features data/processed/features.csv
```
*Generates Point-Biserial correlation matrices, Logistic Regression summaries, and McNemar's test results. Outputs `data/results/metrics.json`.*

### Step 5: Human Verification (Optional)
```bash
python -m src.cli.main verify --subset-size 100
```
*Selects a random subset for manual review to assess label noise (FR-011).*

## Verifying Results
Check `data/results/metrics.json` for:
- `nagelkerke_r2`: Should be reported with p-values.
- `mcnemar_p`: P-value for LLM vs. Baseline comparison.
- `correlations`: List of feature correlations with FDR-adjusted p-values.
- `r2_threshold_check`: Pass/Fail against SC-002 (pseudo-R² > 0.10).

## Troubleshooting
- **OOM Error**: Reduce `--batch-size` to 5 or 2.
- **Parsing Error**: Check `logs/parse_errors.log` for malformed snippets.
- **Model Load Fail**: Ensure `torch` is installed for CPU (not CUDA) and `bitsandbytes` is configured for CPU.
