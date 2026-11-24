# Quickstart: Evaluating the Impact of Code Generation on Code Review Quality with LLM Assistance

## Prerequisites
- Python 3.11+
- Internet access (GitHub API, HuggingFace model hub)
- Approx. several GB RAM, Multiple CPU cores (standard GitHub Actions free tier)

## Installation
```bash
git clone <repo-url>
cd code
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Pipeline

### 1. Smoke test (fast, no model download)
```bash
python -m src.cli.main --run smoke
```
- Checks that the CLI starts, emits a `"cli_start"` event to `logs/pipeline.jsonl`, and produces `data/results/smoke_report.json`.  
- Exits 0 on success.

### 2. Run unit tests
```bash
pytest tests/ -v
```
All tests (unit, integration, contract) must pass.

### 3. Verify extraction on a small fixed set
```bash
python -m src.extraction.fetch_prs --test-set 10
```
Ensures each of the sampled PR JSONs contains non‑empty `diff`, `human_review_comments`, and `linked_issue_ids`. Logs `event: "test_set_ok"`.

### 4. Full analysis (adjust `--max-prs` if needed)
```bash
python -m src.cli.main --run all --max-prs 500 --seed 42
```
Executes the complete pipeline:
- Live GitHub extraction (respecting rate limits & streaming)
- Pre‑processing & triangulated ground‑truth construction
- LLM inference (StarCoder2‑3B, CPU‑only)
- Alignment, metrics, sensitivity sweep
- Runtime recording (`total_runtime_seconds`)
- Final JSON report (`data/results/final_report.json`) **including the required clarification that “affect” is interpreted as “correlate with” (FR‑014).**

### 5. Individual stages (for debugging)
```bash
python -m src.extraction.fetch_prs --repos microsoft/vscode pytorch/pytorch tensorflow/tensorflow --max-prs 200
python -m src.extraction.preprocess_and_ground_truth
python -m src.inference.run_inference
python -m src.analysis.sensitivity
python -m src.reporting.generate_report
```

## Output Artifacts
- `data/raw/` – Raw GitHub API JSON + `checksums.json`.
- `data/derived/` – Cleaned PRs, human annotations, LLM flags, LLM bug detections, alignments.
- `data/results/` – `runtime.json`, `final_report.json`, `sensitivity_analysis.csv`.
- `logs/pipeline.jsonl` – JSON‑lines log (must contain `"cli_start"`).
- `logs/timeout.log` – Records any global deadline skips.

## Troubleshooting
- **MemoryError** – Reduce `--max-prs` or lower per‑PR diff truncation length in `settings.py`.  
- **LLM JSON parse failure** – Automatic retries are performed; persistent failures are logged as `"llm_error"` and the PR is excluded.  
- **Timeout** – `RuntimeGuard` will log `"timeout"` and skip remaining PRs; total runtime is recorded in `runtime.json`.  
- **Insufficient PRs** – If fewer than 50 usable PRs are fetched, the pipeline aborts with `event: "audit_failure"`; consider adding another repository.  
- **Missing `"cli_start"` log** – Ensure `src/pipeline/logging_utils.py` is imported before any other pipeline code; the CLI entry point logs the event at the very beginning.

---


