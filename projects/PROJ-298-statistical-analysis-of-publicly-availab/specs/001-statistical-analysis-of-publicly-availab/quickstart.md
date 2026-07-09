# Quickstart: Statistical Analysis of Publicly Available Stack Overflow Question Tags

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions runner (or local environment with 7GB+ RAM)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-298-statistical-analysis-of-publicly-availab
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Data Download

The `PostsTags` table is downloaded from the canonical Archive.org URL.

```bash
python code/data/download.py
```

*Note: This step requires internet access and may take time depending on the archive size.*

## Running the Analysis

Execute the full pipeline:

```bash
python code/main.py
```

This will:
1. Download and preprocess data.
2. Run Mann-Kendall tests.
3. Perform time series decomposition.
4. Execute clustering.
5. Generate reports and visualizations.

## Output Artifacts

- `data/processed/trend_results.csv`: Trend classifications and statistics.
- `data/processed/clusters.json`: Cluster membership and alignment scores.
- `reports/analysis_report.html`: Full report with limitation headers.
- `state/projects/PROJ-298-statistical-analysis-of-publicly-availab.yaml`: Updated with checksums.
- `notebooks/`: Reproducible Jupyter notebooks for each analysis step.

## Troubleshooting

- **Memory Error**: Ensure you are on a runner with ≥7GB RAM. If local, close other applications.
- **API Rate Limits**: GitHub/NPM API calls may be rate-limited. The system caches results automatically.
- **Missing Data**: If a tag has <12 months of data, it is automatically excluded.