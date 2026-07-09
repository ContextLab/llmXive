# Quickstart: Evaluating the Impact of Code Generation on Long-Term Code Maintainability

## 1. Prerequisites

- **Python**: 3.11+
- **Dependencies**: `pip install -r code/requirements.txt`
- **GitHub Token**: Set `GITHUB_TOKEN` environment variable (with `repo` scope).
- **RAM**: ≥ 7GB (for processing).
- **Disk**: ≥ 14GB (for git clones and data).

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-247-evaluating-the-impact-of-code-generation

# Install dependencies
pip install -r code/requirements.txt

# Set environment variables
export GITHUB_TOKEN="your_token_here"
```

## 3. Running the Pipeline

### Step 1: Data Curation (FR-001, FR-002, FR-008)
```bash
python code/01_data_curation.py
```
- **Output**: `data/processed/tagged_blocks.csv`, `data/processed/matched_pairs.csv`
- **Time**: ~2-3 hours (depends on repo count).
- **Note**: Includes collinearity checks and repository-level matching.

### Step 2: Metric Extraction (FR-004)
```bash
python code/02_metric_extraction.py
```
- **Output**: `data/processed/maintenance_metrics.csv`
- **Time**: ~1-2 hours.
- **Note**: Includes linking bias analysis.

### Step 3: Ground Truth Verification (FR-007)
- **Manual Step**: Review 10+ blocks in `data/ground_truth/manual_labels.csv`.
- **Action**: Update labels; **run `python code/utils/checksum_ground_truth.py` to generate and record the SHA-256 checksum in `state/`**.
- **Output**: `data/ground_truth/manual_labels.csv` (checksummed).

### Step 4: Statistical Analysis (FR-005, FR-006)
```bash
python code/03_analysis.py
```
- **Output**: `results/stats.json`, `results/figures/boxplot_churn.png`, `results/figures/boxplot_latency.png`
- **Time**: [deferred].
- **Note**: Performs Linear Mixed-Effects Model (LMM) and Sensitivity Analysis.

## 4. Verification

- **Contract Tests**: `pytest tests/contract/`
- **Unit Tests**: `pytest tests/unit/`
- **Data Integrity**: Check `state/` for checksums (including ground truth).

## 5. Troubleshooting

| Issue | Solution |
|-------|----------|
| **GitHub API Rate Limit** | Wait 1 hour or use a different token. |
| **Memory Error** | Reduce repo count in config; ensure 7GB RAM. |
| **Classifier Low Confidence** | Check `data/processed/exclusions.log`. |
| **Missing Issue Links** | Pairs excluded from latency analysis (expected). |
| **Timeout** | The pipeline automatically reduces sample size if approaching 6 hours. |

## 6. Output Artifacts

- **Stats**: `results/stats.json` (p-values, effect sizes, **bias-corrected effect sizes**).
- **Figures**: `results/figures/*.png` (box plots).
- **Reports**: `results/report.md` (summary of findings, including sensitivity analysis).
