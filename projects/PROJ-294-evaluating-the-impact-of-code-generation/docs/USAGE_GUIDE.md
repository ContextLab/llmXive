# Usage Guide: Evaluating the Impact of Code Generation Models on Code Testability

This guide provides detailed instructions for using each component of the pipeline.

## Prerequisites

- Python 3.9+
- 8GB+ RAM (for local model execution)
- Stable internet connection (for API fallback and dataset download)
- HuggingFace account with API token (optional, for CodeLlama-7B)

## Step-by-Step Pipeline Execution

### 1. Environment Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # Linux/Mac
# venv\Scripts\activate # Windows

# Install dependencies
pip install -r code/requirements.txt

# Set up environment variables (optional)
export HUGGINGFACE_TOKEN="your_token_here"
export LOG_LEVEL="INFO"
```

### 2. Download HumanEval Dataset

```bash
python code/download_data.py
```

**What it does:**
- Downloads HumanEval dataset from HuggingFace
- Verifies SHA256 checksum for integrity
- Performs stratified sampling based on human pass-rate quartiles
- Saves 50 representative tasks to `data/analysis/sampled_tasks.json`

**Expected output:**
```
[INFO] Downloading HumanEval dataset...
[INFO] Checksum verification passed: sha256:abc123...
[INFO] Stratified sampling: 50 tasks selected
[INFO] Saved to data/analysis/sampled_tasks.json
```

**Troubleshooting:**
- **Checksum mismatch**: Delete `data/raw/humaneval.json` and rerun
- **Network error**: Check internet connection, retry with `--retry 3` flag

### 3. Generate Code with LLMs

```bash
python code/generate_code.py
```

**What it does:**
- Loads CodeLlama-350M model locally
- Attempts to load CodeLlama-3B with 4-bit quantization (CPU)
- Falls back to HuggingFace Inference API for CodeLlama-7B if needed
- Generates code for each sampled task with 3-retry logic
- Logs failures to `errors.log`

**Model Selection Strategy:**
1. **Primary**: CodeLlama-350M (fast, local)
2. **Secondary**: CodeLlama-3B (4-bit quantized, local)
3. **Tertiary**: CodeLlama-7B (API, if local models unavailable)

**Expected output:**
```
[INFO] Loading CodeLlama-350M...
[INFO] Attempting CodeLlama-3B 4-bit quantization...
[INFO] CodeLlama-3B loaded successfully
[INFO] Generating code for 50 tasks...
[INFO] Task HumanEval/0: SUCCESS (model: CodeLlama-350M)
[INFO] Task HumanEval/1: FAILED (retry 1/3)
[INFO] Task HumanEval/1: SUCCESS (retry 2/3)
[INFO] Saved to data/generated/code_samples.json
```

**Troubleshooting:**
- **OOM error**: Reduce batch size or use API fallback
- **API rate limit**: Wait 60 seconds and retry
- **Model loading failure**: Check RAM availability, use `--force-api` flag

### 4. Analyze Metrics

```bash
python code/analyze_metrics.py
```

**What it does:**
- Calculates Cyclomatic Complexity using `radon`
- Calculates Halstead Volume using `radon`
- Executes test suites with `pytest` to determine pass_rate
- Runs `pytest --cov` for branch coverage percentage
- Handles execution failures gracefully (marks as `[deferred]`)
- Aggregates results to `data/analysis/metrics.json`

**Metrics Calculated:**
- `cyclomatic_complexity`: Integer, higher = more complex
- `halstead_volume`: Float, measures program volume
- `branch_coverage_pct`: Float (0-100), percentage of branches covered
- `pass_rate`: Binary (0 or 1), 1 = all tests passed

**Expected output:**
```
[INFO] Analyzing 50 code samples...
[INFO] Sample HumanEval/0: CC=3, HV=45.2, Coverage=85.5%, Pass=1
[INFO] Sample HumanEval/1: CC=5, HV=67.8, Coverage=[deferred], Pass=0
[INFO] Aggregated metrics saved to data/analysis/metrics.json
```

**Troubleshooting:**
- **Coverage failure**: Some complex control flow may not be measurable
- **Test execution timeout**: Increase timeout in `analyze_metrics.py`
- **Missing radon**: `pip install radon`

### 5. Run Statistical Tests

```bash
python code/statistical_tests.py
```

**What it does:**
- Performs Wilcoxon Signed-Rank test on all continuous metrics
- Runs McNemar's test on pass_rate (binary)
- Executes Fisher's Exact test for unpaired exploration
- Runs Permutation test for paired branch coverage
- Calculates Spearman correlation (complexity vs. success)
- Performs A Priori and Post-Hoc power analysis
- Saves results to `results/statistical_results.json`

**Expected output:**
```
[INFO] Running Wilcoxon test on Cyclomatic Complexity...
[INFO] W=123, p-value=0.032 (significant at α=0.05)
[INFO] Running McNemar test on Pass Rate...
[INFO] χ²=4.56, p-value=0.033 (significant)
[INFO] Power analysis: Achieved power=0.82 (target ≥0.8)
[INFO] Results saved to results/statistical_results.json
```

**Interpretation:**
- **p-value < 0.05**: Significant difference between models
- **Power ≥ 0.8**: Adequate sample size for detected effect
- **Correlation coefficient**: Strength of relationship (0 = no correlation, 1 = perfect)

### 6. Generate Final Report

```bash
python code/report_generator.py
```

**What it does:**
- Creates histograms and boxplots for all metrics
- Compiles Jinja2 template into `results/report.md`
- Includes sensitivity analysis comparison (7B/3B vs 350M)
- Embeds statistical test results and power analysis
- Saves figures to `results/figures/`

**Expected output:**
```
[INFO] Generating histograms for Cyclomatic Complexity...
[INFO] Generating boxplots for Halstead Volume...
[INFO] Compiling Markdown report...
[INFO] Report saved to results/report.md
[INFO] Figures saved to results/figures/
```

**Output Files:**
- `results/report.md`: Complete analysis report
- `results/figures/histogram_complexity.png`: CC distribution
- `results/figures/boxplot_halstead.png`: HV comparison
- `results/figures/coverage_pass_rate.png`: Coverage vs. pass rate

## Advanced Usage

### Running Sensitivity Analysis Only

```bash
# Generate code with specific model
python code/generate_code.py --model CodeLlama-7B --api-only

# Re-analyze specific samples
python code/analyze_metrics.py --input data/generated/sensitivity_samples.json
```

### Custom Sampling Strategy

```bash
python code/download_data.py --quartiles 4 --sample-size 100
```

### Parallel Execution

```bash
# Analyze metrics in parallel (experimental)
python code/analyze_metrics.py --workers 4
```

### Debug Mode

```bash
export LOG_LEVEL=DEBUG
python code/download_data.py
```

## Data Validation

### Verify Artifact Integrity

```bash
python code/utils.py --verify-all
```

### Check Dataset Completeness

```bash
python code/download_data.py --validate
```

## Performance Tips

1. **Memory Optimization**: Use 4-bit quantization for local models
2. **Batch Processing**: Process tasks in batches of 5-10
3. **Caching**: Reuse downloaded models across runs
4. **API Fallback**: Set `--force-api` if local models fail

## Common Issues

### Issue: "Module not found: radon"
**Solution**: `pip install radon`

### Issue: "CUDA out of memory"
**Solution**: Use CPU-only mode: `python code/generate_code.py --cpu-only`

### Issue: "HuggingFace API rate limit exceeded"
**Solution**: Wait 60 seconds or use local models as fallback

### Issue: "Coverage measurement failed"
**Solution**: This is expected for complex control flow; marked as `[deferred]`

### Issue: "Power analysis shows low power (<0.8)"
**Solution**: Increase sample size or reduce effect size threshold

## Exporting Results

### Export to CSV

```python
import json
import pandas as pd

with open('data/analysis/metrics.json') as f:
 data = json.load(f)

df = pd.DataFrame(data['samples'])
df.to_csv('results/metrics_export.csv', index=False)
```

### Export Statistical Results

```python
import json

with open('results/statistical_results.json') as f:
 stats = json.load(f)

# Export specific test results
wilcoxon_results = stats['wilcoxon_tests']
```

## Next Steps

1. Review `results/report.md` for insights
2. Visualize additional metrics in `results/figures/`
3. Share findings with research team
4. Iterate on hypothesis based on results

## Support

For additional help, refer to:
- `README.md` in project root
- `specs/001-evaluating-the-impact-of-code-generation/` for detailed requirements
- GitHub Issues for bug reports and feature requests
