# Quickstart Guide: llmXive Pipeline

This guide provides the commands to run the full llmXive pipeline end-to-end.

## Prerequisites

- Python 3.11+
- Virtual environment with dependencies installed (`pip install -r requirements.txt`)

## Execution

Run the full pipeline with the following command:

```bash
python -m code.main --seed 42
```

This command executes the following stages in order:
1. **Code Drift Check**: Verifies code integrity.
2. **Oracle Generation**: Parses source code and builds the state-transition oracle.
3. **Rule Extraction**: Extracts logical rules from CoT traces.
4. **Divergence Analysis**: Classifies errors and calculates metrics.
5. **Final Reporting**: Aggregates all results into `data/processed/final_report.json`.

## Individual Stages

You can also run specific stages:

```bash
# Generate Oracle
python -m code.main --stage=oracle

# Extract Rules
python -m code.main --stage=rules

# Analyze Divergence
python -m code.main --stage=diverge

# Generate Final Report
python -m code.main --stage=report
```

## Output Artifacts

The pipeline produces the following artifacts in `data/processed/`:
- `oracle_graph.json`: The deterministic state-transition oracle.
- `extracted_rules.json`: Rules extracted from CoT traces.
- `divergence_report.json`: Classification of divergence types.
- `rule_precision.json`: Precision metric for extracted rules.
- `cot_quality_scores.json`: Quality scores for CoT traces.
- `correlation_result.json`: Correlation between rule precision and CoT quality.
- `boundary_conditions.json`: Adherence boundary analysis.
- `rate_metrics.json`: Hallucination and Rule Gap rates.
- `final_report.json`: Aggregated final report.

## Troubleshooting

- If you encounter a "Code drift detected" error, ensure your code matches the reference checksum.
- If a stage fails, check the logs for specific error messages.
- Ensure all required data files exist in `data/raw/`.