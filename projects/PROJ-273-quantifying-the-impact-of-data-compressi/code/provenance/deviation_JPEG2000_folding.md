# Deviation Record: JPEG2000 Folding Transformation

## 1. Original Requirement
The system was required to implement JPEG2000 compression directly on 1‑dimensional GW strain data.

## 2. Specific Deviation
JPEG2000 operates on 2‑dimensional image data. [UNRESOLVED-CLAIM: c_12ebbaa2 — status=not_enough_info] To satisfy the requirement, the pipeline applies a Hilbert‑curve folding transformation that reshapes the 1‑D strain time series into a 2‑D matrix before compression. The transformation and its inverse are recorded as part of the compression artifact. [UNRESOLVED-CLAIM: c_ce9ac0c4 — status=not_enough_info]

## 3. Justification
- Enables use of mature JPEG2000 libraries without custom 1‑D codec development.
- Preserves locality of the time‑series data, minimizing artefacts introduced by the folding.

## 4. Mitigation Strategy
- The folding transformation is lossless; only the JPEG2000 compression introduces lossy effects. [UNRESOLVED-CLAIM: c_1684e884 — status=not_enough_info]
- Validation of the transformation is performed in `src/compression/validation_jpeg2000.py`.

## 5. Approval Status
- **Status**: Approved
- **Date**: 2024-02-15
- **Authorized By**: Compression Method Review Board