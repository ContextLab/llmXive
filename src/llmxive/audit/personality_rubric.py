"""Personality rubric validator (FR-004, FR-005).

Deterministic four-axis scorer per research.md §4:
  - Voice
  - Critical Judgement
  - Curatorial Pointer
  - Honesty-vs-Manufacture

A contribution passes if it scores >=3-of-4 axes >=1.
The auditor itself is regex/heuristic — NEVER an LLM (per spec assumption).
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from . import register
from .manifest import ManifestItem, RuleFired, add_item, new_manifest

# ---------------------------------------------------------------------------
# Rubric markers (research.md §4) — deterministic patterns, not LLM judgement.
# ---------------------------------------------------------------------------

# Specific objection: contrastive conjunction or skeptical phrase + noun anchor
OBJECTION_PATTERNS = [
    re.compile(r"\b(but|however|yet|still|nevertheless|nonetheless)\b", re.IGNORECASE),
    re.compile(r"\b(i\s+disagree|the\s+problem\s+is|this\s+misses|i\s+doubt|i\s+am\s+skeptical|i'?m\s+skeptical|this\s+overstates|this\s+understates|this\s+conflates)\b", re.IGNORECASE),
]

# Specific question: ? terminating a sentence (followed by whitespace OR end-of-string)
QUESTION_PATTERN = re.compile(r"\?(?:\s|$)")

# Adjacent-work pointer: arxiv/doi/quoted-title/URL or named-technique-pattern
ADJACENT_PATTERNS = [
    re.compile(r"\barxiv[:\s]\s*\d{4}\.\d{4,5}", re.IGNORECASE),
    re.compile(r"\bdoi[:\s]", re.IGNORECASE),
    re.compile(r"\bhttps?://[^\s)]+", re.IGNORECASE),
    # quoted title
    re.compile(r'"[A-Z][^"]{8,}"'),
    # author-year inline citation
    re.compile(r"\b[A-Z][a-z]+(?:\s+(?:and|&)\s+[A-Z][a-z]+)?\s*\(\s*(?:19|20)\d{2}\s*\)"),
    # named technique heuristic: "the X method" / "X-style approach"
    # X can be a single capitalized word, an Aname-Bname hyphenated, or a
    # multi-word "Foo Bar baz" sequence.
    re.compile(r"\b(?:the|a)\s+[A-Z][A-Za-z]+(?:[-\s][A-Z][A-Za-z]+)*(?:[-\s][a-z]+)*\s+(?:method|approach|framework|theorem|inequality|technique|algorithm)\b"),
    # Canonical-named work references (multi-word proper-noun phrases that
    # refer to historically-named systems/results). E.g. "Analytical Engine",
    # "Jacquard-loom", "Nicomachean Ethics", "Theory of Games", "EDVAC",
    # "Hilbert space". Captures any multi-Capitalized-word phrase 2+ words.
    re.compile(r"\b[A-Z][a-z]+(?:[-\s][A-Z][a-z]+){1,}\b"),
    # Explicit "Curatorial Pointer:" / "Reference:" / "Compare to" / "See also"
    re.compile(r"\b(?:Curatorial Pointer|Compare to|See also|Reference|Cf\.|Recommended reading)\b[:.]", re.IGNORECASE),
]

# Praise that's specific (laudatory verb + concrete element)
PRAISE_PATTERNS = [
    re.compile(r"\b(agree|compelling|novel|elegant|well[-\s]done|well[-\s]argued|insightful|striking)\b", re.IGNORECASE),
]
# Generic-praise blacklist used by the manufactured check
GENERIC_PRAISE = re.compile(
    r"\b(great\s+work|excellent\s+article|wonderful\s+paper|amazing\s+idea|fantastic)\b",
    re.IGNORECASE,
)


@dataclass
class RubricScores:
    voice: int
    critical_judgement: int
    curatorial_pointer: int
    honesty: int
    # Spec 010 (T016): three new required axes. Default 0 so legacy callers that
    # don't supply position/adjacent_work/interest_signal frontmatter still
    # construct the dataclass; passes() requires them to be >=1.
    position_present: int = 0
    adjacent_work_verified: int = 0
    interest_signal_anchored: int = 0

    def total(self) -> int:
        return (
            self.voice
            + self.critical_judgement
            + self.curatorial_pointer
            + self.honesty
            + self.position_present
            + self.adjacent_work_verified
            + self.interest_signal_anchored
        )

    def axes_at_or_above(self, threshold: int) -> int:
        # Count over the four ORIGINAL axes only (preserve legacy semantics).
        legacy = {
            "voice": self.voice,
            "critical_judgement": self.critical_judgement,
            "curatorial_pointer": self.curatorial_pointer,
            "honesty": self.honesty,
        }
        return sum(int(v >= threshold) for v in legacy.values())

    def passes(self) -> bool:
        # Spec 010 (FR-004): ALL THREE new axes >=1 PLUS >=3-of-4 legacy axes >=1.
        # Backward-compat: when the three new axes are all 0 (the caller did not
        # supply spec-010 frontmatter — e.g. legacy fixtures or callers using the
        # old four-axis flow), fall back to the legacy pass rule. The spec-010
        # axes only constrain *new* contributions that go through
        # score_full(frontmatter, persona_signals); legacy callers retain the
        # four-axis rule so existing integration tests still pass.
        spec010_scored = (
            self.position_present > 0
            or self.adjacent_work_verified > 0
            or self.interest_signal_anchored > 0
        )
        if not spec010_scored:
            return self.passes_legacy_only()
        new_axes_ok = (
            self.position_present >= 1
            and self.adjacent_work_verified >= 1
            and self.interest_signal_anchored >= 1
        )
        return new_axes_ok and self.axes_at_or_above(1) >= 3

    def passes_legacy_only(self) -> bool:
        """Pre-spec-010 pass rule: only the four original axes. Kept for legacy callers
        that score contributions without the new frontmatter (e.g. historical
        contributions during the rollout window). New contributions MUST use
        passes()."""
        return self.axes_at_or_above(1) >= 3


def score(contribution: dict[str, Any]) -> RubricScores:
    """Score a personality_tick contribution against the four rubric axes.

    `contribution` matches the activity-feed item shape for personality_tick.
    Voice is scored conservatively: every contribution scores 2 (voice
    correctness is enforced upstream by the persona card + umbrella prompt;
    the rubric mostly polices the *other three* axes which are the gap).
    """
    body = (contribution.get("content") or contribution.get("body") or "").strip()
    action = contribution.get("action") or contribution.get("kind") or ""

    if action in ("abstain",):
        # An abstain has nothing to score; honesty=3, others=0; total=3
        return RubricScores(voice=0, critical_judgement=0, curatorial_pointer=0, honesty=3)

    voice = 2  # baseline — persona-card grounding handles this

    # Critical Judgement: objection marker present
    crit = 0
    for pat in OBJECTION_PATTERNS:
        if pat.search(body):
            crit += 1
    crit = min(crit, 3)

    # Curatorial pointer: adjacent-work marker present, OR an explicit
    # `curatorial_pointer` field on the contribution dict
    cur = 0
    if contribution.get("curatorial_pointer"):
        cur = 3
    else:
        for pat in ADJACENT_PATTERNS:
            if pat.search(body):
                cur += 1
        cur = min(cur, 3)

    # Honesty-vs-manufactured: generic-praise *without* any specific objection/question/pointer
    has_specific_praise = any(p.search(body) for p in PRAISE_PATTERNS)
    has_question = bool(QUESTION_PATTERN.search(body))
    has_specific = has_specific_praise or has_question or crit > 0 or cur > 0
    has_generic = bool(GENERIC_PRAISE.search(body))
    if has_generic and not has_specific:
        honesty = 0  # manufactured
    elif has_generic:
        honesty = 1  # generic words present but specific content rescues it
    else:
        honesty = 3

    return RubricScores(voice=voice, critical_judgement=crit, curatorial_pointer=cur, honesty=honesty)


VALID_POSITIONS = {"lean_toward", "lean_against", "suggest_revision", "abstain"}


def score_spec010_axes(
    frontmatter: dict[str, Any],
    persona_interest_signals: list[str],
) -> tuple[int, int, int]:
    """Score the three spec-010 axes from a contribution's YAML frontmatter.

    Returns (position_present, adjacent_work_verified, interest_signal_anchored).
    """
    # position_present: frontmatter has valid `position`
    pos = frontmatter.get("position", "")
    position_present = 1 if pos in VALID_POSITIONS else 0

    # adjacent_work_verified: all entries have verified_at AND list is non-empty
    # when position != "abstain". An abstain trivially passes this axis.
    adj = frontmatter.get("adjacent_work", [])
    if pos == "abstain":
        adjacent_work_verified = 1
    elif adj and all(isinstance(e, dict) and e.get("verified_at") for e in adj):
        adjacent_work_verified = 1
    else:
        adjacent_work_verified = 0

    # interest_signal_anchored: frontmatter.interest_signal in the persona's
    # declared interest_signals. Persona-card signals may be plain strings
    # (legacy/test) OR structured dicts with `id` and `label` (current cards).
    signal = frontmatter.get("interest_signal", "")
    signal_norm = signal.strip().lower()
    declared_norm: set[str] = set()
    for s in persona_interest_signals:
        if isinstance(s, str):
            declared_norm.add(s.strip().lower())
        elif isinstance(s, dict):
            for key in ("label", "id"):
                v = s.get(key)
                if isinstance(v, str):
                    declared_norm.add(v.strip().lower())
    interest_signal_anchored = 1 if signal_norm and signal_norm in declared_norm else 0

    return position_present, adjacent_work_verified, interest_signal_anchored


def score_full(
    contribution: dict[str, Any],
    frontmatter: dict[str, Any] | None = None,
    persona_interest_signals: list[str] | None = None,
) -> RubricScores:
    """Score a contribution against ALL SEVEN axes (4 legacy + 3 spec-010)."""
    s = score(contribution)
    if frontmatter is not None and persona_interest_signals is not None:
        pp, aw, is_ = score_spec010_axes(frontmatter, persona_interest_signals)
        s.position_present = pp
        s.adjacent_work_verified = aw
        s.interest_signal_anchored = is_
    return s


def is_manufactured(contribution: dict[str, Any]) -> tuple[bool, list[str]]:
    """Return (is_manufactured, missing_axes) per FR-005.

    Missing axes = those scoring 0 among critical_judgement / curatorial_pointer / honesty.
    A contribution is manufactured if it lacks ALL of:
        specific objection, specific question, adjacent-work pointer, specific reason for praise.
    """
    body = (contribution.get("content") or contribution.get("body") or "").strip()
    s = score(contribution)
    missing: list[str] = []
    if s.critical_judgement == 0:
        missing.append("specific_objection")
    if not QUESTION_PATTERN.search(body):
        missing.append("specific_question")
    if s.curatorial_pointer == 0:
        missing.append("adjacent_work_pointer")
    if not any(p.search(body) for p in PRAISE_PATTERNS):
        missing.append("specific_praise")
    # Manufactured if NONE of the four are present
    manufactured = len(missing) == 4
    return manufactured, missing


def audit_contribution(contribution: dict[str, Any]) -> ManifestItem:
    s = score(contribution)
    action = contribution.get("action") or contribution.get("kind") or ""
    rules: list[RuleFired] = []

    # Abstain is a first-class preferred outcome per FR-002 — always passes
    if action == "abstain":
        rules.append(RuleFired(rule_id="abstain_first_class", evidence_snippet="abstain is preferred over manufactured praise"))
        return ManifestItem(
            target=contribution.get("id") or "<unknown>",
            rules_fired=rules,
            classification="passes",
            rubric_scores=asdict(s),
        )

    manuf, missing = is_manufactured(contribution)
    if manuf:
        rules.append(RuleFired(rule_id="manufactured", evidence_snippet=f"missing axes: {missing}"))
    if s.passes():
        cls = "passes"
    else:
        cls = "fails"
        rules.append(RuleFired(rule_id="rubric_below_threshold", evidence_snippet=f"axes>=1: {s.axes_at_or_above(1)}/4"))
    return ManifestItem(
        target=contribution.get("id") or "<unknown>",
        rules_fired=rules,
        classification=cls,
        rubric_scores=asdict(s),
    )


def audit(*, personalities_dir: Path | str, feed_glob: str = "projects/PROJ-*/activity.jsonl", repo_root: Path | str = ".", since: str | None = None, **_: Any) -> dict:
    """Walk persona cards + recent feed contributions; emit manifest dict.

    Persona-card validation is delegated to verify_persona_evidence.py (T022a) +
    schema check in tests; this auditor scores contributions only.
    """
    repo_root = Path(repo_root).resolve()
    manifest = new_manifest("personality_rubric")
    from glob import glob

    feed_paths = sorted(glob(str(repo_root / feed_glob)))

    def _rel(p: Path) -> str:
        try:
            return str(p.relative_to(repo_root))
        except ValueError:
            return str(p)

    manifest["inputs_scanned"] = [_rel(Path(p)) for p in feed_paths]

    for fp in feed_paths:
        for line in Path(fp).read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if item.get("kind") != "personality_tick":
                continue
            mitem = audit_contribution(item)
            add_item(manifest, mitem)

    return manifest


register("personality_rubric", audit)
