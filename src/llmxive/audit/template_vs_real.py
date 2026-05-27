"""Template-vs-real auditor (FR-006, FR-007).

Deterministic classifier per research.md §3:
  1. Literal-template-string density >=3 hits  -> template
  2. Unfilled [bracket] markers >=40%          -> template
  3. Body length <60% bodies short             -> partial (escalates with #1)
  Legacy-migration discriminator (research.md §10) rescues real prose
  even when templated headings remain.

Outputs an Audit Manifest. Pruning is a separate mode invoked by audit.cli.
"""

from __future__ import annotations

import json
import re
from glob import glob
from pathlib import Path
from typing import Any

from . import register
from .manifest import ManifestItem, RuleFired, add_item, new_manifest

# Literal placeholder strings drawn from .specify/templates/*.md
# We extract them at runtime so we stay in sync with template evolution.
PLACEHOLDER_BRACKET_RE = re.compile(r"\[[A-Z][^\]]{2,80}\]")  # [FEATURE NAME], [Brief Title], etc.

# Structural task-format labels (e.g. "[US1]", "[Story]", "[TaskID]") appear
# VERBATIM in a *real* tasks.md ("- [ ] T001 [P] [US1] ...") — they are required
# format markers, not fill-in placeholders. They MUST NOT be learned as template
# phrases, or every correctly-formatted tasks.md would mis-classify 'template'.
STRUCTURAL_LABEL_RE = re.compile(r"^\[(Story\??|US\d+|TaskID|ID|P\??)\]$")
ACTION_REQUIRED_RE = re.compile(r"ACTION REQUIRED:", re.IGNORECASE)
META_INSTRUCTION_RE = re.compile(
    r"(fill (?:them|it|this|out|in) (?:out )?with the right|placeholders\?|REMOVE IF UNUSED)",
    re.IGNORECASE,
)
LEGACY_MIGRATION_RE = re.compile(
    r"\*\*Status\*\*:\s*migrated from legacy technical-design|^\*\*Status\*\*:\s*active",
    re.MULTILINE,
)

# H2 + H3 headings to gauge body density
HEADING_RE = re.compile(r"^(##+)\s+(.*?)$", re.MULTILINE)


def _load_template_phrases(templates_dir: Path) -> list[str]:
    """Pull literal placeholder/meta strings from the template files."""
    phrases: list[str] = []
    for tmpl in sorted(templates_dir.glob("*.md")):
        text = tmpl.read_text()
        # Take [Bracketed Placeholder] strings, excluding structural task-format
        # labels that legitimately survive into a real tasks.md.
        phrases.extend(
            p for p in PLACEHOLDER_BRACKET_RE.findall(text)
            if not STRUCTURAL_LABEL_RE.match(p)
        )
        # Take meta-instruction sentences
        for m in META_INSTRUCTION_RE.finditer(text):
            phrases.append(m.group(0))
    # Dedupe; keep stable order
    seen = set()
    out: list[str] = []
    for p in phrases:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _placeholder_scan_text(text: str) -> str:
    """Return ``text`` with content that legitimately contains brackets removed,
    so template-placeholder detection (Rules 1 & 2) sees only standalone
    ``[PLACEHOLDER]`` tokens in prose.

    Strips fenced code/diagram blocks (```...``` and ~~~...~~~ — e.g. a mermaid
    ER diagram or an ASCII data-flow chart whose node labels look like
    ``[Dataset Download]``), HTML comments, and markdown link/image targets
    (``[text](url)``, ``[text][ref]``). Brackets in those constructs are
    CONTENT, not fill-in placeholders, and previously caused real planner
    artifacts to mis-classify ``template`` (spec 014).
    """
    t = re.sub(r"```.*?```", "", text, flags=re.S)
    t = re.sub(r"~~~.*?~~~", "", t, flags=re.S)
    t = re.sub(r"<!--.*?-->", "", t, flags=re.S)
    t = re.sub(r"!?\[[^\]]*\]\([^)]*\)", "", t)   # [text](url) / ![alt](url)
    t = re.sub(r"!?\[[^\]]*\]\[[^\]]*\]", "", t)  # [text][ref]
    return t


def classify(path: Path, templates_dir: Path | None = None) -> tuple[str, list[RuleFired]]:
    """Classify one artifact as real | partial | template."""
    text = Path(path).read_text()
    # Rule 2 (raw bracket density) operates on a "scan" view with fenced blocks,
    # HTML comments, and markdown links removed — brackets there are content
    # (mermaid labels, code, link text), not placeholders. Rule 1 (learned
    # phrases) uses the full text.
    scan = _placeholder_scan_text(text)
    rules: list[RuleFired] = []

    # Rule 0: legacy migration with substantive body -> always real
    if LEGACY_MIGRATION_RE.search(text) and len(_strip_md(text)) >= 500:
        rules.append(RuleFired(
            rule_id="legacy_migration_discriminator",
            evidence_snippet=text.splitlines()[2][:200] if len(text.splitlines()) > 2 else "<status>",
        ))
        return "real", rules

    # Rule 1: literal template strings
    template_phrases = _load_template_phrases(templates_dir) if templates_dir else []
    hits = 0
    sample_hits: list[str] = []
    for phrase in template_phrases:
        # Rule 1 matches LEARNED template phrases (e.g. "[REMOVE IF UNUSED]",
        # "[FEATURE]") against the FULL text — they are genuine template signals
        # wherever they appear, including inside a template's fenced examples.
        # (Structural task labels like "[US1]" are already excluded at learn
        # time, so a real tasks.md does not trip this rule.)
        if phrase and phrase in text:
            hits += 1
            if len(sample_hits) < 3:
                sample_hits.append(phrase)
    if hits >= 3:
        rules.append(RuleFired(
            rule_id="literal_template_phrases>=3",
            evidence_snippet=f"hits={hits}; sample={sample_hits}",
        ))
        # Also check action-required meta-instructions
        if ACTION_REQUIRED_RE.search(text):
            rules.append(RuleFired(
                rule_id="action_required_marker_present",
                evidence_snippet="<ACTION REQUIRED block remains>",
            ))
        return "template", rules

    # Rule 2: unfilled bracket density (on the scan view).
    # Count ONLY multi-word descriptive placeholders ("[FEATURE NAME]",
    # "[e.g., ...]", "[Brief Title]") — the genuine "saturated unfilled
    # template" signal. Single-token brackets are excluded: they are either
    # real template placeholders ("[FEATURE]", "[DATE]"), which Rule 1 already
    # catches from the learned set, OR LLM-emitted labels/annotations
    # ("[P]", "[US1]", "[REVISION]", "[X]") that legitimately appear in a real
    # tasks.md and must not be mistaken for unfilled placeholders.
    brackets = [
        b for b in PLACEHOLDER_BRACKET_RE.findall(scan)
        if not STRUCTURAL_LABEL_RE.match(b) and " " in b[1:-1].strip()
    ]
    if brackets and len(brackets) >= 6:
        # treat >=6 unfilled multi-word bracket placeholders as template
        rules.append(RuleFired(
            rule_id="unfilled_bracket_density",
            evidence_snippet=f"{len(brackets)} bracket markers; sample={brackets[:3]}",
        ))
        return "template", rules

    # Rule 3: section-body density
    short_bodies, total_bodies = _body_density(text)
    if total_bodies >= 3 and short_bodies / total_bodies >= 0.6:
        rules.append(RuleFired(
            rule_id="body_density_short>=60pct",
            evidence_snippet=f"{short_bodies}/{total_bodies} sections <20 chars",
        ))
        # Escalate to template if rule 1 also fired -> already returned above
        return "partial", rules

    # Default: real
    rules.append(RuleFired(rule_id="default_real", evidence_snippet="no template signal"))
    return "real", rules


def _body_density(text: str) -> tuple[int, int]:
    """Count (short, total) section bodies between H2+ headings.

    A section counts as "short" only when it has essentially no content of any
    kind. Markdown tables, fenced code/diagram blocks (```...``` — including
    mermaid), and list items all count as real content: a data-model.md that
    specifies entities via attribute tables or an ER diagram is NOT "partial".
    A parent heading whose immediate body is empty because its content lives in
    deeper subsections (e.g. ``## Entity Definitions`` followed by ``### Foo``)
    is structural, not missing content, and is likewise not short.

    Spec 014 bug-fix: the previous implementation stripped fenced blocks before
    measuring, so a legitimately diagram/table/code-heavy artifact (mermaid ER
    diagram, per-entity tables, fenced CSV schemas) was mis-classified
    ``partial`` and the Planner could never advance any project past
    ``clarified``. Genuinely empty/stub sections (headings with no content) are
    still flagged; literal-template artifacts are still caught earlier by the
    template-phrase and bracket-density rules.
    """
    headings = list(HEADING_RE.finditer(text))
    if not headings:
        return 0, 0
    short = 0
    total = 0
    for i, h in enumerate(headings):
        level = len(h.group(1))
        body_start = h.end()
        body_end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        raw_body = text[body_start:body_end]
        # Parent heading: the next heading is deeper and the immediate body is
        # whitespace-only -> content lives in the children; not "missing".
        if (
            i + 1 < len(headings)
            and len(headings[i + 1].group(1)) > level
            and not raw_body.strip()
        ):
            total += 1
            continue
        # Strip only template meta-instruction comments. KEEP fenced blocks,
        # tables, and lists — they are real content.
        body = re.sub(r"<!--.*?-->", "", raw_body, flags=re.S)
        body_clean = re.sub(r"\s+", " ", body).strip()
        if len(body_clean) < 20:
            short += 1
        total += 1
    return short, total


def _strip_md(text: str) -> str:
    """Strip markdown for body-length heuristics (rule 0)."""
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"^#+\s+.*$", "", text, flags=re.M)
    text = re.sub(r"\[[^\]]{0,80}\]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def audit(*, projects_dir: Path | str, templates_dir: Path | str, repo_root: Path | str = ".", **_: Any) -> dict:
    repo_root = Path(repo_root).resolve()
    projects_dir = Path(projects_dir).resolve()
    templates_dir = Path(templates_dir).resolve()
    if not projects_dir.exists():
        raise FileNotFoundError(f"projects_dir does not exist: {projects_dir}")
    if not templates_dir.exists():
        raise FileNotFoundError(f"templates_dir does not exist: {templates_dir}")

    manifest = new_manifest("template_vs_real")

    artifacts = sorted(
        [p.resolve() for p in projects_dir.glob("PROJ-*/specs/**/*.md")]
        + [p.resolve() for p in projects_dir.glob("PROJ-*/specs/**/*.yaml")]
        + [p.resolve() for p in projects_dir.glob("PROJ-*/specs/**/*.yml")]
    )

    def _rel(p: Path) -> str:
        try:
            return str(p.relative_to(repo_root))
        except ValueError:
            return str(p)

    manifest["inputs_scanned"] = [_rel(p) for p in artifacts]

    for art in artifacts:
        cls, rules = classify(art, templates_dir=templates_dir)
        add_item(manifest, ManifestItem(
            target=_rel(art),
            rules_fired=rules,
            classification=cls,
        ))

    return manifest


register("template_vs_real", audit)
