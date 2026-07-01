# Data Model: Reproduce & Validate OpenComputer

## 1. Overview

This document defines the data structures used in the reproduction pipeline. All data is stored in JSON or CSV formats to ensure portability and ease of validation. The model supports the flow: `Task` → `Execution` → `Verification` → **Dual Manual Adjudication** → `Aggregation`.

## 2. Entity Definitions

### 2.1. Task
A unit of work defined in the OpenComputer submodule.
- **Source**: `external/OpenComputer/task_generator/`
- **Key Fields**: `task_id`, `app_name`, `expected_outcome`, `env_manifest`.

### 2.2. Execution Result
The raw output of running a task in a Docker container.
- **Source**: `run_eval.py` / `smoke_loop.py`
- **Key Fields**: `task_id`, `status` (success/failed/skipped), `error_message`, `artifact_path`.

### 2.3. Verification Report
The judgment of the hard-coded verifier.
- **Source**: `external/OpenComputer/evaluation/`
- **Key Fields**: `task_id`, `verifier_verdict` (pass/fail), `failure_reason`, `confidence`.

### 2.4. Blinded Ground Truth (Dual-Inspection)
The manual human adjudication of the artifact.
- **Source**: `prepare_ground_truth.py` (generated) + **Two Independent Inspectors** + Arbitration
- **Key Fields**: `task_id`, `inspector_1_verdict`, `inspector_2_verdict`, `arbitration_verdict`, `manual_judgment_notes` (must include tool evidence).

### 2.5. Aggregated Result
The merged view of verifier and manual results.
- **Source**: `compare_verdicts.py`
- **Key Fields**: `task_id`, `verifier_verdict`, `manual_verdict` (arbitration), `alignment` (match/mismatch), `discrepancy_reason`.

## 3. File Schemas

### 3.1. `data/verification_results.csv`
The primary row-level record of the experiment.

| Column | Type | Description | Allowed Values |
| :--- | :--- | :--- | :--- |
| `task_id` | string | Unique identifier for the task. | e.g., `audacity_export_wav_440` |
| `app_name` | string | Application used. | e.g., `audacity`, `gimp` |
| `execution_status` | string | Did the task run without system error? | `pass`, `fail`, `skipped` |
| `verifier_verdict` | string | Verdict from the hard-coded verifier. | `pass`, `fail` |
| `manual_verdict` | string | Verdict from **Arbitration** of dual inspection. | `pass`, `fail`, `uninspected` |
| `alignment` | string | Agreement between verifier and manual. | `match`, `mismatch`, `N/A` |
| `discrepancy_reason` | string | Explanation if mismatch. | e.g., `verifier_too_strict`, `artifact_corrupted` |
| `failure_reason` | string | If failed, why? | e.g., `file_not_found`, `timeout` |

### 3.2. `data/blinded_ground_truth.json`
The auditable record of manual inspection (Dual-Inspection Protocol).

```json
{
  "metadata": {
    "inspection_date": "2026-05-22",
    "inspector_1_id": "human_01",
    "inspector_2_id": "human_02",
    "arbitrator_id": "human_03",
    "sample_size": 5
  },
  "records": [
    {
      "task_id": "audacity_export_wav_440",
      "artifact_hash": "abc123...",
      "inspector_1_verdict": "pass",
      "inspector_1_notes": "Used ffprobe: frequency 440Hz, duration 5s.",
      "inspector_2_verdict": "pass",
      "inspector_2_notes": "Used ffprobe: frequency 440Hz, duration 5s.",
      "arbitration_verdict": "pass",
      "manual_judgment_notes": "Consistent tool-assisted verification."
    }
  ]
}
```

### 3.3. `data/summary.json`
Aggregated statistics and metadata.

```json
{
  "pipeline_version": "1.0.0",
  "opencomputer_commit": "sha1234",
  "docker_image_id": "sha5678",
  "total_tasks_attempted": 5,
  "tasks_passed_execution": 5,
  "tasks_passed_verification": 4,
  "tasks_passed_manual": 4,
  "alignment_consistency": "consistent",
  "limitations": [
    "Sample size N=5",
    "CPU-only environment",
    "No statistical significance testing",
    "Qualitative assessment only"
  ]
}
```

## 4. Data Flow

1.  **Ingest**: `run_batch_eval.sh` generates `verification_report.json`, validated against `contracts/verification_report.schema.yaml`.
2.  **Extract**: `collect_artifacts.py` moves artifacts to `results/blinded_artifacts/`.
3.  **Blind**: `prepare_ground_truth.py` creates `blinded_ground_truth.json` (initially with `uninspected` verdicts).
4.  **Inspect**: Two independent researchers inspect artifacts and populate `inspector_1_verdict` and `inspector_2_verdict`.
5.  **Arbitrate**: If needed, `human_03` updates `arbitration_verdict`.
6.  **Merge**: `compare_verdicts.py` reads both JSONs, validates output against `contracts/verification_results.schema.yaml`, and writes `verification_results.csv` and `data/summary.json`.
7.  **Report**: `generate_report.py` reads `summary.json` and `verification_results.csv` to produce `reproduction_report.md`.