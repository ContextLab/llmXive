# Quickstart: Evaluating the Impact of Code Generation on Code Vulnerability Density

## Prerequisites

- Python 3.11, ~2 GB free disk, no GPU required.

## Setup

```bash
cd code
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Smoke run (50-file subset, US-1 independent test)

```bash
python -m src.pipeline --smoke 50
```

Verifies: manifest built, Bandit + Semgrep produce `data/derived/per_file_analysis.csv` with valid counts/CWE IDs, no crash or timeout. Output JSON summary printed to stdout.

## Full run

```bash
python -m src.pipeline
```

Runs all phases in order (ingest → analysis → density → stats → audit-sample → figures). Outputs:

- `data/derived/file_manifest.csv`, `findings.csv`, `per_file_analysis.csv`, `per_file_density.csv`, `audit_sample.csv`
- `results/tables/group_summary.csv`, `statistical_tests.csv`, `cwe_density_by_group.csv`, `resource_usage.csv`
- `results/figures/density_boxplot.{png,svg}`, `cwe_distribution.{png,svg}`

## Manual audit (FR-007)

Fill the `verdict` column of `data/derived/audit_verdicts.csv` (seeded stratified sample), then:

```bash
python -m src.audit --compute-metrics
```

writes precision/recall/FPR by group to `results/tables/audit_metrics.csv`.

## Tests

```bash
cd code && pytest
```

Includes contract tests against `specs/001-evaluating-the-impact-of-code-generation/contracts/*.schema.yaml` and the known-p-value synthetic tests (US-2, US-3).

## Expected failure mode

If no corpus source is reachable at ingest time, the pipeline exits non-zero with a data-availability error listing what was attempted. It never fabricates or synthesizes data.
