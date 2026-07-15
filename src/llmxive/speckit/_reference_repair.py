"""Autonomous repair of dead references in a project's ``research.md``.

The FR-006 hard gate (:func:`llmxive.speckit._research_guard.assert_urls_reachable`)
raises on the FIRST unreachable reference, holding the project at ``clarified``.
A single rotted dataset link (e.g. a HuggingFace dataset that has since 404'd)
should NOT tank the whole project: a librarian agent should first SEARCH for the
correct location of the same resource — or a suitable replacement dataset for the
same intent — and only fail the gate when no reachable replacement can be found.

This module runs BEFORE the hard gate (wired into ``plan_cmd._write_and_validate``)
and, for each dead reference:

1. derives the *intent* the reference served (the markdown link anchor, the
   surrounding sentence, and the salient name tokens in the URL path — e.g. the
   HuggingFace ``owner/dataset`` slug);
2. asks the EXISTING librarian (:func:`llmxive.librarian.dataset_resolver.resolve_datasets`,
   the planner's own verified-URL source) for a VERIFIED, reachable replacement
   URL for that intent;
3. RE-PROBES the proposed replacement with the research-guard's own
   :func:`llmxive.speckit._research_guard._probe` — never swapping one dead URL
   for another, and never fabricating one (Constitution II);
4. replaces the dead URL in the ``research.md`` text and records the swap to an
   auditable log (``state/reference_repairs/<project>.json``) plus an appended
   note in ``research.md`` — repairs are NEVER silent.

A librarian/search failure for any single reference degrades that reference to
"unresolved" (the gate will then raise for it) — it never crashes the plan run
(Constitution V: fail fast at the gate, not by an unhandled exception).

SSoT (Constitution I): reachability + reference extraction are reused from
``_research_guard`` (``_probe`` / ``find_unreachable_references``); the search is
reused from the librarian (``dataset_resolver``) — nothing is re-implemented here.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from llmxive.speckit._research_guard import (
    UnreachableReference,
    _probe,
    find_unreachable_references,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReplacementResult:
    """Outcome of searching for a replacement for ONE dead reference.

    ``url`` is the verified, re-probed replacement (``None`` when none was used).
    ``reason`` makes the WHY actionable — distinguishing a LEGITIMATE no-op
    (``"no_verified_replacement"`` — the librarian searched and found nothing
    reachable) from a SYSTEMIC breakage (``"resolver_error: <Type>: <detail>"`` —
    the resolver/network itself broke). Both still fail-open (the dead URL falls
    through to the FR-006 gate), but a systemic breakage is logged as a WARNING so
    "the repair machinery is down" is not silently indistinguishable from "there
    is genuinely no replacement." ``reason`` is ``""`` on a successful swap.
    """

    url: str | None
    reason: str = ""

# Reachability probe budget for a candidate replacement (seconds). Matches the
# hard gate's default so "reachable here" == "reachable at the gate".
_PROBE_TIMEOUT = 10

# Per-resolver wall-clock budget for finding a replacement for ONE dead ref.
_RESOLVE_BUDGET_S = 120

# Tokens in a URL path that are structural, not part of the resource name, so
# they don't pollute the derived search intent.
_URL_NOISE_TOKENS = {
    "datasets", "dataset", "resolve", "main", "raw", "blob", "tree", "data",
    "download", "files", "record", "records", "api", "v1", "v2", "www", "com",
    "org", "co", "huggingface", "github", "zenodo", "figshare", "http", "https",
}


def _markdown_anchor_for(text: str, url: str) -> str:
    """Return the markdown link anchor ``[anchor](url)`` for ``url`` if present."""
    m = re.search(
        r"\[([^\]]+)\]\(\s*" + re.escape(url) + r"[^)]*\)",
        text,
    )
    return m.group(1).strip() if m else ""


def _surrounding_line(text: str, url: str) -> str:
    """Return the (cleaned) line containing ``url`` — its in-prose context."""
    for line in text.splitlines():
        if url in line:
            # Strip markdown noise that dilutes a search query.
            cleaned = re.sub(r"https?://\S+", " ", line)
            cleaned = re.sub(r"[#*`>\-\[\]\(\)|]", " ", cleaned)
            return re.sub(r"\s+", " ", cleaned).strip()
    return ""


def _name_tokens_from_url(url: str) -> str:
    """Salient resource-name tokens from a URL path (e.g. the HF dataset slug).

    ``https://huggingface.co/datasets/AcmeOrg/cool_dataset/resolve/main/x.csv``
    → ``AcmeOrg cool dataset``. Structural tokens (``datasets``, ``resolve``,
    ``main``, …) and file extensions are dropped.
    """
    path = re.sub(r"^https?://", "", url)
    raw = re.split(r"[/?#]", path)
    out: list[str] = []
    for seg in raw:
        seg = seg.strip()
        if not seg or ("." in seg and re.search(r"\.[a-z0-9]{1,6}$", seg)):
            # Skip filenames / hostnames with extensions (x.csv, host.co).
            if seg.lower() in _URL_NOISE_TOKENS:
                continue
            # A hostname like huggingface.co → drop entirely.
            if re.search(r"\.[a-z]{2,}$", seg) and "/" not in seg and len(seg.split(".")) <= 3 and not seg[0].isdigit():
                continue
        words = re.split(r"[-_]+", seg)
        for w in words:
            wl = w.lower()
            if not w or wl in _URL_NOISE_TOKENS or len(w) < 2:
                continue
            if w not in out:
                out.append(w)
    return " ".join(out[:8])


def _derive_intent(research_md_text: str, url: str) -> str:
    """Best free-text *intent* for the resource the dead ``url`` pointed at.

    Combines (in priority order) the markdown link anchor, the salient name
    tokens from the URL path, and the surrounding prose line. The anchor + URL
    slug are the highest-signal cues for "what dataset/paper was this".
    """
    anchor = _markdown_anchor_for(research_md_text, url)
    slug = _name_tokens_from_url(url)
    line = _surrounding_line(research_md_text, url)
    parts = [p for p in (anchor, slug, line) if p]
    # De-dup tokens while preserving order; cap length so a verbose line doesn't
    # dilute the dataset-resolver's name-token extraction.
    seen: set[str] = set()
    toks: list[str] = []
    for tok in " ".join(parts).split():
        key = tok.lower()
        if key not in seen:
            seen.add(key)
            toks.append(tok)
    return " ".join(toks[:24]).strip()


def _find_replacement_url(
    intent: str, *, project_dir: Path, repo_root: Path
) -> ReplacementResult:
    """Ask the librarian for a VERIFIED, reachable replacement URL for ``intent``.

    Uses the planner's existing verified-URL source
    (:func:`llmxive.librarian.dataset_resolver.resolve_datasets`), which web-
    searches real registries (HF Hub / Zenodo / figshare / DataCite), probes each
    candidate for reachability + a sample-format sniff, and returns only verified
    candidates. The chosen URL is then RE-PROBED with the research-guard's own
    ``_probe`` so it is guaranteed to pass the identical hard gate.

    Returns a :class:`ReplacementResult`. NEVER raises — but instead of
    flattening every failure to a bare ``None`` (which made a systemic resolver/
    network breakage indistinguishable from a legitimate "nothing found"), it
    threads a typed ``reason``: ``"resolver_error: …"`` when the resolver itself
    raised (systemic — logged as a WARNING), ``"no_verified_replacement"`` when it
    searched and found nothing reachable (a legitimate no-op), and ``""`` on a
    successful swap.
    """
    if not intent.strip():
        return ReplacementResult(None, "empty_intent")
    try:
        # Imported lazily: dataset_resolver pulls ``requests``/``urllib3`` and
        # the registry-search path, which offline unit tests monkeypatch.
        from llmxive.librarian.dataset_resolver import resolve_datasets

        resolved = resolve_datasets(
            intent,
            project_dir=project_dir,
            repo_root=repo_root,
            budget_s=_RESOLVE_BUDGET_S,
        )
    except Exception as exc:  # degrade, never crash the plan run.
        # Systemic breakage (resolver bug / network down): keep fail-open but make
        # the WHY actionable rather than an indistinguishable None.
        reason = f"resolver_error: {type(exc).__name__}: {exc}"
        logger.warning(
            "reference-repair: librarian search BROKE for %r (%s) — degrading to "
            "unresolved; this is a systemic failure, NOT 'no replacement found'",
            intent, reason,
        )
        return ReplacementResult(None, reason)

    for ds in resolved.datasets:
        if ds.status != "verified":
            continue
        for cand in ds.candidates:
            cand_url = str(cand.get("url") or "")
            if not cand_url:
                continue
            # Re-probe with the SAME gate probe — never trust a candidate URL
            # blindly; it must pass FR-006's exact reachability check.
            try:
                _probe(cand_url, timeout=_PROBE_TIMEOUT)
            except UnreachableReference:
                continue
            return ReplacementResult(cand_url, "")
    return ReplacementResult(None, "no_verified_replacement")


def _project_slug(project_dir: Path) -> str:
    """Stable per-project log filename stem (the ``PROJ-###-…`` dir name)."""
    return project_dir.name


def _log_repairs(
    repairs: list[dict[str, str]], *, project_dir: Path, repo_root: Path
) -> Path | None:
    """Append the swap records to ``state/reference_repairs/<project>.json``.

    Returns the log path written, or ``None`` when there were no repairs.
    """
    if not repairs:
        return None
    log_dir = Path(repo_root) / "state" / "reference_repairs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{_project_slug(project_dir)}.json"
    existing: list[dict[str, object]] = []
    if log_path.exists():
        try:
            loaded = json.loads(log_path.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                existing = loaded
        except (json.JSONDecodeError, OSError):
            existing = []
    entry = {
        "repaired_at": datetime.now(UTC).isoformat(),
        "project": _project_slug(project_dir),
        "repairs": repairs,
    }
    existing.append(entry)
    log_path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    return log_path


_REPAIR_NOTE_HEADER = "## Reference repairs (autonomous, FR-006)"


def _append_repair_note(research_md: str, repairs: list[dict[str, str]]) -> str:
    """Append an auditable note to ``research.md`` listing each swap.

    A dead → live swap is NEVER silent: the note records the original dead URL,
    its reason, the verified replacement, and the derived intent, so a reviewer
    can see exactly what the librarian changed.
    """
    if not repairs:
        return research_md
    lines = [
        "",
        _REPAIR_NOTE_HEADER,
        "",
        (
            "The following references were unreachable at plan time and were "
            "automatically replaced by a librarian-verified, reachable source "
            "for the same intent (each replacement was re-probed for HTTP "
            "2xx/3xx):"
        ),
        "",
    ]
    for r in repairs:
        lines.append(
            f"- `{r['dead_url']}` ({r['reason']}) → `{r['replacement_url']}` "
            f"[intent: {r['intent']}]"
        )
    note = "\n".join(lines) + "\n"
    body = research_md.rstrip("\n")
    return f"{body}\n{note}"


def repair_research_references(
    files: dict[str, str], *, project_dir: Path, repo_root: Path
) -> tuple[dict[str, str], list[str]]:
    """Repair dead references in ``files['research.md']`` before the FR-006 gate.

    For every unreachable reference (found via
    :func:`llmxive.speckit._research_guard.find_unreachable_references`), derive
    the intent and ask the librarian for a VERIFIED, reachable replacement URL
    (which is re-probed). Each successful swap is applied to the ``research.md``
    text and recorded both in an appended note and in
    ``state/reference_repairs/<project>.json`` (auditable, never silent).

    Args:
        files: the plan-artifact map (as produced by ``plan_cmd._split_multi_file``).
        project_dir: the project directory (``projects/PROJ-###-…``).
        repo_root: the repository root (for the ``state/`` repair log).

    Returns:
        ``(updated_files, unresolved)`` where ``updated_files`` is ``files`` with
        a possibly-rewritten ``research.md`` (a NEW dict; the input is not
        mutated), and ``unresolved`` is the list of dead URLs for which no
        reachable replacement was found (the FR-006 gate will then raise on
        them). When nothing was dead, ``files`` is returned unchanged and
        ``unresolved`` is empty.
    """
    research_md = files.get("research.md", "")
    if not research_md:
        return files, []

    dead = find_unreachable_references(research_md)
    if not dead:
        return files, []

    updated = research_md
    repairs: list[dict[str, str]] = []
    unresolved: list[str] = []
    for dead_url, reason in dead:
        intent = _derive_intent(research_md, dead_url)
        result = _find_replacement_url(
            intent, project_dir=project_dir, repo_root=repo_root
        )
        if result.url and result.url != dead_url:
            updated = updated.replace(dead_url, result.url)
            repairs.append(
                {
                    "dead_url": dead_url,
                    "reason": reason,
                    "replacement_url": result.url,
                    "intent": intent,
                }
            )
            logger.info(
                "reference-repair: swapped dead %r → verified %r (intent=%r)",
                dead_url, result.url, intent,
            )
        else:
            unresolved.append(dead_url)
            if result.reason.startswith("resolver_error:"):
                # Systemic breakage — surface it distinctly (WARNING) so an
                # outage isn't silently read as "no replacement exists".
                logger.warning(
                    "reference-repair: could NOT repair dead %r (intent=%r) due to "
                    "a SYSTEMIC failure (%s) — leaving for the FR-006 gate",
                    dead_url, intent, result.reason,
                )
            else:
                logger.info(
                    "reference-repair: NO verified replacement for dead %r "
                    "(intent=%r, %s) — leaving for the FR-006 gate",
                    dead_url, intent, result.reason or "no_verified_replacement",
                )

    if repairs:
        updated = _append_repair_note(updated, repairs)
        _log_repairs(repairs, project_dir=project_dir, repo_root=repo_root)
        new_files = dict(files)
        new_files["research.md"] = updated
        return new_files, unresolved

    return files, unresolved


__all__ = ["ReplacementResult", "repair_research_references"]
