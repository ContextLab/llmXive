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

The entry point orchestrates every step, writes checksums, validates schemas, runs the analysis, and produces plots **and** a deterministic verification log.

```bash
python -m code.pipeline.run_all --config code/config/study_config.yaml
```

### What the command does
1. **Download & verify** SART/Ospan task code from the OSF URLs (verified dataset block).  
2. **Validate** raw participant files against `contracts/dataset.schema.yaml` and `contracts/compliance.schema.yaml`.  
3. **Generate** `data/checksums.sha256` for all raw files.  
4. **Aggregate** daily compliance logs (`code/compliance/aggregate_compliance.py`).  
5. **Merge** baseline and post measurement records (`code/pipeline/merge_data.py`).  
6. **Run** the statistical analysis (`code/analysis/run_statistics.py`).  
7. **Generate** visualizations (`code/viz/generate_plots.py`).  
8. **Write** `results/statistical_summary.json` (single source of truth) and `results/pipeline.log` (includes a final line `STATUS: SUCCESS`).  

> **Important**: The pipeline expects **real participant data** in `data/raw/`. If the directory is empty, the pipeline will stop with a validation error, prompting you to collect the required baseline and post‑intervention measurements.

## Testing

Run the full test suite to confirm schema compliance and pipeline integrity:

```bash
pytest -v
```

- **Unit tests** verify scoring functions against OSF reference implementations.  
- **Contract tests** validate every output file against the JSON schemas in `contracts/`.  
- **Integration test** runs the end‑to‑end pipeline on a **real** dataset (if present) and checks that `pipeline.log` reports `STATUS: SUCCESS`.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `validation error` on a CSV | Row violates schema (e.g., missing field) | Inspect the validation report; correct the source file. |
| `checksum mismatch` | File was altered after checksum generation | Re‑run `python -m code.validation.generate_checksums` or regenerate the raw file. |
| Pipeline exits with non‑zero code | One of the scripts failed (e.g., missing data) | Check `pipeline.log` for the failing step; ensure all required raw files are present and correctly formatted. |
| Plots not appearing | `results/statistical_summary.json` missing required keys | Verify that the analysis step completed successfully; re‑run the pipeline. |
| `pipeline.log` missing `STATUS: SUCCESS` | Unexpected crash or early termination | Review the log for error messages; address the indicated issue and re‑run. |

---
