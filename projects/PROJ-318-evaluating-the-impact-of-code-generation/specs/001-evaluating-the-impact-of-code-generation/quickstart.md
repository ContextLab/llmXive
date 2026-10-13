# Quickstart Guide: Evaluating Code Generation Model Documentation Completeness

This guide walks you through running the full research pipeline on the GitHub Actions free‑tier environment (or locally on a comparable CPU‑only machine).

## Prerequisites
- **Python** ≥ 3.9 (the CI runner uses 3.11)
- **Git** (for cloning repositories)
- **Internet access** (to fetch PyPI metadata, GitHub repos, and model weights)
- **≤ 7 GB RAM** (the free runner limit)  
  *No GPU is required; the pipeline runs entirely on CPU.*

## 1. Set Up the Environment
```bash
# Clone the project repository (if you haven't already)
git clone https://github.com/your-org/PROJ-318-evaluating-the-impact-of-code-generation.git
cd PROJ-318-evaluating-the-impact-of-code-generation

# Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r code/requirements.txt
```

## 2. Freeze the Repository List (once)
```bash
python code/utils/repo_fetcher.py   # Writes data/raw/frozen_repo_list.json
```
*The script queries the PyPI JSON API, selects the most‑downloaded packages, and saves the list. This file is committed to the repo, guaranteeing reproducibility.*

## 3. Clone the Selected Repositories
```bash
python code/utils/git_clone.py   # Clones each repo into data/raw/repos/
```
*Only public GitHub URLs are used; no authentication is needed.*

## 4. Extract Method Signatures & Human Docstrings
```bash
python code/extract.py
```
*Outputs `data/raw/repos/{repo_slug}.json` for each repository. Each file contains ≤ 1 000 public methods, their AST parameters, and any existing docstring (`null` if absent).*

## 5. Generate LLM Docstrings (4‑bit CPU)
```bash
python code/generate.py
```
*Loads `Salesforce/codegen-350M-mono` in 4‑bit mode, runs with temperature = 0.2, and writes `data/processed/generation_batch_{repo_slug}.json`. Each record includes `generated_docstring`, **`generation_status`** (`success`, `timeout`, or `error`), and **`error_message`** (if applicable) as defined in `contracts/dataset.schema.yaml`.*

## 6. Post‑process Generated Docs
```bash
python code/post_process.py
```
*Adds `needs_review` flags for empty/whitespace generations and propagates `generation_status`/`error_message` fields.*

## 7. Aggregate All Batches
```bash
python code/aggregate.py
```
*Creates `data/processed/results.json` containing every method record (≤ 20 000 rows).*

## 8. Compute Parameter Coverage
```bash
python code/analyze.py --step=coverage
```
*Writes `data/processed/results_with_coverage.json` with a `coverage_score` for each record.*

## 9. Compute Semantic Similarity (auxiliary)
```bash
python code/analyze.py --step=similarity
```
*Appends `semantic_similarity` and produces `data/processed/results_with_scores.json`.*

## 10. Perform Statistical Testing
```bash
python code/analyze.py --step=stats
```
*Runs the Wilcoxon signed‑rank test and writes `data/processed/final_report.json` that conforms to `contracts/results.schema.yaml` (fields: `total_pairs`, `human_scores`, `llm_scores`, `wilcoxon_statistic`, `wilcoxon_p_value`, `significance`, `execution_time_seconds`).*

## 11. Verify Reproducibility
```bash
bash scripts/verify_repro.sh   # Checks hashes, seeds, and that all outputs exist
```

## 12. Run the Test Suite
```bash
pytest tests/ -v
```
*Ensures that AST parsing, coverage calculation, and the end‑to‑end pipeline behave as expected, including tests for generation status handling and coverage edge cases.*

## Troubleshooting
- **Memory limit exceeded**: The pipeline aborts with a clear error; reduce the number of repositories in `frozen_repo_list.json` and re‑run.
- **4‑bit quantization error**: The job stops; verify that `bitsandbytes` is correctly installed (`pip install bitsandbytes==0.43.1`). No fallback is permitted per Constitution VII.
- **API rate limiting**: The scripts implement exponential backoff; if failures persist, increase the backoff max retries in `utils/api_helpers.py`.
- **Generation status ≠ success**: Check `generation_status` and `error_message` fields in the cleaned batch files for details.

You now have a fully reproducible workflow that can be executed on the free CI runner or any comparable CPU‑only environment.

---


