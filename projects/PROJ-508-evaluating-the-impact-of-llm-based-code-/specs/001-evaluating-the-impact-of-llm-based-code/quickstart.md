# Quickstart: Evaluating the Impact of LLM-Based Code Completion on Developer Cognitive Load

## Prerequisites

- Python 3.11+
- GitHub Personal Access Token (with `public_repo` scope) stored in `GITHUB_TOKEN` env var.
- 50+ repositories defined in `data/target_repos.json`.

## Installation

1.  **Clone & Setup**:
    ```bash
    cd projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Configure**:
    Create `data/target_repos.json` with a list of repository strings (e.g., `["owner/repo1", "owner/repo2"]`).
    Set `export GITHUB_TOKEN="ghp_..."`

## Running the Pipeline

Execute the full pipeline (Ingest -> Preprocess -> Validate -> Analyze -> Sensitivity):

```bash
python code/main.py
```

### Expected Outputs

- `data/processed/cleaned_prs.csv`: The dataset ready for analysis.
- `results/validity.json`: Construct validity correlations (FR-007).
- `results/regression.json`: Primary regression coefficients, CIs, and hypothesis test results.
- `results/sensitivity.json`: Sensitivity analysis results.
- `logs/pipeline.log`: Execution logs (including VIF/Ridge switches, coverage check).

## Verification

1.  **Check Data**:
    ```bash
    python -c "import pandas as pd; df = pd.read_csv('data/processed/cleaned_prs.csv'); print(df['llm_adopted'].value_counts())"
    ```
    Ensure both 0 and 1 values exist.

2.  **Check Validity**:
    Verify `results/validity.json` contains `revert_valid_proxy` and the correlation values.

3.  **Check Results**:
    Verify `results/regression.json` contains `coefficient_llm`, `p_value`, `ci_lower`/`ci_upper`, and `significant_at_0.05`.

4.  **Run Tests**:
    ```bash
    pytest tests/
    ```

## Troubleshooting

- **API Rate Limit**: The script implements exponential backoff. If it fails after 3 retries, check your token scope.
- **Coverage Fail**: If the pipeline aborts with a "Coverage < 80%" error, verify your `target_repos.json` list and network connectivity.
- **Memory Error**: If the dataset is too large, the script will automatically apply Stratified Sampling. If it still fails, reduce the `max_prs_per_repo` setting in `code/utils.py`.
- **No LLM Repos**: Ensure `target_repos.json` includes known LLM-adopting projects (e.g., those with `.cursorrules`).
- **Domain Complexity Warning**: If you see a warning about `domain_complexity` being excluded, this is expected behavior to avoid collinearity (see Plan.md).