# Quickstart: Centroid‑Based Drift Detection for AgentDoG 1.5

## Prerequisites
- Python 3.11+, `git`, internet access (Hugging  Face + GitHub API).  
- GitHub Actions free‑tier runner (or equivalent local environment) with ≤ 7 GB RAM.

## Installation
```bash
git clone <repo‑url>
cd projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5
python -m venv venv && source venv/bin/activate
pip install -r code/requirements.txt
```

## Verify Setup (T010d evidence)
```bash
pytest tests/unit/ -v | tee data/processed/test_results.log
```
*Expected:* `test_config.py` asserts `RANDOM_SEED == 42`, `MAX_RAM_GB == 7`, `BATCH_SIZE == 64`, `DRIFT_THRESHOLD == 0.5`; `test_tooling.py` confirms presence of `pyproject.toml` with a `[tool.ruff]` section. The tee‑ed log is the committed proof of passing tests.

## Run the Pipeline

### 1. Data loading (HF taxonomy + GitHub novel corpus)
```bash
python code/data_loader.py --download
```
- Downloads `agentdog/safety-v1`.  
- Fetches ≥ 500 post‑2025 GitHub issue logs, scrubs PII, stores in `data/raw/novel_corpus.jsonl`.  

### 2. Build centroids & compute drift scores (US‑01)
```bash
python code/embeddings.py --generate-centroids
python code/embeddings.py --score
```
Outputs: `data/processed/centroids.json` and `data/processed/drift_scores.parquet`.

### 3. Prepare annotation batches (US‑02 part 1)
```bash
python code/main.py --prepare-annotation
```
Creates blinded JSONL files under `data/processed/annotation_batches/` and a uniform random sample of ≥ 100 logs spanning the full drift range.

### 4. **Manual step** – Human annotation
Three independent annotators label the files in `annotation_batches/`.  
Collect the results into `data/human_annotations.json` (exact schema required).

### 5. Statistical validation (US‑02) – requires `human_annotations.json`
```bash
python code/validation.py --validate
```
Produces `data/processed/metrics.json` and prints κ, Mann‑Whitney, logistic regression, chi‑squared results.

### 6. Baseline LLM comparison (US‑03)
```bash
python code/baseline_llm.py --baseline
```
Computes Flan‑T5 AUC‑ROC, checks baseline AUC ≥ 0.70, measures latency, performs **DeLong’s test** for AUC equivalence, and stores results in `metrics.json`.

### 7. Final report (US‑03 AC5)
```bash
python code/report.py --generate
```
Generates `data/processed/report.md` and `data/processed/metrics.json` with all required tables, ROC curves, and resource usage.

### One‑shot run (all steps except manual annotation)
```bash
python code/main.py --all
```
*Note:* The pipeline will stop with status `Incomplete` if `human_annotations.json` is missing or κ < 0.6, per Constitution Principle VI.

## Configuration (`code/config.py`)
```python
RANDOM_SEED = 42
MAX_RAM_GB = 7
BATCH_SIZE = 64          # verified fact, arXiv:2410.21676
DRIFT_THRESHOLD = 0.5    # pre‑registered operating point (calibrated in Phase 4)
HIGH_DRIFT_QUANTILE = None   # determined at runtime
LOW_DRIFT_QUANTILE = None    # determined at runtime
```

## Outputs
- `data/processed/drift_scores.parquet` – per‑log `drift_score` & `review_flag`.  
- `data/processed/centroids.json` – taxonomy centroids.  
- `data/processed/annotation_batches/` – blinded batches for annotators (include `log_length` and `source` for confound control).  
- `data/processed/metrics.json` – all statistical and resource metrics.  
- `data/processed/report.md` – human‑readable final report with figures.

## Troubleshooting
- **`agentdog/safety-v1` load failure**: blocking data‑availability gap; raise an issue – do **not** substitute another dataset.  
- **Missing `human_annotations.json`**: pipeline exits with `Incomplete`; obtain real annotations.  
- **Out‑of‑memory**: only reduce `BATCH_SIZE` *with documented justification* (deviates from the verified batch size).  
- **GitHub API rate limit** (60 req/h unauthenticated): the loader caches raw responses; rerun will resume where it left off.
