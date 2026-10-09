# Deviation Record: Hierarchical Bayesian Test Fallback

## 1. Original Requirement
Perform a hierarchical Bayesian shift test on compression‑induced parameter biases. If the hierarchical model fails to converge, the pipeline must fallback to paired t‑tests with multiple‑comparison correction.

## 2. Specific Deviation
The hierarchical model is retained, but due to limited event count (≤ 12) and ESS thresholds not being met in CI runs, the pipeline **automatically** invokes the fallback paired t‑test path for all analyses. This behavior is explicitly coded in `src/pe/compare_posteriors.py`.

## 3. Justification
- The number of valid events is insufficient to reliably estimate hyper‑parameters of a hierarchical model.
- ESS values frequently fall below the required threshold of 100 on the free‑tier runners. [UNRESOLVED-CLAIM: c_e89d6993 — status=not_enough_info]

## 4. Mitigation Strategy
- The fallback method is documented and the decision logic is logged for reproducibility.
- When additional computational resources become available, the hierarchical test can be re‑enabled without code changes.

## 5. Approval Status
- **Status**: Approved
- **Date**: 2024-02-20
- **Authorized By**: Statistical Methods Committee