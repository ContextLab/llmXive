# Quickstart: The Impact of Digital Decluttering on Cognitive Performance and Well‑being

## Prerequisites
- Python 3.11 or newer
- `pip` (or a virtual‑environment manager)
- Git

## Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd projects/PROJ-249-the-impact-of-digital-decluttering-on-co
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Full Pipeline

The single entry‑point orchestrates every step, writes checksums, validates schemas, runs the analysis, and produces plots **and** a deterministic verification log.

```bash
python -m code.pipeline.run_all --config code/config/study_config.yaml
```

### What the command does
1. **Download & verify** SART/Ospan task code from the OSF URLs (verified dataset block).  
2. **Generate synthetic baseline & post data** (for CI verification).  
3. **Create `data/checksums.sha256`** for all raw files.  
4. **Validate** raw files against `contracts/dataset.schema.yaml` and `contracts/compliance.schema.yaml`.  
5. **Aggregate compliance logs** (`code/compliance/aggregate_compliance.py`).  
6. **Merge baseline & post measurements** (`code/pipeline/merge_data.py`).  
7. **Run statistical analysis** (`code/analysis/run_statistics.py`).  
8. **Generate visualizations** (`code/viz/generate_plots.py`).  
9. **Write `results/statistical_summary.json`** (single source of truth) and **`results/smoke_results.json`** (full‑field example).  
10. **Append a deterministic `pipeline.log`** containing timestamps for each stage and a final line `STATUS: SUCCESS`.

All steps are deterministic; the final log can be inspected by the test suite (`tests/integration/test_pipeline_success.py`) to confirm successful execution.

## Testing

Run the full test suite to confirm schema compliance and pipeline integrity:

```bash
pytest -v
```

- **Unit tests** verify scoring functions against OSF reference implementations.  
- **Contract tests** validate every output file against the JSON schemas in `contracts/`.  
- **Integration test** runs the end‑to‑end pipeline and checks that `pipeline.log` reports success and that `results/smoke_results.json` contains all required fields.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `validation error` on a CSV | Row violates schema (e.g., missing field) | Inspect `validation_report.csv` for the offending row; correct the source file. |
| `checksum mismatch` | File was altered after checksum generation | Re‑run `python -m code.validation.generate_checksums` or regenerate the raw file. |
| Pipeline exits with non‑zero code | One of the scripts failed (e.g., missing dependency) | Check `pipeline.log` for the failing step; ensure all dependencies are installed and the random seed is set. |
| Plots not appearing | `results/statistical_summary.json` missing required keys | Verify that the analysis step completed successfully; re‑run the pipeline. |
| `pipeline.log` missing `STATUS: SUCCESS` | Unexpected crash or early termination | Review the log for error messages; address the indicated issue and re‑run. |

---


