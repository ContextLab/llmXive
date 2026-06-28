# Quickstart: Statistical Analysis of GitHub Issue Resolution Times

## Prerequisites

- Python 3.11 or higher
- GitHub account with API token (optional but recommended for rate limits)
- 7GB+ available RAM, 14GB+ available disk
- Git (for repository cloning)

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd projects/PROJ-208-statistical-analysis-of-publicly-availab
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   cd code
   pip install -r requirements.txt
   ```

4. **Set GitHub token** (optional but recommended):
   ```bash
   export GITHUB_TOKEN="your_github_personal_access_token"
   ```

## Running the Pipeline

### Step 1: Data Collection (Phase 1)

```bash
# Collect issues from configured repositories
python collect/fetch_issues.py

# Preprocess and clean data
python collect/preprocess.py
```

**Expected output**: `data/processed/issues_clean.parquet` with ≥1000 issues

### Step 2: Distribution Analysis (Phase 2)

```bash
# Generate ECDF plots and fit parametric distributions
python analyze/distributions.py
```

**Expected output**: `data/figures/ecdf_*.png`, KS statistics for log-normal and Weibull

### Step 3: Hypothesis Testing (Phase 3)

```bash
# Run hypothesis tests with Holm-Bonferroni correction
python analyze/hypothesis_tests.py

# Fit mixed-effects model with LOO-CV
python analyze/mixed_effects.py
```

**Expected output**: `data/processed/analysis_results.parquet` with p-values, effect sizes, MAE, R²

### Step 4: Diagnostics (Phase 4)

```bash
# Calculate VIF and run sensitivity analysis
python analyze/diagnostics.py

# Generate result text with associational language
python analyze/results.py
```

**Expected output**: `data/figures/vif_*.png`, `data/figures/loo_cv_*.png`, result summaries

### Step 5: Validation (Phase 5)

```bash
# Run contract validation tests
pytest tests/contract/

# Verify data checksums
python utils/validators.py --verify-checksums
```

## Configuration

Edit `code/utils/config.py` to customize:

- `REPOSITORY_LIST`: List of GitHub repos to analyze (≥100 required, ≥10 issues each)
- `SINCE_DATE`: Collection start date (default: 2020-01-01)
- `RANDOM_SEED`: For reproducibility (default: 42)
- `OUTLIER_THRESHOLD`: Days for outlier detection (default: 30)
- `VIF_THRESHOLD`: Collinearity flag threshold (default: 5)
- `MIN_ISSUES_PER_REPO`: Minimum issues per repo for mixed-effects (default: 10)

## Troubleshooting

### GitHub API Rate Limit Exceeded

```
Error: 403 - Rate limit exceeded
```

**Solution**: The script implements exponential backoff with ≥60s wait (FR-001). If persistent, reduce `REPOSITORY_LIST` size or use authenticated token.

### Memory Error (>7GB)

```
Error: MemoryError or segfault
```

**Solution**: Reduce issue count by sampling in `preprocess.py`. Target a substantial number of issues within the available memory budget..

### Mixed-Effects Model Convergence Failure

```
Error: ConvergenceWarning
```

**Solution**: Use `statsmodels` fallback or simplify random effects structure. Report convergence failure in results per protocol.

### Missing Programming Language

```
Warning: language field is null for repo X
```

**Solution**: Repository excluded from language-group analyses. Logged as missing data per SC-001.

### Insufficient Issues Per Repository

```
Warning: Repository X has only Y issues (<10 required for mixed-effects)
```

**Solution**: Repository excluded from mixed-effects modeling but may be included in descriptive analyses. Logged separately.

### Zero Resolution Time

```
Warning: Issue X has zero resolution time (created_at == closed_at)
```

**Solution**: Issue included in analysis with log(x+1) transform for distribution fitting. Flagged in results.

## Verification

After pipeline completes, verify:

1. **Dataset completeness**: `issues_clean.parquet` has ≥95% non-missing required columns (SC-001)
2. **Distribution fit**: KS p-value reported for at least one parametric family (SC-002)
3. **Hypothesis tests**: Adjusted p-values <0.05 reported as significant (SC-003)
4. **Model performance**: LOO-CV MAE and R² reported with standard deviation (SC-004)
5. **Runtime**: Total execution ≤6 hours (SC-005)
6. **Power analysis**: Confirmed ≥10 issues per repository for mixed-effects modeling

## Next Steps

- Review `paper/` directory for draft manuscript
- Run `pytest tests/` for full test suite
- Check `state/projects/*.yaml` for artifact hashes and stage progression