# Quickstart Guide: Evaluating the Impact of Code Generation on Code Review Time

## Prerequisites

- Python 3.11+
- Git
- A GitHub Personal Access Token (with `public_repo` scope), exported as
 `GITHUB_TOKEN` (optional but recommended to avoid REST API rate limits)
- Sufficient disk space (~15 GB for intermediate data)

## 1. Clone and Set Up the Environment

```bash
git clone <repository-url>
cd projects/PROJ-302-evaluating-the-impact-of-code-generation

python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt
```

All dependencies (including `statsmodels`) are pinned to exact versions in
`requirements.txt`, so a fresh install is reproducible.

## 2. Verify the Setup

```bash
python code/verify_setup.py
```

This checks the project skeleton (`code/`, `data/`, `tests/`, `docs/`),
validates that every required package is pinned in `requirements.txt`,
imports each dependency, and writes the evidence to
`results/setup_verification.json`. Exit code `0` indicates success.

## 3. Run-the-Pipeline

**Run-the-pipeline command:**

```bash
python code/main.py --full-run
```

This executes the full end-to-end pipeline: data acquisition (GitHub REST
API with exponential backoff), prompt engineering, synthetic LLM code
generation (CPU-only CodeLlama-7B-4bit-GGUF, <= 30 s per snippet), feature
extraction (LOC, radon complexity, CI build time, all‑MiniLM‑L6‑v2
similarity), review‑timestamp simulation, propensity‑score matching,
statistical testing, sensitivity analysis, visualisation, report
generation, and runtime measurement (`data/processed/runtime_report.json`,
total <= 6 h).

## 4. Project Structure

```
.
├── code/ # Source modules (data acquisition, analysis,...)
├── data/
│ ├── raw/ # Immutable streamed PR parquet files
│ ├── processed/ # Features, matched pairs, analysis results
│ ├── synthetic/ # Generated snippets + provenance
│ └── reports/ # PDFs, PNGs, JSON summaries, runtime_report.json
├── docs/
│ └── quickstart.md
├── tests/ # Unit and integration tests
└── requirements.txt # Pinned dependencies
```

## 5. Validation Checklist

- `results/setup_verification.json` reports all packages available.
- `data/processed/runtime_report.json` shows total <= 6 h. [UNRESOLVED-CLAIM: c_190b49e2 — status=not_enough_info]
- `data/processed/covariate_balance.json` shows all SMD < 0.1. [UNRESOLVED-CLAIM: c_66ab34f0 — status=not_enough_info]
- `data/processed/analysis_results.json` conforms to
 `contracts/test_result.schema.yaml`.

## 6. Troubleshooting

- **Rate limiting**: export a personal access token: `export GITHUB_TOKEN=your_token`.
- **Memory errors**: reduce streaming batch size or limit PR count.
- **Matching failure**: inspect `data/reports/matching_failure_report.json` for covariates with high SMD; you may increase the caliper or drop the most imbalanced covariate and re‑run.
- **LLM generation timeout**: the script retries up to 3 times; persistent failures are logged and the corresponding commit is excluded.
- **Evaluation PRs not reviewed**: ensure the reviewer panel has been invited; unreviewed PRs are logged and excluded after 48 h.
- **Runtime > 6 h**: review `runtime_report.json` for the longest stage; consider reducing the number of synthetic snippets (`--max-snippets`) or the number of target repositories.

## 7. Reproducibility Guarantees

- All random seeds are pinned (`utils.set_seed(<fixed_value>)`).
- External data are fetched from the GitHub API with a deterministic list; their cryptographic hash checksums are recorded.
- The CodeLlama model version and generation parameters are stored alongside each snippet.
- Every figure and statistic in the PDF can be traced back to a single row in a Parquet/JSON artifact.

Enjoy your reproducible study!