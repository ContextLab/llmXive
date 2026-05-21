"""One-shot patcher for the spec-013 prototype appendix that was rendered
by a buggy version of `gen_appendix.py`. Walks the file character-by-
character and undoes the systematic over-escaping:

  \textbackslash\{\}<word>\{...\}  →  \<word>{...}
  \$ ... \$                          →  $ ... $   (math mode restored)
  \textasciicircum\{\}\{...\}        →  ^{...}    (rare super-script case)
  "..."                              →  ``...''   (curly quotes)

Brace balancing treats real `{` / `}` (already-correct LaTeX commands
inside the over-escaped wrapper, e.g. `\texttt{x}`) as nesting that does
NOT change the escaped-brace depth, so we correctly find the matching
`\}` even when the wrapped content has its own real braces.

Usage:  python fix_appendix.py main-llmxive.tex 2820 3014 main-llmxive.tex
        (start/end are 1-based, inclusive)
"""
from __future__ import annotations
import re
import sys

TBS = "\\textbackslash\\{\\}"  # 18 chars
# `\textasciicircum` may appear with real `{}` (`\textasciicircum{}`) or
# escaped braces (`\textasciicircum\{\}`) depending on which escape pass
# saw it first. Same for tilde.
TCARET_VARIANTS = ("\\textasciicircum{}", "\\textasciicircum\\{\\}")
TTILDE_VARIANTS = ("\\textasciitilde{}", "\\textasciitilde\\{\\}")


def parse_escaped_arg(text: str, i: int) -> tuple[str, int]:
    """Starting at position i pointing at `\\{`, return (inner_text, end_index)
    where end_index points just past the matching `\\}`. Real `{`/`}` are
    preserved as-is and do not affect depth."""
    assert text[i:i+2] == "\\{", f"expected \\{{ at {i}, got {text[i:i+10]!r}"
    i += 2
    depth = 1
    out: list[str] = []
    while i < len(text) and depth > 0:
        two = text[i:i+2]
        if two == "\\{":
            depth += 1
            out.append("\\{")
            i += 2
        elif two == "\\}":
            depth -= 1
            if depth > 0:
                out.append("\\}")
            i += 2
        else:
            out.append(text[i])
            i += 1
    return "".join(out), i


def _match_prefix(text: str, i: int, prefixes: tuple[str, ...]) -> int:
    """Return prefix length if any prefix matches at position i, else 0."""
    for p in prefixes:
        if text[i:i+len(p)] == p:
            return len(p)
    return 0


def transform_inside(text: str) -> str:
    """Inside a math span or wrapper argument, undo `\\textbackslash\\{\\}word`
    sequences and convert `\\textasciicircum{}` → `^` (math superscript).
    Nested `\\textbackslash\\{\\}cmd\\{...\\}` is parsed recursively."""
    out: list[str] = []
    i = 0
    while i < len(text):
        if text[i:i+len(TBS)] == TBS:
            i += len(TBS)
            j = i
            while j < len(text) and text[j].isalpha():
                j += 1
            out.append("\\" + text[i:j])
            i = j
            if text[i:i+2] == "\\{":
                inner, i = parse_escaped_arg(text, i)
                out.append("{" + transform_inside(inner) + "}")
        elif (n := _match_prefix(text, i, TCARET_VARIANTS)):
            i += n
            if text[i:i+2] == "\\{":
                inner, i = parse_escaped_arg(text, i)
                out.append("^{" + transform_inside(inner) + "}")
            elif text[i:i+1] == "{":
                # Real-brace argument form; consume balanced.
                depth = 1
                i += 1
                arg = []
                while i < len(text) and depth > 0:
                    if text[i] == "{":
                        depth += 1
                        arg.append("{")
                    elif text[i] == "}":
                        depth -= 1
                        if depth > 0:
                            arg.append("}")
                    else:
                        arg.append(text[i])
                    i += 1
                out.append("^{" + transform_inside("".join(arg)) + "}")
            else:
                out.append("^")
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


_REFLIKE_CMDS = (
    "ref", "cref", "Cref", "autoref", "eqref",
    "label", "pageref",
    "cite", "citep", "citet", "citeauthor", "citeyear", "citealp", "citealt",
    "url", "href",  # path-like arguments
)


def _unescape_reflike(text: str) -> str:
    """Inside `\\ref{...}`, `\\cite{...}`, `\\label{...}` etc., undo
    over-escaping of underscores and other special chars so the argument
    matches the original key. We can't do this in the body text (where
    `\\_` is correct LaTeX for a literal underscore), but inside a
    label/citation key the underscore is part of the identifier and must
    NOT be escaped.

    Operates on already-real `\\ref{...}` syntax (from the in-place fix
    pass) — handles balanced braces inside the argument.
    """
    cmd_alt = "|".join(_REFLIKE_CMDS)
    pattern = re.compile(r"\\(" + cmd_alt + r")\{")
    out: list[str] = []
    i = 0
    while i < len(text):
        m = pattern.match(text, i)
        if not m:
            out.append(text[i])
            i += 1
            continue
        out.append(m.group(0))  # e.g. `\ref{`
        i = m.end()
        depth = 1
        arg_chars: list[str] = []
        while i < len(text) and depth > 0:
            two = text[i:i+2]
            if two == "\\_":
                arg_chars.append("_")
                i += 2
            elif two == "\\&":
                arg_chars.append("&")
                i += 2
            elif two == "\\#":
                arg_chars.append("#")
                i += 2
            elif text[i] == "{":
                depth += 1
                arg_chars.append("{")
                i += 1
            elif text[i] == "}":
                depth -= 1
                if depth > 0:
                    arg_chars.append("}")
                i += 1
            else:
                arg_chars.append(text[i])
                i += 1
        out.append("".join(arg_chars) + "}")
    return "".join(out)


def fix_text(text: str) -> str:
    """Top-level fixer: handles \\textbackslash\\{\\}word\\{...\\} and \\$...\\$."""
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i:i+len(TBS)] == TBS:
            i += len(TBS)
            j = i
            while j < n and text[j].isalpha():
                j += 1
            cmd = text[i:j]
            i = j
            out.append("\\" + cmd)
            if text[i:i+2] == "\\{":
                inner, i = parse_escaped_arg(text, i)
                out.append("{" + transform_inside(inner) + "}")
        elif text[i:i+2] == "\\$":
            # Math span: collect until matching \$
            i += 2
            buf: list[str] = []
            while i < n and text[i:i+2] != "\\$":
                buf.append(text[i])
                i += 1
            if i < n:
                i += 2  # consume closing \$
            out.append("$" + transform_inside("".join(buf)) + "$")
        else:
            out.append(text[i])
            i += 1
    text = "".join(out)
    # ASCII straight double quotes → LaTeX curly quotes.
    text = re.sub(r'"([^"\n]*)"', r"``\1''", text)
    # Literal Greek/math Unicode → math mode (Fraunces has no Greek glyphs,
    # so `κ=0.86` from a reviewer renders as a tofu box; wrap in `$...$`).
    for uchar, tex in UNICODE_MATH.items():
        text = text.replace(uchar, tex)
    # Unescape underscores/ampersands inside ref/cite/label keys, where
    # they are part of the identifier (e.g. `app:image_release`) and
    # must NOT be backslash-escaped or the label lookup fails.
    text = _unescape_reflike(text)
    return text


# Common Unicode glyphs reviewers paste inline that need LaTeX math mode.
UNICODE_MATH = {
    "α": "$\\alpha$", "β": "$\\beta$", "γ": "$\\gamma$",
    "δ": "$\\delta$", "ε": "$\\epsilon$", "ζ": "$\\zeta$",
    "η": "$\\eta$", "θ": "$\\theta$", "ι": "$\\iota$",
    "κ": "$\\kappa$", "λ": "$\\lambda$", "μ": "$\\mu$",
    "ν": "$\\nu$", "ξ": "$\\xi$", "π": "$\\pi$",
    "ρ": "$\\rho$", "σ": "$\\sigma$", "τ": "$\\tau$",
    "υ": "$\\upsilon$", "φ": "$\\phi$", "χ": "$\\chi$",
    "ψ": "$\\psi$", "ω": "$\\omega$",
    "Α": "$\\Alpha$", "Β": "$\\Beta$", "Γ": "$\\Gamma$",
    "Δ": "$\\Delta$", "Θ": "$\\Theta$", "Λ": "$\\Lambda$",
    "Ξ": "$\\Xi$", "Π": "$\\Pi$", "Σ": "$\\Sigma$",
    "Φ": "$\\Phi$", "Ψ": "$\\Psi$", "Ω": "$\\Omega$",
    "±": "$\\pm$", "×": "$\\times$", "÷": "$\\div$",
    "≈": "$\\approx$", "≠": "$\\neq$",
    "≤": "$\\leq$", "≥": "$\\geq$",
    "≪": "$\\ll$", "≫": "$\\gg$",
    "∞": "$\\infty$", "∑": "$\\sum$", "∏": "$\\prod$",
    "√": "$\\sqrt{\\,}$", "∂": "$\\partial$",
    "→": "$\\to$", "←": "$\\leftarrow$", "↔": "$\\leftrightarrow$",
    "⇒": "$\\Rightarrow$", "⇐": "$\\Leftarrow$",
}


def main() -> int:
    if len(sys.argv) != 5:
        print("Usage: fix_appendix.py <infile> <start_line> <end_line> <outfile>",
              file=sys.stderr)
        return 2
    infile, start_s, end_s, outfile = sys.argv[1:]
    start = int(start_s)
    end = int(end_s)
    with open(infile, encoding="utf-8") as f:
        lines = f.readlines()
    for idx in range(start - 1, end):
        lines[idx] = fix_text(lines[idx])
    with open(outfile, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return 0


if __name__ == "__main__":
    sys.exit(main())
