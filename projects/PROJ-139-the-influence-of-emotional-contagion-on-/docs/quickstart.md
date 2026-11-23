# Quickstart Guide: The Influence of Emotional Contagion on Collective Decision-Making

## Project Layout

The repository follows a minimal, reproducible layout:

```
<project root>/
├── code/ # All source code (modules, scripts, tests)
├── data/
│ ├── raw/ # Unprocessed source files (e.g., Reddit JSONL)
│ └── processed/ # Derived artefacts (CSV, JSON, logs)
├── docs/ # Documentation, including this Quickstart and the paper draft
└── figures/ # Generated plots and visualisations
```

> **Note:** The `state/` directory is managed by the platform for checksum
> tracking and runtime logs; the project code does **not** create or modify
> this folder directly.

## Prerequisites

- Python 3.11 or higher
- Internet access (to fetch real data)
- (Optional) Reddit API credentials for the fallback data source

## Setup

```bash
# 1. Clone the repository and navigate to the project root
git clone <repo‑url>
cd projects/PROJ-139-the-influence-of-emotional-contagion-on-

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r code/requirements.txt

# 4. Download NLTK resources needed for VADER
python -c "import nltk; nltk.download('vader_lexicon')"
```

## Running a Minimal Sample

The pipeline can be exercised on a tiny real‑world sample without downloading the full dataset:

```bash
python -m code.analysis.run_pipeline --sample 5
```

This command:
1. Streams a few records from the public HuggingFace `reddit_comments` dataset.
2. Writes a CSV with the columns `id, subreddit, created_utc, body` to:
 `data/results/sample_run.csv`.
3. Completes in seconds and requires no Reddit API credentials.

Verify the output:

```bash
ls data/results/
# Expected file: sample_run.csv
head data/results/sample_run.csv
```

## Full Pipeline

When you are ready to run the complete analysis (data download, extraction,
sentiment scoring, modelling, etc.), execute:

```bash
python -m code.analysis.run_pipeline
```

The script will:
1. Create the required directories (`code/`, `data/raw/`, `data/processed/`, `docs/`, `figures/`).
2. Download Reddit threads for the configured subreddits.
3. Perform all downstream processing steps, producing the artefacts listed in the
 project documentation.

## Verification

After any run, you can check that the expected artefacts exist:

```bash
# Sample run verification
[ -f data/results/sample_run.csv ] && echo "Sample CSV created"

# Full run verification (partial list)
ls data/processed/
```

## Troubleshooting

- **Missing `sample_run.csv`** – Ensure the `datasets` library is installed
 (`pip install datasets`) and that you have internet connectivity.
- **Data download failures** – Check that your Reddit API credentials are set
 (environment variables `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`,
 `REDDIT_USER_AGENT`). The script will fall back to the Pushshift API; if all
 sources fail, it raises a clear `RuntimeError`.
- **Platform‑owned `state/` directory** – Do not modify files inside `state/`;
 it is automatically managed by the verification harness.