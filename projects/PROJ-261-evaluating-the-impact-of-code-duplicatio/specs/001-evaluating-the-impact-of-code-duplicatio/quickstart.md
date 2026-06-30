# Quick‑start guide for the code‑duplication impact study

This document describes the minimal steps required to reproduce the
end‑to‑end analysis. All commands are intended to be run from the
repository root.

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

## 2. Run the full pipeline

The single command below executes the complete workflow:

```bash
python code/main.py
```

The script will:

1. Download a 500 MB (or a reduced sample if bandwidth is limited) subset
 of the `codeparrot/github-code` dataset and store it at
 `data/raw/github-code-sample.csv`.
2. Compute AST clone‑density metrics and write them to
 `data/processed/clone_metrics.csv`.
3. Compute token‑level perplexity scores using the CodeGen model and write
 them to `data/processed/perplexity_scores.csv`.
4. Log any parse failures, memory usage, or other diagnostics to the
 appropriate locations under `data/`.

## 3. Verify outputs

After the pipeline finishes, you can confirm that the expected files are
present:

```bash
ls -l data/raw/github-code-sample.csv
ls -l data/processed/clone_metrics.csv
ls -l data/processed/perplexity_scores.csv
```

The unit and integration tests can be executed with:

```bash
pytest -q
```

If any test fails, consult the logs in `data/logs/` and `data/parse_failures.csv`
for details.