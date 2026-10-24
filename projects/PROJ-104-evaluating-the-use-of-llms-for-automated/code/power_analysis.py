"""Monte‑Carlo power analysis for the Friedman test (T002).

This script simulates paired precision scores for three models across a
range of effect sizes and estimates the statistical power of the Friedman
test for a target sample size (n = 500) and a medium effect defined by
Cohen's *f* = 0.25.  The simulation respects the project‑wide random seed
(``code.seeds.SEED``) to ensure reproducibility.

The resulting markdown report is written to ``results/power_report.md``.
The report contains a single numeric power estimate for the medium effect
(as required by the task) and an ``exploratory`` flag that is ``true`` when
the estimated power is below 0.8.
"""

from __future__ import annotations

from llmxive_toolkit import get_logger, paths

from code.seeds import SEED

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Design constants (aligned with the specification)
# ----------------------------------------------------------------------
N_SAMPLES = 500          # paired samples required by the spec
N_REPLICATES = 1000      # Monte‑Carlo replicates
ALPHA = 0.05             # significance level
MEDIUM_F = 0.25          # Cohen's f for a medium effect (task requirement)
WITHIN_SUBJECT_RHO = 0.5 # within‑subject correlation (repeated measures)
BASE_MEAN = 0.60         # baseline mean precision score
BASE_SD = 0.15           # within‑subject standard deviation
POWER_THRESHOLD = 0.8    # exploratory if power below this

# ----------------------------------------------------------------------
# Helper: translate Cohen's f into a mean shift for one of the three models.
# For a balanced one‑way ANOVA with k=3 groups, Cohen's f is defined as:
#   f = sqrt( sum_i (mu_i - mu)^2 / (k * sigma^2) )
# Solving for a single shifted group (mu_shift) while keeping the other
# two at the baseline yields:
#   mu_shift = mu + f * sigma * sqrt(k)
# We use this relationship to generate a realistic medium effect.
# ----------------------------------------------------------------------
def _mean_shift_for_f(f: float, sigma: float, k: int = 3) -> float:
    """Return the mean for the shifted model given Cohen's f."""
    return BASE_MEAN + f * sigma * (k ** 0.5)

# ----------------------------------------------------------------------
# Power estimation
# ----------------------------------------------------------------------
def estimate_power(
    n_samples: int = N_SAMPLES,
    effect_f: float = MEDIUM_F,
    n_replicates: int = N_REPLICATES,
    seed: int = SEED,
    alpha: float = ALPHA,
) -> float:
    """Estimate Friedman‑test power via Monte‑Carlo simulation.

    The simulation proceeds as follows:

    1. For each replicate we generate ``n_samples`` subject‑level
       observations for three models.
    2. All three models share a common subject effect to create the
       repeated‑measures structure (correlation ``WITHIN_SUBJECT_RHO``).
    3. One model receives a mean shift corresponding to the supplied
       Cohen's *f* (``effect_f``); the other two remain at ``BASE_MEAN``.
    4. A Friedman chi‑square test is performed; if the p‑value is below
       ``alpha`` the replicate is counted as a detection.

    The returned value is the proportion of replicates that yielded a
    significant result – i.e. the estimated statistical power.
    """
    import numpy as np
    from scipy.stats import friedmanchisquare

    rng = np.random.default_rng(seed)

    # Compute the shifted mean for the “effect” model.
    shifted_mean = _mean_shift_for_f(effect_f, BASE_SD)

    # Vector of means for the three models: [baseline, shifted, baseline]
    means = np.array([BASE_MEAN, shifted_mean, BASE_MEAN], dtype=float)

    # Subject‑level random effect (shared across models)
    subject = rng.standard_normal((1, n_samples, 1))

    # Independent residual noise for each model/subject
    eps = rng.standard_normal((n_replicates, n_samples, 3))

    # Construct the simulated scores matrix:
    #   mean + sqrt(rho) * subject + sqrt(1 - rho) * eps * sigma
    scores = (
        means[None, None, :]
        + (WITHIN_SUBJECT_RHO ** 0.5) * subject
        + ((1.0 - WITHIN_SUBJECT_RHO) ** 0.5) * eps * BASE_SD
    )

    n_significant = 0
    for r in range(n_replicates):
        _, p = friedmanchisquare(
            scores[r, :, 0], scores[r, :, 1], scores[r, :, 2]
        )
        if p < alpha:
            n_significant += 1

    power = n_significant / n_replicates
    log.debug(
        "Power simulation complete: %d/%d replicates significant (power=%.4f)",
        n_significant,
        n_replicates,
        power,
    )
    return power

# ----------------------------------------------------------------------
# Report rendering
# ----------------------------------------------------------------------
def format_report(power: float, n_samples: int = N_SAMPLES) -> str:
    """Render the markdown power‑analysis report.

    The report follows the layout required by the test suite:
    it contains a line ``- estimated_power_n{n_samples}: {power}`` and an
    ``exploratory`` flag that matches the power threshold.
    """
    exploratory = power < POWER_THRESHOLD
    lines = [
        "# Power Analysis Report (T002)",
        "",
        "Monte‑Carlo power analysis for the Friedman test comparing",
        "fidelity scores across the three LLM architectures (FR‑005,",
        "SC‑004). This operationalises the specification's assumption",
        "about statistical validity: if power is low, downstream results",
        "are framed as exploratory associations rather than definitive",
        "claims.",
        "",
        "## Design",
        "",
        f"- Test: Friedman test (three paired models), alpha = {ALPHA}",
        f"- Target effect: medium, Cohen's f = {MEDIUM_F:.2f}",
        f"- Within‑subject correlation: {WITHIN_SUBJECT_RHO}",
        f"- Paired samples: n = {n_samples}",
        f"- Monte‑Carlo replicates: {N_REPLICATES}",
        f"- Pinned seed: {SEED} (Constitution I, ``code.seeds``)",
        "",
        "## Result",
        "",
        f"- estimated_power_n{n_samples}: {power:.4f}",
        f"- exploratory: {'true' if exploratory else 'false'}",
        "",
        "## Interpretation",
        "",
    ]
    if exploratory:
        lines.append(
            f"Estimated power ({power:.4f}) is below the 0.8 convention, so the "
            "statistical reporting (T009) and the summary (T010) MUST frame the "
            "Friedman‑test results as exploratory associations, not definitive "
            "claims."
        )
    else:
        lines.append(
            f"Estimated power ({power:.4f}) meets or exceeds the 0.8 convention, "
            "so the planned sample size is adequate to detect a medium effect; "
            "results need not be framed as exploratory on power grounds."
        )
    lines.append("")
    return "\n".join(lines)

# ----------------------------------------------------------------------
# Entry point used by the quick‑start and CI
# ----------------------------------------------------------------------
def run_power_analysis(
    n_samples: int = N_SAMPLES,
    n_replicates: int = N_REPLICATES,
) -> dict:
    """Run the full power analysis and write ``results/power_report.md``."""
    power = estimate_power(
        n_samples=n_samples,
        n_replicates=n_replicates,
        seed=SEED,
    )
    report = format_report(power, n_samples=n_samples)
    out_path = paths.results("power_report.md")
    out_path.write_text(report, encoding="utf-8")
    log.info(
        "Power analysis complete: power=%.4f (n=%d), exploratory=%s",
        power,
        n_samples,
        power < POWER_THRESHOLD,
    )
    print(
        f"Power analysis: estimated power for n={n_samples} is "
        f"{power:.4f}; exploratory={power < POWER_THRESHOLD}"
    )
    print(f"Wrote {out_path}")
    return {
        "n_samples": n_samples,
        "estimated_power": power,
        "exploratory": power < POWER_THRESHOLD,
        "report_path": str(out_path),
    }

if __name__ == "__main__":
    run_power_analysis()
