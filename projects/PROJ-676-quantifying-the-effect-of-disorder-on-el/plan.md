# Plan: Quantifying the Effect of Disorder on Electronic Transport in 1D Chains

## Project Overview
This project quantifies the effect of disorder on electronic transport in 1D tight-binding chains.
We compute localization lengths via two independent methods (Participation Ratio finite-size scaling
and Transfer Matrix Method) and validate their agreement. Statistical significance is assessed
with Bonferroni correction for the full family of disorder widths.

## User Stories
- US1: Compute localization length via Participation Ratio (PR) finite-size scaling.
- US2: Verify PR results with Transfer Matrix (TM) method.
- US3: Visualize eigenstate localization patterns.

## Functional Requirements (FR)
- FR-001: Generate 1D tight-binding Hamiltonians with disorder width W.
- FR-002: Compute Participation Ratio (PR) for eigenstates within |E| < 0.1.
- FR-003: Perform finite-size scaling of PR(L) to extract localization length ξ.
- FR-004: Implement Transfer Matrix Method with QR orthogonalization to compute Lyapunov exponent γ.
- FR-005: Perform linear regression of log(ξ) vs log(W) for weak disorder (W < 1.0).
- FR-006: Visualize eigenstate probability densities.
- FR-007: Parallelize disorder realization generation and analysis.
- FR-008: Handle numerical stability (memory limits, convergence failures).
- FR-009: Monitor convergence of TM method.
- FR-010: Apply Bonferroni correction for the full family of disorder widths.
- FR-011: Orchestrate parallel execution with joblib.

## Statistical Constraints (SC)
- SC-001: Validate slope of log(ξ) vs log(W) is -2 for weak disorder (W < 1.0).
- SC-002: Verify ξ_TM ≈ ξ_PR within 10% for L ≥ 400 and ≥ 80% of realizations.
- SC-003: Perform a priori power analysis to ensure ≥80% power for slope deviation test.
- SC-004: Use weak disorder cutoff W = 1.0 for slope validation.
- SC-005: Control Family-Wise Error Rate (FWER) across the full family of disorder widths using Bonferroni correction.
- SC-006: Complete 1000 realizations within 6 hours.

## FR/SC Coverage Matrix
| Requirement | US1 | US2 | US3 | Notes |
|-------------|-----|-----|-----|-------|
| FR-001 | ✓ | ✓ | | Shared infrastructure |
| FR-002 | ✓ | | | PR computation |
| FR-003 | ✓ | | | Finite-size scaling |
| FR-004 | | ✓ | | TM method |
| FR-005 | ✓ | | | Slope validation |
| FR-006 | | | ✓ | Visualization |
| FR-007 | ✓ | ✓ | | Parallelization |
| FR-008 | ✓ | ✓ | | Numerical stability |
| FR-009 | | ✓ | | TM convergence |
| FR-010 | ✓ | | | Bonferroni correction for the full family of disorder widths |
| FR-011 | ✓ | | | Orchestration |
| SC-001 | ✓ | | | Slope -2 validation |
| SC-002 | | ✓ | | Method agreement |
| SC-003 | ✓ | | | Power analysis |
| SC-004 | ✓ | | | Weak disorder cutoff |
| SC-005 | ✓ | | | FWER control across full family |
| SC-006 | ✓ | | | Performance target |

## Plan Summary
1. **Setup**: Initialize project structure, configure tools, define schemas.
2. **Foundational**: Implement core infrastructure (config, Hamiltonian generator, storage, logging).
3. **US1**: Compute PR, perform finite-size scaling, apply Bonferroni correction for the full family of disorder widths.
4. **US2**: Implement TM method, validate against US1.
5. **US3**: Visualize eigenstates, generate physical interpretation.
6. **Polish**: Performance optimization, power analysis, narrative generation.

## Data Model
- Disorder Realization: W, L, realization_index, seed, Hamiltonian, eigenvalues, eigenvectors.
- Localization Length: disorder_width, xi, uncertainty, fit_params, L_values, PR_values, p_value.
- TM Result: disorder_width, gamma, convergence_trace, L_values.

## Execution Order
1. Phase 1: Setup (T001a-T003c)
2. Phase 2: Foundational (T004-T015a) - **BLOCKS all user stories**
3. Phase 3: US1 (T012, T017a, T017b, T013a, T013b, T015, T014)
4. Phase 4: US2 (T020b, T022)
5. Phase 4.5: Cross-Story Validation (T023)
6. Phase 5: US3 (T026, T027, T028, T029, T035)
7. Phase N: Polish (T015b, T032, T033, T034, T036)

## Notes
- All data generation must use real random seeds logged in provenance.json.
- Bonferroni correction is applied for the full family of disorder widths (SC-005).
- Numerical stability logging is required for every eigenvalue problem (Constitution Principle VI).
- T029 and T035 address the "Feynman" review by providing quantitative physical interpretations.
- T013a implements finite-size scaling saturation logic (not simple proportionality).
- T015 dynamically calculates Bonferroni factor based on len(processed_widths).