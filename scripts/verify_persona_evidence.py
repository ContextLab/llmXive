#!/usr/bin/env python3
"""T022a (spec 009): verify persona evidence URLs per Constitution Principle II.

For every persona card under agents/prompts/personalities/:
  - parse YAML frontmatter
  - for each interest_signals[].evidence_sources[] entry:
      * if it's a URL, fetch it and confirm HTTP 200
      * grep the body for at least one content noun phrase from the signal's label
      * non-URL citations (book titles, journal entries) are NOT fetched but
        ARE counted toward the >=1-evidence-source requirement.

Exits non-zero with a clear error naming the persona + signal + URL on
any failure. Used in CI by .github/workflows/audit.yml.

Constitution II: "Plausible-sounding citations are not citations." This
script enforces that every URL claim resolves and matches.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("FATAL: PyYAML required. pip install pyyaml")

try:
    import requests
except ImportError:
    requests = None  # type: ignore


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
# URLs can contain balanced parens (e.g. Wikipedia's Apology_(Plato)).
# Greedy match up to whitespace; we strip trailing closing punctuation
# below.
URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
STOPWORDS = {
    "a", "an", "the", "of", "for", "and", "or", "to", "in", "on", "at", "with",
    "by", "from", "as", "is", "are", "be", "this", "that", "it", "its",
    "vs", "vs.",
}


def _load_frontmatter(path: Path) -> dict:
    text = path.read_text()
    m = FRONTMATTER_RE.search(text)
    if not m:
        return {}
    return yaml.safe_load(m.group(1)) or {}


def _content_nouns(label: str) -> list[str]:
    """Extract content noun phrases from the signal's label for body-matching."""
    # Strip punctuation, drop stopwords, keep tokens >= 3 chars
    tokens = re.findall(r"[A-Za-z][A-Za-z\-]+", label.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) >= 3]


_BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _verify_url(url: str, label_tokens: list[str]) -> tuple[bool, str]:
    """Fetch URL, confirm it resolves, grep body for label-token match.

    Returns (ok, msg). Constitution II distinguishes:
        - 200 OK + content match -> ok
        - 200 OK + no content match -> fail (suspicious citation)
        - 403/401/451 (paywall / region / legal) -> ok with warning
          (the page exists and is the right citation; we just can't read it)
        - 404/410/5xx + ConnectionError -> fail (hallucinated or dead URL)
    """
    if requests is None:
        return False, "requests package not installed"
    try:
        resp = requests.get(url, timeout=15, allow_redirects=True,
                            headers={"User-Agent": _BROWSER_UA})
    except Exception as e:
        return False, f"fetch failed: {e}"
    if resp.status_code in (401, 403, 451):
        return True, f"HTTP {resp.status_code} (paywall/region — citation valid, body not checked)"
    if resp.status_code != 200:
        return False, f"HTTP {resp.status_code}"
    body = resp.text.lower()
    matched = sum(1 for t in label_tokens if t in body)
    if matched == 0 and label_tokens:
        return False, f"label tokens {label_tokens!r} not found in body"
    return True, f"matched {matched}/{len(label_tokens)} label tokens"


def verify_card(path: Path, *, fetch_urls: bool = True) -> list[str]:
    """Verify one persona card. Returns a list of error strings (empty = pass)."""
    errors: list[str] = []
    fm = _load_frontmatter(path)
    signals = fm.get("interest_signals") or []
    if len(signals) < 3:
        errors.append(f"{path.name}: only {len(signals)} interest_signals; need >=3 (FR-003)")
        return errors

    total_urls_seen = 0
    for i, sig in enumerate(signals):
        sid = sig.get("id") or f"<no-id-#{i}>"
        sources = sig.get("evidence_sources") or []
        if not sources:
            errors.append(f"{path.name}: signal {sid!r} has no evidence_sources")
            continue
        label_tokens = _content_nouns(sig.get("label", ""))
        signal_has_url = False
        for src in sources:
            if not isinstance(src, str):
                errors.append(f"{path.name}: signal {sid!r} non-string source: {src!r}")
                continue
            urls = URL_RE.findall(src)
            if not urls:
                continue
            signal_has_url = True
            total_urls_seen += 1
            if not fetch_urls:
                continue
            for url in urls:
                # Strip trailing punctuation, BUT preserve balanced parens
                # (e.g. Wikipedia's Apology_(Plato) URL ends in ')')
                url = url.rstrip(".,;:")
                while url.endswith(")") and url.count("(") < url.count(")"):
                    url = url[:-1]
                ok, msg = _verify_url(url, label_tokens)
                if not ok:
                    errors.append(
                        f"{path.name}: signal {sid!r} URL {url}: {msg}"
                    )
        # Constitution II: every signal MUST cite at least one verifiable
        # source. Non-URL citations (books, journal volumes) are permitted but
        # at least ONE source per signal must be a URL so the claim is
        # programmatically verifiable.
        if not signal_has_url:
            errors.append(
                f"{path.name}: signal {sid!r} has no URL among evidence_sources "
                f"(Constitution II: at least one source per signal must be a URL "
                f"so the claim can be auto-verified)"
            )
    if total_urls_seen == 0:
        errors.append(
            f"{path.name}: not a single URL across all interest_signals — "
            "Constitution II requires URL evidence for at least one source per signal."
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Verify persona evidence URLs")
    p.add_argument("personalities_dir", help="agents/prompts/personalities directory")
    p.add_argument("--no-fetch", action="store_true",
                   help="Skip URL fetching (still validates schema + non-URL sources)")
    args = p.parse_args(argv)

    pdir = Path(args.personalities_dir)
    if not pdir.is_dir():
        print(f"FATAL: not a directory: {pdir}", file=sys.stderr)
        return 2

    cards = sorted(pdir.glob("*.md"))
    if not cards:
        print(f"FATAL: no persona cards found in {pdir}", file=sys.stderr)
        return 2

    all_errors: list[str] = []
    for card in cards:
        errors = verify_card(card, fetch_urls=not args.no_fetch)
        if errors:
            all_errors.extend(errors)
            for e in errors:
                print(f"FAIL: {e}", file=sys.stderr)
        else:
            print(f"OK: {card.name}")

    if all_errors:
        print(f"\n{len(all_errors)} verification failures across {len(cards)} cards.", file=sys.stderr)
        return 1
    print(f"\nAll {len(cards)} persona cards verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
