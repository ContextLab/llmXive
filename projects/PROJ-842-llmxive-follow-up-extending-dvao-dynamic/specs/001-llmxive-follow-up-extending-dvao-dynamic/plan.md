# Implementation Plan: llmXive follow-up: extending "DVAO: Dynamic Variance-adaptive Advantage Optimization for Multi-reward"

**Branch**: `001-llmxive-noise-scaling` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-noise-scaling/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-noise-scaling/spec.md`

## Summary

This project extends the "DVAO" framework by deriving a theoretical lower bound on sample complexity for Pareto optimality as the number of reward objectives ($N$) increases under independent noise. It validates this bound using synthetic multi-objective tabular MDPs and a "Moving-Window Heuristic" for variance estimation. The implementation strictly adheres to CPU-only constraints (2 cores, ≤7 GB RAM) and ensures statistical rigor through sensitivity analysis on window size, noise correlation, and reward distribution.

**Critical Methodological Correction**: The plan replaces the Kolmogorov-Smirnov (KS) test for slope validation with **Linear Regression and a t-test on the slope coefficient**. The KS test is inappropriate for validating regression slopes. A formal **Spec Amendment Proposal** is included to update FR-009 in the source spec to reflect this correction.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `sympy`, `pytest`, `pyyaml`  
**Storage**: Local filesystem (`data/` directory for processed JSON/CSV artifacts)  
**Testing**: `pytest` with coverage enforcement  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Computational research library / CLI  
**Performance Goals**: Complete full experiment suite (N=5,10,20,50) within 6 hours; memory footprint ≤7 GB.  
**Constraints**: No GPU; strict resource monitoring; synthetic data only (no external downloads required beyond standard libraries).  
**Scale/Scope**: N up to 50; State space size dynamically reduced if N > 50 to fit memory.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Action Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`. `requirements.txt` pins versions. Synthetic data generation is deterministic. |
| **II. Verified Accuracy** | **PASS** | **New Mechanism**: A `docs/citations.md` file will be created listing all theoretical assumptions (MORL, Pareto) and library references. A `src/verification/verify_citations.py` script will cross-reference these against primary sources (e.g., DVAO paper, MORL bounds) to ensure validity before implementation. Version pinning is insufficient; this audit is now required. |
| **III. Data Hygiene** | **PASS** | All generated data (`data/processed/`) will be checksummed. No raw data modification; derivations write new files. |
| **IV. Single Source of Truth** | **PASS** | Figures/Stats in final report will trace to `data/processed/empirical_results.json` and `src/derivation/`. |
| **V. Versioning Discipline** | **PASS** | Artifacts will carry content hashes in `state/`. |
| **VI. Theoretical Lower Bound Validation** | **PASS** | Plan explicitly includes a module for formal derivation (`src/derivation/`) and a separate module for empirical validation. **Validation Independence** is satisfied by **Phase 4.3: Held-Out Set Validation** which tests against heavy-tailed noise distributions. The held-out set is generated in a distinct pass with a different seed and distribution type. |
| **VII. Computational Resource Constraint Adherence** | **PASS** | Plan enforces CPU-only, tabular MDPs, and explicit memory degradation logic for N > 50 in `src/environment/synthetic_mdp.py`. The `reduce_state_space()` function within this module handles the graceful degradation. **Static Scalarization Baseline** is implemented in `src/analysis/baseline_scalarization.py` (see FR-011/FR-018 mapping). |

## Spec Gap Analysis & Amendment Proposal

### Missing Requirement (FR-011)
The source spec lists FR-001 through FR-010, then jumps to FR-012. FR-011 is missing.
**Resolution**: The plan treats the "Static Scalarization Baseline" requirement (mandated by Constitution Principle VII) as the functional equivalent of the missing FR-011.
**Action**: The plan includes a specific task to implement `src/analysis/baseline_scalarization.py` and explicitly maps it to the missing FR-011 in the Constitution Check table. This will be ratified in the spec amendment process.

### Methodological Correction (FR-009)
The source spec FR-009 mandates a "Kolmogorov-Smirnov goodness-of-fit test for the slope". This is methodologically incorrect for validating a linear regression slope.
**Resolution**: The plan implements a **Linear Regression with a t-test on the slope coefficient** instead. This applies to BOTH the primary scaling law validation (Task 4.5) AND the correlation sensitivity analysis (Task 4.7).
**Action**: A formal **Spec Amendment Proposal** is included below to request the modification of FR-009 in the source spec. The plan proceeds with the corrected statistical method (t-test) pending this amendment. The plan explicitly rejects the KS test for all slope validations in this project.

### Spec Amendment Proposal
**Issue**: FR-009 mandates a KS test for slope validation.
**Proposal**: Replace "Kolmogorov-Smirnov" with "t-test on the regression slope" in FR-009.
**Justification**: The KS test is a goodness-of-fit test for distributions, not for regression slopes. Using it here is a category error. The t-test on the slope coefficient is the standard statistical method for this hypothesis.
**Status**: Pending ratification. Implementation proceeds with t-test for both scaling law and correlation sweep.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-noise-scaling/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── src/
│   ├── derivation/
│   │   ├── sample_complexity.py   # Theoretical derivation (Symbolic Math)
│   │   └── verify_symbolic.py     # Verification script for SC-001
│   ├── environment/
│   │   ├── synthetic_mdp.py       # Tabular MDP generator (N objectives)
│   │   └── reward_generators.py   # Linear, Sparse, Non-Convex, Heavy-tailed
│   ├── analysis/
│   │   ├── heuristic.py           # Moving-Window Heuristic implementation
│   │   ├── statistics.py          # Regression, T-tests, Binomial tests
│   │   ├── pareto_oracle.py       # Distance to Pareto frontier calculation
│   │   └── baseline_scalarization.py # Static Scalarization Baseline (FR-011/FR-018)
│   ├── verification/
│   │   └── verify_citations.py    # Citation audit script (Constitution II)
│   └── main.py                    # Orchestration script
├── scripts/
│   └── validate_construct_validity.py # Validates construct validity results
├── tests/
│   ├── unit/
│   │   ├── test_derivation.py
│   │   ├── test_mdp.py
│   │   └── test_heuristic.py
│   └── integration/
│       └── test_full_suite.py
├── data/
│   ├── raw/                       # (Empty, synthetic generation only)
│   └── processed/
│       ├── noise_properties.json  # Correlation matrix logs
│       ├── empirical_results.json # Main results
│       ├── construct_validity_results.json
│       ├── heavy_tailed_validation.json
│       └── symbolic_verification.json
├── docs/
│   └── citations.md               # List of theoretical assumptions and sources
├── requirements.txt
└── pyproject.toml
```

**Structure Decision**: Selected a modular research library structure (`code/src/`) separating derivation, environment, and analysis to enforce the "Single Source of Truth" principle. This allows the theoretical module to be tested independently of the empirical simulation. The `scripts/` directory is explicitly included for validation utilities.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Separate Derivation Module** | Required by Constitution Principle VI to ensure the theoretical bound is not biased by empirical implementation. | A monolithic script mixing math and simulation risks "code as truth" contamination where empirical heuristics leak into the theoretical proof. |
| **Dynamic State Space Reduction** | Required by FR-016 and FR-005 to fit N > 50 into 7 GB RAM. Logic resides in `src/environment/synthetic_mdp.py` via `reduce_state_space()`. | A fixed state space would cause OOM errors at N > 50, failing the compute feasibility requirement. |
| **Multiple Reward Distributions** | Required by FR-010 for Construct Validity. | Testing only Linear rewards would fail to validate the robustness of the noise scaling law against non-convex or sparse landscapes. |
| **Static Scalarization Baseline** | Required by Constitution Principle VII and the missing FR-011 to provide a comparative baseline for the Moving-Window Heuristic. | Without a baseline, it is impossible to quantify the improvement or failure of the heuristic relative to standard scalarization methods. |
| **Citation Audit** | Required by Constitution Principle II to verify theoretical assumptions. | Version pinning alone does not verify the validity of the research concepts (MORL, Pareto) used. |

## Unresolved panel concerns (addressed in this revision)

The following concerns from the previous iteration have been resolved in the plan design:

1.  **T052c (KS test) Fragmentation & Methodology**: The plan replaces the KS test with **Linear Regression and a t-test on the slope coefficient** (Methodology Phase 4.5 and 4.7). The correlation sweep generation and test execution are consolidated into a unified "Sensitivity Analysis" phase in `src/analysis/statistics.py`. The plan explicitly rejects the KS test for all slope validations.
2.  **T026b (Symbolic Verification)**: The plan mandates the creation of `src/derivation/verify_symbolic.py` which executes the symbolic engine and writes a JSON report (`data/processed/symbolic_verification.json`) as a hard deliverable.
3.  **T034c/e/g (Fine-grained Distributions)**: The plan consolidates reward generation into a single task/module `src/environment/reward_generators.py` which implements all three distributions (Linear, Sparse, Non-Convex) and heavy-tailed variants, ensuring all are available for the sensitivity sweep.
4.  **T087 (Correlation Logging)**: The `synthetic_mdp.py` design explicitly includes a method to log the achieved correlation matrix to `data/processed/noise_properties.json` upon generation.
5.  **T089 (Missing Artifacts)**: The plan defines the exact schema and generation logic for `scripts/validate_construct_validity.py` and the resulting JSON artifacts in the `analysis` phase. The schema is now formally versioned in `contracts/construct_validity_results.schema.yaml`. The `scripts/` directory is now explicitly included in the Project Structure.
6.  **FR-011/FR-018 (Static Scalarization)**: Added explicit mapping to FR-011 (the missing requirement) and FR-018 in the Constitution Check table and implemented `src/analysis/baseline_scalarization.py`.
7.  **FR-012 (Held-Out Set)**: Explicitly defined as **Phase 4.3: Held-Out Set Validation** with a distinct generation pass and configuration.
8.  **FR-017 (Pareto Oracle)**: Explicitly defined as **Phase 4.4: Pareto Frontier Distance Calculation** with a clear algorithm (Exhaustive Enumeration) to ensure independence.
9.  **FR-014 (Noise Sanity Check)**: Explicitly defined as **Phase 4.1: Noise Sanity Check**.
10. **Statistical Rigor (T-tests vs KS)**: Replaced KS test with Linear Regression + Slope T-Test. Distinguished between `scaling_slope_t_p_value` (for SC-002) and `heuristic_bias_t_p_value` (for FR-015) in data models. Added `regression_slope` and `r_squared` to schemas.
11. **Binomial Test for Stability**: Added **Phase 4.2: Stability Significance Test** to validate heuristic stability rates.
12. **Numerical Evaluation**: Added **Phase 1.2: Numerical Evaluation** to convert symbolic expressions to numerical functions, explicitly linking to empirical parameters.
13. **Convergence Criterion**: Explicitly defined the "distance < 5%" threshold in the Theoretical Background to avoid tautology. The failure criterion (A factor of approximately one and a half times.) is now explicitly distinct from the derivation target.
14. **Citation Audit**: Added **Phase 0.1: Citation Verification** to satisfy Constitution Principle II.
15. **Data Flow (Oracle to Scaling Law)**: Explicitly traced the consumption of `pareto_frontier_distance` from Task 4.4 into Task 4.5's regression analysis.
16. **Held-Out Generation**: Explicitly defined the separate generation pass for heavy-tailed noise in Phase 2.
17. **Oracle Algorithm**: Explicitly defined the Exhaustive Enumeration algorithm for the Pareto Oracle to ensure independence.

## Methodology

### 0. Pre-Implementation Verification (Phase 0)
*   **Task 0.1: Citation Audit**: Run `src/verification/verify_citations.py` to verify all theoretical assumptions (MORL, Pareto) against primary sources listed in `docs/citations.md`. This satisfies Constitution Principle II.

### 1. Theoretical Derivation (Phase 1)
*   **Task 1.1**: Symbolic Derivation using `sympy` to derive the closed-form equation for $Var(A_{weighted})$ and $S_{theoretical}(N)$.
    *   **Crucial Distinction**: The bound is derived specifically for the **5% Pareto distance threshold**.
*   **Task 1.2: Numerical Evaluation**: Convert the symbolic `sympy` expression into a numerical Python function `lambda N, sigma, epsilon: ...` for empirical comparison.
    *   **Explicit Linkage**: This function will be evaluated using `N` from the experiment configuration and `sigma_injected` (the known theoretical noise variance) from `noise_properties.json` or the experiment parameters. This ensures the theoretical bound is directly comparable to the empirical results.
*   **Verification**: Automated check via `src/derivation/verify_symbolic.py` comparing algebraic steps.

### 2. Synthetic Environment Generation (Phase 2)
*   **Implementation**: `src/environment/synthetic_mdp.py`.
*   **Logic**:
    *   Generate state features.
    *   Create $N$ reward weight vectors.
    *   Inject noise with specified $\sigma^2$ and correlation $\rho$.
    *   **Constraint**: If $N > 50$, automatically reduce the state space size by a significant factor using the `reduce_state_space()` function (FR-016) and log the effective parameters.
    *   **Held-Out Set Generation**: A separate execution pass with `--distribution heavy_tailed` and a distinct seed is performed to generate the held-out set required by FR-012. This ensures the held-out set is not a subset of the training data but a distinct distributional sample.
    *   **Logging**: Explicitly log the achieved correlation matrix to `data/processed/noise_properties.json` (resolving T087).
*   **Validation**: Log achieved correlation matrix to `data/processed/noise_properties.json`.

### 3. Heuristic Implementation & Training (Phase 3)
*   **Implementation**: `src/analysis/heuristic.py`.
*   **Logic**:
    *   Execute training episodes.
    *   Calculate variance using a window of size $k$.
    *   Compare heuristic estimate to known $\sigma^2$.
*   **Resource Control**: Enforce a dedicated allocation of CPU cores. and 7 GB RAM limit.

### 4. Statistical Validation (Phase 4)
*   **Task 4.1: Noise Sanity Check (FR-014)**: Before any advantage analysis, compare empirical noise variance to theoretical $\sigma^2$. If mismatch > 5%, log failure and halt.
*   **Task 4.2: Stability Significance Test (SC-003)**: Perform a **Binomial Test** on the heuristic stability rate (ratio $\in [, 1.1]$) to determine if stability is statistically significant against a random baseline.
*   **Task 4.3: Held-Out Set Validation (FR-012)**: Apply the heuristic to the held-out heavy-tailed set generated in Phase 2. Compare sample complexity to the theoretical bound. Output `data/processed/heavy_tailed_validation.json`.
*   **Task 4.4: Pareto Frontier Distance (FR-017)**: Use `src/analysis/pareto_oracle.py` to calculate the distance of the final policy to the theoretical Pareto frontier.
    *   **Algorithm**: For the synthetic tabular MDPs (small state space), the oracle computes the true frontier via **Exhaustive Enumeration of all deterministic policies**. This provides an independent ground truth that does not rely on the heuristic being validated, avoiding circularity.
    *   **Data Flow**: The resulting `pareto_frontier_distance` is stored in `empirical_results.json` and consumed by Task 4.5.
*   **Task 4.5: Scaling Law Validation (SC-002)**:
    *   Perform **Linear Regression** of `log(Empirical Sample Count)` vs `log(N)`.
    *   Perform a **t-test on the slope coefficient** to verify if the empirical slope matches the theoretical slope.
    *   **Correction**: The previous plan incorrectly used a KS test. This is replaced by the t-test on the slope.
    *   **Data Consumption**: This task explicitly consumes `pareto_frontier_distance` from `empirical_results.json` (produced by Task 4.4) to identify the failure point (where distance > 5%).
 * **Failure Criterion**: Empirical samples > 1.5 * theoretical_bound (distinct from the [deferred] derivation target).
*   **Task 4.6: Variance Estimator Validation (FR-015)**: Perform a **One-sample t-test** comparing the mean deviation (Heuristic - $\sigma^2$) against zero. This is distinct from the scaling law test.
*   **Task 4.7: Correlation Sensitivity (FR-009)**: Sweep $\rho$ across a range of values including zero. and repeat Task 4.5 (Linear Regression + t-test on slope).
    *   **Correction**: The plan explicitly rejects the KS test for this task as well, applying the same t-test methodology as Task 4.5.

### 5. Construct Validity (Phase 5)
*   **Task 5.1**: Run `scripts/validate_construct_validity.py` to aggregate results from Linear, Sparse, and Non-Convex distributions.
*   **Output**: `data/processed/construct_validity_results.json` (validated against `contracts/construct_validity_results.schema.yaml`).

## Baseline Implementation (FR-011/FR-018)

*   **Module**: `src/analysis/baseline_scalarization.py`.
*   **Logic**: Implement a standard static scalarization (weighted sum) baseline.
*   **Purpose**: Compare the Moving-Window Heuristic performance against this baseline to quantify improvement.
*   **Mapping**: This module satisfies the missing FR-011 requirement as identified in the Spec Gap Analysis.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Memory Overflow at N=50** | High | Implement FR-016: Reduce state space by factor of 2 if $N > 50$ via `reduce_state_space()` in `src/environment/synthetic_mdp.py`. Log effective parameters. |
| **Heuristic Instability for Small k** | Medium | Enforce minimum $k$ in `heuristic.py`. If $k$ is too small, report convergence failure. |
| **Non-Gaussian Noise Violation** | Medium | FR-012 and FR-014 explicitly test heavy-tailed noise. If the bound fails, it is logged as a construct validity finding, not a failure of the code. |
| **Correlation Assumption Failure** | Low | FR-009 and US-5 explicitly test correlated noise. The theoretical bound is defined for independent noise; deviations under correlation are expected and documented. |
| **Spec Contradiction (KS vs t-test)** | High | **Mitigation**: The plan proceeds with the t-test (methodologically correct) for ALL slope validations and includes a formal Spec Amendment Proposal to update FR-009. |
| **Tautology Risk (Bound vs Failure)** | Medium | **Mitigation**: The bound is derived for "distance < 5%". The failure is defined as "empirical > 1.5 * bound". These are mathematically distinct. |
| **Circular Validation (Oracle)** | High | **Mitigation**: The Pareto Oracle uses Exhaustive Enumeration (independent of the heuristic) to compute the true frontier, ensuring the validation is not circular. |