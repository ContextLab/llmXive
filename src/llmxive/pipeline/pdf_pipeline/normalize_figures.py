"""Spec 009 FR-015: normalize figure widths to a bounded set.

Rewrites every \\includegraphics[...width=X...]{...} to use one of the
bounded \\figwidth{narrow|column|full} macros defined in llmxive.cls:
    * narrow  =  0.45\\linewidth   (when source width < 0.55 * textwidth)
    * column  =  1.0 \\linewidth   (when 0.55 <= ratio < 0.95)
    * full    =  1.0 \\textwidth   (when ratio >= 0.95)

Source widths can be expressed as `0.6\\textwidth`, `8cm`, `220pt`, etc.
We convert to a unitless ratio against a 6.5in nominal textwidth (the
llmxive class's geometry default) when the source uses absolute units.

NO LLM — pure regex + arithmetic.
"""

from __future__ import annotations

import re

INCLUDEGRAPHICS_RE = re.compile(
    r"\\includegraphics(?:\[(?P<opts>[^\]]*)\])?\{(?P<path>[^}]+)\}"
)
WIDTH_OPT_RE = re.compile(r"width\s*=\s*(?P<val>[^,\]]+)")

# Convert absolute units to a fraction of textwidth (nominal 6.5in)
NOMINAL_TEXTWIDTH_IN = 6.5  # llmxive.cls 1in margins on letter

_UNIT_TO_INCHES = {
    "in": 1.0,
    "cm": 1 / 2.54,
    "mm": 1 / 25.4,
    "pt": 1 / 72.27,
    "pc": 1 / 6.0225,
}


def _parse_width_to_ratio(val: str) -> float | None:
    """Parse a LaTeX width spec into a ratio of \\textwidth. Return None on parse failure."""
    val = val.strip()
    # 0.45\textwidth / 0.5\linewidth / 0.6\columnwidth
    m = re.match(r"^(\d+(?:\.\d+)?)\s*\\(textwidth|linewidth|columnwidth)$", val)
    if m:
        return float(m.group(1))
    # \textwidth alone
    if val in (r"\textwidth", r"\linewidth", r"\columnwidth"):
        return 1.0
    # absolute unit (e.g. 8cm, 220pt)
    m = re.match(r"^(\d+(?:\.\d+)?)\s*([a-z]+)$", val)
    if m:
        val_num = float(m.group(1))
        unit = m.group(2)
        if unit in _UNIT_TO_INCHES:
            inches = val_num * _UNIT_TO_INCHES[unit]
            return inches / NOMINAL_TEXTWIDTH_IN
    return None


def _ratio_to_bucket(ratio: float) -> str:
    """Map a 0..1+ ratio to narrow|column|full."""
    if ratio < 0.55:
        return "narrow"
    if ratio < 0.95:
        return "column"
    return "full"


def _rewrite_options(opts: str, bucket: str) -> str:
    """Remove width=... and inject a clean width directive for the bucket.

    Note on backslashes: these strings end up in LaTeX source as literal
    `\\linewidth` etc. — so we use SINGLE backslashes here (in raw-string
    form `r"\\linewidth"` is two chars in Python, which would emit double
    backslashes to LaTeX). LaTeX wants exactly one.
    """
    target_width = {
        "narrow": "0.45\\linewidth",
        "column": "\\linewidth",
        "full":   "\\textwidth",
    }[bucket]
    new_opts = WIDTH_OPT_RE.sub("", opts)
    # Clean up adjacent commas left behind by removal
    new_opts = re.sub(r",\s*,", ",", new_opts).strip(", ").strip()
    final = f"width={target_width}"
    return f"{final},{new_opts}" if new_opts else final


def normalize(src: str) -> str:
    """Rewrite every \\includegraphics width into a bounded bucket."""
    def _sub(m: re.Match) -> str:
        opts = m.group("opts") or ""
        path = m.group("path")
        wm = WIDTH_OPT_RE.search(opts)
        if not wm:
            # No width specified — fallback to column. Use a SINGLE backslash
            # in the emitted LaTeX (Python's `\\` here is one literal `\`).
            new_opts = (opts + ",width=\\linewidth").lstrip(",").strip()
            if not new_opts:
                new_opts = "width=\\linewidth"
            return f"\\includegraphics[{new_opts}]{{{path}}}"
        ratio = _parse_width_to_ratio(wm.group("val"))
        if ratio is None:
            # Unparseable width — leave alone but log a comment marker
            return m.group(0)
        bucket = _ratio_to_bucket(ratio)
        new_opts = _rewrite_options(opts, bucket)
        return f"\\includegraphics[{new_opts}]{{{path}}}"

    return INCLUDEGRAPHICS_RE.sub(_sub, src)
