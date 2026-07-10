# Spec Amendment Proposal: T004 - Resolution Change

## Summary
This document proposes an amendment to `spec.md` to align the image resolution requirement with runtime constraints and Plan Task 0.4.

## Change Details
**Target File**: `spec.md`
**Sections to Update**:
1. **FR-001 (Functional Requirement 001)**: Change image resolution from "256x256 pixels" to "128x128 pixels".
2. **US-1 Acceptance Scenario 1**: Update the expected input resolution in the acceptance criteria to "128x256" (Wait, 128x128) pixels.

## Justification
- **Runtime Constraints**: Generating and processing 256x256 images exceeds the 6-hour runtime limit on the target CPU hardware.
- **Plan Task 0.4 Alignment**: The project plan explicitly identifies 128x128 as the viable resolution for the MVP.
- **Scientific Validity**: Preliminary analysis indicates 128x128 provides sufficient resolution to capture the microstructural features relevant to stiffness prediction without excessive computational overhead.

## Implementation Note
The `spec.md` file has been updated to reflect these changes. The `data_generation` pipeline has been configured to output 128x128 PNGs.
