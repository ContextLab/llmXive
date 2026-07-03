# Quickstart: Evaluating Automated Code Review Tools Effectiveness

## Prerequisites

- **Python 3.11+**
- **Docker** (for tool execution)
- **GitHub Token** (for API access; set as `GITHUB_TOKEN` env var)
- **7 GB RAM** available (for repository analysis)
- **6 GB Disk** space (for cloned repos and reports)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-org/your-repo.git
    cd your-repo
    ```

2.  **Set up virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

4.  **Set environment variables**:
    ```bash
    export GITHUB_TOKEN="your_github_token"
    ```

## Running the Pipeline

The pipeline is executed in stages. Run each stage sequentially:

### Stage 1: Data Acquisition
```bash
python code/01_data_acquisition.py
```
- Clones a subset of repositories.
- Executes SonarQube, DeepSource, and CodeClimate.
- Outputs: `data/raw/repo_list.json`, `data/raw/tool_reports/`

### Stage 2: Human Annotation
```bash
python code/02_human_annotation.py
```
- Extracts PR comments.
- Applies keyword heuristics AND random sampling.
- Outputs: `data/processed/annotations.json`

### Stage 3: Alignment
```bash
python code/03_alignment.py
```
- Aligns tool issues with human annotations.
- Outputs: `data/processed/aligned_pairs.json`

### Stage 4: Metrics & Analysis
```bash
python code/04_metrics.py
python code/05_regression.py
```
- Computes precision, recall, F1.
- Runs statistical tests and mixed-effects regression.
- Outputs: `results/metrics.csv`, `results/regression_table.csv`, `results/plots/`

## Validation

Run contract tests to verify data schemas:
```bash
pytest tests/contract/
```

Run integration tests to verify pipeline stages:
```bash
pytest tests/integration/
```

## Troubleshooting

- **GitHub API Rate Limits**: Ensure `GITHUB_TOKEN` is set and valid.
- **Tool Execution Failures**: Check Docker logs; verify tool versions in `code/versions.yaml`.
- **Memory Errors**: Reduce repository sample size; exclude large repos.
- **Alignment Errors**: Check `data/processed/aligned_pairs.json` for ambiguous matches.

## Output Artifacts

- `data/raw/`: Raw data (repos, tool reports, PR comments)
- `data/processed/`: Processed data (annotations, aligned pairs, metrics)
- `results/`: Final artifacts (CSV, PNG plots, regression tables)

For detailed documentation, refer to `docs/` and `specs/`.