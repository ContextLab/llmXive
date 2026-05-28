"""Golden + weak project fixtures (spec 015 T072).

Curated calibration-positive ideas covering ``LIBRARIAN_DEFAULT_FIELDS``
in THREE shapes so the panels exercise a realistic mix (not just
"follow-up to anchor X" — that shape is one of three):

| Shape          | Field        | Project ID                                     |
|-|-|-|
| follow-up      | computer science | PROJ-903-attention-circuit-recovery        |
| follow-up      | psychology       | PROJ-908-prospect-theory-llm-replication   |
| follow-up      | statistics       | PROJ-909-lasso-stability-survey            |
| theory / sim   | chemistry        | PROJ-902-correlation-energy-scaling        |
| theory / sim   | materials sci    | PROJ-904-tmd-tight-binding                 |
| theory / sim   | mathematics      | PROJ-905-sgd-convergence-numerics          |
| public data    | biology          | PROJ-901-tcga-tumor-suppressor-survival    |
| public data    | neuroscience     | PROJ-906-openneuro-motor-m1-consistency    |
| public data    | physics          | PROJ-907-gw150914-chirp-mass-posterior     |
| weak (control) | computer science | PROJ-912-attention-spurious-correlation    |

The 9 golden ideas SHOULD reach ``posted`` when run through the
pipeline (gated by maintainer DOI sign-off). The weak idea SHOULD be
kicked back to ``brainstormed`` or ``flesh_out``.

The weak idea is INTENTIONALLY DISGUISED — title, project id, and body
all read as a plausible submission at first glance. Its three hidden
flaws (circular RQ, fabricated dataset, plan↔tasks contradiction
potential) are calibrated to be detectable by an honest panel but
NOT obvious enough for the panel to game by spotting the word
"calibration" anywhere. See ``_WEAK_IDEA`` below.

Every external reference cited here (DOIs, dataset URLs, anchor
papers) is verified via CrossRef / arXiv / direct fetch before
commit; see the verify-external-references memory.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .domains import ANCHOR_PAPERS, AnchorPaper

# --- dataclass ------------------------------------------------------------


IdeaShape = Literal["followup", "theory", "data"]


@dataclass(frozen=True)
class GoldenProject:
    """A calibration-positive idea fixture (or the weak negative control)."""

    project_id: str
    field_name: str
    title: str
    slug: str
    idea_md: str
    anchor: AnchorPaper
    shape: IdeaShape = "followup"
    weak: bool = False
    expected_kickback_lens: str | None = None


# --- shape helpers -------------------------------------------------------


def _followup_idea(*, anchor: AnchorPaper, rq: str, hyp: str, methods: str) -> str:
    """Idea shape: methodological follow-up to a high-profile anchor paper."""
    return (
        f"# Idea — follow-up to {anchor.title} ({anchor.field_name})\n\n"
        f"Anchor paper: {anchor.title} ({anchor.authors[0]} et al., "
        f"{anchor.year}; DOI {anchor.doi}, {anchor.url}).\n\n"
        f"Research question: {rq}\n\n"
        f"Hypothesis: {hyp}\n\n"
        f"Methods: {methods}\n\n"
        f"Feasibility: implementable with free open-source tooling + "
        f"publicly available data; no paid services or proprietary "
        f"compute required.\n"
    )


def _theory_idea(*, field: str, title: str, rq: str, hyp: str, methods: str) -> str:
    """Idea shape: theoretical or pure-simulation project. No external
    dataset required; everything is computable in-process."""
    return (
        f"# Idea — {title} ({field})\n\n"
        f"Research question: {rq}\n\n"
        f"Hypothesis: {hyp}\n\n"
        f"Methods: {methods}\n\n"
        f"Feasibility: theoretical / simulation project; no external "
        f"data required. Implementable with free open-source libraries "
        f"on a single CPU machine.\n"
    )


def _data_idea(*, field: str, title: str, rq: str, hyp: str, methods: str,
               data_name: str, data_url: str) -> str:
    """Idea shape: secondary analysis of a curated public dataset.
    The cited data source MUST be verified-reachable before commit."""
    return (
        f"# Idea — {title} ({field})\n\n"
        f"Data source: {data_name} ({data_url}); publicly accessible "
        f"under an open-access policy.\n\n"
        f"Research question: {rq}\n\n"
        f"Hypothesis: {hyp}\n\n"
        f"Methods: {methods}\n\n"
        f"Feasibility: implementable with free open-source tooling + "
        f"the publicly-accessible dataset cited above.\n"
    )


# --- the 9 golden projects -----------------------------------------------


_GOLDEN_PROJECTS: list[GoldenProject] = []
_by_field = {a.field_name: a for a in ANCHOR_PAPERS}


# === Follow-up shape (3 of 9) ============================================

_GOLDEN_PROJECTS.append(GoldenProject(
    project_id="PROJ-903-attention-circuit-recovery",
    field_name="computer science",
    title="Replicating the IOI circuit on small open-weight Transformers",
    slug="attention-circuit-recovery",
    shape="followup",
    anchor=_by_field["computer science"],
    idea_md=_followup_idea(
        anchor=_by_field["computer science"],
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
    ),
))

_GOLDEN_PROJECTS.append(GoldenProject(
    project_id="PROJ-908-prospect-theory-llm-replication",
    field_name="psychology",
    title="LLM replication of Prospect Theory's certainty-equivalent shifts",
    slug="prospect-theory-llm-replication",
    shape="followup",
    anchor=_by_field["psychology"],
    idea_md=_followup_idea(
        anchor=_by_field["psychology"],
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
    ),
))

_GOLDEN_PROJECTS.append(GoldenProject(
    project_id="PROJ-909-lasso-stability-survey",
    field_name="statistics",
    title="Selection-stability of Lasso on UCI benchmark regression datasets",
    slug="lasso-stability-survey",
    shape="followup",
    anchor=_by_field["statistics"],
    idea_md=_followup_idea(
        anchor=_by_field["statistics"],
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
    ),
))


# === Theory / simulation shape (3 of 9) ==================================

_GOLDEN_PROJECTS.append(GoldenProject(
    project_id="PROJ-902-correlation-energy-scaling",
    field_name="chemistry",
    title="Correlation-energy scaling with system size in small molecules",
    slug="correlation-energy-scaling",
    shape="theory",
    anchor=_by_field["chemistry"],  # placeholder; not cited in body
    idea_md=_theory_idea(
        field="chemistry",
        title=(
            "Correlation-energy scaling with system size in small "
            "molecules under restricted Hartree-Fock"
        ),
        rq=(
            "How does the correlation-energy gap (E_CCSD(T) - E_HF) scale "
            "with electron count N across a curated set of small molecules "
            "(N=2-30) at fixed basis-set quality (cc-pVDZ)?"
        ),
        hyp=(
            "The gap scales as approximately C * N^p with exponent "
            "p in [1.0, 1.3]; the prefactor C depends weakly on element "
            "identity but more strongly on bond character (sigma vs pi "
            "density)."
        ),
        methods=(
            "Use PySCF (open-source quantum-chemistry library) to compute "
            "HF + CCSD(T) energies on a curated set of 30 small molecules; "
            "fit log-log scaling laws; report exponent confidence "
            "intervals by bootstrap over molecule selection. No external "
            "dataset — every input geometry is generated in-script from "
            "published bond-length tables."
        ),
    ),
))

_GOLDEN_PROJECTS.append(GoldenProject(
    project_id="PROJ-904-tmd-tight-binding",
    field_name="materials science",
    title="Tight-binding band structure of 2D transition-metal dichalcogenides",
    slug="tmd-tight-binding",
    shape="theory",
    anchor=_by_field["materials science"],
    idea_md=_theory_idea(
        field="materials science",
        title=(
            "Tight-binding band structure of 2D transition-metal "
            "dichalcogenides"
        ),
        rq=(
            "Using a single-orbital tight-binding model parametrized from "
            "first-principles bandstructures of MoS2, can we predict the "
            "K-point bandgaps of the full TMD family (MoX2, WX2 where "
            "X=S,Se,Te) within 0.1 eV of literature DFT values?"
        ),
        hyp=(
            "Per-element on-site energies + nearest-neighbor hoppings "
            "explain ≈90% of the variation in K-point bandgaps; the "
            "remaining 10% is explained by spin-orbit-coupling strength "
            "scaling with X identity."
        ),
        methods=(
            "Implement the Slater-Koster tight-binding model from scratch "
            "in Python (numpy + scipy); fit parameters to the MoS2 "
            "bandstructure; extrapolate to other TMDs; compare to "
            "literature DFT bandstructures. Pure theoretical / "
            "computational — no external data beyond literature DFT "
            "reference values for comparison."
        ),
    ),
))

_GOLDEN_PROJECTS.append(GoldenProject(
    project_id="PROJ-905-sgd-convergence-numerics",
    field_name="mathematics",
    title="Numerical convergence rate of SGD on smooth convex objectives",
    slug="sgd-convergence-numerics",
    shape="theory",
    anchor=_by_field["mathematics"],
    idea_md=_theory_idea(
        field="mathematics",
        title=(
            "Numerical convergence rate of stochastic gradient descent on "
            "smooth strongly-convex objectives"
        ),
        rq=(
            "For smooth strongly-convex objectives, does the asymptotic "
            "O(1/T) convergence rate of SGD with decaying step size "
            "η_t = c/t hold under finite-sample averaging at "
            "T ∈ {10², 10³, 10⁴, 10⁵}?"
        ),
        hyp=(
            "The empirical convergence rate matches the theoretical 1/T "
            "asymptote within constants of 2x; the empirical "
            "multiplicative constant depends sub-linearly on the "
            "condition number κ in the small-κ regime."
        ),
        methods=(
            "Implement SGD on a battery of synthetic strongly-convex "
            "quadratics with varying κ ∈ {1, 10, 100}; measure "
            "||x_t - x*|| over 1000 sample paths; fit power-law "
            "convergence laws; report empirical constants vs. "
            "theoretical bounds."
        ),
    ),
))


# === Public-data shape (3 of 9) ==========================================

_GOLDEN_PROJECTS.append(GoldenProject(
    project_id="PROJ-901-tcga-tumor-suppressor-survival",
    field_name="biology",
    title=(
        "Cross-cancer-type consistency of survival associations for "
        "tumor-suppressor genes"
    ),
    slug="tcga-tumor-suppressor-survival",
    shape="data",
    anchor=_by_field["biology"],
    idea_md=_data_idea(
        field="biology",
        title=(
            "Cross-cancer-type consistency of survival associations for "
            "the most-cited tumor-suppressor genes"
        ),
        data_name=(
            "NCI Genomic Data Commons (TCGA open-access mutation + "
            "clinical data)"
        ),
        data_url="https://portal.gdc.cancer.gov/",
        rq=(
            "Across the 5 most-cited tumor-suppressor genes (TP53, RB1, "
            "PTEN, CDKN2A, BRCA1), how consistent are per-gene overall-"
            "survival associations across the 32 TCGA primary-cancer "
            "types, and how do the associations depend on tumor stage "
            "and somatic-mutation burden?"
        ),
        hyp=(
            "TP53-mutation impact on overall survival is negative across "
            "most cancer types but loses significance (or reverses) in "
            "3-5 cancer types where TP53 mutations are near-universal "
            "(loss of dynamic range); the other 4 genes show "
            "cancer-type-specific patterns."
        ),
        methods=(
            "Pull open-access mutation + clinical data from the NCI "
            "Genomic Data Commons; per-gene Kaplan-Meier + Cox "
            "proportional-hazards analysis stratified by cancer type; "
            "multiple-testing correction via Benjamini-Hochberg."
        ),
    ),
))

_GOLDEN_PROJECTS.append(GoldenProject(
    project_id="PROJ-906-openneuro-motor-m1-consistency",
    field_name="neuroscience",
    title=(
        "Cross-study consistency of M1 activation in OpenNeuro motor-task "
        "fMRI"
    ),
    slug="openneuro-motor-m1-consistency",
    shape="data",
    anchor=_by_field["neuroscience"],
    idea_md=_data_idea(
        field="neuroscience",
        title=(
            "Cross-study consistency of right-M1 activation in publicly-"
            "released OpenNeuro motor-task fMRI datasets"
        ),
        data_name="OpenNeuro (publicly-released motor-task fMRI datasets)",
        data_url="https://openneuro.org/",
        rq=(
            "Across publicly-available motor-task fMRI datasets on "
            "OpenNeuro spanning right-hand finger-tapping protocols, how "
            "consistent are the peak right-M1 activation Z-statistics "
            "and voxel coordinates after harmonized preprocessing?"
        ),
        hyp=(
            "Peak voxel coordinates cluster within ≈8 mm across studies; "
            "peak Z-statistics show 30-50% inter-study variance "
            "attributable to scanner vendor + TR differences."
        ),
        methods=(
            "Identify 5-8 OpenNeuro motor-task datasets matching the "
            "right-hand finger-tapping protocol; apply fMRIPrep "
            "harmonized preprocessing; per-subject GLM with right-hand-"
            "vs-rest contrast; extract peak voxel coordinates + Z-stats "
            "in a literature-derived M1 ROI; report inter-study variance "
            "decomposition."
        ),
    ),
))

_GOLDEN_PROJECTS.append(GoldenProject(
    project_id="PROJ-907-gw150914-chirp-mass-posterior",
    field_name="physics",
    title=(
        "Sensitivity of the GW150914 chirp-mass posterior to detector-"
        "noise priors"
    ),
    slug="gw150914-chirp-mass-posterior",
    shape="data",
    anchor=_by_field["physics"],
    idea_md=_data_idea(
        field="physics",
        title=(
            "Sensitivity of the GW150914 chirp-mass posterior to "
            "detector-noise prior assumptions"
        ),
        data_name=(
            "LIGO/Virgo Open Science Center — GW150914 strain data "
            "(see also the discovery paper Abbott et al. 2016, DOI "
            "10.1103/PhysRevLett.116.061102)"
        ),
        data_url="https://gw-openscience.org/",
        rq=(
            "For the GW150914 binary-black-hole merger detected by LIGO-"
            "Virgo, how sensitive is the inferred chirp-mass posterior "
            "to the assumed detector-noise prior model (Welch PSD vs. "
            "parametric Gaussian-process model vs. the official LIGO/"
            "Virgo PSD)?"
        ),
        hyp=(
            "Posterior chirp-mass medians differ by <2% across the three "
            "noise models; 90% credible intervals widen by 15-25% under "
            "the parametric GP model relative to the official PSD."
        ),
        methods=(
            "Pull LIGO/Virgo GW150914 strain data from the GW Open "
            "Science Center; implement matched-filter chirp-mass "
            "inference under each PSD model; compare posterior moments "
            "+ KL divergence between posteriors."
        ),
    ),
))


# === The deliberately weak project (1 of 10) =============================
#
# Project id 912 (out of the 901-909 golden sequence — looks like a
# separate submission). Field is "computer science" — plausible since
# BERT is CS. No "weak", "calibration", or "control" markers anywhere in
# the title or body. The body reads as a plausible interpretability /
# fairness submission an honest panel would take seriously at first
# glance.
#
# Hidden flaws (the panel SHOULD catch at least one):
#
#   1. CIRCULAR RQ (rq_validity / idea panel): The question asks "do
#      attention patterns reveal spurious correlations the model has
#      learned?" The hypothesis is "yes, because spurious correlations
#      leave characteristic signatures IN attention". The reasoning is
#      self-verifying — "we can detect X via attention because X leaves
#      detectable signatures in attention" treats the operationalization
#      and the phenomenon as the same thing.
#
#   2. FABRICATED DATASET (data_resources / plan panel — if the project
#      survives idea): `spurcor-research/SpurCorBench-v3` is NOT a real
#      HuggingFace dataset. The dataset_resolver pre-filter should fail
#      on it; if the panel reaches the data_resources lens, that lens
#      should flag it.
#
#   3. METHODOLOGY LOOSENESS (constraint_preservation / plan panel —
#      softer signal): the methods mix 5-fold CV (a fixed evaluation
#      protocol) with leave-one-out subgroup analysis (a different
#      protocol) without clarifying whether they're hierarchically
#      composed or in tension. A careful reviewer would request
#      clarification; less critical than the other two.

_WEAK_IDEA = """\
# Idea — attention-pattern signatures of spurious correlations in fine-tuned BERT classifiers

Background: Recent interpretability work has suggested that
transformer attention patterns may carry signal about which input
features the model relies on during prediction. We investigate this
in the context of known spurious correlations in text classification
tasks, where models are known to acquire shortcuts during fine-tuning.

Research question: When a fine-tuned BERT-base classifier exhibits
spurious correlations between protected attributes (e.g. gender or
race tokens) and sentiment labels, do those correlations manifest as
identifiable patterns in the model's attention? In other words: does
attention reveal the spurious correlations that the classifier has
already learned?

Hypothesis: The presence of spurious correlations is detectable via
attention-pattern analysis, because spurious correlations leave
characteristic interpretability signatures in the attention weights.

Methods: Fine-tune BERT-base on the SpurCorBench-v3 corpus
(HuggingFace: `spurcor-research/SpurCorBench-v3`, ≈25k labeled review
sentences spanning gender / race / sentiment confound axes). Use
5-fold stratified cross-validation. For each fold, compute
attention-pattern signatures per layer via Integrated Gradients,
aggregated over each test sentence. Conduct leave-one-out subgroup
analysis to rank attention heads by spurious-correlation salience.

Feasibility: implementable with free-model + free-compute resources;
BERT-base + Integrated Gradients run on a single CPU.
"""


_GOLDEN_PROJECTS.append(GoldenProject(
    project_id="PROJ-912-attention-spurious-correlation",
    field_name="computer science",
    title=(
        "Attention-pattern signatures of spurious correlations in "
        "fine-tuned BERT classifiers"
    ),
    slug="attention-spurious-correlation",
    idea_md=_WEAK_IDEA,
    shape="followup",  # body shape — not a real follow-up; calibration only
    anchor=_by_field["computer science"],  # placeholder; not referenced
    weak=True,
    expected_kickback_lens="rq_validity",  # the circular RQ is the FIRST flaw
))


GOLDEN_PROJECTS: tuple[GoldenProject, ...] = tuple(_GOLDEN_PROJECTS)


# --- accessors -----------------------------------------------------------


def all_golden() -> list[GoldenProject]:
    """Return every golden + weak fixture in stable order."""
    return list(GOLDEN_PROJECTS)


def golden_for_field(field_name: str) -> GoldenProject:
    """Look up the (non-weak) golden project for a field. Raises
    ``ValueError`` for unknown fields (fail loud on typos)."""
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
    "IdeaShape",
    "all_golden",
    "golden_for_field",
    "weak_project",
]
