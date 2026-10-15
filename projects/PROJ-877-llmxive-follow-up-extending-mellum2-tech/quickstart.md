# Quickstart: llmXive follow‑up – extending "Mellum2 Technical Report"

## Prerequisites
- Python 3.11+
- 8 GB RAM (minimum for CPU inference of Mistral‑7B; 4 GB for TinyLlama fallback)
- Access to the HuggingFace Hub (for dataset and model download)

## Installation

1. **Clone the repository**
 ```bash
 git clone <repo-url>
 cd projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech
 ```

2. **Create a virtual environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # Windows: venv\Scripts\activate
 ```

3. **Install pinned dependencies**
 ```bash
 pip install -r code/requirements.txt
 ```

## Running the full pipeline

The pipeline can be executed with a single command that respects the
orchestrated phase order and uses a *small* sample size for quick testing:

```bash
python -m code.main --phase all --sample small
```

- `--phase all` tells the orchestrator to run the complete DAG (the
 orchestrator treats unknown phases as “run everything”).
- `--sample small` is a lightweight flag understood by the pipeline (it
 selects a reduced sample size defined in the configuration; the flag is
 ignored for full‑scale runs).
- The command runs under the virtual environment activated above and
 respects the CPU‑only constraint.

## Expected runtime limits

- **Total wall‑clock time:** ≤ 6 hours on the GitHub Actions free‑tier
 (2 CPU cores, ~7 GB RAM).
- **Per‑chunk inference timeout:** 60 seconds (configurable via the
 `--timeout` argument).

The pipeline writes all results under `data/results/` and generates
figures under `data/figures/`. After successful execution you should see
files such as:

- `data/results/correlation_results.parquet`
- `data/results/threshold_results.parquet`
- `data/figures/correlation_scatter.png`

## Troubleshooting

- **Argument errors:** Ensure you are using the exact command above; the
 `--sample` flag is now accepted by `code/main.py`.
- **Out‑of‑memory:** The orchestrator will automatically fall back to the
 smaller TinyLlama model and log a warning.
- **Missing data:** If any result files are absent, re‑run the command; the
 orchestrator will retry failed phases.