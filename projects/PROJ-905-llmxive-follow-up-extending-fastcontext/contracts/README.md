# Contracts Directory

This directory contains JSON Schema definitions (`*.schema.json`) that enforce data integrity for the llmXive research pipeline.

## Purpose

These schemas define the strict structure for data artifacts produced by the pipeline. They are used to:
1. Validate data outputs during the execution of analysis scripts.
2. Document the expected format for downstream consumers.
3. Ensure consistency across different experimental runs.

## Files

- `ground_truth_annotations.schema.json`: Defines the structure for raw ground truth data extracted from SWE-bench.
- `regularity_scores.schema.json`: Defines the structure for processed repository regularity scores and split assignments.
- `exploration_logs.schema.json`: Defines the structure for performance metrics logged during FastContext execution.
- `statistical_summary.schema.json`: Defines the structure for the final comparative analysis results.

## Usage

Schemas can be validated using standard JSON Schema validators (e.g., `jsonschema` Python library):

```python
import json
import jsonschema

with open("contracts/statistical_summary.schema.json") as f:
 schema = json.load(f)

with open("data/results/statistical_summary.json") as f:
 data = json.load(f)

jsonschema.validate(data, schema)
```