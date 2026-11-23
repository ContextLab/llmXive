# Quickstart Guide: Evaluating the Impact of LLM-Generated Code Documentation

This guide provides a step-by-step process to run the pilot study for PROJ-274.

## Prerequisites

- Python 3.9+
- `git` installed and in PATH
- (Optional) OpenAI API key if using primary LLM (not required for local fallback)

## Installation

1. Navigate to the project root:
 ```bash
 cd projects/PROJ-274-evaluating-the-impact-of-llm-generated-c
 ```

2. Create and activate a virtual environment:
 ```bash
 python -m venv code/.venv
 source code/.venv/bin/activate # On Windows: code\.venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

4. Verify the project structure:
 ```bash
 python scripts/verify_structure.py
 ```

## Running the Pipeline

The pipeline consists of three main stages: Data Collection, Documentation Generation, and Analysis.

### Step 1: Run Mock Data Collection (User Story 1)

Simulate participant sessions to generate raw logs.

```bash
python code/experiment/experiment.py --mode mock --participants 3
```

**Output:** `data/raw/participant_logs.json`

### Step 2: Generate Documentation (User Story 2)

Generate documentation for a sample repository. This uses the local `phi-2` model as a fallback to ensure the pipeline runs without external API keys.

**Note:** Replace `<repo_url>` and `<commit_hash>` with real values. For testing, you can use a small public repo.

```bash
python code/generation/doc_pipeline.py --repo https://github.com/psf/requests --commit 94a5e15 --output data/processed/docs/repo_docs.md
```

**Output:** `data/processed/docs/repo_docs.md`

### Step 3: Run Statistical Analysis (User Story 3)

Process the collected data and run the statistical tests.

```bash
python code/analysis/stats_runner.py --input data/processed/task_logs_anon.json --output data/processed/analysis_results.json
```

**Output:** `data/processed/analysis_results.json`

## Troubleshooting

- **Missing Scripts:** If you encounter "No such file or directory" errors, ensure you are running commands from the project root and that the virtual environment is activated.
- **Data Fetch Errors:** If the documentation generation fails to fetch the repository, verify the repository URL and commit hash are valid. The pipeline is designed to fail loudly on data fetch errors (T055).
- **Memory Issues:** If you encounter memory errors during analysis, ensure you have sufficient RAM (limit is set to 7GB per FR-007).

## Next Steps

- Review `docs/README.md` for detailed API documentation.
- Check `data/reports/final_report.md` after a full run for the summary of results.