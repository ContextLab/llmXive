# Constitution Amendment: Principle VII

## 1. Original Principle Text
**Constitution Principle VII**: Parameter estimation MUST be performed using LALInference in CPU‑mode with default settings.

## 2. Amendment
The pipeline substitutes LALInference with **Bilby** (Dynesty sampler) for the pilot phase to meet CI runtime constraints.

## 3. Reasoning
- Full LALInference runs exceed the allowed execution time on the GitHub Actions free tier. [UNRESOLVED-CLAIM: c_3ed12f8a — status=not_enough_info]
- Bilby provides comparable posterior estimates for synthetic injections while allowing configurable iteration limits. [UNRESOLVED-CLAIM: c_df48ecd1 — status=not_enough_info]

## 4. Implementation Details
- Wrapper `src/pe/run_bilby.py` records sampler settings and ESS.
- Results are cross‑validated against an externally generated `Bias_Original` baseline (see `data/external/baseline_bias_original.json`).

## 5. Approval Status
- **Status**: Approved
- **Date**: 2024-02-12
- **Authorized By**: Computational Resources Committee