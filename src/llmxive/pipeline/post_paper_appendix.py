"""Generate the post-paper appendix (reviews + revision history) as LaTeX,
deterministically from the project's filesystem state. NO LLM summary.

Usage: python gen_appendix.py <project_dir> > appendix.tex

Reads:
  - <project_dir>/paper/reviews/paper_reviewer*.md   (one review per file)
  - <project_dir>/paper/revision_history.yaml        (revision rounds, if any)

Emits a LaTeX fragment that fits inside an llmxive.cls document.

Inline-markdown processing strategy: extract inline spans (code, bold,
italic) into placeholders BEFORE latex-escaping the rest of the line.
This is the only reliable way to handle nested patterns like
``**[Candidate Examples (`ie_entity_candidates.pdf`, etc.)]**`` — a
naive regex that tries to escape AFTER substitution will produce
literal `\textbf{...}` text in the output (the prior version's bug).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def latex_escape(s: str) -> str:
    """Escape literal text for LaTeX body (NOT inside any inline command)."""
    s = s.replace("\\", r"\textbackslash{}")
    s = s.replace("&", r"\&").replace("%", r"\%").replace("$", r"\$")
    s = s.replace("#", r"\#").replace("_", r"\_").replace("{", r"\{").replace("}", r"\}")
    s = s.replace("~", r"\textasciitilde{}").replace("^", r"\textasciicircum{}")
    # Curly quotes: prefer LaTeX-style open/close. Replace ASCII pairs.
    s = re.sub(r'"([^"]*)"', r"``\1''", s)
    return s


def _escape_inside_texttt(s: str) -> str:
    """Escape special chars inside `\texttt{...}` (already a monospace
    box; we don't want to convert `_` → `\textbackslash{}_`, just `\\_`)."""
    s = s.replace("\\", r"\textbackslash{}")
    s = s.replace("&", r"\&").replace("%", r"\%").replace("$", r"\$")
    s = s.replace("#", r"\#").replace("_", r"\_")
    # Don't touch { } here — caller ensures content has no literal braces.
    return s


def _expand(s: str, spans: list[str]) -> str:
    """Walk `s` and turn placeholder tokens (`\x00N\x00`) back into LaTeX
    using the shared `spans` table. Non-token text is latex-escaped."""
    parts = re.split(r"(\x00\d+\x00)", s)
    out = []
    for part in parts:
        m = re.fullmatch(r"\x00(\d+)\x00", part)
        if m:
            token = spans[int(m.group(1))]
            if token.startswith("\\"):
                # Raw LaTeX command (whitelisted passthrough): emit
                # verbatim — `\ref{...}`, `\cite{...}`, etc.
                out.append(token)
            elif token.startswith("$"):
                # Math span: preserve verbatim so `$\kappa$` etc. render.
                out.append(token)
            elif token.startswith("`"):
                inner = token[1:-1]
                out.append(r"\texttt{" + _escape_inside_texttt(inner) + "}")
            elif token.startswith("**"):
                inner = token[2:-2]
                # _expand on the inner text — same shared spans table, so
                # nested code/math placeholders inside the bold span resolve.
                out.append(r"\textbf{" + _expand(inner, spans) + "}")
            else:  # starts with *
                inner = token[1:-1]
                out.append(r"\textit{" + _expand(inner, spans) + "}")
        else:
            out.append(latex_escape(part))
    return "".join(out)


# Reviewers sometimes paste raw LaTeX commands into their markdown body
# (e.g., `\ref{app:image_release}`, `\cite{foo2024}`). We must preserve
# those verbatim — if we let latex_escape see them, the `\` becomes
# `\textbackslash{}` and the inner `_` becomes `\_`, breaking the ref
# lookup entirely. Whitelist of safe-to-pass-through commands:
_LATEX_PASSTHROUGH_CMDS = (
    "ref", "cref", "Cref", "autoref", "eqref",
    "label", "pageref",
    "cite", "citep", "citet", "citeauthor", "citeyear", "citealp", "citealt",
    "S",  # \S (section symbol) is sometimes written with braces too
    "url", "href",
)
_LATEX_CMD_RE = re.compile(
    r"\\(?:" + "|".join(_LATEX_PASSTHROUGH_CMDS) + r")\b(?:\s*\{[^{}]*\})?"
)


def render_inline(s: str) -> str:
    """Render an inline string with markdown emphasis/code → LaTeX,
    safely handling nested commands. Strategy: stash inline spans into
    placeholders, escape the rest, then expand placeholders.
    """
    spans: list[str] = []

    def stash(m: re.Match) -> str:
        spans.append(m.group(0))
        return f"\x00{len(spans) - 1}\x00"

    # Raw LaTeX commands FIRST: pass `\ref{app:foo_bar}` etc. through
    # verbatim. Without this, `latex_escape` turns the backslash into
    # `\textbackslash{}` and the inner `_` into `\_`, so the label
    # lookup fails and the PDF shows `Appendix ??appfoobar`.
    s = _LATEX_CMD_RE.sub(stash, s)
    # Inline math: `$...$` is LaTeX math. Reviewers write things like
    # `Cohen's $\kappa$` or `$n=789$` in markdown; without preserving
    # the math span, our escape would turn `$` into `\$` and `\kappa`
    # into literal backslash-text. Stash math spans verbatim.
    s = re.sub(r"\$[^$\n]+\$", stash, s)
    # Code (so its content isn't reinterpreted as bold/italic).
    s = re.sub(r"`([^`]+)`", stash, s)
    # Italic BEFORE bold so that nested italic inside bold (`**a *b* c**`)
    # gets stashed first; the lookbehind/lookahead guards skip `**` markers
    # so we never mis-match a bold open/close as an italic span.
    s = re.sub(r"(?<!\*)\*(?!\*)([^*\n]+?)(?<!\*)\*(?!\*)", stash, s)
    # Bold (with italic already stashed, the inner contains no bare `*`).
    s = re.sub(r"\*\*([^*]+)\*\*", stash, s)

    return _expand(s, spans)


def render_markdown_body(body: str) -> str:
    """Render a markdown review body as LaTeX with proper inline handling."""
    body = re.sub(r"^#\s*Free-form review body\s*\n+", "", body, count=1, flags=re.M)
    lines = body.split("\n")
    out: list[str] = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        # Headings: display block above + below for proper spacing.
        if stripped.startswith("## "):
            if in_list:
                out.append(r"\end{itemize}")
                in_list = False
            out.append(r"\medskip\noindent\textbf{" +
                       render_inline(stripped[3:]) + r"}\par\medskip\noindent")
            continue
        if stripped.startswith("### "):
            if in_list:
                out.append(r"\end{itemize}")
                in_list = False
            out.append(r"\smallskip\noindent\textit{" +
                       render_inline(stripped[4:]) + r"}\par\smallskip\noindent")
            continue
        # Bullet lists.
        if stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                out.append(r"\begin{itemize}\setlength\itemsep{2pt}")
                in_list = True
            out.append(r"\item " + render_inline(stripped[2:]))
            continue
        # Blank line → paragraph break.
        if not stripped:
            if in_list:
                out.append(r"\end{itemize}")
                in_list = False
            out.append("")
            continue
        # Plain text line.
        if in_list:
            out.append(r"\end{itemize}")
            in_list = False
        out.append(render_inline(line))
    if in_list:
        out.append(r"\end{itemize}")
    return "\n".join(out)


def parse_review_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {"reviewer_name": path.stem.split("__")[0],
                "verdict": "?", "reviewed_at": "", "feedback": "", "body": text}
    front = yaml.safe_load(m.group(1)) or {}
    return {
        "reviewer_name": front.get("reviewer_name") or path.stem.split("__")[0],
        "verdict": front.get("verdict", "?"),
        "reviewed_at": str(front.get("reviewed_at", "")),
        "feedback": front.get("feedback", ""),
        "body": m.group(2),
    }


def render_reviews(project_dir: Path) -> str:
    review_dir = project_dir / "paper" / "reviews"
    if not review_dir.is_dir():
        return ""
    files = sorted(review_dir.glob("paper_reviewer*.md"))
    out = [r"\section*{Reviews}", r"\sloppy"]
    for f in files:
        rec = parse_review_file(f)
        out.append(r"\subsection*{" + render_inline(rec["reviewer_name"]) +
                   r" \hfill \textit{verdict: " + render_inline(str(rec["verdict"])) + "}}")
        if rec.get("feedback"):
            out.append(r"\noindent\textit{Feedback summary:} " +
                       render_inline(rec["feedback"]) + r"\par\medskip")
        out.append(render_markdown_body(rec["body"]))
        out.append(r"\bigskip")
        out.append("")
    return "\n".join(out)


def _strip_backend(name: str) -> str:
    """Drop ' on <backend>' suffix from an implementer display name."""
    return re.sub(r"\s+on\s+[a-z0-9_-]+", "", name or "")


def render_history(project_dir: Path) -> str:
    hist_path = project_dir / "paper" / "revision_history.yaml"
    if not hist_path.is_file():
        return (r"\section*{Revision history}" + "\n\n" +
                "This manuscript has not yet undergone any implementer-driven revision rounds.")
    data = yaml.safe_load(hist_path.read_text(encoding="utf-8")) or {}
    rounds = data.get("rounds", [])
    out = [r"\section*{Revision history}", r"\sloppy"]
    for r in rounds:
        out.append(r"\subsection*{Round " + str(r.get("round_number", "?")) +
                   r" \hfill \textit{" + render_inline(str(r.get("ran_at", ""))) + ", " +
                   render_inline(_strip_backend(r.get("implementer_agent", ""))) + "}}")
        out.append(r"Summary: " + str(r.get("tasks_done", 0)) + " done, " +
                   str(r.get("tasks_failed", 0)) + " compile-failed, " +
                   str(r.get("tasks_skipped", 0)) + " skipped.")
        items = r.get("task_outcomes", [])
        if items:
            out.append(r"\begin{itemize}\setlength\itemsep{2pt}")
            for it in items:
                out.append(r"\item \textbf{[" + render_inline(it.get("id", "")) + "]} (" +
                           render_inline(it.get("severity", "")) + ") " +
                           render_inline(it.get("text", "")) + r" \hfill \textit{" +
                           render_inline(it.get("status", "")) + "}")
            out.append(r"\end{itemize}")
        out.append(r"\bigskip")
        out.append("")
    return "\n".join(out)


_GITHUB_PROJECT_URL_FMT = "https://github.com/ContextLab/llmXive/tree/main/projects/{project_id}/"


def render_spacer(project_id: str) -> str:
    """Render the spacer page that demarcates where the paper ends and
    the reviews + revision history begin (FR-036). Single page, no
    headers/footers, centered text + GitHub project-directory link
    (NOT the dashboard root — FR-033)."""
    url = _GITHUB_PROJECT_URL_FMT.format(project_id=project_id)
    return "\n".join([
        r"\clearpage",
        r"\thispagestyle{empty}",
        r"\vspace*{\fill}",
        r"\begin{center}",
        r"  {\Large\bfseries End of paper.}\par\vspace{1em}",
        r"  The remainder of this PDF contains the reviews and",
        r"  revision history for this manuscript.\par\vspace{1em}",
        r"  Full revision history, source, and review records:",
        r"  \par\vspace{0.5em}",
        r"  \texttt{\href{" + url + "}{" + url + "}}",
        r"\end{center}",
        r"\vspace*{\fill}",
        r"\clearpage",
        "",
    ])


def render_to_file(
    project_dir: Path, output_tex: Path, *, project_id: str | None = None,
) -> None:
    """Render the complete post-paper appendix (spacer + reviews +
    revision history) to a single `.tex` file that the publisher
    `\\input{...}`s before `\\end{document}`. Used by the publisher
    agent's recompile path."""
    pid = project_id or project_dir.name
    parts = [
        render_spacer(pid),
        render_reviews(project_dir),
        "",
        r"\clearpage",
        "",
        render_history(project_dir),
    ]
    output_tex.parent.mkdir(parents=True, exist_ok=True)
    output_tex.write_text("\n".join(parts), encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: post_paper_appendix.py <project_dir>", file=sys.stderr)
        return 2
    project_dir = Path(sys.argv[1])
    print(render_spacer(project_dir.name))
    print(render_reviews(project_dir))
    print()
    print(r"\clearpage")
    print()
    print(render_history(project_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
