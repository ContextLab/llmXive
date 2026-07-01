"""No-code branch of the ingested-paper reprocessor (spec 024).

An externally-ingested paper that ships **no runnable code** cannot be re-run or
back-filled, and we cannot rewrite a third party's paper. Instead we treat it as
prior art and spin up a NEW llmXive *follow-up* study that builds on it:

    summarise the paper -> extract its core ideas -> propose a concrete EXTENSION
    -> write that extension as a ``brainstormed`` idea the normal ``flesh_out``
       agent consumes unchanged.

Because the follow-up is *our* study (not the original authors'), we DROP the
original byline (``paper/metadata.json::authors`` -> ``[]`` and clear the idea
front-matter ``paper_authors:``) so ``web_data._project_authors`` credits only
the llmXive model contributors. We still CITE the original — a parseable
``@article`` in ``paper/source/reference.bib`` plus a "Builds on" lineage line
(with the arXiv URL) in the idea doc.

The single LLM call reuses the SAME backend/model/router the brainstorm and
flesh_out agents use (resolved from ``agents/registry.yaml`` via
:mod:`llmxive.agents.registry`), so this branch inherits the free-model
guarantee and the Dartmouth credit guard automatically. The deterministic
disk-writing helpers are factored out so they can be unit-tested without any
network access (a known summary/extension string is passed straight in).
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

from llmxive.config import repo_root as _repo_root
from llmxive.paper_reprocess.reprocess import project_dir
from llmxive.types import Project, Stage

# The brainstorm/flesh_out agents share one free reasoning model + backend; we
# reuse the brainstorm registry entry so this branch tracks any registry change
# (and inherits ``paid_opt_in: false`` + the credit guard) without duplication.
_SEED_AGENT = "brainstorm"

# Keep the prompt within the model's input window while preserving the parts of
# the paper that carry the science (abstract + body intro/method). 24K chars of
# LaTeX is comfortably inside every free Dartmouth model's context (>=128K tok).
_MAX_PAPER_CHARS = 24_000


# --------------------------------------------------------------------------- #
# Paper-text assembly (deterministic)
# --------------------------------------------------------------------------- #
def _load_metadata(pdir: Path) -> dict:
    meta_path = pdir / "paper" / "metadata.json"
    if not meta_path.is_file():
        raise FileNotFoundError(f"ingested paper has no metadata.json: {meta_path}")
    data = json.loads(meta_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"metadata.json is not a JSON object: {meta_path}")
    return data


def _read_toplevel_tex(pdir: Path, metadata: dict) -> str:
    """Return the concatenated text of the declared top-level .tex file(s),
    falling back to every ``paper/source/*.tex`` when none are declared."""
    source = pdir / "paper" / "source"
    names = [str(n) for n in (metadata.get("toplevel_tex") or []) if str(n).strip()]
    paths: list[Path] = []
    for name in names:
        cand = source / name
        if cand.is_file():
            paths.append(cand)
    if not paths and source.is_dir():
        paths = sorted(source.glob("*.tex"))
    chunks: list[str] = []
    for p in paths:
        try:
            chunks.append(p.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    return "\n\n".join(chunks)


def assemble_paper_text(pdir: Path, metadata: dict, *, max_chars: int = _MAX_PAPER_CHARS) -> str:
    """Assemble the paper text fed to the LLM: title + abstract + the top-level
    LaTeX body, capped at ``max_chars`` so the prompt stays within budget."""
    title = str(metadata.get("title") or "").strip()
    abstract = str(metadata.get("abstract") or "").strip()
    body = _read_toplevel_tex(pdir, metadata)

    parts: list[str] = []
    if title:
        parts.append(f"# Title\n\n{title}")
    if abstract:
        parts.append(f"# Abstract\n\n{abstract}")
    if body:
        parts.append(f"# Full LaTeX source\n\n{body}")
    text = "\n\n".join(parts).strip()
    if len(text) > max_chars:
        text = text[:max_chars].rstrip() + "\n\n[... source truncated ...]"
    return text


# --------------------------------------------------------------------------- #
# The single LLM call (free model, shared router)
# --------------------------------------------------------------------------- #
def _propose_extension(paper_text: str) -> str:
    """ONE real LLM call: summarise the paper, extract its core ideas, and
    propose a concrete CPU-tractable follow-up extension. Returns the model's
    markdown body (consumed verbatim as the idea body)."""
    from llmxive.agents import registry as registry_loader
    from llmxive.backends.base import ChatMessage
    from llmxive.backends.router import chat_with_fallback
    from llmxive.credentials import load_dartmouth_key

    # Resolve the Dartmouth key the SSoT way (never read os.environ directly);
    # populate the env the langchain client reads so the dartmouth backend works.
    key = load_dartmouth_key(prompt_if_missing=False)
    if key:
        import os

        os.environ.setdefault("DARTMOUTH_CHAT_API_KEY", key)

    # The agent registry is PLATFORM config (agents/registry.yaml at the repo
    # root), not per-project state — resolve it via the platform default
    # (config.repo_root(), honoring $LLMXIVE_REPO_ROOT) rather than a project
    # subdir. ``repo_root`` here is the *project* tree, which has no agents/.
    entry = registry_loader.get(_SEED_AGENT)

    system = (
        "You are a research-ideation agent for llmXive, an automated scientific-"
        "discovery platform. You are given an existing (third-party) paper. Your "
        "job is to design a NEW follow-up study that BUILDS ON it — not to "
        "rewrite or critique the original. Respond with GitHub-flavored Markdown "
        "ONLY (no code fences around the whole reply)."
    )
    user = (
        "## Existing paper (prior art)\n\n"
        f"{paper_text}\n\n"
        "## Your task\n\n"
        "1. In 2-4 sentences, summarise what the paper does and its core ideas.\n"
        "2. Propose ONE concrete follow-up research direction that extends the "
        "paper: a new, specific, falsifiable research question that builds on its "
        "findings. Prefer a design that is CPU-tractable (runnable without GPUs) "
        "while remaining scientifically sound and non-trivial.\n"
        "3. Sketch a methodology (data, procedure, expected result) for the "
        "extension.\n\n"
        "Format your reply with these exact sections:\n\n"
        "## Summary of the prior work\n<...>\n\n"
        "## Proposed extension\n<the new research question + why it matters>\n\n"
        "## Methodology sketch\n<data, procedure, expected result>\n"
    )

    response = chat_with_fallback(
        [ChatMessage(role="system", content=system), ChatMessage(role="user", content=user)],
        default_backend=entry.default_backend.value,
        fallback_backends=[b.value for b in entry.fallback_backends],
        model=entry.default_model,
        max_tokens=4096,
    )
    body = (response.text or "").strip()
    if not body:
        raise ValueError("LLM returned an empty extension proposal")
    return body


# --------------------------------------------------------------------------- #
# Deterministic disk writers (unit-testable without a network)
# --------------------------------------------------------------------------- #
def _slugify(text: str) -> str:
    """Mirror submission_intake._slugify: lowercase, hyphenated, ascii-only."""
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return (slug or "idea")[:40].strip("-") or "idea"


def _drop_original_authors(pdir: Path, metadata: dict) -> dict:
    """Set ``paper/metadata.json::authors`` to ``[]`` (the follow-up is ours) and
    persist it. Returns the mutated metadata dict."""
    metadata = dict(metadata)
    metadata["authors"] = []
    meta_path = pdir / "paper" / "metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return metadata


def _bibtex_key(metadata: dict) -> str:
    """A stable, BibTeX-safe citation key for the original paper."""
    arxiv = str(metadata.get("arxiv_id") or "").strip()
    if arxiv:
        return "orig_arxiv_" + re.sub(r"[^A-Za-z0-9]+", "_", arxiv).strip("_")
    title = str(metadata.get("title") or "ingested").strip()
    return "orig_" + (re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_")[:32] or "paper")


def _bibtex_escape(value: str) -> str:
    """Escape the few characters that would break a BibTeX field value."""
    return value.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}").replace('"', "")


def build_bibtex_entry(metadata: dict) -> str:
    """Return a parseable ``@article{...}`` BibTeX entry citing the original."""
    key = _bibtex_key(metadata)
    title = _bibtex_escape(str(metadata.get("title") or "Untitled").strip())
    authors = metadata.get("authors") or metadata.get("_original_authors") or []
    author_field = _bibtex_escape(" and ".join(str(a).strip() for a in authors if str(a).strip()))
    arxiv = str(metadata.get("arxiv_id") or "").strip()
    arxiv_url = str(metadata.get("arxiv_url") or "").strip()
    if not arxiv_url and arxiv:
        arxiv_url = f"https://arxiv.org/abs/{arxiv}"
    # Year: prefer an explicit field, else derive YYYY from an arXiv id (YYMM.*).
    year = str(metadata.get("year") or "").strip()
    if not year:
        m = re.match(r"(\d{2})(\d{2})", arxiv)
        if m:
            year = f"20{m.group(1)}"
    lines = [f"@article{{{key},"]
    lines.append(f"  title = {{{title}}},")
    if author_field:
        lines.append(f"  author = {{{author_field}}},")
    if year:
        lines.append(f"  year = {{{year}}},")
    if arxiv:
        lines.append(f"  eprint = {{{arxiv}}},")
        lines.append("  archivePrefix = {arXiv},")
        lines.append(f"  journal = {{arXiv preprint arXiv:{arxiv}}},")
    if arxiv_url:
        lines.append(f"  url = {{{arxiv_url}}},")
    # Drop a trailing comma on the final field for tidy (and still-parseable) bib.
    lines[-1] = lines[-1].rstrip(",")
    lines.append("}")
    return "\n".join(lines)


def _append_reference_bib(pdir: Path, metadata: dict) -> str:
    """Create/append ``paper/source/reference.bib`` with the original-paper
    citation. Idempotent on the citation key. Returns the citation key."""
    source = pdir / "paper" / "source"
    source.mkdir(parents=True, exist_ok=True)
    bib_path = source / "reference.bib"
    entry = build_bibtex_entry(metadata)
    key = _bibtex_key(metadata)
    existing = bib_path.read_text(encoding="utf-8") if bib_path.is_file() else ""
    if f"@article{{{key}," in existing or f"@article{{{key} " in existing:
        return key  # already cited
    sep = "\n\n" if existing.strip() else ""
    bib_path.write_text(existing.rstrip() + sep + entry + "\n", encoding="utf-8")
    return key


def _write_followup_idea(
    pdir: Path,
    *,
    project: Project,
    metadata: dict,
    extension_body: str,
) -> Path:
    """Write the follow-up idea into ``idea/`` in the EXACT brainstormed format
    (front-matter + ``# <title>`` + body) so ``flesh_out`` consumes it unchanged.
    Clears ``paper_authors:`` and adds a "Builds on" lineage line + arXiv URL."""
    idea_dir = pdir / "idea"
    idea_dir.mkdir(parents=True, exist_ok=True)
    # Replace any pre-existing intake stub idea file(s) so flesh_out reads ONLY
    # the follow-up body (idea_lifecycle globs idea/*.md and concatenates).
    for stale in idea_dir.glob("*.md"):
        stale.unlink()

    title = (project.title or str(metadata.get("title") or "").strip() or "Follow-up study").strip()
    arxiv = str(metadata.get("arxiv_id") or "").strip()
    arxiv_url = str(metadata.get("arxiv_url") or "").strip()
    if not arxiv_url and arxiv:
        arxiv_url = f"https://arxiv.org/abs/{arxiv}"
    orig_title = str(metadata.get("title") or "the ingested paper").strip()

    # Front-matter mirrors submission_intake._create_brainstormed_project, but
    # with NO paper_authors (this is our follow-up — byline = llmXive models).
    fm = ["---", f"field: {project.field}", "submitter: llmxive-paper-reprocess"]
    if arxiv:
        fm.append(f"builds_on_arxiv: {arxiv}")
    fm += ["---", "", f"# {title}", ""]

    lineage = f"**Builds on**: [{orig_title}]({arxiv_url})" if arxiv_url else f"**Builds on**: {orig_title}"
    body = [
        lineage,
        "",
        "This is a llmXive follow-up study that extends the prior work above. "
        "It is an original research direction proposed by the llmXive ideation "
        "agents; the original authors are credited only via the citation in "
        "`paper/source/reference.bib`.",
        "",
        extension_body.strip(),
        "",
    ]

    slug = _slugify(title)
    target = idea_dir / f"{slug}.md"
    target.write_text("\n".join(fm + body), encoding="utf-8")
    return target


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def transform_to_followup(
    project: Project,
    *,
    repo_root: Path,
    extension_body: str,
    metadata: dict,
    pdir: Path,
) -> Project:
    """Deterministic core: given an already-computed ``extension_body``, write
    every artifact (drop authors, cite original, write the brainstormed idea),
    persist the project at ``Stage.BRAINSTORMED``, and return the updated Project.

    Split out from :func:`to_followup_idea` so it can be unit-tested with a known
    summary/extension string and zero network access.
    """
    from llmxive.state import project as project_store

    # Cite the ORIGINAL before we drop the byline from metadata (the bib needs
    # the original author list).
    _append_reference_bib(pdir, metadata)
    # Now drop the original authors from the canonical metadata.
    cleared = _drop_original_authors(pdir, metadata)
    # Write the brainstormed idea (paper_authors already absent from front-matter).
    _write_followup_idea(pdir, project=project, metadata=cleared, extension_body=extension_body)

    now = datetime.now(UTC)
    updated = project.model_copy(update={"current_stage": Stage.BRAINSTORMED, "updated_at": now})
    project_store.save(updated, repo_root=repo_root)
    return updated


def to_followup_idea(project: Project, *, repo_root: Path | None = None) -> Project:
    """Transform a bare no-code ingested paper into a ``brainstormed`` follow-up.

    1. Resolve the project dir; read ``paper/metadata.json`` + the top-level .tex.
    2. ONE free-model LLM call summarises the paper and proposes an extension.
    3. Write the extension as a brainstormed idea (flesh_out-consumable), drop
       the original authors, and cite the original paper.

    Returns ``project.model_copy(update={current_stage: BRAINSTORMED, ...})`` and
    persists it via ``llmxive.state.project.save``.
    """
    repo = repo_root or _repo_root()
    pdir = project_dir(project, repo)
    metadata = _load_metadata(pdir)
    paper_text = assemble_paper_text(pdir, metadata)
    if not paper_text:
        raise ValueError(f"ingested paper has no usable text (title/abstract/tex): {pdir}")
    extension_body = _propose_extension(paper_text)
    return transform_to_followup(
        project,
        repo_root=repo,
        extension_body=extension_body,
        metadata=metadata,
        pdir=pdir,
    )


def spawn_followup_project(
    preprint_project: Project,
    *,
    repo_root: Path | None = None,
    _extension_fn=None,
) -> str:
    """Create a SEPARATE llmXive brainstorm project that extends a Reviewed Preprint.

    Reviewed-Preprints ethics change (2026-07-01): the ingested paper stays a
    review-only preprint (original byline intact); THIS spawns our own follow-up
    study as a FRESH project (new PROJ id at BRAINSTORMED) whose idea proposes a
    concrete extension and CITES the source (we credit the original authors only via
    the citation, never as authors of our study). The preprint project is left
    untouched. Returns the new project's id. ``_extension_fn`` overrides the real
    LLM extension call in tests.
    """
    from llmxive.state import project as project_store
    from llmxive.state.project_id_lock import (
        next_available_proj_num,
        project_id_lock,
    )

    repo = repo_root or _repo_root()
    ppdir = project_dir(preprint_project, repo)
    metadata = _load_metadata(ppdir)
    paper_text = assemble_paper_text(ppdir, metadata)
    propose = _extension_fn or _propose_extension
    extension_body = (propose(paper_text) or "").strip()

    orig_title = str(metadata.get("title") or preprint_project.title or "preprint").strip()
    title = f'llmXive follow-up: extending "{orig_title[:70]}"'
    slug = _slugify(title)
    now = datetime.now(UTC)
    with project_id_lock(repo):
        n = next_available_proj_num(repo_root=repo)
        pid = f"PROJ-{n:03d}-{slug}"
        proj = Project(
            id=pid,
            title=title,
            field=preprint_project.field,
            current_stage=Stage.BRAINSTORMED,
            points_research={},
            points_paper={},
            created_at=now,
            updated_at=now,
            artifact_hashes={},
        )
        project_store.save(proj, repo_root=repo)
        idea_dir = repo / "projects" / pid / "idea"
        idea_dir.mkdir(parents=True, exist_ok=True)

    # The follow-up is OURS — NO `paper_authors:` (the original byline stays on the
    # preprint). Cite the source in the body + a bibtex block.
    src_url = str(metadata.get("arxiv_url") or metadata.get("source_url") or "").strip()
    src_authors = ", ".join(
        str(a).strip() for a in (metadata.get("authors") or []) if str(a).strip()
    )
    cite = f"- **{orig_title}**"
    if src_authors:
        cite += f" — {src_authors}"
    if src_url:
        cite += f". {src_url}"
    cite += "."
    body = "\n".join([
        "---",
        f"field: {preprint_project.field}",
        "submitter: llmxive-preprint-followup",
        "---",
        "",
        f"# {title}",
        "",
        extension_body,
        "",
        "## Motivated by (source preprint — reviewed, not authored, by llmXive)",
        "",
        cite,
        "",
        "```bibtex",
        build_bibtex_entry(metadata).strip(),
        "```",
        "",
    ])
    (idea_dir / f"{slug}.md").write_text(body, encoding="utf-8")
    return pid
