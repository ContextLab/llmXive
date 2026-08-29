# Decision Record 001: Exclusion of ChestX-ray14 Dataset

## Status
Accepted

## Context
The original project specification (FR-003) and User Story 2 (US-2) included the ChestX-ray14 dataset as a primary source for validating resolution invariance and high-fidelity reconstruction in medical imaging contexts.

However, during the implementation of the data loading pipeline (T005), it was determined that:
1. There is no verified, programmatic, and CI-compatible source for the ChestX-ray14 dataset that allows for automated fetching without manual intervention or unstable external mirrors.
2. Attempts to fetch the dataset in the automated execution environment consistently fail due to rate limiting, broken links, or authentication requirements not supported in the current CI setup.
3. Continuing to rely on this dataset introduces significant CI instability and blocks the automated validation of the core hypothesis (resolution invariance) on other available datasets.

## Decision
We hereby **exclude** the ChestX-ray14 dataset from the project scope.

This decision updates:
- **FR-003**: Removed the requirement to use ChestX-ray14.
- **US-2**: Removed the specific use of ChestX-ray14 for high-resolution inference testing.
- **T005**: The data loader explicitly excludes ChestX-ray14 and fails loudly if the fetch fails, rather than falling back to synthetic data.

## Consequences
- **Positive**: The project pipeline becomes robust, reproducible, and compatible with automated CI/CD environments. Validation can proceed on ImageNet-1K and COCO without external blockers.
- **Negative**: The specific validation of resolution invariance on medical imaging data (ChestX-ray14) is deferred to a future phase if a verified source becomes available.
- **Mitigation**: T019b was added to explicitly validate the hypothesis on the remaining datasets (ImageNet + COCO) to ensure the core research question is still addressed.
