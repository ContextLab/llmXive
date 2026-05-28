"""Per-domain calibration set definitions (spec 015 T066).

Defines an :class:`AnchorPaper` per ``LIBRARIAN_DEFAULT_FIELDS`` field
that calibration drivers use as the "real, peer-reviewed positive
example" for that domain. Each anchor:

- Has a stable, verifiable DOI or arXiv id (the maintainer's manual
  adjudication pass at T068 must be able to look the paper up; the URL
  lets them open it without typing the title into a search engine).
- Was a high-impact, broadly recognized contribution in its field —
  the calibration set wants UNAMBIGUOUSLY good papers as positives
  so any "this paper has fatal flaws" verdict from the panel is a
  clear miscalibration.
- Carries a ``held_out`` flag for the one field reserved for
  domain-generality validation (T069): no prompt tuning is allowed
  against the held-out anchor; if the panel still works on it, the
  prompts are domain-general.

The HF-daily + backlog samples are NOT pinned here — they're picked at
calibration time by the driver because they change daily. See the
domain accessors for the contract the driver follows.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from llmxive.librarian import LIBRARIAN_DEFAULT_FIELDS

# --- Anchor papers --------------------------------------------------------


@dataclass(frozen=True)
class AnchorPaper:
    """A real peer-reviewed paper that anchors one calibration domain."""

    field_name: str
    title: str
    authors: tuple[str, ...]
    year: int
    doi: str
    url: str
    abstract_summary: str
    held_out: bool = False
    """``True`` for the domain reserved for held-out generality
    validation (T069). Drivers MUST NOT tune prompts against a
    held-out anchor."""


# The anchors below are real, broadly-cited published papers with stable
# DOIs / arXiv ids. The maintainer SHOULD verify each link before the
# T068 calibration run (the calibration harness's manual-adjudication
# step covers this).
#
# Held-out choice: psychology. Rationale: spec-015's panel prompts have
# been authored with research-paper conventions in mind; psychology's
# (slightly different) framing around effect sizes + replication
# requirements is a strong proxy for "domain whose conventions the
# prompts weren't specifically tuned for". A successful held-out run
# evidences domain generality.

_ANCHOR_BIOLOGY = AnchorPaper(
    field_name="biology",
    title=(
        # CrossRef record uses an en-dash (U+2013) in the title;
        # match it verbatim so downstream string-equality citation checks
        # don't fail on ASCII vs en-dash. Verified via CrossRef API.
        "A Programmable Dual-RNA–Guided DNA Endonuclease in Adaptive "  # noqa: RUF001
        "Bacterial Immunity"
    ),
    authors=("Jinek M", "Chylinski K", "Fonfara I", "Hauer M",
             "Doudna JA", "Charpentier E"),
    year=2012,
    doi="10.1126/science.1225829",
    url="https://doi.org/10.1126/science.1225829",
    abstract_summary=(
        "Introduces the Cas9 / dual-guide-RNA programmable DNA-cleavage "
        "system that became CRISPR gene editing. Nobel Prize 2020."
    ),
)

_ANCHOR_CHEMISTRY = AnchorPaper(
    field_name="chemistry",
    title="C60: Buckminsterfullerene",
    authors=("Kroto HW", "Heath JR", "O'Brien SC", "Curl RF", "Smalley RE"),
    year=1985,
    doi="10.1038/318162a0",
    url="https://doi.org/10.1038/318162a0",
    abstract_summary=(
        "Discovery of C60 (Buckminsterfullerene), opening the field of "
        "fullerene chemistry. Nobel Prize 1996."
    ),
)

_ANCHOR_COMPUTER_SCIENCE = AnchorPaper(
    field_name="computer science",
    title="Attention Is All You Need",
    authors=("Vaswani A", "Shazeer N", "Parmar N", "Uszkoreit J",
             "Jones L", "Gomez AN", "Kaiser L", "Polosukhin I"),
    year=2017,
    doi="10.48550/arXiv.1706.03762",
    url="https://arxiv.org/abs/1706.03762",
    abstract_summary=(
        "Introduces the Transformer architecture. The most-cited paper "
        "in modern deep learning; the basis for GPT, BERT, and most LLMs."
    ),
)

_ANCHOR_MATERIALS_SCIENCE = AnchorPaper(
    field_name="materials science",
    title="Electric Field Effect in Atomically Thin Carbon Films",
    authors=("Novoselov KS", "Geim AK", "Morozov SV", "Jiang D",
             "Zhang Y", "Dubonos SV", "Grigorieva IV", "Firsov AA"),
    year=2004,
    doi="10.1126/science.1102896",
    url="https://doi.org/10.1126/science.1102896",
    abstract_summary=(
        "Demonstrates the isolation + field-effect characterization of "
        "graphene. Nobel Prize 2010."
    ),
)

_ANCHOR_MATHEMATICS = AnchorPaper(
    field_name="mathematics",
    title=(
        "The Entropy Formula for the Ricci Flow and its Geometric "
        "Applications"
    ),
    authors=("Perelman G",),
    year=2002,
    doi="10.48550/arXiv.math/0211159",
    url="https://arxiv.org/abs/math/0211159",
    abstract_summary=(
        "Perelman's proof of the Geometrization Conjecture (subsuming "
        "the Poincaré Conjecture). Fields Medal 2006 (declined)."
    ),
)

_ANCHOR_NEUROSCIENCE = AnchorPaper(
    field_name="neuroscience",
    title=(
        "The Hippocampus as a Spatial Map: Preliminary Evidence from "
        "Unit Activity in the Freely-Moving Rat"
    ),
    authors=("O'Keefe J", "Dostrovsky J"),
    year=1971,
    doi="10.1016/0006-8993(71)90358-1",
    url="https://doi.org/10.1016/0006-8993(71)90358-1",
    abstract_summary=(
        "First report of hippocampal place cells. Nobel Prize 2014 "
        "(with Moser+Moser for grid cells)."
    ),
)

_ANCHOR_PHYSICS = AnchorPaper(
    field_name="physics",
    title=(
        "Observation of a New Particle in the Search for the Standard "
        "Model Higgs Boson with the ATLAS Detector at the LHC"
    ),
    authors=("The ATLAS Collaboration",),
    year=2012,
    doi="10.1016/j.physletb.2012.08.020",
    url="https://doi.org/10.1016/j.physletb.2012.08.020",
    abstract_summary=(
        "Discovery of the Higgs boson at the LHC. Nobel Prize 2013 "
        "(Higgs, Englert)."
    ),
)

_ANCHOR_PSYCHOLOGY = AnchorPaper(
    field_name="psychology",
    title="Prospect Theory: An Analysis of Decision under Risk",
    authors=("Kahneman D", "Tversky A"),
    year=1979,
    doi="10.2307/1914185",
    url="https://doi.org/10.2307/1914185",
    abstract_summary=(
        "Introduces Prospect Theory: a descriptive theory of how people "
        "weigh probable outcomes. Nobel Prize 2002 (Kahneman)."
    ),
    held_out=True,
)

_ANCHOR_STATISTICS = AnchorPaper(
    field_name="statistics",
    title="Regression Shrinkage and Selection via the Lasso",
    authors=("Tibshirani R",),
    year=1996,
    doi="10.1111/j.2517-6161.1996.tb02080.x",
    url="https://doi.org/10.1111/j.2517-6161.1996.tb02080.x",
    abstract_summary=(
        "Introduces the Lasso (L1-regularized regression). The most-"
        "cited paper in modern statistical methodology."
    ),
)


ANCHOR_PAPERS: tuple[AnchorPaper, ...] = (
    _ANCHOR_BIOLOGY, _ANCHOR_CHEMISTRY, _ANCHOR_COMPUTER_SCIENCE,
    _ANCHOR_MATERIALS_SCIENCE, _ANCHOR_MATHEMATICS, _ANCHOR_NEUROSCIENCE,
    _ANCHOR_PHYSICS, _ANCHOR_PSYCHOLOGY, _ANCHOR_STATISTICS,
)


# --- Calibration domain (anchor + driver-time samples) -------------------


@dataclass
class CalibrationDomain:
    """One calibration domain: the anchor paper + the calibration
    driver's job at run time is to fill in `hf_daily_sample` (a paper
    from the HuggingFace daily papers feed for this field) and
    `backlog_samples` (one or more existing llmXive backlog projects in
    this field) so the calibration covers BOTH high-prestige (anchor)
    AND quotidian (backlog/HF-daily) workloads."""

    field_name: str
    anchor: AnchorPaper
    hf_daily_sample: dict[str, str] | None = None
    """Filled in by the driver at calibration time. Schema:
    ``{"title": ..., "url": ..., "abstract": ...}``."""
    backlog_samples: list[str] = field(default_factory=list)
    """Paths to existing llmXive backlog projects (PROJ-NNN-...) in this
    field. Filled in by the driver at calibration time."""


def all_domains() -> list[CalibrationDomain]:
    """Return one :class:`CalibrationDomain` per
    :data:`LIBRARIAN_DEFAULT_FIELDS` field."""
    by_field = {a.field_name: a for a in ANCHOR_PAPERS}
    return [
        CalibrationDomain(field_name=f, anchor=by_field[f])
        for f in LIBRARIAN_DEFAULT_FIELDS
    ]


def get_anchor(field_name: str) -> AnchorPaper:
    """Look up the anchor for a field. Raises ``ValueError`` for unknown
    fields rather than returning ``None`` (so a typo in driver code
    fails loud)."""
    for a in ANCHOR_PAPERS:
        if a.field_name == field_name:
            return a
    raise ValueError(
        f"no anchor paper for field {field_name!r}; expected one of "
        f"{[a.field_name for a in ANCHOR_PAPERS]!r}"
    )


def held_out_domain() -> str:
    """Return the field name of the one held-out anchor. Drivers use
    this to enforce the no-prompt-tuning rule for T069 generality
    validation."""
    held = [a.field_name for a in ANCHOR_PAPERS if a.held_out]
    if len(held) != 1:
        raise RuntimeError(
            f"exactly one anchor must be held-out; got {len(held)}: {held!r}"
        )
    return held[0]


__all__ = [
    "ANCHOR_PAPERS",
    "AnchorPaper",
    "CalibrationDomain",
    "all_domains",
    "get_anchor",
    "held_out_domain",
]
