# Statistical Analysis Plan

**Project**: PROJ-884 — Symbolic backward-step substitution in Bidirectional Evolutionary Search
**Feature branch**: `001-symbolic-bes`
**Task**: T013 (US2) — Pre-registered statistical analysis plan
**Status**: Pre-registered before any experimental results are inspected
**Implementation module**: `code/analysis/stats.py` (functions `two_proportion_z_test`, `tost_equivalence_test`, `calculate_effect_size`, `calculate_power_z_test`, `required_sample_size_for_power`)

This document pre-registers the statistical framework for comparing the
symbolic‑guided BES variant against the neural‑verifier baseline, per FR‑004,
FR‑005, and SC‑001–SC‑004. All numeric parameters below are fixed prior to
analysis; no post‑hoc re‑specification is permitted without an amendment note.

## 1. Primary endpoints

| Endpoint | Type | Test | Module function |
|---|---|---|---|
| E1: Puzzle success rate (proportion of puzzles solved) | Binary per puzzle | Two‑proportion z‑test (two‑sided) + TOST equivalence | `two_proportion_z_test`, `tost_equivalence_test` |
| E2: Computational cost per puzzle (wall‑clock seconds, CPU) | Continuous | Welch's two‑sample t‑test (log‑transformed if skewed) | t‑test in `code/analysis/stats.py` |
| E3: Energy per puzzle (Joules, `cpu_time * TDP_WATTS`) | Continuous | Welch's two‑sample t‑test | same |

Secondary/descriptive: exclusion rate of the symbolic planner (FR‑006),
logical‑contradiction rate of sub‑goals (SC‑003), empirical complexity class
via log‑log regression (SC‑005).

## 2. Pre‑registered numeric parameters

| Parameter | Symbol | Value |
|---|---|---|
| Equivalence margin (TOST bound on proportion difference) | Δ | **0.05** (±5 percentage points) |
| Family‑wise significance level | α | **0.0497** |
| Two‑proportion z‑test α (two‑sided) | α_z | **0.0497** |
| TOST per‑side α | α_TOST | **0.0497** (90 % CI corresponds to two one‑sided 4.97 % tests) |
| Target statistical power | 1 − β | **0.80** |
| Minimum detectable effect size (Cohen's h) | h | **0.20** (small effect) |
| Required sample size per group | n | **393** (see power analysis, Section 3) |
| Total puzzles (both arms share the same fixed puzzle set) | N | **500** |
| Effect‑size target for cost reduction (E2) | — | ≥ 20 % reduction in mean wall‑clock time, reported with Cohen's d |
| Random seed | — | 42 |

## 3. Power analysis

Using the normal‑approximation formula implemented in
`code/analysis/stats.py::required_sample_size_for_power`:

```
n = 2 * ((z_{α/2} + z_{β}) / h)^2
```

With α = 0.0497 (z_{α/2} ≈ 1.959), power = 0.80 (z_{β} ≈ 0.842),
and h = 0.20:

```
n = 2 * ((1.959 + 0.842) / 0.20)^2
 = 2 * (14.005)^2
 = 2 * 196.14
 ≈ 392.28 → 393 puzzles per group (rounded up)
```

**Required sample size: 393 per group. [UNRESOLVED-CLAIM: c_0ad9f100 — status=not_enough_info]** Because both methods are evaluated on
the *same* fixed set of puzzles (a paired design in the puzzle dimension),
the dataset of N = 500 puzzles (see `specs/001-llmxive-follow-up-extending-self-improvi/design_dataset.md`)
satisfies this requirement with margin: 500 ≥ 393. For the McNemar‑style paired
sensitivity check, 500 pairs provide > 0.80 power for h = 0.20.

For reference, the required n for other effect sizes at α = 0.0497,
power = 0.80:

| Cohen's h | n per group |
|---|---|
| 0.10 | 1568 |
| 0.20 | 393 |
| 0.50 | 63 |
| 0.80 | 25 |

## 4. Hypotheses

### 4.1 Success‑rate equivalence (primary, SC‑001)

- H0 (non‑equivalence): \|p_symbolic − p_neural\| ≥ Δ = 0.05
- H1 (equivalence): \|p_symbolic − p_neural\| < Δ = 0.05

Decision rule: TOST procedure — compute the two one‑sided z‑tests at
α_TOST = 0.0497 against the +Δ and −Δ margins. Equivalence is declared only
if **both** one‑sided tests reject (equivalently, the 90 % CI for the
proportion difference lies entirely within (‑0.05, +0.05)).

### 4.2 Success‑rate difference (secondary, SC‑004)

- H0: p_symbolic = p_neural
- H1: p_symbolic ≠ p_neural

Two‑proportion z‑test (pooled variance), two‑sided, α_z = 0.0497. Reported
as `p_value_z` together with the observed difference, Cohen's h, and a 95 % CI.
Significance is declared when p_value_z < 0.05.

### 4.3 Cost comparison (SC‑002)

- H0: mean(cost_symbolic) = mean(cost_neural)
- H1: mean(cost_symbolic) ≠ mean(cost_neural)

Welch's two‑sample t‑test on per‑puzzle wall‑clock seconds (log‑transformed if
Shapiro–Wilk on either group rejects normality at 0.05), α = 0.0497,
reported as `p_value_t` with Cohen's d and a 95 % CI. The pre‑registered
efficiency claim requires **both** statistical significance (p < 0.05) **and**
a point estimate of ≥ 20 % mean reduction in wall‑clock time and energy.

## 5. Multiple comparisons and error control

Three confirmatory tests are run (E1‑TOST, E1‑z, E2/E3 cost family). To
control the family‑wise error rate at α = 0.0497 across the two cost
endpoints (E2, E3), a Bonferroni correction is applied within the cost family
(α_cost = 0.0497 / 2 ≈ 0.02485 each). The success‑rate endpoints (E1) are
treated as the co‑primary family and tested at the uncorrected 0.0497 level as
pre‑registered above.

## 6. Handling of exclusions and missing data

- Puzzles excluded by the symbolic planner (FR‑006: `PARSE_FAILURE`,
 `CONTRADICTION_DETECTED`) are counted as **failures** for the symbolic arm
 in the primary intent‑to‑treat analysis (conservative), and the per‑protocol
 analysis (exclusions removed from both arms) is reported as a sensitivity
 analysis.
- The exclusion rate itself is reported descriptively with a 95 % CI.
- No imputation of missing cost measurements; puzzles with missing cost are
 dropped from E2/E3 only, with the drop count reported.

## 7. Reporting template

The statistical report (`data/processed/statistical_report.json`, produced by
`code/analysis/stats.py`) MUST contain at minimum:

- `p_value_z`, `p_value_t`, `significance` (boolean, p < 0.05)
- `tost_delta`, `tost_p_value`, `tost_equivalent` (boolean)
- `effect_size_h` (success rates), `effect_size_d` (cost)
- `n_symbolic`, `n_neural`, `success_rate_symbolic`, `success_rate_neural`
- `energy_joules_symbolic`, `energy_joules_neural`
- `gpu_hours_estimate` (documented conversion factor, per FR‑004/plan)
- `power_analysis`: `{alpha, power_target, effect_size_h, required_n_per_group: 393, achieved_n}`

## 8. Traceability

- Δ = 0.05, α = 0.0497, required n = 393 per group (numeric values above).
- Spec: FR‑004, FR‑005, SC‑001–SC‑004; Plan Task 0.2.
- Dataset basis: N = 500 puzzles per `design_dataset.md` (T012).
- Implementation: `code/analysis/stats.py` — `two_proportion_z_test`,
 `tost_equivalence_test`, `calculate_effect_size`,
 `calculate_power_z_test`, `required_sample_size_for_power`.