# Contracts Directory

This directory contains JSON Schema definitions for the data models used in the statistical significance simulation pipeline.

## Files

- `simulation_config.json`: Defines the structure for `SimulationConfig` objects used to configure experiments.
- `error_metric.json`: Defines the structure for `ErrorMetric` objects representing empirical Type I error calculations.
- `pvalue_distribution.json`: Defines the structure for `PValueDistribution` objects storing raw p-value outputs.

## Usage

These schemas are used to validate JSON artifacts produced by the simulation scripts (e.g., `data/processed/us1_results.json`).

Validation can be performed using the `jsonschema` Python library:

```python
import json
from jsonschema import validate, ValidationError

with open('contracts/error_metric.json') as f:
 schema = json.load(f)

with open('data/processed/us1_results.json') as f:
 data = json.load(f)

try:
 validate(instance=data, schema=schema)
 print("Validation successful.")
except ValidationError as e:
 print(f"Validation failed: {e.message}")
```