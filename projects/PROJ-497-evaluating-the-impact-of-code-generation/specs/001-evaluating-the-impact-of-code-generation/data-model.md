# Data Model: Evaluating the Impact of Code Generation Models on Code Vulnerability Density

## Entities

### CodeSample
Represents a single unit of code (generated or human) with attributes:
- `source_type`: str (LLM/Human)
- `model_name`: str (e.g., "starcoder", "codegen")
- `benchmark_name`: str (e.g., "humaneval", "mbpp")
- `task_id`: str (e.g., "HumanEval/0", "MBPP/1")
- `lines_of_code`: int
- `vulnerability_count`: int (raw)
- `adjusted_vulnerability_count`: float (adjusted for FPR, **sensitivity metric only**)
- `complexity_score`: float (Cyclomatic Complexity)
- `is_valid`: bool (passed benchmark tests)
- `file_path`: str (path to code file)

### VulnerabilityReport
Represents the output of a static analysis tool for a specific file:
- `file_path`: str
- `cwe_id`: str (e.g., "CWE-89")
- `severity`: str (Low/Medium/High)
- `line_number`: int
- `description`: str

### StatisticalResult
Represents the outcome of a hypothesis test:
- `test_type`: str (Permutation/ZINB)
- `p_value`: float
- `confidence_interval`: tuple (lower, upper)
- `effect_size`: float (IRR or Risk Ratio)
- `adjusted_p_value`: float (after FDR correction)
- `convergence_status`: str (Converged/Failed)
- `category`: str (e.g., "SQLi", "XSS") or "Overall"
- `power`: float (post-hoc power)
- `flag`: str (OK/UNDER_POWERED/INSUFFICIENT_DATA)

## Data Flow

1. **Raw Data**: `data/raw/humaneval.parquet`, `data/raw/mbpp.parquet` (downloaded benchmarks).
2. **Generated Code**: `data/generated/starcoder_humaneval/*.py`, `data/generated/codegen_mbpp/*.py`.
3. **Vulnerability Reports**: `data/processed/vuln_reports/starcoder_humaneval.json`, etc.
4. **Complexity Metrics**: `data/processed/complexity_metrics.csv` (Cyclomatic Complexity per sample).
5. **Adjusted Counts**: `data/processed/adjusted_counts.csv` (with FPR adjustments, **sensitivity only**).
6. **FPR Metrics**: `data/processed/fpr_metrics.json` (group-specific FPRs).
7. **Statistical Results**: `data/processed/stats_results.json` (Permutation/ZINB outputs).
8. **Visualizations**: `results/plots/*.png` (boxplots, bar charts).
9. **Report**: `results/summary.md` (final summary with stats, images, raw + sensitivity metrics).

## Constraints

- **Immutability**: Raw data never modified; derivations in new files.
- **Checksums**: All files in `data/` checksummed and recorded in `state/`.
- **Traceability**: Each `CodeSample` links to `file_path` and `task_id`; stats trace to `data/processed`.
- **Validation**: `CodeSample` requires `is_valid=True` for inclusion in analysis.
- **Primary Metric**: Statistical tests use `vulnerability_count` (raw). `adjusted_vulnerability_count` is for sensitivity analysis only.