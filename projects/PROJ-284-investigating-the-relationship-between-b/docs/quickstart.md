# Quickstart Guide

Get up and running with the Brain Network Dynamics pipeline in 5 minutes.

## 1. Prerequisites

- Python 3.11+
- Git
- (Optional) FSL and AFNI for local preprocessing validation.

## 2. Setup

```bash
# Clone the repository
git clone <repository-url>
cd PROJ-284-investigating-the-relationship-between-b

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Configure Credentials

Set your HCP credentials as environment variables:

```bash
export HCP_USERNAME="your_username"
export HCP_PASSWORD="your_password"
```

## 4. Run the Pipeline

Execute the full pipeline with a single command:

```bash
python code/main.py
```

This will:
1. Download a subset of HCP data (if not already present).
2. Preprocess the data.
3. Extract network metrics.
4. Run correlation analysis.
5. Generate visualizations and a report.

*Note: Running the full pipeline may take time and require significant disk space. For a quick test, you can run individual modules as described in `docs/running_the_pipeline.md`.*

## 5. View Results

- **Reports:** Check `docs/report.md` for the generated analysis report.
- **Plots:** Find visualizations in the `figures/` directory.
- **Data:** Processed data and metrics are in `data/analysis/`.

## Next Steps

- Read the [Running the Pipeline](running_the_pipeline.md) guide for detailed module execution.
- Review the [API Reference](api_reference.md) for module details.
- Explore the [Limitation Statement](limitation_statement.md) to understand study constraints.
