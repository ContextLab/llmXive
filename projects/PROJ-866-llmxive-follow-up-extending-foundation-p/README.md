# llmXive Follow‑up: Extending "Foundation Protocol: A Coordination Layer for Agentic Society"

This repository contains the implementation of the simulation pipeline that quantifies the trade‑off between policy‑provenance compression and policy‑violation error rates in multi‑agent workflows.

## Table of Contents

- [Overview](#overview)
- [Quickstart](#quickstart)
- [Reproducibility and Verification](#reproducibility-and-verification)
- [License](#license)

## Overview

The project generates synthetic workflows, executes them under full‑context and compressed‑context regimes, and performs statistical analysis (GLMM, bootstrapping, multiple‑comparison correction) to identify the safe operating zone where the error‑rate remains ≤ 1 % [UNRESOLVED-CLAIM: c_48a54a44 — status=not_enough_info]. All steps are deterministic and fully reproducible.

## Quickstart

See `quickstart.md` for detailed installation instructions. The core pipeline can be run with a single command:

```bash
python code/main.py --generate --compress --analyze
```

This command will:

1. **Generate** `data/raw/workflows.json` (500 deterministic synthetic workflows).
2. **Execute** full‑context logs (`data/processed/full_context_logs.json`) and compressed‑context logs for a range of depths (`data/processed/compressed_context_logs.json`).
3. **Analyze** the results, producing:
 - `data/results/tradeoff_curve.csv`
 - `data/results/threshold_report.json`
 - `data/results/run_metrics.json`

## Reproducibility and Verification

### 1. Full Pipeline Command

The canonical command to reproduce all results is:

```bash
python code/main.py --generate --compress --analyze
```

- `--generate` creates the deterministic workflow set.
- `--compress` runs the compressed‑context engine across the predefined depth list.
- `--analyze` runs the statistical analysis and writes the final artefacts.

### 2. Checksum Verification

After the pipeline finishes, a reproducibility report is written to:

```
data/results/reproducibility_report.json
```

This JSON contains SHA‑256 hashes of **all files** under the `data/` directory for the two most recent runs:

```json
{
 "run1_hash": "<hex‑digest>",
 "run2_hash": "<hex‑digest>",
 "identical": true|false,
 "timestamp": "2023-10-27T10:00:00Z",
 "discrepancies": []
}
```

- **Identical**: `true` indicates the two runs produced exactly the same data artefacts, confirming deterministic behaviour.
- **Discrepancies**: If non‑empty, each entry describes a file whose hash differed between runs.

The hashes are computed by the utility script `code/utils/checksum_utils.py`. To manually recompute the hash for the current `data/` directory, run:

```bash
python code/utils/checksum_utils.py --output data/results/current_hash.json
```

Compare the resulting hash with `run1_hash` / `run2_hash` to ensure integrity.

### 3. Interpreting `data/results/reproducibility_report.json`

- **run1_hash / run2_hash**: Global SHA‑256 of the entire `data/` tree (concatenated file hashes).
- **identical**: When `true`, you can be confident that the pipeline is fully reproducible on the same hardware/software stack.
- **timestamp**: Indicates when the report was generated.
- **discrepancies**: An empty list means no file‑level mismatches; any entries would need inspection (e.g., re‑run the pipeline or investigate nondeterministic sources).

### 4. Invalid‑Workflow Exclusion Check (Task T067)

The pipeline automatically flags workflows that are internally inconsistent (e.g., contradictory policy constraints). These are marked with `"is_valid": false` in `data/raw/workflows.json` and must be excluded from the trade‑off analysis.

To verify that exclusion was performed correctly, run the dedicated validator:

```bash
python code/utils/verify_invalid_workflow_exclusion.py
```

The script cross‑references the `is_valid` flag against the rows used to build `data/results/tradeoff_curve.csv`. It produces:

- `data/results/invalid_exclusion_report.json` containing:
 ```json
 {
 "invalid_workflow_count": <int>,
 "excluded_count": <int>,
 "status": "PASS" | "FAIL"
 }
 ```
- A console summary indicating whether any invalid workflow contributed to the final CSV.

**Interpretation**:
- `invalid_workflow_count` = total number of workflows flagged as invalid.
- `excluded_count` = number of those that were successfully removed from the analysis.
- `status` = `"PASS"` when `excluded_count` equals `invalid_workflow_count`; otherwise `"FAIL"` and you should investigate the offending rows.

### 5. Summary of Reproducibility Artifacts

| Artifact | Description |
|----------|-------------|
| `data/raw/workflows.json` | Deterministic synthetic workflow definitions (seeded). |
| `data/processed/*.json` | Execution logs for full and compressed contexts. |
| `data/results/tradeoff_curve.csv` | CSV of context‑reduction vs. error‑rate with confidence intervals. |
| `data/results/threshold_report.json` | Safe‑operating‑zone threshold (≤ 1 % error) and bootstrap CI. |
| `data/results/reproducibility_report.json` | Global SHA‑256 hashes and identity check for two runs. |
| `data/results/invalid_exclusion_report.json` | Verification that invalid workflows were excluded. |

By following the steps above you can fully reproduce the study, verify data integrity, and confirm that invalid workflows have been correctly omitted from the final analysis.

## License

This project is licensed under the MIT License. See `LICENSE` for details.