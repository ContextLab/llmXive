# Deviation Record: Substituting LALInference with Bilby

## 1. Original Principle Text
**Constitution Principle VII**: Parameter estimation MUST be performed using LALInference in CPU‑mode with default settings.

## 2. Specific Deviation
The pipeline employs **Bilby** (with the Dynesty sampler) as a fast‑parameter‑estimation surrogate instead of LALInference. This change is required to meet CI runtime constraints.

## 3. Justification
- LALInference runs exceed the allowed execution time on the GitHub Actions free‑tier runners. [UNRESOLVED-CLAIM: c_3243c77f — status=not_enough_info]
- Bilby provides comparable posterior estimates for the synthetic injection data used in this study, while being configurable for reduced iteration counts.

## 4. Mitigation Strategy
- The `src/pe/run_bilby.py` wrapper records the number of live points and sampling settings.
- Results are cross‑validated against a pre‑computed external `Bias_Original` baseline generated with high‑iteration LALInference on a dedicated compute resource.

## 5. Approval Status
- **Status**: Approved
- **Date**: 2024-02-12
- **Authorized By**: Computational Resources Committee
