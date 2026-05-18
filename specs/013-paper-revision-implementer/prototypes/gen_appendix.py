"""Generate the post-paper appendix (reviews + revision history) as LaTeX,
deterministically from the project's filesystem state. NO LLM summary.

Usage: python gen_appendix.py <project_dir> > appendix.tex

Reads:
  - <project_dir>/paper/reviews/paper_reviewer*.md   (one review per file)
  - <project_dir>/paper/revision_history.yaml        (revision rounds, if any)

Emits a LaTeX fragment that fits inside an llmxive.cls document.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def latex_escape(s: str) -> str:
    """Minimal LaTeX-text escape. Preserves markdown line breaks as \\par."""
    s = s.replace("\\", r"\textbackslash{}")
    s = s.replace("&", r"\&").replace("%", r"\%").replace("$", r"\$")
    s = s.replace("#", r"\#").replace("_", r"\_").replace("{", r"\{").replace("}", r"\}")
    s = s.replace("~", r"\textasciitilde{}").replace("^", r"\textasciicircum{}")
    return s


def render_markdown_body(body: str) -> str:
    """Render a review's markdown body as LaTeX. Handles headings, bullets,
    and bold/italic minimally."""
    # Remove the leading "# Free-form review body" if present.
    body = re.sub(r"^#\s*Free-form review body\s*\n+", "", body, count=1, flags=re.M)
    lines = body.split("\n")
    out: list[str] = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        # Heading levels (## → \subsection*, ### → \paragraph)
        if stripped.startswith("## "):
            if in_list:
                out.append(r"\end{itemize}")
                in_list = False
            out.append(r"\paragraph*{" + latex_escape(stripped[3:]) + "}")
            continue
        if stripped.startswith("### "):
            if in_list:
                out.append(r"\end{itemize}")
                in_list = False
            out.append(r"\subparagraph*{" + latex_escape(stripped[4:]) + "}")
            continue
        # Bullet list
        if stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                out.append(r"\begin{itemize}\setlength\itemsep{2pt}")
                in_list = True
            item = stripped[2:]
            # Inline bold + italic + code
            item = re.sub(r"\*\*([^*]+)\*\*", r"\\textbf{\1}", item)
            item = re.sub(r"\*([^*]+)\*", r"\\textit{\1}", item)
            item = re.sub(r"`([^`]+)`", r"\\texttt{\1}", item)
            # Escape AFTER the inline patterns (so we don't mangle them).
            # But the \textbf/\textit/\texttt content already has braces;
            # we need to escape inside that content. Simpler approach:
            # apply escape to whole line, then un-escape the LaTeX commands.
            # Use a placeholder approach.
            out.append(r"\item " + _safe_escape_keeping_inline_commands(item))
            continue
        if not stripped:
            if in_list:
                out.append(r"\end{itemize}")
                in_list = False
            out.append("")
            continue
        # Plain paragraph line.
        if in_list:
            out.append(r"\end{itemize}")
            in_list = False
        # Inline bold + italic + code in plain lines too.
        line2 = re.sub(r"\*\*([^*]+)\*\*", r"\\textbf{\1}", line)
        line2 = re.sub(r"\*([^*]+)\*", r"\\textit{\1}", line2)
        line2 = re.sub(r"`([^`]+)`", r"\\texttt{\1}", line2)
        out.append(_safe_escape_keeping_inline_commands(line2))
    if in_list:
        out.append(r"\end{itemize}")
    return "\n".join(out)


def _safe_escape_keeping_inline_commands(s: str) -> str:
    """Escape & % $ # _ { } in a string that may already contain
    \textbf{..}, \textit{..}, \texttt{..}. We split on those commands,
    escape the literal segments, and re-join."""
    pattern = re.compile(r"(\\(?:textbf|textit|texttt)\{[^{}]*\})")
    parts = pattern.split(s)
    out: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            # This is a \textbf{..} / \textit{..} / \texttt{..} segment;
            # only escape inside the braces.
            m = re.match(r"(\\(?:textbf|textit|texttt))\{([^{}]*)\}", part)
            if m:
                cmd, inner = m.group(1), m.group(2)
                inner = inner.replace("\\", r"\textbackslash{}")
                inner = inner.replace("&", r"\&").replace("%", r"\%").replace("$", r"\$")
                inner = inner.replace("#", r"\#").replace("_", r"\_")
                out.append(cmd + "{" + inner + "}")
            else:
                out.append(part)
        else:
            # Literal segment; escape everything.
            out.append(latex_escape(part))
    return "".join(out)


def parse_review_file(path: Path) -> dict:
    """Return {'reviewer_name', 'verdict', 'reviewed_at', 'feedback', 'body'}."""
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
    out = [r"\section*{Reviews}"]
    for f in files:
        rec = parse_review_file(f)
        out.append(r"\subsection*{" + latex_escape(rec["reviewer_name"]) +
                   r" \hfill \textit{verdict: " + latex_escape(rec["verdict"]) + "}}")
        if rec.get("feedback"):
            out.append(r"\noindent\textit{Feedback summary:} " +
                       latex_escape(rec["feedback"]) + r"\par\medskip")
        out.append(render_markdown_body(rec["body"]))
        out.append(r"\bigskip")
        out.append("")
    return "\n".join(out)


def render_history(project_dir: Path) -> str:
    hist_path = project_dir / "paper" / "revision_history.yaml"
    if not hist_path.is_file():
        return (r"\section*{Revision history}" + "\n\n" +
                "This manuscript has not yet undergone any implementer-driven revision rounds.")
    data = yaml.safe_load(hist_path.read_text(encoding="utf-8")) or {}
    rounds = data.get("rounds", [])
    out = [r"\section*{Revision history}"]
    for r in rounds:
        out.append(r"\subsection*{Round " + str(r.get("round_number", "?")) +
                   r" \hfill \textit{" + latex_escape(str(r.get("ran_at", ""))) + ", " +
                   latex_escape(r.get("implementer_agent", "")) + "}}")
        out.append(r"Summary: " + str(r.get("tasks_done", 0)) + " done, " +
                   str(r.get("tasks_failed", 0)) + " compile-failed, " +
                   str(r.get("tasks_skipped", 0)) + " skipped.")
        items = r.get("task_outcomes", [])
        if items:
            out.append(r"\begin{itemize}\setlength\itemsep{2pt}")
            for it in items:
                out.append(r"\item \textbf{[" + latex_escape(it.get("id", "")) + "]} (" +
                           latex_escape(it.get("severity", "")) + ") " +
                           latex_escape(it.get("text", "")) + r" \hfill \textit{" +
                           latex_escape(it.get("status", "")) + "}")
            out.append(r"\end{itemize}")
        out.append(r"\bigskip")
        out.append("")
    return "\n".join(out)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: gen_appendix.py <project_dir>", file=sys.stderr)
        return 2
    project_dir = Path(sys.argv[1])
    print(render_reviews(project_dir))
    print()
    print(r"\clearpage")
    print()
    print(render_history(project_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
