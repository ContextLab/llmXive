# Quickstart: Investigating the Correlation Between Code Churn and Technical Debt

## Prerequisites

- Python 3.11+  
- Git (for cloning)  
- ≥ 7 GB RAM, ≥ 14 GB disk space  
- GitHub API token (optional, for higher rate limits)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd <repository-name>

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies (requirements.txt will be generated in Phase 1)
pip install -r requirements.txt
```

## Configuration

1. **GitHub Token** (recommended):
   ```bash
   export GITHUB_TOKEN="your_token_here"
   ```

2. **Repository List** (optional):
   - Edit `data/raw/repos_list.txt` to supply a custom list, or let the pipeline query GitHub automatically.

3. **Parameter Tweaks** (optional, edit `code/config.py`):
   - `FILE_SIZE_THRESHOLD = 10` LOC (default) – can be set to 5 or 20 for sensitivity runs.  
   - `MAX_REPOS = 50` – number of repositories to analyze.  
   - `MIN_STARS = 500` – star cutoff.  
   - `MIN_AGE_YEARS = 2`.

## Running the Pipeline

### Full Execution (Phase 0–6)

```bash
python code/main.py
```

This orchestrates:
1. Repository selection (GitHub API).  
2. Cloning & git‑history extraction.  
3. Static analysis with Radon (Python) and **Semgrep** (other languages).  
4. Pre‑processing & metric calculation (raw metrics).  
5. Mixed‑effects correlation analysis + meta‑analysis.  
6. Sensitivity analysis (thresholds 5, 10, 20 LOC).  
7. Visualization and generation of `summary_report.txt`.

### Individual Stages (for debugging)

- **Data Extraction**: `python code/data_extraction.py --repos 10`  
- **Static Analysis**: `python code/static_analysis.py --repos 10`  
- **Analysis**: `python code/analysis.py`  
- **Visualization**: `python code/visualization.py`  
- **Reporting**: `python code/reporting.py`

### Testing

```bash
# Unit tests
pytest tests/unit/

# Contract (schema) tests
pytest tests/contract/

# End‑to‑end integration (small sample)
pytest tests/integration/
```

## Expected Outputs

```
data/
├── raw/
│   ├── repos_metadata.csv
│   ├── git_history/
│   └── static_analysis/
├── processed/
│   └── unified_metrics.csv
├── results/
│   ├── correlation_results.csv
│   ├── sensitivity_analysis.csv
│   ├── plots/
│   │   ├── repo_1_scatter.png
│   │   └── aggregate_scatter.png
│   └── summary_report.txt
└── logs/
    └── tool_validation_log.csv   # Contains tool version, star count, citation
```

- `summary_report.txt` includes a **correlation strength classification** per SC‑001 (|r| ≥ 0.3 → *moderate*).  
- `tool_validation_log.csv` satisfies SC‑005 by logging each tool’s citation and star count.

## Troubleshooting

- **API rate limits** – set `GITHUB_TOKEN`.  
- **Static analysis failures** – check `logs/tool_validation_log.csv` for error messages; problematic repos are skipped.  
- **Out‑of‑memory** – reduce `MAX_REPOS` or process repositories sequentially (`--repos` flag).  
- **Disk space** – delete `data/raw/git_history/` after successful extraction.

## Debug Mode

```bash
python code/main.py --verbose
```

Enables detailed logging to `logs/`.

## Verification Checklist

1. Run on a small subset (`--repos 5`).  
2. Confirm `data/processed/unified_metrics.csv` has non‑null `total_lines_changed` and `debt_score`.  
3. Verify `correlation_results.csv` and `sensitivity_analysis.csv` are generated.  
4. Ensure scatter plots appear in `data/results/plots/`.  
5. Check `summary_report.txt` flags any correlation with |r| ≥ 0.3 as *moderate*.

## Next Steps

- Increase `MAX_REPOS` to the full 50‑100 range.  
- Review `summary_report.txt` for findings.  
- Share results with stakeholders or incorporate into a manuscript.