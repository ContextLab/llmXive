"""Monte-Carlo power analysis for the Friedman test (T002).

Simulates paired precision scores for the three models under a medium
effect (Cohen's d = 0.5) and estimates the probability that the
Friedman test detects it with n = 500 paired samples. If estimated
power < 0.8 the report flags ``exploratory: true`` so downstream
statistical reporting (T009) frames results as exploratory.

This is a statistical *method* (Monte-Carlo simulation of the test
procedure itself, as mandated by the task); it produces no analysis
data and never substitutes for real measurements.
"""

from __future__ import annotations

from llmxive_toolkit import get_logger, paths

from code.seeds import SEED

log = get_logger(__name__)

# Design constants (spec: "Assumption about statistical validity")
N_SAMPLES = 500          # paired samples (FR-001 target)
N_REPLICATES = 1000      # Monte-Carlo replicates
ALPHA = 0.05             # significance level (SC-004)
MEDIUM_D = 0.5           # Cohen's d for a medium effect
WITHIN_SUBJECT_RHO = 0.5 # within-subject correlation (repeated measures)
BASE_MEAN = 0.60         # baseline mean precision score
BASE_SD = 0.15           # within-subject SD of precision scores
POWER_THRESHOLD = 0.8    # exploratory if power below this


def estimate_power(
    n_samples: int = N_SAMPLES,
    effect_d: float = MEDIUM_D,
    n_replicates: int = N_REPLICATES,
    seed: int = SEED,
    alpha: float = ALPHA,
) -> float:
    """Estimate Friedman-test power via Monte-Carlo simulation.

    Three models' paired precision scores are simulated with a shared
    subject effect (within-subject correlation ``WITHIN_SUBJECT_RHO``).
    A medium effect is injected as a shift of ``effect_d`` standard
    deviations for one model relative to the other two. Returns the
    fraction of replicates in which the Friedman test rejects at
    ``alpha``.
    """
    import numpy as np
    from scipy.stats import friedmanchisquare

    rng = np.random.default_rng(seed)
    means = np.array(
        [BASE_MEAN, BASE_MEAN + effect_d * BASE_SD, BASE_MEAN],
        dtype=float,
    )
    # Shared subject effect induces the repeated-measures pairing.
    subject = rng.standard_normal((1, n_samples, 1))
    eps = rng.standard_normal((n_replicates, n_samples, 3))
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
    return n_significant / n_replicates


def format_report(power: float, n_samples: int = N_SAMPLES) -> str:
    """Render the power-analysis markdown report.

    The ``exploratory`` flag is ``true`` exactly when
    ``power < POWER_THRESHOLD`` (0.8).
    """
    exploratory = power < POWER_THRESHOLD
    lines = [
        "# Power Analysis Report (T002)",
        "",
        "Monte-Carlo power analysis for the Friedman test comparing",
        "fidelity scores across the three LLM architectures (FR-005,",
        "SC-004). This operationalizes the spec's assumption about",
        "statistical validity: if power is low, downstream results are",
        "framed as exploratory associations rather than definitive",
        "claims.",
        "",
        "## Design",
        "",
        f"- Test: Friedman test (three paired models), alpha = {ALPHA}",
        f"- Target effect: medium, Cohen's d = {MEDIUM_D:.2f} (one model shifted vs. the other two)",
        f"- Within-subject correlation: {WITHIN_SUBJECT_RHO}",
        f"- Paired samples: n = {n_samples}",
        f"- Monte-Carlo replicates: {N_REPLICATES}",
        f"- Pinned seed: {SEED} (Constitution I, ``code/seeds.py``)",
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
            f"Estimated power ({power:.4f}) is below the 0.8 "
            "convention, so the statistical reporting (T009) and the "
            "summary (T010) MUST frame the Friedman-test results as "
            "exploratory associations, not definitive claims."
        )
    else:
        lines.append(
            f"Estimated power ({power:.4f}) meets or exceeds the 0.8 "
            "convention, so the planned sample size is adequate to "
            "detect a medium effect; results need not be framed as "
            "exploratory on power grounds."
        )
    lines.append("")
    return "\n".join(lines)


def run_power_analysis(
    n_samples: int = N_SAMPLES,
    n_replicates: int = N_REPLICATES,
) -> dict:
    """Run the full power analysis and write ``results/power_report.md``."""
    power = estimate_power(
        n_samples=n_samples, n_replicates=n_replicates, seed=SEED
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
