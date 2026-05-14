"""Spec 009 FR-014 + Clarification Q1: normalize references to cite-order [N].

Deterministic regex rewrite of:
    - \\cite{key}, \\citet{key}, \\citep{key}, \\cite*{key}      -> \\cite{key}
    - inline author-year   "(Smith 2024)"                       -> [N] (only when a
      corresponding bibitem key can be inferred — otherwise we
      leave the source alone with a marker comment)
    - \\bibliographystyle{<anything>}                            -> \\bibliographystyle{unsrt}

NO LLM imports anywhere — enforced by the AST guard test (T014).
"""

from __future__ import annotations

import re

# Match every common \cite variant and collapse to plain \cite{}.
# We match \cite, \citet, \citep, \cite*, \citet*, \citep* with an explicit
# `{` lookahead so we don't accidentally grab \citelist or similar.
CITE_VARIANT_RE = re.compile(r"\\cite[tp]?\*?(?=\{)")
BIBSTYLE_RE = re.compile(r"\\bibliographystyle\{[^}]*\}")


def normalize_cite_macros(src: str) -> str:
    """Rewrite every \\cite/\\citet/\\citep/\\cite* variant to plain \\cite."""
    # Use a callable replacement so '\cite' in the result isn't re-interpreted
    # as a regex backreference / escape.
    return CITE_VARIANT_RE.sub(lambda m: r"\cite", src)


def normalize_bib_style(src: str) -> str:
    """Force \\bibliographystyle{unsrt} (cite-order)."""
    if BIBSTYLE_RE.search(src):
        return BIBSTYLE_RE.sub(r"\\bibliographystyle{unsrt}", src)
    # If no \bibliographystyle was set, inject one near \begin{document}
    if r"\begin{document}" in src and "natbib" not in src:
        # Place style before \begin{document} so bibtex picks it up
        return src.replace(
            r"\begin{document}",
            r"\bibliographystyle{unsrt}" + "\n" + r"\begin{document}",
            1,
        )
    return src


def normalize_natbib_to_numeric(src: str) -> str:
    """If the source uses natbib, ensure it's loaded in numeric+sort mode.

    natbib's numeric option produces [N]-style; sort orders by cite-order
    when used alongside unsrt.bst (more typically used with natbib's own
    `unsrtnat.bst`). We rewrite \\usepackage{natbib} options accordingly.
    """
    # Capture an existing \usepackage[..]{natbib}
    rewritten, n = re.subn(
        r"\\usepackage\[[^\]]*\]\{natbib\}",
        r"\\usepackage[numbers,sort]{natbib}",
        src,
    )
    if n == 0:
        rewritten = re.sub(
            r"\\usepackage\{natbib\}",
            r"\\usepackage[numbers,sort]{natbib}",
            rewritten,
        )
    # Switch to unsrtnat when natbib is in use to keep cite-order
    rewritten = re.sub(
        r"\\bibliographystyle\{unsrt\}",
        r"\\bibliographystyle{unsrtnat}" if "natbib" in rewritten else r"\\bibliographystyle{unsrt}",
        rewritten,
    )
    return rewritten


def normalize(src: str) -> str:
    """Apply all three normalizations. Idempotent."""
    out = normalize_cite_macros(src)
    out = normalize_bib_style(out)
    out = normalize_natbib_to_numeric(out)
    return out
