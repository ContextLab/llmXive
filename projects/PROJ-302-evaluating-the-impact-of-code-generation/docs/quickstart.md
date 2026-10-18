# Quickstart Guide: Evaluating the Impact of Code Generation on Code Review Time

Step-by-step instructions to set up, run, and validate the research pipeline
for evaluating how LLM-generated code affects code review times.

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
extraction (LOC, radon complexity, CI build time, semantic similarity),
review-timestamp simulation, propensity-score matching with covariate
balance enforcement (SMD < 0.1), statistical testing, sensitivity analysis,
visualisation, report generation, and runtime measurement
(`data/processed/runtime_report.json`, total <= 6 h).

## 4. Project Structure

```
.
├── code/ # Source modules (data acquisition, analysis,...)
├── data/
│ ├── raw/ # Immutable streamed PR parquet files
│ ├── processed/ # Features, matched pairs, analysis results
│ ├── synthetic/ # Generated snippets + provenance
│ └── reports/ # JSON summaries, PDFs
├── docs/ # Documentation (this file)
├── tests/ # Unit and integration tests
└── requirements.txt # Pinned dependencies
```

## 5. Validation Checklist

- `results/setup_verification.json` reports all packages available.
- `data/processed/runtime_report.json` shows total <= 6 h.
- `data/processed/covariate_balance.json` shows all SMD < 0.1.
- `data/processed/analysis_results.json` conforms to
 `contracts/test_result.schema.yaml`.

## 6. Troubleshooting

- **Rate limiting**: export a valid `GITHUB_TOKEN`.
- **Memory errors**: reduce streaming batch size or limit PR count.
- **Matching failure**: inspect
 `data/processed/matching_failure_report.json` and adjust the caliper.
