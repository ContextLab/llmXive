# Decision Record 001: ChestX-ray14 Exclusion

## Status
Accepted

## Context
The original project specification (FR-003) and User Story 2 (US-2) included the ChestX-ray14 dataset as a primary source for high-resolution medical imaging evaluation. This dataset was intended to validate the resolution invariance hypothesis on medical imagery.

However, during the implementation phase, it was determined that:
1. There is no verified, programmatic access point for the ChestX-ray14 dataset that guarantees long-term availability and reproducibility in the CI environment.
2. Downloading and processing the full dataset poses significant risks to the CI runner's storage and memory constraints (7GB RAM limit).
3. The dataset's licensing and access requirements introduce non-deterministic failures in automated pipelines.

## Decision
The project will explicitly exclude the ChestX-ray14 dataset from the scope of this research implementation.

This decision modifies:
- **FR-003**: The requirement to use ChestX-ray14 is removed.
- **US-2**: The evaluation scope is restricted to ImageNet-1K and COCO datasets only.

## Consequences
- **Positive**:
 - Ensures the research pipeline is reproducible and deterministic in the CI environment.
 - Eliminates risks associated with missing or inaccessible data sources.
 - Focuses the validation of the resolution invariance hypothesis on general-purpose natural images (ImageNet, COCO), which are sufficient for the primary hypothesis regarding the ViQ architecture's behavior.

- **Negative**:
 - The hypothesis is not validated on medical imagery in this iteration.
 - Future work must be undertaken to validate the model on medical datasets if that specific domain is a target.

## References
- Plan.md: "ChestX-ray14 is excluded from scope (Decision Record 001)."
- T005: Data loader implementation explicitly excludes ChestX-ray14.
- T019: High-res evaluation script explicitly documents exclusion.
