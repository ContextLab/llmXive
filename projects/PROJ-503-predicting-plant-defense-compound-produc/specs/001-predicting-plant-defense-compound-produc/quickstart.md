# Quickstart: Predicting Plant Defense Compound Production from Publicly Available Genomic and Transcriptomic Data

## Prerequisites

- Python 3.11+ installed
- Git for version control
- GitHub account with Actions access (free tier)
- Access to GEO and Metabolomics Workbench (public, no credentials required)

## Quick Start Commands

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/<org>/<repo>.git
cd <repo>/projects/PROJ-503-predicting-plant-defense-compound-produc

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

### 2. Configure Dataset Accessions

Edit `data/sources.yaml` to specify the GEO series IDs and Metabolomics Workbench experiment IDs:

```yaml
datasets:
  - name: arabidopsis_expression
    source: GEO
    accession: GSE[deferred]  # Replace with actual accession
    download_date: 2026-06-24
    preprocessing_version: 1.0.0
  - name: solanum_expression
    source: GEO
    accession: GSE[deferred]  # Replace with actual accession
    download_date: 2026-06-24
    preprocessing_version: 1.0.0
  - name: arabidopsis_metabolites
    source: MetabolomicsWorkbench
    accession: MW[deferred]  # Replace with actual accession
    download_date: 2026-06-24
    preprocessing_version: 1.0.0
  - name: solanum_metabolites
    source: MetabolomicsWorkbench
    accession: MW[deferred]  # Replace with actual accession
    download_date: 2026-06-24
    preprocessing_version: 1.0.0
```

### 3. Run the Pipeline

```bash
# Run the full pipeline (E2E)
python code/main.py

# Or run individual phases
python code/main.py --phase download    # Phase 1: Data acquisition
python code/main.py --phase preprocess  # Phase 2: Normalization, feature selection
python code/main.py --phase model       # Phase 3: Modeling, evaluation
python code/main.py --phase log         # Phase 4: Runtime logging, output generation
```

### 4. Validate Outputs

```bash
# Run contract tests
pytest tests/contract/

# Verify checksums
python code/validation/checksum_validator.py

# Check pairing rate
python code/validation/pairing_validator.py
```

## Expected Outputs

| Output | Location | Description |
|--------|----------|-------------|
| Expression matrix | `data/processed/expression_matrix.csv` | Normalized, pathway-filtered gene expression |
| Metabolite matrix | `data/processed/metabolite_matrix.csv` | Log-transformed, paired metabolite concentrations |
| Model artifacts | `outputs/model_artifact.pkl` | Serialized Ridge Regression models |
| CV metrics | `outputs/cv_metrics.csv` | RMSE, Pearson r per metabolite |
| Permutation results | `outputs/permutation_results.csv` | p-values, Bonferroni-corrected |
| Logs | `logs/` | Pairing mismatches, feature filtering, runtime |

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| E-PAIRING error | <95% sample-level pairing | Verify GEO and MW accessions have overlapping sample IDs |
| E-CHECKSUM error | Download corruption | Re-download; check network; verify SHA-256 |
| E-TIMEOUT error | Runtime > 4 hours | Reduce sample size; optimize code; check for infinite loops |
| E-RETENTION error | <75% pathway genes retained | Check KEGG annotation coverage; use ortholog fallback |
| E-NEGATIVE error | Negative expression values | Check normalization; exclude affected samples |
| E-PATHWAY error | Gene not in defense pathways | Verify KEGG pathway mapping; check species annotation |
| E-CORRELATION error | Correlation below threshold | Report achieved correlation with power context; not a hard failure |
| E-SIGNIFICANCE error | Permutation p-value not significant | Report non-significant results; document power limitation |
| ImportError | Missing dependencies | Re-run `pip install -r code/requirements.txt` |

## Running on GitHub Actions

The pipeline is configured to run on GitHub Actions free-tier runners:

```yaml
# .github/workflows/pipeline.yml (created by Implementer Agent)
name: Plant Defense Pipeline
on: [push, workflow_dispatch]
jobs:
  run-pipeline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r code/requirements.txt
      - name: Run pipeline
        run: python code/main.py
        timeout-minutes: 240  # 4 hours
```

## Next Steps

1. **Verify Dataset Accessions**: Update `data/sources.yaml` with actual GEO and Metabolomics Workbench IDs
2. **Review Research**: Read `research.md` for methodological details and limitations
3. **Check Data Model**: Review `data-model.md` for schema specifications
4. **Run Tests**: Execute contract tests to validate data formats
5. **Implement**: Follow `tasks.md` (Phase 2 output) for implementation tasks