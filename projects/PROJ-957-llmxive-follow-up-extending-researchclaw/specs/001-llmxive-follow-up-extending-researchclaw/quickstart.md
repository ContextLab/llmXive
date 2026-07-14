# Quickstart: llmXive follow-up: extending "ResearchClawBench: A Benchmark for End-to-End Autonomous Scientific Re"

## Prerequisites

- Python 3.11+
- Git
- GitHub Actions Runner (or local environment matching 2-core, 7GB RAM constraints)

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-957-llmxive-follow-up-extending-researchclaw
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Data Preparation

1. **Fetch Dataset**:
   Run the data loader to fetch ResearchClawBench.
   ```bash
   python code/data/loader.py --fetch
   ```
   *Note: If the dataset is not available via a verified URL, this step will abort with a critical error.*

2. **Filter Tasks**:
   Select the 10 tasks with "experimental protocol mismatch".
   ```bash
   python code/data/filter.py --mode protocol_mismatch --limit 10
   ```
   This creates `data/processed/10_tasks_protocol_mismatch.json`.

## Running the Experiment

1. **Execute Agents**:
   Run the full experiment (7 agents × 2 conditions × 10 tasks).
   ```bash
   python code/main.py --run_experiment
   ```
   - **Timeout**: 6 hours per run.
   - **Concurrency**: 7 agents.
   - **Total Budget**: 24 hours.

2. **Monitor Logs**:
   Check `results/logs/` for execution status.

## Analysis & Reporting

1. **Score Runs**:
   Apply the rubric to all execution logs.
   ```bash
   python code/scoring/engine.py
   ```

2. **Run Statistical Tests**:
   Perform paired tests and TOST.
   ```bash
   python code/analysis/stats.py
   ```

3. **Generate Report**:
   ```bash
   python code/analysis/report.py
   ```
   Outputs: `results/paired_scores.json`, `results/failure_mode_audit.csv`, and a summary report.

## Verification

1. **Contract Test**:
   Verify the rubric scores dummy outputs correctly.
   ```bash
   python code/scoring/dummy_test.py
   ```

2. **Checksum Verification**:
   Verify data integrity.
   ```bash
   python code/data/checksum.py --verify
   ```

## Troubleshooting

- **Timeout Errors**: If runs exceed 6 hours, they are logged as "Timeout" and excluded.
- **Dataset Missing**: If "protocol mismatch" metadata is missing, the system aborts (FR-006).
- **Scaffold Conflict**: If a template conflicts with task constraints, the run is excluded and logged.
