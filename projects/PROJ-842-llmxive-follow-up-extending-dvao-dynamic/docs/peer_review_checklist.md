# Peer Review Checklist: SC-001 Alternative Path Validation

**Project**: llmXive follow-up: extending "DVAO: Dynamic Variance-adaptive Advantage Optimization for Multi-reward"
**Task ID**: T030
**User Story**: US1 - Theoretical Derivation of Noise Scaling Law
**Success Criteria**: SC-001 (Alternative Path: Peer Review & Algebraic Consistency)

---

## 1. Document Verification

### 1.1 Theoretical Derivation Document (`docs/theoretical_derivation.md`)
- [ ] **Closed-form Equation**: The document contains an explicit closed-form equation for `Var(A)` as a function of `N` (number of objectives) and `ε_i` (noise terms).
 - *Reference*: Equation must match output from `src/derivation/variance_scaling.py`.
- [ ] **Sample Complexity Bound**: The document includes the derivation of the sample complexity bound by inverting the variance equation.
 - *Reference*: Matches logic in `src/derivation/sample_complexity.py`.
- [ ] **Assumptions**: Explicit list of assumptions is present, specifically:
 - [ ] i.i.d. noise assumption is clearly stated.
 - [ ] Linearity of variance accumulation is justified.
- [ ] **Verification Results**: Output from `sympy` verification (symmetry, linearity checks) is included and matches the theoretical claims.

---

## 2. Algebraic Consistency Checklist

*Reviewer must verify the mathematical steps between the code implementation and the written derivation.*

### 2.1 Variance Accumulation (`src/derivation/variance_scaling.py`)
- [ ] **Symbolic Representation**: The code correctly defines `Var(A) = Σ Var(ε_i)` (assuming independence) or the appropriate correlated form if `ρ > 0`.
- [ ] **Symmetry Check**: The `verify_symmetry_and_linearity` function output confirms that permuting `ε_i` does not change the total variance expression.
- [ ] **Linearity Check**: The derivation confirms that `Var(Σ ε_i) = Σ Var(ε_i)` holds under the stated assumptions.
- [ ] **N-Scaling**: The final expression explicitly shows the dependency on `N` (e.g., `N * σ²` for i.i.d. case).

### 2.2 Sample Complexity Inversion (`src/derivation/sample_complexity.py`)
- [ ] **Inversion Logic**: The step from `Var(A) ≤ ε` to `N_samples ≥ f(N, ε, σ)` is algebraically correct.
- [ ] **Closed-Form String**: The `derive_sample_complexity_bound` function returns a valid closed-form string representation of the bound.
- [ ] **Boundary Conditions**: The formula behaves correctly at limits (e.g., as `ε → 0`, `N_samples → ∞`).

---

## 3. Validation Methodology Compliance (Plan vs. Spec)

*CRITICAL: This project follows the **Plan's** revised validation strategy, superseding the original Spec.*

### 3.1 Correlation vs. Coincidence
- [ ] **Metric Selection**: The validation strategy **does NOT** rely on "exact coincidence" of heuristic and theoretical values (which was discarded per Plan).
- [ ] **Correlation Analysis**: The project verifies **correlation** between variance estimation error and distance to Pareto frontier (as per SC-002 revised).
- [ ] **Statistical Test**: The primary validation uses a **Paired T-Test** (Heuristic vs. Full-Batch) as defined in `src/analysis/stats.py`, NOT a one-sample t-test against a theoretical bound (which is explicitly FORBIDDEN).

### 3.2 Failure Mode Definition
- [ ] **Failure Point**: The criteria for "failure" is defined as the smallest `N` where the paired t-test p-value < 0.05, indicating a statistically significant divergence between the heuristic and the full-batch empirical variance.
- [ ] **Correlation Threshold**: Success is defined by a significant correlation coefficient between estimation error and Pareto distance, not by a zero-error point.

---

## 4. Peer Review Sign-Off Template

**Reviewer Name**: __________________________
**Date**: __________________________

**I certify that:**
1. I have reviewed the theoretical derivation in `docs/theoretical_derivation.md`.
2. I have verified the algebraic consistency between the symbolic derivation code (`src/derivation/`) and the written document.
3. I confirm that the validation methodology adheres to the **Plan's** revised criteria (Correlation & Paired T-Test) and does not rely on the discarded "coincidence" metric.
4. The assumptions (i.i.d. noise, etc.) are clearly stated and justified.

**Decision**:
- [ ] **APPROVED**: The derivation is mathematically sound and the validation plan is compliant.
- [ ] **CONDITIONAL APPROVAL**: Approved pending minor clarifications (see notes).
- [ ] **REJECTED**: The derivation contains errors or the validation plan does not comply with the revised criteria.

**Notes / Comments**:
__________________________________________________________________________
__________________________________________________________________________
__________________________________________________________________________

**Sign-off**: __________________________