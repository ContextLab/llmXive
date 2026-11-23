# Deployment Guide

## Environment Setup

1. **Dependencies**: Ensure all packages in `requirements.txt` are installed.
 ```bash
 pip install -r requirements.txt
 ```
2. **antiSMASH**: Must be installed system-wide and accessible via `antismash` command.
3. **Environment Variables**: Set required keys in `.env` or system environment.
 ```bash
 export NCBI_API_KEY=your_key
 export DATA_ROOT=/path/to/data
 ```

## Running the Pipeline

### Local Execution
```bash
python -m code.cli.main
```

### CI/CD Integration
- **Test Stage**: `pytest tests/unit/ tests/integration/`
- **Lint Stage**: `ruff check code/`
- **Format Stage**: `black --check code/`

### Output Verification
After execution, verify:
1. `data/processed/aligned_matrix.csv` exists and has > 0 rows.
2. `data/processed/final_report.md` contains "PGLS R²" and "Sensitivity Analysis".
3. `state/projects/PROJ-198-*.yaml` is updated with new checksums.

## Troubleshooting

- **antiSMASH not found**: Ensure it is in PATH.
- **Network Timeout**: Check `NCBI_API_KEY` and internet connection.
- **Alignment Failure**: Verify species names match between genomic and metabolomic sources.
