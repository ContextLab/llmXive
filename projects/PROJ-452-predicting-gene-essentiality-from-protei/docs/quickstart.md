# Quick Start Guide: Predicting Gene Essentiality from Protein Interaction Network Topology

This guide provides the exact steps to set up the environment, fetch real data, run the analysis pipeline, and verify reproducibility for the PROJ-452 project.

## 1. Environment Setup

Ensure you have Python 3.11+ installed.

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Data Fetching

The pipeline fetches data from real sources (STRING, DEG, OpenTree). Ensure your network connection is stable.

```bash
# Run the main pipeline (this triggers data fetching)
python code/main.py
```

**Note:** The first run will download the phylogenetic tree and PPI networks. This may take several minutes depending on network speed.

## 3. Pipeline Execution

To run the full analysis (Correlation, Null Models, PGLS, Sensitivity):

```bash
python code/main.py
```

To run a dry-run (fetch data only, no analysis):

```bash
python code/main.py --dry-run
```

To run sensitivity analysis only:

```bash
python code/main.py --sensitivity-only
```

## 4. Reproducibility Verification

After the pipeline completes, verify the outputs:

1. Check `results/correlations.json` for valid Spearman ρ and p-values.
2. Check `results/pgls_results.json` for PGLS statistics (if tree was fetched).
3. Check `results/sensitivity_report.md` and `results/sensitivity_summary.json` for stability metrics.
4. Run `python code/hash_checker.py` to generate `state/` hashes.

## 5. Troubleshooting

This section lists known error codes, log messages, and resolution steps based on the implementation of tasks T073, T074, T075, and T076.

### Data Fetching Errors (T073)

| Log Message / Error Code | Cause | Resolution Steps |
|:--- |:--- |:--- |
| `DataFetchError: STRING API failed for organism {id}` | The STRING API returned a 404, 500, or timed out for the specific organism ID. | 1. Check network connectivity.<br>2. Verify the organism ID in `code/config.py` matches the STRING database format (e.g., '9606' for Human).<br>3. Wait 60s and retry. The pipeline will skip this organism and continue with others. |
| `DataFetchError: DEG fetch failed` | The primary FTP or API endpoint for DEG is unreachable. | 1. Check firewall settings for FTP/HTTP access.<br>2. Verify the URL `ftp://ftp.ncbi.nlm.nih.gov/pub/microarray/deg/` is accessible in a browser.<br>3. If persistent, check `research.md` for alternative mirror URLs. |

### ID Mapping Errors (T074)

| Log Message / Error Code | Cause | Resolution Steps |
|:--- |:--- |:--- |
| `DataFetchError: ID mapping failed for {organism}` | BioMart API failed, and the secondary Gene Symbol fallback also failed (coverage < 10%). | 1. Check `results/mapping_coverage.json` to see the exact coverage percentage.<br>2. Ensure `code/config.py` has the correct organism ID.<br>3. If BioMart is down, wait and retry. The fallback uses strict case-sensitive matching, so ensure gene names in DEG match the reference. |
| `Warning: Low mapping coverage ({percent}%)` | Primary mapping succeeded but coverage is low. | 1. Review `results/mapping_coverage.json`.<br>2. If coverage is < 10%, the pipeline will raise an error (T074). If it is between 10-50%, the analysis proceeds with a warning. Consider manually curating the gene list if results are unexpected. |

### Sensitivity Analysis Errors (T075)

| Log Message / Error Code | Cause | Resolution Steps |
|:--- |:--- |:--- |
| `Warning: Threshold {val} skipped for {organism}` | Data fetch or centrality calculation failed for a specific confidence threshold. | 1. Check `results/sensitivity_summary.json` for the `error_reason` field.<br>2. Common causes: Network too sparse (edges < 500) or data fetch timeout.<br>3. The pipeline records the failure as `null` in the summary rather than crashing. |
| `Warning: Sensitivity loop integrity check failed` | The loop failed to process all defined thresholds for an organism. | 1. Verify `code/config.py` `CONFIDENCE_THRESHOLDS` list is valid (e.g., `[500, 700, 900]`).<br>2. Ensure no network connectivity issues interrupted the loop. |

### PGLS / Model Convergence Errors (T076)

| Log Message / Error Code | Cause | Resolution Steps |
|:--- |:--- |:--- |
| `PGLS model failed to converge for {organism_list}` | `statsmodels` raised a singular matrix or convergence error, often due to small sample size or collinearity. | 1. Check `results/pgls_results.json` for the `failure_reason` field.<br>2. Ensure the phylogenetic tree (`data/phylogeny/tree.newick`) is valid and contains tips for the organisms with data.<br>3. If sample size (n) < 10, the pipeline skips PGLS automatically (FR-009). |
| `Warning: Power insufficient: n={count}` | The number of organisms with valid correlation data is less than 10. | 1. This is a statistical limitation, not a code error.<br>2. The PGLS result will be omitted from the output JSON.<br>3. To proceed, you must include more organisms in `code/config.py` or wait for more data sources to be processed. |

### Network Topology Errors (T070)

| Log Message / Error Code | Cause | Resolution Steps |
|:--- |:--- |:--- |
| `Warning: Network too sparse for {organism} at threshold {val}` | The confidence threshold resulted in a network with < 500 edges. | 1. Centrality metrics are set to `NaN` for this organism/threshold.<br>2. This is recorded in `results/sensitivity_summary.json`.<br>3. Consider lowering the confidence threshold in `code/config.py` if biological relevance allows. |

## 6. Output Files Reference

- `results/correlations.json`: Spearman correlations and empirical p-values.
- `results/pgls_results.json`: Phylogenetic Generalized Least Squares results.
- `results/sensitivity_report.md`: Human-readable stability report.
- `results/sensitivity_summary.json`: Machine-readable stability metrics.
- `results/topology_validation.json`: Scale-free topology verification.
- `state/projects/PROJ-452-*.yaml`: Reproducibility hashes.