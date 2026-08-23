# Known Limitations and Constraints

## 1. Data Availability
The pipeline is designed for **real data only**. It does not include a built-in fallback to synthetic data for production runs.
- **Constraint**: If `data/config/real_data_sources.yaml` is missing, invalid, or the URL returns an error, the pipeline halts with a `RealDataFetchError`.
- **Mitigation**: Ensure a verified real data source is configured before execution. For local testing, use the explicit `--mode synthetic` flag in `ingest.py`.

## 2. Computational Resources
- **Time Limit**: The pipeline enforces a 6-hour timeout (`timeout=21600`) on the main analysis step. Large datasets (>100k samples) or complex compositional corrections (SpiecEasi) may exceed this limit.
- **Memory**: The current implementation loads the full dataset into memory. Datasets exceeding available RAM (~16GB) will cause a `MemoryError`. Streaming support is planned for future iterations.

## 3. Statistical Assumptions
- **Compositionality**: The pipeline assumes microbiome data is compositional (sums to a constant). If the input data is already normalized (e.g., CPM, TPM) and not compositional, the SparCC/SpiecEasi correction may be inappropriate.
- **Zero-Inflation**: The ZINB model is selected based on a >30% zero threshold. Datasets with moderate zero-inflation (<30%) but non-normal distribution may require manual method override.

## 4. Causal Language
The `report.py` module scans for causal language ("causes", "leads to"). If found, the pipeline halts. This prevents over-interpretation of correlational data but may flag legitimate conditional statements if not phrased carefully.

## 5. Taxonomic Hierarchy
Collinearity detection relies on the `data/raw/ncbi_taxonomy_dump.tsv`. If this file is missing or outdated, the "Perfect Multicollinearity" check for parent-child taxa pairs may be incomplete.

## 6. Reproducibility
- **Seeds**: All random processes (synthetic generation, bootstrapping) use fixed seeds defined in `code/analysis.py` and `code/diagnostics.py`.
- **Dependencies**: Pin versions in `requirements.txt` are critical. Changes in `scipy` or `statsmodels` versions may alter statistical results slightly.
