# Dataset Exclusion Policy

## Overview

This document outlines the policy regarding dataset selection and exclusion within the "Evaluating the Effectiveness of Differential Privacy in Federated Learning" project.

## Excluded Datasets

### Shakespeare Dataset

**Status**: Excluded

**Reason**: The Shakespeare dataset was initially considered as a secondary dataset for federated learning experiments. However, after a thorough gap analysis in the project plan (`plan.md`), it was determined that there is no verified, programmatically-accessible source for this dataset that meets our reliability and reproducibility standards.

**Impact**: Any code paths or configuration attempts to use "shakespeare" as a dataset will raise a `ValueError` with a clear message indicating the exclusion per plan.md Gap Analysis.

**Reference**:
- Plan.md Gap Analysis section
- Task T006: `code/config.py` raises `ValueError` for Shakespeare
- Task T011: `code/data/download.py` rejects non-FEMNIST datasets

## Supported Datasets

### FEMNIST

**Status**: Active / Supported

**Source**: Hugging Face Datasets (`leaf/femnist`)

**Verification**: Verified real data source with reliable programmatic access.

**Implementation**:
- Downloaded via `code/data/download.py`
- Partitioned via `code/data/partition.py`
- Used in all training and analysis tasks

## Future Considerations

If a verified source for the Shakespeare dataset (or other datasets) becomes available in the future, the exclusion policy can be updated. Any new dataset addition must:
1. Pass the verified source criteria (reliable, programmatic access).
2. Be documented in `plan.md`.
3. Update relevant task implementations and error handling logic.

## Compliance

All implementation tasks (T006, T011, T028, etc.) explicitly enforce this exclusion policy to ensure project consistency and reproducibility.