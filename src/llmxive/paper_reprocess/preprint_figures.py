"""Vision figure review for Reviewed Preprints (2026-07-01; migrated to
``route_chat`` spec 026 slice 7, 2026-07-19).

The text paper-review panel cannot see figures — its ``figure_critic`` lens gets
only figure FILENAMES + the captions embedded in the LaTeX, so it guesses (and
often complains about things it can't actually see). This module renders the
paper's ACTUAL figures and has the ``vision`` profile's model review them
against their captions, producing a normal ``paper_reviewer_figure_critic``
review record.

The call goes through ``model_selection.route.route_chat(profile="vision")`` —
the SAME breaker/retry/failure-classification/credit-guard machinery every
other agent call gets — rather than a private ``urllib`` request to the
Dartmouth endpoint. ``qwen.qwen3.5-122b`` is real-call verified to genuinely
UNDERSTAND image input (Constitution II;
``tests/real_call/test_vision_real.py``) and is attributed the ``vision``
capability in the policy (``SELECTION_POLICY_VERSION`` 2, see
``model_selection.policy``); ``qwen.qwen3-vl`` remains the dedicated vision
peer. It is best-effort: if rendering or the vision call fails,
``run_preprint_review`` falls back to skipping the figure lens (like any other
lens failure).
"""

from __future__ import annotations

import io
import re
from datetime import UTC, datetime
from pathlib import Path

from llmxive.backends.base import ChatMessage, ImagePart, TextPart
from llmxive.config import repo_root as _repo_root
from llmxive.model_selection.route import route_chat
from llmxive.model_selection.tokens import MAX_IMAGE_DIMENSION_PX
from llmxive.types import Project

_MAX_FIGURES = 12  # cap the number of per-figure review calls per paper
_RENDER_DPI = 110

_FIG_EXTS = {".pdf", ".png", ".jpg", ".jpeg"}
# A ``figure``/``figure*`` environment with its \includegraphics + \caption.
_FIG_ENV_RE = re.compile(r"\\begin\{figure\*?\}(.*?)\\end\{figure\*?\}", re.DOTALL)
_GRAPHIC_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")


def _extract_caption(env: str) -> str:
    """Return a figure environment's caption text, brace-matched (so nested
    ``\\textbf{...}`` / ``{Oz}`` groups don't truncate it) and macro-stripped."""
    m = re.search(r"\\caption(?:\[[^\]]*\])?\{", env)
    if not m:
        return "(no caption)"
    depth, i, start = 0, m.end() - 1, m.end()
    while i < len(env):
        if env[i] == "{":
            depth += 1
        elif env[i] == "}":
            depth -= 1
            if depth == 0:
                break
        i += 1
    raw = env[start:i]
    # Drop \label / \ref-family entirely (with their braced arg), then any
    # remaining macros; unescape the LaTeX non-breaking space.
    raw = re.sub(r"\\(?:label|ref|cref|Cref|autoref|eqref)\{[^}]*\}", "", raw)
    raw = re.sub(r"\\[a-zA-Z]+\*?", "", raw)             # drop remaining macros
    raw = raw.replace("~", " ").replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", raw).strip()[:700] or "(no caption)"


def _resolve_graphic(source: Path, ref: str) -> Path | None:
    """Resolve a ``\\includegraphics`` reference to a real file (LaTeX omits the
    extension and searches the tree)."""
    ref = ref.strip().strip('"')
    cand = source / ref
    if cand.is_file() and cand.suffix.lower() in _FIG_EXTS:
        return cand
    for ext in (".pdf", ".png", ".jpg", ".jpeg"):
        c = source / (ref + ext)
        if c.is_file():
            return c
    # Fall back to a basename match anywhere under source/.
    base = Path(ref).name
    for p in sorted(source.rglob("*")):
        if p.is_file() and p.suffix.lower() in _FIG_EXTS and p.stem == Path(base).stem:
            return p
    return None


def _render_png(path: Path) -> tuple[bytes, int, int] | None:
    """Render one figure file to PNG bytes (PDF via pdf2image, raster via PIL).

    Downscales so neither dimension exceeds ``MAX_IMAGE_DIMENSION_PX`` — the
    hard limit :class:`~llmxive.backends.base.ImagePart` validates and REJECTS
    a render for — rather than letting a legitimately large figure raise.
    Returns ``(png_bytes, width, height)`` — the REAL post-downscale
    dimensions ``ImagePart`` needs — or ``None`` on any render failure.
    """
    try:
        if path.suffix.lower() == ".pdf":
            from pdf2image import convert_from_path

            imgs = convert_from_path(str(path), dpi=_RENDER_DPI)
            if not imgs:
                return None
            img = imgs[0]
        else:
            from PIL import Image

            img = Image.open(path).convert("RGB")
        if max(img.size) > MAX_IMAGE_DIMENSION_PX:
            scale = MAX_IMAGE_DIMENSION_PX / max(img.size)
            img = img.resize((
                max(1, int(img.size[0] * scale)),
                max(1, int(img.size[1] * scale)),
            ))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue(), img.size[0], img.size[1]
    except Exception:  # a bad figure must not sink the review
        return None


def collect_figures(pdir: Path) -> list[tuple[str, bytes, int, int]]:
    """Return up to ``_MAX_FIGURES`` ``(caption, png_bytes, width, height)``
    tuples from the paper.

    Parses ``figure`` environments from the top-level ``.tex`` (in document
    order) to pair each graphic with its caption; renders each to PNG.
    """
    source = pdir / "paper" / "source"
    if not source.is_dir():
        return []
    # Concatenate the non-llmxive .tex so \input'd sections are covered.
    tex = ""
    for p in sorted(source.rglob("*.tex")):
        if "-llmxive" in p.name:
            continue
        try:
            tex += p.read_text(encoding="utf-8", errors="replace") + "\n"
        except OSError:
            continue
    out: list[tuple[str, bytes, int, int]] = []
    for env in _FIG_ENV_RE.findall(tex):
        graphics = _GRAPHIC_RE.findall(env)
        if not graphics:
            continue
        caption = _extract_caption(env)
        for ref in graphics:
            fpath = _resolve_graphic(source, ref)
            if fpath is None:
                continue
            rendered = _render_png(fpath)
            if rendered is None:
                continue
            png, width, height = rendered
            out.append((f"{caption} [{Path(ref).name}]", png, width, height))
            break  # one representative render per figure environment
        if len(out) >= _MAX_FIGURES:
            break
    return out


_SYSTEM = (
    "You are the FIGURE reviewer on an automated peer-review panel assessing a "
    "third-party scientific preprint. You are shown ONE rendered figure at a time "
    "(plus every figure's caption, for cross-reference). Review the figure on "
    "SUBSTANCE and communication: does it support the claims it's cited for; are "
    "axes, units, legends, and error bars present and clear; is anything "
    "illegible, cluttered, or mislabeled; does the caption match what's shown; "
    "are there missing baselines/controls or misleading scales. Judge only what "
    "you can actually SEE plus the captions — do NOT invent content, and before "
    "calling something 'missing' CHECK the caption (a symbol/line/legend may be "
    "defined there). Prefer a few substantive observations over trivial nitpicks; "
    "if the figure is clear and well-supported, say so.\n\n"
    "Respond with a YAML MAPPING ONLY — no ``---`` fences, no ```` ``` ```` code "
    "fences, and nothing before or after it. Exactly two keys:\n"
    "issues: a YAML list (use `issues: []` when the figure is clear). Each item "
    "has `severity` (one of writing | science | fatal) and `text` (ONE concrete, "
    "actionable problem that NAMES the figure, double-quoted, UNDER 500 chars).\n"
    "summary: a double-quoted one-to-three sentence prose assessment of the figure.\n\n"
    "Example:\n"
    "issues:\n"
    "  - severity: science\n"
    "    text: \"Figure 3: axis labels ('Training author'/'Comparison author') "
    "contradict the caption's row/column description; fix one to match.\"\n"
    "  - severity: writing\n"
    "    text: \"Figure 3: no colorbar/legend maps color intensity to values.\"\n"
    "summary: \"The heatmap is readable but its axis labels contradict the caption "
    "and it lacks a colorbar.\"\n"
)


def _review_one_figure(
    index: int, caption: str, png: bytes, width: int, height: int, *,
    all_captions: str, title: str,
) -> tuple[str, str]:
    """Review a SINGLE figure (its image) with the FULL labeled caption set for
    cross-reference. Returns ``(response_text, model_used)``.

    Reviewing one figure per call keeps the model focused (a batched call misses
    details), and including every caption lets it resolve captions that
    cross-reference other figures ("follows the format of Figure 1", a legend
    entry defined in a sibling caption, etc.). Routes through
    ``model_selection.route.route_chat`` (the ``vision`` profile), which owns
    model choice, retry, failure-classification and the credit guard — this
    module no longer duplicates any of that. thinking-mode is already disabled
    centrally by the backend (SSoT), so it is NOT re-set here.
    """
    prompt_text = (
        f"# Paper title\n{title}\n\n"
        "# ALL figure captions in this paper (for cross-reference ONLY)\n"
        f"{all_captions}\n\n"
        f"# YOUR TASK\nReview ONLY **Figure {index}**, whose rendered image "
        "is shown below. Its own caption is:\n\n"
        f"Figure {index}: {caption}\n\n"
        "Use the other captions above only to resolve cross-references "
        "(e.g. a legend or symbol defined in another figure's caption, or "
        "'same format as Figure N'). Before flagging something as missing "
        "(a legend entry, a symbol, a definition), CHECK whether it is "
        "already defined in Figure "
        f"{index}'s caption or a cross-referenced caption. Return the "
        "review record for Figure "
        f"{index} per the system contract."
    )
    # A REAL budget: reasoning/vision models return empty content when the
    # budget is too small (the qwen "empty reply" trap).
    resp = route_chat(
        [
            ChatMessage(role="system", content=_SYSTEM),
            ChatMessage(role="user", content=(
                TextPart(prompt_text),
                ImagePart(mime="image/png", data=png, width=width, height=height),
            )),
        ],
        profile="vision",
        max_tokens=2000,
        temperature=0,
    )
    return resp.text, resp.model


# Regex fallback: pull `severity`/`text` pairs when the YAML won't load cleanly.
_ITEM_RE = re.compile(
    r"severity:\s*(?P<sev>writing|science|fatal).*?text:\s*(?P<q>[\"'])(?P<text>.*?)(?P=q)",
    re.DOTALL | re.IGNORECASE,
)


def _parse_figure(text: str) -> tuple[list[dict], str]:
    """Parse one per-figure vision response into ``(items, summary)``.

    Tolerant of the model's formatting drift: strips code/``---`` fences, tries
    YAML, and falls back to a regex sweep for ``severity``/``text`` pairs.
    """
    import yaml

    from llmxive.types import action_item_id

    raw = text.strip()
    raw = re.sub(r"^```[a-zA-Z]*\s*", "", raw)          # opening code fence
    raw = re.sub(r"\s*```$", "", raw)                   # closing code fence
    raw = re.sub(r"^---\s*\n", "", raw)                 # stray frontmatter fences
    raw = re.sub(r"\n---\s*$", "", raw)

    items: list[dict] = []
    summary = ""
    doc: object = None
    try:
        doc = yaml.safe_load(raw)
    except yaml.YAMLError:
        doc = None
    if isinstance(doc, dict):
        summary = str(doc.get("summary") or "").strip()
        for it in (doc.get("issues") or doc.get("action_items") or []):
            if not isinstance(it, dict):
                continue
            t = str(it.get("text") or "").strip()[:500]
            sev = it.get("severity")
            if t and sev in ("writing", "science", "fatal"):
                items.append({"id": action_item_id(t), "text": t, "severity": sev})
    if not items:  # YAML failed or had none — regex sweep the raw text
        for m in _ITEM_RE.finditer(raw):
            t = m.group("text").strip()[:500]
            if t:
                items.append({"id": action_item_id(t), "text": t, "severity": m.group("sev").lower()})
    if not summary:
        sm = re.search(r"summary:\s*(?P<q>[\"'])(?P<s>.*?)(?P=q)", raw, re.DOTALL)
        summary = sm.group("s").strip() if sm else ""
    return items, summary


def vision_figure_review(
    project: Project, *, repo_root: Path | None = None
) -> Path | None:
    """Render the paper's figures, have the vision model review them, and write a
    ``paper_reviewer_figure_critic`` review record. Returns the record path, or
    None when there are no figures or the review can't be produced.
    """
    import logging

    from llmxive.paper_reprocess.reprocess import project_dir
    from llmxive.state import project as project_store  # noqa: F401 - parity
    from llmxive.state import reviews as reviews_store
    from llmxive.types import (
        ReviewerKind,
        ReviewRecord,
        canonical_llm_review_score,
    )

    log = logging.getLogger(__name__)
    repo = repo_root or _repo_root()
    pdir = project_dir(project, repo)
    figs = collect_figures(pdir)
    if not figs:
        log.info("preprint figure review: no renderable figures for %s", project.id)
        return None

    # Review ONE figure per call (focused; a batched call misses details), and
    # pass EVERY caption (labeled) each time so caption cross-references resolve.
    all_captions = "\n".join(f"Figure {i}: {cap}" for i, (cap, _, _, _) in enumerate(figs, 1))
    used_model = ""
    items: list[dict] = []
    body_parts: list[str] = []
    seen: set[str] = set()
    any_ok = False
    for i, (caption, png, width, height) in enumerate(figs, 1):
        try:
            text, used_model = _review_one_figure(
                i, caption, png, width, height,
                all_captions=all_captions, title=project.title,
            )
        except Exception as exc:  # best-effort per figure (route_chat auth/breaker/
            # chain-exhaustion failures land here exactly like a render failure)
            log.warning("preprint figure review: figure %d failed for %s: %s",
                        i, project.id, exc)
            continue
        any_ok = True
        its, summary = _parse_figure(text)
        for it in its:
            if it["text"] not in seen:
                seen.add(it["text"])
                items.append(it)
        body_parts.append(f"### Figure {i}\n\n{summary or '(no summary returned)'}")
    if not any_ok:
        return None
    body = "\n\n".join(body_parts)
    # Verdict is DERIVED from the collected figure issues (worst severity wins).
    severities = {it["severity"] for it in items}
    if severities & {"fatal", "science"}:
        verdict = "major_revision_science"
    elif "writing" in severities:
        verdict = "minor_revision"
    else:
        verdict = "accept"

    meta_path = pdir / "paper" / "metadata.json"
    from llmxive.state.project import hash_file

    record = ReviewRecord(
        reviewer_name="paper_reviewer_figure_critic",
        reviewer_kind=ReviewerKind.LLM,
        artifact_path=str(meta_path.relative_to(repo)),
        artifact_hash=hash_file(meta_path),
        score=canonical_llm_review_score(verdict),
        verdict=verdict,
        feedback=f"Vision review of {len(figs)} figure(s) via {used_model}.",
        reviewed_at=datetime.now(UTC),
        prompt_version="1.1.0",
        model_name=used_model,
        backend="dartmouth",
        action_items=items,
    )
    path = reviews_store.write(
        record, body=body, stage="paper", review_type="paper",
        produced_by_agent=None, repo_root=repo,
    )
    return path


__all__ = ["collect_figures", "vision_figure_review"]
