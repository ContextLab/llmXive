# Quickstart: Zero-Shot Drift Detection

## Prerequisites

- Python 3.11+, git, internet access (Hugging Face + GitHub API).

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5
python -m venv venv && source venv/bin/activate
pip install -r code/requirements.txt
```

## Verify Setup (T010d evidence)

```bash
pytest tests/unit/ -v | tee data/processed/test_results.log
```

Expected: `test_config.py` asserts `RANDOM_SEED == 42`, `MAX_RAM_GB == 7`, `BATCH_SIZE == 64`, `DRIFT_THRESHOLD == 0.5`; `test_tooling.py` asserts `pyproject.toml` with a `[tool.ruff]` section. The tee'd log is the committed proof of passing tests.

## Run the Pipeline

```bash
# 1. Data loading (agentdog/safety-v1 + GitHub novel corpus), checksums
python code/data_loader.py --download

# 2. Centroids + drift scores (US-01)
python code/embeddings.py --generate-centroids
python code/embeddings.py --score

# 3. Stratification, blinded annotation batches, full-range sample
python code/main.py --prepare-annotation

# 4. [MANUAL] Three annotators label data/processed/annotation_batches/;
#    results collected into data/human_annotations.json

# 5. Statistical validation (US-02) — requires human_annotations.json
python code/validation.py --validate

# 6. Baseline comparison (US-03)
python code/baseline_llm.py --baseline

# 7. Final report (US-03 AC5)
python code/report.py --generate
```

Or all automated steps at once:

```bash
python code/main.py --all
```

## Configuration (`code/config.py`)

```python
RANDOM_SEED = 42
MAX_RAM_GB = 7
BATCH_SIZE = 64          # verified fact, arXiv:2410.21676
DRIFT_THRESHOLD = 0.5    # pre-registered operating point (FR-002)
HIGH_DRIFT_QUANTILE = None   # [deferred]
LOW_DRIFT_QUANTILE = None    # [deferred]
```

## Outputs

- `data/processed/drift_scores.parquet` — per-log drift scores + review flags
- `data/processed/centroids.json` — taxonomy centroids
- `data/processed/annotation_batches/` — blinded batches for annotators
- `data/processed/metrics.json`, `data/processed/report.md` — final metrics and report

## Troubleshooting

- **`agentdog/safety-v1` load failure**: blocking data-availability gap; surface for scope revision — do not substitute another dataset.
- **Missing `data/human_annotations.json`**: pipeline reports status `Incomplete` and exits non-zero (Constitution Principle VI). No simulated annotations.
- **OOM**: reduce batch size below 64 only with documented justification (deviates from the verified batch size).
- **GitHub API rate limit**: unauthenticated limit is 60 req/h; the seeded acquisition script resumes across runs and caches raw responses in `data/raw/`.
