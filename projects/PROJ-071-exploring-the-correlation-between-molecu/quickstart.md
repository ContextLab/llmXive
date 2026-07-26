# llmXive Pipeline - Quick Start Guide

## Overview

This guide helps you quickly set up and run the llmXive pipeline for exploring
the correlation between molecular complexity and degradation rates in pharmaceuticals.

## Quick Start

### 1. Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd PROJ-071-exploring-the-correlation-between-molecu

# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Full Pipeline

```bash
python code/run_pipeline.py
```

This will:
1. Ingest FDA-approved drug structures
2. Calculate molecular descriptors
3. Standardize degradation data
4. Perform correlation analysis
5. Generate visualizations and reports

### 3. Run Memory Profiling (T059)

```bash
python code/memory_profiler.py
```

This will:
1. Profile memory usage across all pipeline stages
2. Identify peak memory usage points
3. Generate `data/memory_profile.log`

### 4. Verify Outputs

```bash
# Check that all artifacts were created
ls -la data/
ls -la data/processed/
ls -la data/outputs/
```

Expected artifacts:
- `data/processed/structural_subset.csv`
- `data/processed/analysis_results.json`
- `data/memory_profile.log`
- `results_report.md`
- `reproducibility_log.json`

## Memory Profiling Details

### Why Profile Memory?

Memory profiling helps identify:
- Memory bottlenecks in the pipeline
- Potential out-of-memory errors
- Opportunities for optimization

### Key Stages to Profile

1. **Data Ingestion (T012, T016a)**: Loading and merging datasets
2. **Descriptor Calculation (T014)**: RDKit molecule processing
3. **Analysis (T022-T025)**: Statistical computations

### Interpreting Results

- **Peak Memory < 7GB**: Pipeline is within constraints
- **Peak Memory > 7GB**: May need optimization or larger instance
- **Stage-specific peaks**: Target optimization efforts

### Running Individual Stage Profiles

```python
# Profile descriptor calculation only
from memory_profiler import memory_usage
from descriptors import calculate_descriptors_batch

def profile_descriptors():
 # Load sample data
 import pandas as pd
 df = pd.read_csv("data/processed/structural_subset.csv")
 smiles_list = df["SMILES"].tolist()

 # Profile
 mem_usage, result = memory_usage(
 (calculate_descriptors_batch, (smiles_list,)),
 retval=True,
 interval=0.1
)

 print(f"Peak memory: {max(mem_usage):.2f} MB")
```

## Troubleshooting

### Memory Errors

If you encounter memory errors:
1. Run memory profiler to identify the bottleneck
2. Reduce dataset size for testing
3. Use streaming mode for large datasets
4. Clear intermediate variables

### Pipeline Fails at Data Availability Gate

If the pipeline fails at the data availability gate:
1. Check `data/gate_status.json` for details
2. Verify data source availability
3. Review `data_insufficiency_report.md`

### Missing Dependencies

```bash
# Verify all dependencies are installed
python code/verify_requirements.py
```

## Next Steps

1. Review `results_report.md` for analysis findings
2. Check `reproducibility_log.json` for reproducibility metadata
3. Run `tests/` to verify pipeline correctness
4. Consult `README.md` for detailed documentation

## Additional Resources

- Full documentation: `README.md`
- Task list: `tasks.md`
- API reference: `code/` module docstrings
- Memory profiling guide: `README.md` (Memory Profiling Guide section)