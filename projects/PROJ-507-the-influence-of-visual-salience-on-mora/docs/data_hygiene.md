# Data Hygiene and Verified Source Mechanism

## Overview

This document describes the "Verified Source" injection mechanism implemented in `code/data_prep.py` to ensure data integrity, reproducibility, and constitutional compliance in the `llmXive` pipeline.

## The Problem: Reproducibility vs. Execution Environment

In automated scientific pipelines, research code often runs in different environments:
1. **Development**: Local machines with specific dataset versions.
2. **CI/CD**: Ephemeral runners with network restrictions or specific cached artifacts.
3. **Production**: High-performance clusters with access to verified, immutable data stores.

Relying solely on dynamic URLs (e.g., `) introduces non-determinism. The upstream dataset might change, the URL might become unavailable, or the runner might have network issues. A simple `try/except` block that falls back to synthetic data is **strictly forbidden** by the project's Constitution Principle I (Fail Loudly) because it silently substitutes real data with fabricated results, invalidating the science.

## The Solution: Verified Source Injection

The project implements a strict environment-variable-driven override mechanism. If a verified, immutable source of truth is available for the current execution environment, it can be injected without modifying the core code.

### Mechanism: `VERIFIED_DATA_SOURCE`

The `code/data_prep.py` module checks for the environment variable `VERIFIED_DATA_SOURCE` at the start of the `ingest_dataset` function.

#### Behavior

1. **If `VERIFIED_DATA_SOURCE` is NOT set**:
 - The pipeline attempts to fetch data from the **Primary Source** (e.g., `huggingface.co/datasets/morald`).
 - If the Primary Source is unavailable, it attempts the **Secondary Source** (e.g., `huggingface.co/datasets/visual_genome`).
 - If **both** fail, and no explicit synthetic fallback configuration is present, the script **raises `DataFetchError`** and halts execution immediately. **No synthetic data is generated.**

2. **If `VERIFIED_DATA_SOURCE` IS set**:
 - The pipeline **ignores** all default URLs.
 - It interprets the value as a specific, programmatic instruction to fetch from a verified location.
 - The format depends on the source type (see examples below).
 - This path is considered the "Single Source of Truth" for that run.
 - If this verified source fails, the script **raises `DataFetchError`** immediately.

### Implementation Details

The logic resides in `code/data_prep.py`:

```python
import os
from huggingface_hub import hf_hub_download

def ingest_dataset():
 verified_source = os.getenv("VERIFIED_DATA_SOURCE")

 if verified_source:
 # Use the verified source exclusively
 # Example format: "hf_hub:visual_genome:train:0.1.0"
 # or a direct URL to a verified tarball
 if verified_source.startswith("hf_hub:"):
 # Parse and download from HuggingFace Hub explicitly
 parts = verified_source.split(":")
 repo_id = parts[1]
 filename = parts[2]
 #... download logic...
 pass
 else:
 # Handle other verified source formats
 raise DataFetchError(f"Unknown verified source format: {verified_source}")
 else:
 # Fallback to standard dynamic fetching
 #... standard fetch logic...
 pass
```

### Why This Is Critical for Reproducibility

1. **Determinism**: By pinning a specific commit, hash, or file version via the environment variable, the execution stage ensures that the exact same bytes are processed every time, regardless of upstream changes.
2. **Auditability**: The `VERIFIED_DATA_SOURCE` value is logged in `data/raw/sample_metadata.json` alongside the SHA-256 checksum of the downloaded data. This creates an immutable link between the analysis results and the exact data provenance.
3. **Constitutional Compliance**: This mechanism satisfies the requirement to "fail loudly" while allowing the execution stage to inject a verified source that guarantees success without resorting to synthetic data. It prevents the "silent substitution" anti-pattern.

### Usage Examples

#### Scenario A: Local Development (Standard)
No environment variable is set. The script attempts to download from the public HuggingFace hub.
```bash
python code/data_prep.py
```

#### Scenario B: CI/CD with Cached Artifacts
The CI runner has a verified copy of the dataset at a specific path or hash.
```bash
export VERIFIED_DATA_SOURCE="hf_hub:visual_genome:train_subset_42:sample_v1.tar.gz"
python code/data_prep.py
```

#### Scenario C: Production with Immutable Store
The production environment points to an internal, versioned data lake.
```bash
export VERIFIED_DATA_SOURCE="s3://verified-data-lake/morald/v2.1/fixed_sample.tar"
python code/data_prep.py
```

### Verification

To verify that the mechanism is working:
1. Set `VERIFIED_DATA_SOURCE` to a valid, existing source.
2. Run `code/data_prep.py`.
3. Check `data/raw/sample_metadata.json`. It should contain:
 - `source_type`: "verified"
 - `source_id`: The value of `VERIFIED_DATA_SOURCE`
 - `checksum_sha256`: The hash of the downloaded file
4. If the source is invalid or missing, the script must raise `DataFetchError` and **not** produce any output files.

## Related Files

- `code/data_prep.py`: Implementation of the injection logic.
- `data/raw/sample_metadata.json`: Log of the data source and checksum.
- `docs/paper_draft.md`: Section on Data Provenance.
- `code/config.py`: Base configuration for environment variables.