# Quickstart: Evaluating the Impact of Code Generation on Code Review Quality with LLM Assistance

## Prerequisites

- Python 3.11+
- Internet access to GitHub (API) and HuggingFace (model download)
- A modest number of CPU cores, sufficient RAM, and adequate disk space (comparable to the GitHub Actions Free Tier).

## Installation

1. **Clone the repository** and `cd code/`.
2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *`requirements.txt` pins `transformers`, `datasets`, `scikit-learn`, `scipy`, `pandas`, `pyyaml`, `pytest`, `numpy`, `torch` (CPU wheel), and `detectgpt`.*

## Running the Pipeline

All commands run from the repository root (`code/`).

### 1. Smoke test (multi‑PR fixture, fast, no model download)
```bash
python -m src.cli.main --run smoke
```
Exits with a successful status and produces `data/results/smoke_report.json`.

### 2. Run tests
```bash
pytest tests/ -v
```
Runs unit, integration, and contract tests. Must exit 0.

### 3. Initial PR Extraction Verification (US‑1 Acceptance)
```bash
python -m src.extraction.fetch_prs --test-set 10
```
Checks that each PR in the set contains non‑empty `diff`, `human_review_comments`, and `linked_issue_ids`. Exits 0 on success (addresses spec_coverage‑9f6f571f).

### 4. Full Analysis (adjustable PR count)
```bash
python -m src.cli.main --run all --max-prs 500 --seed 42
```
Executes the full pipeline:
- Live GitHub API fetch for the 3‑5 specified repos,
- Pre‑processing & ground‑truth construction,
- LLM inference (StarCoder (subsequent generation)‑3B float16),
- Alignment, metrics, sensitivity sweep,
- Runtime recording (`data/results/runtime.json`),
- Final report (`data/results/final_report.json`).

The effective random seed is logged in `logs/pipeline.jsonl` (event `"seed_used"`).

### 5. Individual phases (debugging)

```bash
python -m src.extraction.fetch_prs --repos microsoft/vscode pytorch/pytorch tensorflow/tensorflow --max-prs 500
python -m src.extraction.preprocess_and_ground_truth
python -m src.inference.run_inference
python -m src.analysis.sensitivity
python -m src.reporting.generate_report
```

## Output Artifacts

- `data/raw/` – Raw GitHub API JSON payloads + `checksums.json`.
- `data/derived/prs_cleaned.json`
- `data/annotations/human_annotations.json`
- `data/derived/llm_code_flags.json`
- `data/derived/llm_bugs.json`
- `data/derived/alignments.json`
- `data/derived/metrics_threshold_0.85.json`
- `data/results/runtime.json` – Total wall‑clock time (seconds) **and** `total_runtime_seconds` field.
- `data/results/final_report.json` – Consolidated statistical report (associational framing, effect sizes, limitations, seed provenance).
- `data/results/sensitivity_analysis.csv`
- `logs/pipeline.jsonl`, `logs/timeout.log`

## Troubleshooting

- **Memory error:** Reduce `--max-prs` or the per‑PR diff truncation limit in `src/config/settings.py`.
- **JSON parse error from LLM:** Automatic retry (≤2, 1 s delay); persistent failures mark the PR `"error"` and exclude it from metrics.
- **Dataset missing columns:** The Data Audit phase will abort with a log entry (`event: "audit_failure"`). Ensure the target repositories expose review comments and linked issues.
- **Timeout:** The global deadline triggers graceful skip of remaining PRs (logged to `logs/timeout.log`). Runtime is recorded in `data/results/runtime.json`.
- **Low prevalence of LLM‑generated code:** If `is_llm_generated` flag rate < 1 %, the subgroup analysis will be omitted with a note in the final report.

