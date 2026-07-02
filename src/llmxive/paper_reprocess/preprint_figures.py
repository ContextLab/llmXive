"""Vision figure review for Reviewed Preprints (2026-07-01).

The text paper-review panel cannot see figures — its ``figure_critic`` lens gets
only figure FILENAMES + the captions embedded in the LaTeX, so it guesses (and
often complains about things it can't actually see). This module renders the
paper's ACTUAL figures and has a free VISION model (``qwen.qwen3.5-122b``, which
is multimodal given a real token budget + thinking off) review them against
their captions, producing a normal ``paper_reviewer_figure_critic`` review record.

It is deliberately ISOLATED from the shared text backend (a direct multimodal
call to the Dartmouth OpenAI-compatible endpoint) so adding image support does
not touch the core ``ChatMessage``/router the whole pipeline depends on. It is
best-effort: if rendering or the vision call fails, ``run_preprint_review`` falls
back to skipping the figure lens (like any other lens failure).
"""

from __future__ import annotations

import base64
import io
import json
import re
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from llmxive.config import repo_root as _repo_root
from llmxive.types import Project

# Free vision model. qwen3.5-122b is vision-capable (with a real token budget +
# thinking OFF — a 150-token budget returns empty because reasoning eats it), is
# the strongest free model, and — unlike gemma-3-27b (capped at 3 images/prompt)
# — accepts the whole figure set at once. gpt-oss-120b is text-only.
_VISION_MODEL = "qwen.qwen3.5-122b"
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


def _endpoint() -> str:
    try:
        from langchain_dartmouth.definitions import CLOUD_BASE_URL as base
    except Exception:  # pragma: no cover - offline fallback
        import os

        base = os.environ.get("LCD_CLOUD_BASE_URL", "https://chat.dartmouth.edu/api/")
    return base.rstrip("/") + "/chat/completions"


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


def _render_png(path: Path) -> bytes | None:
    """Render one figure file to PNG bytes (PDF via pdf2image, raster via PIL)."""
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
        # Bound the longest side so the payload stays reasonable.
        max_side = 1600
        if max(img.size) > max_side:
            scale = max_side / max(img.size)
            img = img.resize((int(img.size[0] * scale), int(img.size[1] * scale)))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:  # a bad figure must not sink the review
        return None


def collect_figures(pdir: Path) -> list[tuple[str, bytes]]:
    """Return up to ``_MAX_FIGURES`` ``(caption, png_bytes)`` pairs from the paper.

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
    out: list[tuple[str, bytes]] = []
    for env in _FIG_ENV_RE.findall(tex):
        graphics = _GRAPHIC_RE.findall(env)
        if not graphics:
            continue
        caption = _extract_caption(env)
        for ref in graphics:
            fpath = _resolve_graphic(source, ref)
            if fpath is None:
                continue
            png = _render_png(fpath)
            if png is None:
                continue
            out.append((f"{caption} [{Path(ref).name}]", png))
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
    index: int, caption: str, png: bytes, *,
    all_captions: str, title: str, model: str, key: str,
) -> tuple[str, str]:
    """Review a SINGLE figure (its image) with the FULL labeled caption set for
    cross-reference. Returns ``(response_text, model_used)``.

    Reviewing one figure per call keeps the model focused (a batched call misses
    details), and including every caption lets it resolve captions that
    cross-reference other figures ("follows the format of Figure 1", a legend
    entry defined in a sibling caption, etc.).
    """
    b64 = base64.b64encode(png).decode()
    content: list[dict] = [
        {
            "type": "text",
            "text": (
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
            ),
        },
        {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}},
    ]
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": content},
        ],
        # A REAL budget: reasoning/vision models return empty content when the
        # budget is too small (the qwen "empty reply" trap). thinking OFF keeps
        # it fast + bounded (the SSoT backend disables it the same way).
        "max_tokens": 2000,
        "temperature": 0,
        "extra_body": {"chat_template_kwargs": {"enable_thinking": False}},
    }
    req = urllib.request.Request(
        _endpoint(),
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:  # fixed Dartmouth host
        data = json.load(resp)
    text = data["choices"][0]["message"]["content"] or ""
    used = data.get("model") or model
    return text, used


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
    project: Project, *, repo_root: Path | None = None, model: str = _VISION_MODEL
) -> Path | None:
    """Render the paper's figures, have the vision model review them, and write a
    ``paper_reviewer_figure_critic`` review record. Returns the record path, or
    None when there are no figures or the review can't be produced.
    """
    import logging

    from llmxive.credentials import load_dartmouth_key
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
    key = load_dartmouth_key(prompt_if_missing=False)
    if not key:
        log.warning("preprint figure review: no Dartmouth key; skipping vision review")
        return None

    # Review ONE figure per call (focused; a batched call misses details), and
    # pass EVERY caption (labeled) each time so caption cross-references resolve.
    all_captions = "\n".join(f"Figure {i}: {cap}" for i, (cap, _) in enumerate(figs, 1))
    used_model = model
    items: list[dict] = []
    body_parts: list[str] = []
    seen: set[str] = set()
    any_ok = False
    for i, (caption, png) in enumerate(figs, 1):
        try:
            text, used_model = _review_one_figure(
                i, caption, png, all_captions=all_captions,
                title=project.title, model=model, key=key,
            )
        except Exception as exc:  # best-effort per figure
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
