# Quickstart: Evaluating the Efficacy of Code Summarization Techniques for Bug Localization

## Prerequisites

- Python 3.11+
- `git`
- Access to a terminal (Linux/macOS/WSL)
- **For Offline Generation**: A GPU machine (optional, only if regenerating LLM summaries)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd <project-dir>
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Study

The study consists of four phases: **Startup**, **Data Preparation**, **Simulation & Analysis**, and **Reproducibility Check**.

### Phase 0: Startup & Validation (Mandatory)
The system MUST perform a local loopback latency test before proceeding.
```bash
python code/simulation/latency_calibrator.py
```
*Output*: If the test passes (≤100ms), the script exits with code 0. If it fails, the script exits with code 1 and an error message. **No further steps will run if this fails.**

### Phase 1: Data Preparation
Download and validate the Defects4J dataset.
```bash
python code/download/fetch_defects4j.py
```
*Output*: `data/raw/defects4j/defects4j.parquet` (validated with checksum) and `data/defects4j_version.txt`.
*Note*: This script also verifies the dataset schema and logs a warning if `bug_report_text` is missing.

### Phase 2: Summary Generation (Offline)
*Note*: In the CI environment, LLM summaries are loaded from pre-generated cache. To regenerate (requires GPU/Offline), use:
```bash
# Only if you have a GPU environment set up
python code/generation/llm_summary.py --regenerate
python code/generation/rule_summary.py
```
*Output*: `data/processed/summaries/`

### Phase 3: Simulation & Analysis
Run the full pipeline (simulates participants, runs stats, generates results).
```bash
python code/main.py
```
*Outputs*:
- `data/interaction_logs/anonymized_logs.csv`
- `data/analysis_results/final_results.csv`
- `data/analysis_results/baseline_results.json`

### Phase 4: Reproducibility Check
Verify the results match the baseline.
```bash
python code/analysis/stats_engine.py --check-baseline
```

## CI/CD (GitHub Actions)

To run the analysis in a CI environment:
1. Push to the `main` branch.
2. The `test_reproducibility.yml` workflow will trigger.
3. It will run the full pipeline on a free-tier runner (CPU-only).
4. **Resource Monitoring**: The job will log RAM and CPU usage. It will fail if usage exceeds 7GB or runtime exceeds 6h.
5. Check the "Analysis" job for success/failure.

## Troubleshooting

- **Latency Calibration Failed**: Ensure your system clock is synchronized. The `latency_calibrator.py` requires <100ms precision. If this fails, the study cannot proceed.
- **LLM Summary Missing**: If running locally without pre-generated cache, ensure you have GPU access or skip the LLM condition (fallback to rule-based).
- **Permission Denied**: Ensure `data/consent/` is excluded from VCS and has `chmod 600` permissions.
- **Schema Mismatch**: If the Defects4J download fails schema verification, check the `verify_schema.py` log for missing fields. The study will proceed with code-only analysis if `bug_report_text` is missing.