# Quickstart: llmXive Follow-up: Structural Mismatch Cost in Heterogeneous Retrieval

## Prerequisites

- Python 3.11+
- Linux environment (required for `resource` module CPU accounting)
- Sufficient free disk space is required to accommodate the data and computational artifacts generated during the study.

## Installation

1. **Clone and Setup Environment**
   ```bash
   cd projects/PROJ-883-llmxive-follow-up-extending-omniretrieva/code/
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Download Datasets**
   Run the data preparation script to fetch verified datasets:
   ```bash
   python scripts/download_data.py
   ```
   *This downloads MS MARCO and DBpedia subsets to `data/raw/`.*

## Running the Experiment

Execute the full pipeline (Generation -> Execution -> Analysis):
```bash
python main.py
```

**What this does:**
1. Generates a set of synthetic queries (Text, Relational, Graph) with varying complexity.
2. Simulates CPU throttling via `resource` accounting and I/O throttling via delay queues.
3. Executes queries against simulated engines (Optimal vs. Mismatched routing).
4. Runs Segmented Regression and ANOVA.
5. Saves results to `data/results/` and updates `state/state.yaml`.

## Expected Outputs

- `data/results/raw_logs.jsonl`: Individual query metrics.
- `data/results/analysis_summary.csv`: Aggregated statistics.
- `data/results/figures/latency_interaction.png`: The key visualization.
- `data/results/stats_report.txt`: ANOVA F-statistics, p-values, and knee points.
- `state/state.yaml`: Artifact hashes for reproducibility.

## Verification

To verify the run completed successfully:
```bash
python scripts/verify_results.py
```
*Checks for:*
- Presence of all query records.
- Segmented Regression p-value < 0.05 (if hypothesis holds).
- Plot file existence.
- `state/state.yaml` update.

## Troubleshooting

- **Error: `resource` module not available**: Ensure you are running on Linux. macOS/Windows do not support `getrusage` in the same way.
- **Error: Dataset download failed**: Check network connection. URLs are verified in `research.md`.
- **Error: Timeout on all queries**: The CPU limit might be too strict. Check `config.py` for `CPU_TIME_LIMIT_SEC`.
- **Error: State file missing**: Ensure `state/` directory exists.