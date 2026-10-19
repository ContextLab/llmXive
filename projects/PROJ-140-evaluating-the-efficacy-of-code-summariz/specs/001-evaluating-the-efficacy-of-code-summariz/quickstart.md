# Quickstart: Evaluating the Efficacy of Code Summarization Techniques for Bug Localization

## 1. Project Layout

```
<project-root>/
├─ code/                     # Source code for the pipeline
│   ├─ __init__.py
│   ├─ main.py               # Entry point (`python -m code.main --mode sim`)
│   ├─ analysis/             # Statistical analysis modules
│   ├─ data_prep/            # Data download & summary generation utilities
│   └─ ...                    # Other sub‑packages (backend, utils, etc.)
├─ data/                     # All data artifacts
│   ├─ raw/                  # Raw downloads (Defects4J, etc.)
│   ├─ processed/            # Processed method extracts, summaries
│   ├─ interaction_logs/     # Anonymized participant interaction logs
│   ├─ analysis_results/     # CSV/JSON results of statistical analyses
│   └─ defects4j_version.txt # Pinned Defects4J version (see below)
├─ specs/                    # Specification documents for this feature
│   └─ 001-evaluating-the-efficacy-of-code-summarization-bug-localization/
│       ├─ plan.md
│       ├─ research.md
│       ├─ quickstart.md     # **You are reading this file**
│       └─ contracts/        # JSON‑Schema contracts for data validation
├─ tests/                    # pytest test suite
├─ docs/                     # Additional documentation (e.g., scope reduction)
└─ requirements.txt          # Project dependencies
```

## 2. Provenance

- **Defects4J version**: The study uses **Defects4J v2.0**. The exact version identifier is stored in `data/defects4j_version.txt` (the file contains the single line `2.0`).
- **Random seeds**: All stochastic components (sampling, Latin‑square design, bootstrapping, etc.) are seeded with **42** to guarantee reproducibility. The seed is hard‑coded in the relevant scripts; no external `.seed` file is required.

## 3. Running the Pipeline

The entire research pipeline can be executed from the command line. The core entry point is `code.main`.

```bash
# Install dependencies (once)
pip install -r requirements.txt

# Verify the entry point works (syntax check only)
python -m code.main --mode sim --help
```

The command above should display the help text and exit with a successful status, confirming that the module is importable and the CLI is correctly defined.

### Typical workflow

1. **Download Defects4J** (real data)  
   ```bash
   python code/download.py --source huggingface --dataset chathuranga-jayanath/defects4j-context-5-len-10000-prompt-3
   ```
   This creates `data/raw/defects4j.parquet` and writes the version string to `data/defects4j_version.txt`.

2. **Generate summaries (simulation mode)** – used for CI and testing  
   ```bash
   python code/summarize.py --mode sim
   ```

3. **Simulate participant interactions** (CI test)  
   ```bash
   python code/simulate_study.py --participants 12 --tasks-per-condition 10 --seed 42
   ```
   Output: `data/interaction_logs/anonymized_logs.csv`

4. **Run statistical analysis**  
   ```bash
   python code/analysis.py --input data/interaction_logs/anonymized_logs.csv --mode ci
   ```
   Output: `data/analysis_results/results.csv` (and accompanying JSON summary).

## 4. Reproducibility

- All random seeds are fixed (`42`).  
- The Defects4J version is pinned (`2.0`).  
- The pipeline can be reproduced on any machine with Python 3.11+ and the dependencies listed in `requirements.txt`.  
- The quickstart verification step (`python -m code.main --mode sim --help`) must succeed with exit code 0.