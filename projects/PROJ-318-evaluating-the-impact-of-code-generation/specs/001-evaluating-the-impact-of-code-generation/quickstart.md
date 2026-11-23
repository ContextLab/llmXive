# Quickstart Guide: Evaluating Code Generation Model Documentation Completeness

This guide walks you through running the full research pipeline on the GitHub Actions free‑tier environment (or locally on a comparable CPU‑only machine).

## Prerequisites
- **Python** ≥ 3.9 (CI runner uses 3.11)  
- **Git** (for cloning repositories)  
- **Internet access** (to fetch PyPI metadata, GitHub repos, and model weights)  
- **≤ 7 GB RAM** (free runner limit) – *No GPU required.*

## 1. Set Up the Environment
```bash
# Clone the project repository (if you haven't already)
git clone 
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
*The script queries the PyPI JSON API, selects the most‑downloaded packages, stratifies across three popularity tiers, adds a supplemental low‑tier sample, and saves the list. The file is committed to guarantee reproducibility.*

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

## 5. Generate LLM Docstrings (CPU full‑precision)
```bash
python code/generate.py
```
*Loads `Salesforce/codegen-350M-mono` in **full‑precision CPU** mode, runs with temperature = 0.2, deterministic seeds (`torch.manual_seed(42)`, `numpy.random.seed(42)`, `random.seed(42)`) via `seed_manager.py`, and writes `data/processed/generation_batch_{repo_slug}.json`. Each record includes `generated_docstring`, **`generation_status`** (`success`, `timeout`, `error`), and **`error_message`** if applicable.*

## 6. Generate Baseline Signature‑Copy Docs
```bash
python code/baseline_copy.py
```
*Creates `data/processed/baseline_batch_{repo_slug}.json` where `baseline_docstring` is the exact method signature. Used later as a control for circularity.*

## 7. Post‑process Generated Docs
```bash
python code/post_process.py
```
*Adds `needs_review` flags for empty/whitespace generations and propagates status fields.*

## 8. Aggregate All Batches
```bash
python code/aggregate.py
```
*Creates `data/processed/results.json` containing every method record (≤ 20 000 rows).*

## 9. Compute Parameter & Description Coverage
```bash
python code/analyze.py --step=coverage
```
*Writes `data/processed/results_with_coverage.json` with `parameter_coverage_score`, `description_coverage_score` (averaged over **all** parameters, zero for undocumented ones), and the **Composite Documentation Completeness Score** (`0.4 * ParameterCoverage + 0.6 * DescriptionCoverage`) for each record.*

## 10. Compute Semantic Similarity (auxiliary)
```bash
python code/analyze.py --step=similarity
```
*Appends `semantic_similarity_score` and produces `data/processed/results_with_scores.json`.*

## 11. Conduct Human‑Evaluation Sampling (FR‑017)
```bash
python code/human_eval.py
```
*Randomly samples a representative set of method pairs, collects 5‑point Likert ratings (simulated locally), and writes `data/processed/human_eval_results.json`. The script logs the average rating; the pipeline proceeds only if the average ≥ 4.0 (SC‑007).*

## 12. Perform Statistical Testing
```bash
# Primary method‑level Wilcoxon test on Composite Scores
python code/analyze.py --step=stats

# Exploratory repository‑level test (Bonferroni‑corrected)
python code/analyze.py --step=exploratory
```
*The script writes `data/processed/final_report.json` that conforms to `contracts/results.schema.yaml` (fields: `total_pairs`, `human_scores`, `llm_scores`, `baseline_scores`, `wilcoxon_statistic`, `wilcoxon_p_value`, `effect_size`, `significance`, `execution_time_seconds`).*

## 13. Verify Reproducibility
```bash
bash scripts/verify_repro.sh   # Checks hashes, seeds, and that all outputs exist
```

## 14. Run the Test Suite
```bash
pytest tests/ -v
```
*Ensures that AST parsing, coverage calculation, generation‑status handling, baseline copy generation, human‑evaluation sampling, and the end‑to‑end pipeline behave as expected, including tests for edge cases (malformed files, empty docstrings, rate‑limit retries, deterministic seed enforcement).*

## Troubleshooting
- **Memory limit exceeded**: The pipeline aborts with a clear error; reduce the number of repositories in `frozen_repo_list.json` and re‑run.  
- **Model load error**: Verify `torch` and `transformers` versions (`pip install torch==2.2.0 transformers==4.41.0`). No GPU fallback is permitted per Constitution VII.  
- **API rate limiting**: Scripts implement exponential backoff; if failures persist, increase `max_retries` in `utils/api_helpers.py`.  
- **Generation status ≠ success**: Inspect `generation_status` and `error_message` fields in the cleaned batch files for details.  
- **Low statistical power**: If total paired records < 30, the script logs a warning but proceeds; consider adding more low‑tier repositories.  
- **Human‑evaluation average below 4.0**: The pipeline will flag the failure; you may increase the sample size or re‑run with different annotators.

You now have a fully reproducible workflow that can be executed on the free CI runner or any comparable CPU‑only environment.

---


