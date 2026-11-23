# Project Limitations and Future Verification Schedule

## Overview

This document tracks known limitations in the current implementation of the
"Investigating the Role of Microglial Morphology in Age-Related Cognitive Decline"
project, along with scheduled verification tasks for future execution when
external dependencies are resolved.

## Current Limitations

### SC-001: Manual Ground Truth Verification (Pending)

**Status**: Scheduled for future verification upon data acquisition.
**Description**: The morphological feature extraction pipeline (specifically
branch point counting via `skeletonize_and_count` in `code/morphometry.py`)
has been validated against synthetic ground truth (Task T010) and algorithmic
consistency. However, validation against real-world manual annotations by
human experts (SC-001) has not yet been performed due to the unavailability
of a verified, programmatically accessible dataset containing human-annotated
microglial structures with ground truth labels.

**Impact**: Without human-grounded verification, there remains a theoretical
risk that algorithmic biases in skeletonization (e.g., over-segmentation of
thin processes or merging of closely spaced branches) could skew the
quantitative metrics (branch_points, total_length, soma_area, sholl_intersections)
relative to expert consensus.

**Mitigation in Current MVP**:
1. The pipeline strictly adheres to the operational definition of morphological
 complexity as the vector `[branch_points, total_length, soma_area, sholl_intersections]`
 (defined in `code/config.py`).
2. Unit tests (T010) verify the algorithmic logic against synthetic data with
 known ground truth within a 10% tolerance.
3. The system fails loudly (T012a) if real data is unavailable, preventing
 silent fallback to synthetic data for the main analysis pipeline.

**Verification Trigger**:
This limitation will be addressed when a real dataset containing manual
annotations (e.g., from the Allen Brain Atlas or a partner institution) is
acquired and made available in the `data/raw/` directory.

**Scheduled Task**:
- **Task ID**: T040 (Re-run)
- **Action**: Re-execute `tests/unit/test_morphometry.py` (specifically the
 real-data validation logic in T010a) against the newly acquired manual
 annotations.
- **Success Criteria**: The extraction accuracy must be <10% deviation from
 manual counts. If successful, this entry will be updated to reflect
 "Verified" and the limitation status will be cleared.
- **Failure Criteria**: If deviation >10%, the `code/morphometry.py` pipeline
 parameters (e.g., skeletonization threshold, Sholl radius steps) must be
 re-tuned, and this limitation will be re-evaluated.

## Future Work & Dependencies

The following tasks are dependent on the resolution of the limitations above:

1. **Real Data Ingestion (T012a)**: Currently blocked pending a verified real
 data source. The implementation is complete and will fail loudly if the
 source is missing, as per design.
2. **Human-Grounded Validation (T010a)**: Scheduled to run automatically
 upon the availability of `allencell_annotations.csv` or equivalent.

## Notes on Operational Definitions

To ensure reproducibility and strict adherence to the project scope (FR-003),
the following definitions are fixed:

- **Morphological Complexity**: Defined strictly as the vector
 `[branch_points, total_length, soma_area, sholl_intersections]`.
- **Fractal Dimension**: Explicitly excluded from the current analysis
 pipeline to maintain CPU-tractability and alignment with the approved
 metric set.
- **Complexity Index**: Explicitly excluded to prevent scope creep.

---
*Last Updated: 2026-06-13*
*Status: SC-001 Pending Verification*