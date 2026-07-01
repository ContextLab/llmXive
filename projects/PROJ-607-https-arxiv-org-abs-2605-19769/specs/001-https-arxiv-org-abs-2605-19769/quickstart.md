# Quickstart: Reproduce & Validate OpenComputer

## 1. Prerequisites

- **OS**: Linux (GitHub Actions free-tier runner).
- **Docker**: Installed and running (`docker --version`).
- **Python**: 3.11+ installed.
- **Git**: Installed and configured.
- **Submodule**: The `external/OpenComputer` submodule must be initialized.
- **Human Inspectors**: Two independent researchers (human_01, human_02) and one arbitrator (human_03) must be available for the manual inspection phase.

## 2. Environment Setup

### 2.1. Initialize Submodule
Ensure the OpenComputer code is available:
```bash
git submodule update --init --recursive
```

### 2.2. Install Dependencies
Install Python requirements for the orchestration scripts:
```bash
pip install -r projects/607-reproduce-opencomputer/requirements.txt
# requirements.txt typically includes: pandas, pyyaml, pytest, ffprobe-utils
```

### 2.3. Configure Docker
Ensure the Docker daemon is running and the user has permissions to build images:
```bash
docker info
```

## 3. Execution Steps

### Step 1: Run Smoke Test (FR-001)
Validate the end-to-end pipeline with a single task.
```bash
cd projects/607-reproduce-opencomputer
bash scripts/run_smoke_test.sh --task audacity_export_wav_440 --backend docker
```
**Expected Output**: `results/smoke_report.json` with `status: "success"` or `"partial_success"`.

### Step 2: Run Batch Evaluation (FR-002)
Execute the 5-task batch.
```bash
bash scripts/run_batch_eval.sh --tasks 5 --agent claude_agent --verifier hardcode
```
**Expected Output**: `results/verification_report.json` containing results for 5 tasks.

### Step 3: Collect Artifacts (T022)
Extract generated files for manual inspection.
```bash
python scripts/collect_artifacts.py --source results/verification_report.json --dest results/blinded_artifacts/
```

### Step 4: Prepare Ground Truth (T023)
Generate the blinded inspection template.
```bash
python scripts/prepare_ground_truth.py --artifacts results/blinded_artifacts/ --output data/blinded_ground_truth.json
```
**Action Required**: 
1. Open `data/blinded_ground_truth.json`.
2. **Inspector 1** and **Inspector 2** must independently inspect each artifact using **distinct tools** (e.g., `ffprobe` for audio, `pandoc` for text).
3. Populate `inspector_1_verdict`, `inspector_1_notes`, `inspector_2_verdict`, `inspector_2_notes`.
4. If verdicts differ, **Arbitrator** updates `arbitration_verdict`.

### Step 5: Compare Verdicts (T024)
Merge results and calculate alignment.
```bash
python scripts/compare_verdicts.py --verifier results/verification_report.json --ground_truth data/blinded_ground_truth.json --output data/verification_results.csv
```

### Step 6: Generate Report (FR-004)
Create the final reproduction report.
```bash
python scripts/generate_report.py --data data/summary.json --results data/verification_results.csv --output docs/reproducibility/reproduction_report.md
```

## 4. Verification

To verify the pipeline worked correctly:
1.  Check `docs/reproducibility/reproduction_report.md` for the "Conclusion" section.
2.  Verify `data/summary.json` contains `alignment_consistency`.
3.  Ensure `data/blinded_ground_truth.json` contains notes from two distinct inspectors using tools.
4.  Ensure no "disk_quota_exceeded" or "container_timeout" errors in `results/` logs.

## 5. Troubleshooting

| Error | Cause | Solution |
| :--- | :--- | :--- |
| `docker: command not found` | Docker not installed. | Install Docker Engine. |
| `Image build failed` | Missing base image or network issue. | Check network; manually run `build_image.sh`. |
| `Disk quota exceeded` | >14 GB used. | Clean up old Docker images (`docker system prune`). |
| `Missing API Key` | Env var not set. | Set `ANTHROPIC_API_KEY` or skip agent. |
| `Inspection Discrepancy` | Inspectors disagree. | Ensure Arbitrator (human_03) resolves the conflict. |