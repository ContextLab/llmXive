# Contracts Directory

This directory contains schema definitions and validation rules for data artifacts
produced and consumed by the llmXive pipeline.

## Schema Files

- `target_list.json`: Schema for the raw target repository list.
- `github_metrics.json`: Schema for raw GitHub metrics extracted from git logs.
- `nvd_cve.json`: Schema for raw NVD CVE data.
- `repo_metrics.json`: Schema for the final merged analysis dataset.
- `model_results.json`: Schema for statistical model outputs.
- `robustness_results.json`: Schema for robustness check outputs.

## Usage

Schemas are loaded by `code/data/schemas.py` to validate DataFrames and JSON files
at runtime.
