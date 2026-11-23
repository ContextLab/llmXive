# Real Data Policy (Constitution Principle VII Compliance)

## Overview

This document explicitly states the project's strict adherence to the "Real Data Only" principle.
All data used in the llmXive pipeline must originate from verified, real-world sources.
**No synthetic data generation, fake samples, or placeholder datasets are permitted.**

## Data Sources

All EEG/MEG datasets must be fetched from:

1. **OpenNeuro**:
 - Auditory Oddball: `ds000246`
 - Visual Oddball: `ds000117` (via HuggingFace mirror if OpenNeuro direct fetch fails)

2. **Verification**:
 - Every dataset fetch is validated immediately after download.
 - Validation includes checking sampling rates (≥500 Hz) and trial counts.
 - If validation fails, the pipeline **halts** with a specific error code (FR-008, FR-009, FR-011).

## Enforcement Mechanisms

### 1. Configuration Flag (`REAL_DATA_ONLY`)

The `code/config/env_config.py` module exposes a `REAL_DATA_ONLY` flag (default: `true`).
If set to `false`, the system logs a severe warning. **Production runs MUST have this set to `true`.**

### 2. No Synthetic Fallbacks

Data loading functions (e.g., `code/data/download.py`) **must not** contain:
- `try/except` blocks that catch fetch failures and generate synthetic data.
- `if` conditions that fall back to `np.random` or mock data generators.

If a real data fetch fails, the script **must raise an exception** and terminate.
This ensures that any "success" is guaranteed to be based on real measurements.

### 3. Checksum Verification

Processed data artifacts are validated against checksums recorded in `data/manifest.json`
(generated during the download phase) to ensure data integrity and provenance.

## Consequences of Violation

Any code that generates or uses synthetic data in place of real measurements is considered
a **critical violation** of the project constitution. Such code will be rejected during
the execution gate review.

## References

- Task T010: Environment configuration management
- Task T011: Documentation of Real Data assumption
- Task T048: Data Integrity Verification
- Task T055: Constitution Amendment VII (Validation Independence)