"""Golden + weak project fixtures (spec 015 T072).

Reverse-engineers one HIGH-QUALITY idea per :data:`LIBRARIAN_DEFAULT_FIELDS`
anchor paper, plus one DELIBERATELY WEAK idea that combines multiple
flaws the panels should catch.

The golden ideas are the calibration set's "positive" entry point for
T073's full-pipeline e2e traversal — when run through the pipeline,
each golden idea SHOULD reach ``posted`` (gated by maintainer DOI sign-
off). The weak idea SHOULD be kicked back to ``brainstormed`` or
``flesh_out`` at a recognizable lens (rq_validity / data_resources /
plan_consistency).

The idea texts here are SCHOLARLY-SHAPED proposals — they cite the
anchor paper's DOI, describe a realistic follow-up research question
that an honest panel would accept as well-formed, and stay within
llmXive's free-model + free-compute constraints. They are NOT
themselves "do CRISPR again" or "rediscover the Higgs"; they're
plausible methodological / replication / cross-domain projects an
LLM-driven research pipeline could honestly tackle.
"""

from __future__ import annotations

from dataclasses import dataclass

from .domains import ANCHOR_PAPERS, AnchorPaper


@dataclass(frozen=True)
class GoldenProject:
    """A reverse-engineered idea fixture for one calibration domain."""

    project_id: str
    field_name: str
    title: str
    slug: str
    idea_md: str
    anchor: AnchorPaper
    weak: bool = False
    expected_kickback_lens: str | None = None
    """For weak projects: the lens that SHOULD catch the flaw (so T075's
    kickback-verification asserts the right lens flagged it)."""


def _golden_idea(anchor: AnchorPaper, research_question: str,
                 hypothesis: str, methods: str) -> str:
    """Compose the canonical golden-idea Markdown shape."""
    return (
        f"# Idea — follow-up to {anchor.title} ({anchor.field_name})\n\n"
        f"Anchor paper: {anchor.title} ({anchor.authors[0]} et al., "
        f"{anchor.year}; DOI {anchor.doi}, {anchor.url}).\n\n"
        f"Research question: {research_question}\n\n"
        f"Hypothesis: {hypothesis}\n\n"
        f"Methods: {methods}\n\n"
        f"Feasibility: implementable with free-model LLM panels + "
        f"publicly available data; no paid services or proprietary "
        f"compute required.\n"
    )


# --- the 9 golden ideas (one per anchor) ---------------------------------


_GOLDEN_PROJECTS: list[GoldenProject] = []


def _add_golden(*, field_name: str, project_id: str, slug: str,
                title: str, rq: str, hyp: str, methods: str) -> None:
    """Helper that closes over the anchor lookup."""
    by_field = {a.field_name: a for a in ANCHOR_PAPERS}
    anchor = by_field[field_name]
    _GOLDEN_PROJECTS.append(GoldenProject(
        project_id=project_id, field_name=field_name, title=title,
        slug=slug,
        idea_md=_golden_idea(anchor, rq, hyp, methods),
        anchor=anchor,
    ))


_add_golden(
    field_name="biology", project_id="PROJ-901-crispr-off-target-survey",
    slug="crispr-off-target-survey",
    title="Computational survey of CRISPR-Cas9 off-target predictions vs. validated cleavages",
    rq=(
        "Across the 5 most-cited CRISPR-Cas9 off-target predictors, how "
        "does precision-recall on the published cleavage-validated "
        "datasets depend on whether the predictor's training set "
        "included that target's genomic neighborhood?"
    ),
    hyp=(
        "Predictor performance is materially inflated when validation "
        "targets are within 1 kb of training-set targets, because of "
        "local sequence context leakage."
    ),
    methods=(
        "Re-train each predictor on three held-out neighborhood-distance "
        "splits (1 kb / 10 kb / chromosome-disjoint); compare precision-"
        "recall curves under matched class balance; bootstrap CIs."
    ),
)

_add_golden(
    field_name="chemistry", project_id="PROJ-902-fullerene-property-prediction",
    slug="fullerene-property-prediction",
    title="Graph-neural-network prediction of fullerene-cage HOMO-LUMO gaps",
    rq=(
        "Can a graph neural network trained on small fullerenes (C20-C60) "
        "predict the HOMO-LUMO gap of larger fullerenes (C70-C100) "
        "with within-DFT-noise accuracy?"
    ),
    hyp=(
        "A GNN with explicit pentagon-adjacency features achieves MAE "
        "below 0.2 eV on the test set, comparable to DFT-method "
        "reproducibility but at <1% of the compute."
    ),
    methods=(
        "Curate a fullerene dataset from public DFT calculations; train "
        "GIN/GAT baselines + a custom pentagon-adjacency-aware GNN; "
        "evaluate by held-out cage size."
    ),
)

_add_golden(
    field_name="computer science",
    project_id="PROJ-903-attention-circuit-recovery",
    slug="attention-circuit-recovery",
    title="Replicating the IOI circuit on small open-weight Transformers",
    rq=(
        "Does the indirect-object-identification (IOI) circuit reported "
        "for GPT-2 small reliably recover in similarly-sized open-weight "
        "Transformers (Pythia 160M, OPT 125M) under matched probing "
        "protocols?"
    ),
    hyp=(
        "The IOI circuit is robust across architectures of similar "
        "scale; circuit-component head identities differ, but the "
        "composition graph matches the GPT-2 reference within 80% "
        "edge overlap."
    ),
    methods=(
        "Implement the original IOI probe; run on Pythia + OPT; compare "
        "circuit graphs by edit-distance; ablate each identified head "
        "to confirm causal role."
    ),
)

_add_golden(
    field_name="materials science",
    project_id="PROJ-904-2d-material-bandgap-survey",
    slug="2d-material-bandgap-survey",
    title="Cross-method validation of 2D material bandgaps from public DFT databases",
    rq=(
        "For the 100 most-deposited 2D materials in the Materials "
        "Project, how do reported DFT bandgaps vary across "
        "exchange-correlation functionals (PBE, HSE06, SCAN), and "
        "which method best matches experimental ARPES measurements?"
    ),
    hyp=(
        "HSE06 matches experimental gaps within 0.3 eV on >70% of "
        "the surveyed materials; PBE systematically underestimates "
        "by ~0.5-1 eV; SCAN sits between the two."
    ),
    methods=(
        "Extract bandgaps from Materials Project + 2DMatPedia; collate "
        "experimental ARPES values from a literature scan; compute "
        "per-material residuals + a method-level winner."
    ),
)

_add_golden(
    field_name="mathematics", project_id="PROJ-905-ricci-flow-numerical-survey",
    slug="ricci-flow-numerical-survey",
    title="Numerical Ricci-flow convergence rates on small genus-2 surfaces",
    rq=(
        "Across a curated set of triangulated genus-2 surfaces with "
        "varying initial-metric perturbations, how does numerical Ricci-"
        "flow convergence to constant curvature scale with mesh "
        "resolution and perturbation magnitude?"
    ),
    hyp=(
        "Convergence time scales linearly with mesh resolution + "
        "quadratically with perturbation magnitude in the small-"
        "perturbation regime, matching the analytic linearization."
    ),
    methods=(
        "Implement discrete Ricci flow via Polthier-Schmies; sweep "
        "mesh + perturbation; fit power-law convergence curves."
    ),
)

_add_golden(
    field_name="neuroscience", project_id="PROJ-906-place-cell-replay-decoding",
    slug="place-cell-replay-decoding",
    title="Decoder-fidelity comparison for hippocampal replay across rest states",
    rq=(
        "In the CRCNS public hc-3 dataset (multi-tetrode rat "
        "hippocampus), how does sequence-decoder fidelity for replay "
        "events differ between non-REM sleep, REM sleep, and quiet "
        "wakefulness, and is the difference better explained by "
        "spike-count or by oscillatory-phase covariates?"
    ),
    hyp=(
        "Non-REM replay yields the highest sequence-fidelity scores; "
        "after controlling for spike count + theta phase, the "
        "non-REM advantage shrinks but persists."
    ),
    methods=(
        "Standard Bayesian place-decoder; matched-spike-count and "
        "phase-stratified comparison; nested-CV for hyperparameters."
    ),
)

_add_golden(
    field_name="physics", project_id="PROJ-907-higgs-coupling-meta",
    slug="higgs-coupling-meta",
    title="Open-data meta-analysis of Higgs coupling-strength measurements",
    rq=(
        "Across the publicly released ATLAS + CMS Higgs coupling-"
        "strength results, how consistent are the per-channel "
        "couplings under a single combined fit, and how does the "
        "answer depend on the systematic-uncertainty correlation "
        "model adopted?"
    ),
    hyp=(
        "A common-systematics combined fit yields a consistent SM-like "
        "coupling pattern within ~10%; assuming uncorrelated "
        "systematics widens the per-channel CIs by 30-50%."
    ),
    methods=(
        "Use HEPData open releases; implement a simple maximum-"
        "likelihood combination; compare correlated vs. uncorrelated "
        "systematics; report per-channel signal-strength CIs."
    ),
)

_add_golden(
    field_name="psychology", project_id="PROJ-908-prospect-theory-llm-replication",
    slug="prospect-theory-llm-replication",
    title="LLM replication of Prospect Theory's certainty-equivalent shifts",
    rq=(
        "Do current open-weight LLMs (qwen-2.5 family, scaled across "
        "1B-72B) reproduce the certainty-equivalent shifts predicted "
        "by Prospect Theory when prompted as decision-makers on the "
        "original Kahneman-Tversky lottery battery?"
    ),
    hyp=(
        "Larger LLMs exhibit human-like risk aversion for gains + "
        "risk seeking for losses; the reflection effect's strength "
        "increases monotonically with model size on the original "
        "lottery set."
    ),
    methods=(
        "Implement the K-T lottery battery as a prompt template; run "
        "100 trials per lottery per model with temperature sweep; fit "
        "per-model Prospect-Theory parameters via MLE; bootstrap CIs."
    ),
)

_add_golden(
    field_name="statistics", project_id="PROJ-909-lasso-stability-survey",
    slug="lasso-stability-survey",
    title="Selection-stability of Lasso on UCI benchmark regression datasets",
    rq=(
        "Across 30 UCI regression benchmark datasets, how does Lasso's "
        "variable-selection stability (measured by Jaccard overlap "
        "across bootstrap replicates) depend on sample size, "
        "predictor dimensionality, and the chosen lambda criterion "
        "(CV-min vs. CV-1SE)?"
    ),
    hyp=(
        "Selection stability scales sub-linearly with n/p; the 1SE "
        "criterion yields more stable selections than CV-min on most "
        "datasets but with measurable predictive-MSE cost."
    ),
    methods=(
        "Bootstrap-resample each dataset 500 times; fit Lasso with "
        "both criteria; report stability + held-out MSE per dataset "
        "+ pooled."
    ),
)


# --- the 1 deliberately weak project (combines multiple flaws) ----------


_WEAK_IDEA = """\
# Idea — deliberately weak project (calibration negative)

Anchor paper: (none — this is a deliberately-flawed control)

Research question: Why is the universal model accurate? We propose to
study why our model is accurate, because models that are accurate are
worth studying. We expect to find that accurate models are accurate
because they have learned the underlying patterns.

Hypothesis: The model will be accurate.

Methods: We will use the FabricatedCalibration2024 benchmark
(`benchmark://fabricated-calibration-v9`, NOT a real dataset) and
report accuracy. The plan calls for supervised regression analysis on
a labeled dataset; the tasks file (separately) implements unsupervised
clustering on synthetic data — this contradiction is deliberate.

Feasibility: should be quick.
"""


_GOLDEN_PROJECTS.append(GoldenProject(
    project_id="PROJ-999-deliberately-weak",
    field_name="(none)",
    title="Deliberately weak control project",
    slug="deliberately-weak",
    idea_md=_WEAK_IDEA,
    # Use the held-out anchor as a placeholder reference — this is
    # NOT the anchor the project is based on (the field is "(none)");
    # it's just any AnchorPaper to satisfy the dataclass shape so we
    # don't need a separate Optional wrapper.
    anchor=next(a for a in ANCHOR_PAPERS if a.held_out),
    weak=True,
    expected_kickback_lens="rq_validity",  # the circular RQ is the
                                            # FIRST flaw the panel hits
))


GOLDEN_PROJECTS: tuple[GoldenProject, ...] = tuple(_GOLDEN_PROJECTS)


def all_golden() -> list[GoldenProject]:
    """Return every golden + weak fixture in stable order."""
    return list(GOLDEN_PROJECTS)


def golden_for_field(field_name: str) -> GoldenProject:
    """Look up the golden project for one anchor field. Raises
    ``ValueError`` for unknown fields (so a typo fails loud)."""
    for p in GOLDEN_PROJECTS:
        if not p.weak and p.field_name == field_name:
            return p
    raise ValueError(
        f"no golden project for field {field_name!r}; expected one of "
        f"{[p.field_name for p in GOLDEN_PROJECTS if not p.weak]!r}"
    )


def weak_project() -> GoldenProject:
    """Return the deliberately-weak control project."""
    return next(p for p in GOLDEN_PROJECTS if p.weak)


__all__ = [
    "GOLDEN_PROJECTS",
    "GoldenProject",
    "all_golden",
    "golden_for_field",
    "weak_project",
]
