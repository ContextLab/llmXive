"""Autonomous discovery of a REAL, programmatically-accessible data source.

Given a free-text ``intent`` describing a research data need, this module
discovers a concrete, machine-loadable source and HARD-verifies it so that LLM
hallucinations are filtered out:

  1. Web search (``ddgs``) seeds candidates from real search results.
  2. An LLM (``openai.gpt-oss-120b`` via the project router) proposes sources as
     JSON: either a pip-installable dataset package or a directly-streamable
     data URL, each with a self-contained ``access_python`` snippet that LOADS
     real data and prints ``RECORDS=<count>``.
  3. Each proposal is verified for real:
       - ``pypi_package``: install into a FRESH ``python -m venv``; if install
         fails the package is not real → reject. Run the snippet and gate on
         ``returncode == 0`` AND a ``RECORDS=<n>`` line with ``n > 0``. If the
         install succeeded but the recipe is wrong, a bounded REPAIR loop
         introspects the installed package's real exports and asks the LLM to
         FIX the snippet — this is what converges first-guess-wrong APIs (e.g.
         ``knotinfo`` → ``link_list``) to a working recipe.
       - ``data_url``: stream + PARSE a real sample via
         :func:`llmxive.librarian.dataset_resolver.sample_records` and require
         ``record_count > 0`` real records with real field coverage (no venv
         needed) — symmetric with the pypi records gate; a format sniff alone is
         a proxy, not a verification, and does NOT qualify the source.

The verification GATE (``parse_records_gate``) is a PURE function so it can be
unit-tested without network or an LLM: a recipe printing ``RECORDS=0`` or
raising ``ImportError`` is REJECTED; one printing ``RECORDS=250`` is accepted.

The discovered package (e.g. ``database-knotinfo``) is installed only at
runtime in an EPHEMERAL venv — it is never added as a project dependency.
"""
from __future__ import annotations

import json
import logging
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from llmxive.backends.base import ChatMessage
from llmxive.backends.router import chat_with_fallback
from llmxive.librarian.dataset_resolver import sample_records

# Free reasoning model on the Dartmouth catalog (router falls back to local).
logger = logging.getLogger(__name__)

_MODEL = "openai.gpt-oss-120b"
#: When the caller specifies required_fields, a verified source must cover at
#: least this fraction of them — else it's the wrong dataset (e.g. a name-only
#: census) and is rejected (a wrong-schema source is worse than none).
_MIN_FIELD_COVERAGE = 0.5

# Subprocess timeouts (seconds).
_PIP_INSTALL_TIMEOUT = 180
_SNIPPET_TIMEOUT = 120
_VENV_CREATE_TIMEOUT = 120

# Markers the access snippet must print on success.
_RECORDS_RE = re.compile(r"^RECORDS=(\d+)\s*$", re.MULTILINE)
_FIELDS_RE = re.compile(r"^FIELDS=(.*)$", re.MULTILINE)


@dataclass(frozen=True)
class VerifiedSource:
    """A data source proven to load real data.

    ``access_python`` is the WORKING recipe (post-repair if the LLM's first
    guess was wrong); ``record_count`` is the non-zero count the recipe printed
    via its ``RECORDS=<n>`` marker; ``sample_fields`` are parsed from an
    optional ``FIELDS=...`` line.
    """

    kind: str  # "pypi_package" | "data_url"
    ref: str
    access_python: str
    record_count: int
    sample_fields: list[str] = field(default_factory=list)
    source: str = "web-discovery"
    #: Fraction (0..1) of the caller's ``required_fields`` present in a sample
    #: record. 1.0 when the caller specified no required fields. A source that
    #: loads records but lacks the needed columns (e.g. only ``name``) scores
    #: low and loses to a richer source during selection.
    field_coverage: float = 1.0


def _norm_field(s: str) -> str:
    """Normalize a field name for fuzzy matching: lowercase alnum tokens."""
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def field_coverage(sample_fields: list[str], required_fields: list[str]) -> float:
    """Fraction of ``required_fields`` matched by ``sample_fields`` (fuzzy).

    A required field matches a sample field if, after normalization, either
    contains a shared significant token (so "braid index" matches "braid_index",
    "hyperbolic volume" matches "volume"). Pure function — unit-testable.
    """
    if not required_fields:
        return 1.0
    sample_tok = [set(_norm_field(s).split()) for s in sample_fields]
    hits = 0
    for req in required_fields:
        rtoks = {t for t in _norm_field(req).split() if len(t) > 2}
        if rtoks and any(rtoks & st for st in sample_tok):
            hits += 1
    return hits / len(required_fields)


# ---------------------------------------------------------------------------
# Pure verification gate (unit-testable: no network, no LLM, no venv).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GateResult:
    """Outcome of gating a recipe run's ``(returncode, stdout, stderr)``."""

    verified: bool
    record_count: int = 0
    sample_fields: list[str] = field(default_factory=list)
    reason: str | None = None


def parse_records_gate(returncode: int, stdout: str, stderr: str) -> GateResult:
    """Decide whether a recipe execution counts as VERIFIED — PURE, no I/O.

    A recipe is verified iff the process exited 0 AND its stdout contains a
    ``RECORDS=<n>`` line with ``n > 0``. A non-zero exit (e.g. ``ImportError``
    raised), or ``RECORDS=0``, or a missing marker, is REJECTED. An optional
    ``FIELDS=a,b,c`` line populates ``sample_fields``.
    """
    if returncode != 0:
        tail = (stderr or stdout or "").strip().splitlines()
        detail = tail[-1] if tail else "no output"
        return GateResult(False, reason=f"non-zero exit ({returncode}): {detail}")
    m = _RECORDS_RE.search(stdout or "")
    if not m:
        return GateResult(False, reason="no RECORDS=<count> marker in stdout")
    count = int(m.group(1))
    if count <= 0:
        return GateResult(False, record_count=0, reason="RECORDS=0 (no real data loaded)")
    fields: list[str] = []
    fm = _FIELDS_RE.search(stdout or "")
    if fm:
        fields = [f.strip() for f in fm.group(1).split(",") if f.strip()]
    return GateResult(True, record_count=count, sample_fields=fields)


# ---------------------------------------------------------------------------
# Step 1 — web search seeds.
# ---------------------------------------------------------------------------


# Salient-keyword tokens: proper nouns (KnotInfo), acronyms (QM9), and
# multi-word capitalized names (Knot Atlas) — used to build a SHORT, high-signal
# search query when the raw intent is a long prose sentence that dilutes search.
_KEYWORD_RE = re.compile(r"\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?|[A-Z]{2,}\d*)\b")


def _keyword_query(intent: str) -> str:
    """A short query of the salient proper-noun / acronym tokens in ``intent``.

    A verbose prose intent (full sentence) makes a poor web query — the
    load-bearing package page gets diluted past the result window. The salient
    names (e.g. "KnotInfo", "Knot Atlas") are what surface the package/registry
    pages, so we issue them as a compact query alongside the full-intent ones.
    """
    toks: list[str] = []
    for m in _KEYWORD_RE.findall(intent):
        t = m.strip()
        if t and t not in toks:
            toks.append(t)
    return " ".join(toks[:6])


def _web_search_seeds(intent: str, *, per_query: int = 5) -> list[dict[str, str]]:
    """Run a few ``ddgs`` queries derived from ``intent``; return unique hits.

    Each query is wrapped in try/except (web search flakes); failures are
    skipped. Results are de-duplicated by URL, preserving order. Besides the
    full-intent variants, a compact salient-keyword query is issued so the
    pip-package / PyPI page actually surfaces for verbose prose intents.
    """
    from ddgs import DDGS

    kw = _keyword_query(intent)
    queries = [
        intent,
        f"{intent} python package pip",
        f"{intent} dataset download",
    ]
    if kw:
        queries += [f"{kw} python package pip", f"{kw} dataset python pip install"]
    seen: set[str] = set()
    seeds: list[dict[str, str]] = []
    for q in queries:
        try:
            results = DDGS().text(q, max_results=per_query)
        except Exception:
            continue
        for d in results or []:
            url = str(d.get("href") or "")
            if not url or url in seen:
                continue
            seen.add(url)
            seeds.append({
                "title": str(d.get("title") or ""),
                "href": url,
                "body": str(d.get("body") or ""),
            })
    return seeds


# ---------------------------------------------------------------------------
# Step 2 — LLM proposal.
# ---------------------------------------------------------------------------

_PROPOSE_SYSTEM = """\
You find a REAL, programmatically-accessible data source for a research data \
need and return STRICT JSON ONLY (no prose, no markdown fences).

Output schema:
{"sources":[{"kind":"pypi_package"|"data_url","ref":"<pip package name OR a \
direct data URL>","access_python":"<self-contained python snippet>"}]}

STRONGLY PREFER a pip-installable dataset package (kind="pypi_package") whose \
import loads the real census/dataset directly in Python. These are far more \
reliable than raw URLs (web pages 404, require scraping, or return HTML). \
ALWAYS include at least one pypi_package candidate, listed FIRST. Only add a \
data_url candidate if it points at a directly-streamable raw data file (csv/\
json/parquet), never an HTML page. For a `pypi_package`, `ref` is the exact \
PyPI distribution name (e.g. with hyphens as published).

Rules for access_python:
- It MUST load REAL data and print exactly one line `RECORDS=<count>` where \
<count> is the NON-ZERO number of records/rows loaded.
- Optionally also print one line `FIELDS=<comma-separated field names>`.
- It must be fully self-contained (all imports inside the snippet).
- NEVER use `getattr(obj, name, [])` or a try/except that hides a wrong API \
behind an empty list / RECORDS=0. If the API is wrong, the snippet must FAIL \
loudly (raise), not silently print RECORDS=0.
- You may not know the package's exact API — that's fine, give your best guess; \
it will be introspected and corrected if wrong.

Propose 2-3 sources, the pip package FIRST."""


def _rank_seeds_for_prompt(seeds: list[dict[str, str]]) -> list[dict[str, str]]:
    """Surface package-registry hits (PyPI / GitHub) FIRST in the prompt.

    The verbose-intent query tends to rank encyclopedic pages (Wikipedia, arXiv)
    above the pip-package page, which would push the load-bearing
    ``pypi.org/project/<pkg>`` link past the truncated seed window. Stable-sort so
    registry/repo URLs lead while otherwise preserving discovery order.
    """
    def priority(s: dict[str, str]) -> int:
        u = s["href"].lower()
        if "pypi.org/project" in u:
            return 0
        if "github.com" in u or "libraries.io/pypi" in u:
            return 1
        return 2

    return sorted(seeds, key=priority)


_PYPI_NAME_RE = re.compile(r"pypi\.org/project/([A-Za-z0-9._-]+)", re.IGNORECASE)


def _pypi_names_from_seeds(seeds: list[dict[str, str]]) -> list[str]:
    """Extract exact PyPI distribution names from any pypi.org/project/<name> seed."""
    names: list[str] = []
    for s in seeds:
        m = _PYPI_NAME_RE.search(s["href"])
        if m:
            name = m.group(1).rstrip("/")
            if name and name not in names:
                names.append(name)
    return names


def _build_propose_messages(
    intent: str, seeds: list[dict[str, str]], required_fields: list[str] | None = None
) -> list[ChatMessage]:
    ranked = _rank_seeds_for_prompt(seeds)
    seed_lines = [
        f"- {s['title']} | {s['href']}\n  {s['body'][:240]}"
        for s in ranked[:12]
    ]
    seed_block = "\n".join(seed_lines) if seed_lines else "(no web results)"
    pypi_names = _pypi_names_from_seeds(seeds)
    pypi_hint = (
        "\n\nPyPI packages found in the search results (use one of these EXACT "
        "names as `ref` for a pypi_package — do NOT shorten or rename them):\n"
        + "\n".join(f"  - {n}" for n in pypi_names)
        if pypi_names
        else ""
    )
    fields_hint = ""
    if required_fields:
        fields_hint = (
            "\n\nThe dataset MUST contain these fields/columns (choose a source "
            "that has them, NOT one with only a name/id): "
            + ", ".join(required_fields)
            + ". In the access snippet, ALSO print one line `FIELDS=<comma-"
            "separated field names>` listing which of these the loaded records "
            "actually contain (map the package's native column names to these "
            "where they correspond)."
        )
    user = (
        f"Research data need:\n{intent}\n\n"
        f"Web search results (candidate sources):\n{seed_block}"
        f"{pypi_hint}{fields_hint}\n\n"
        "Return the JSON object now."
    )
    return [
        ChatMessage(role="system", content=_PROPOSE_SYSTEM),
        ChatMessage(role="user", content=user),
    ]


def _strip_json_fences(text: str) -> str:
    """Tolerantly strip markdown fences / a leading ``json`` token."""
    t = text.strip()
    if t.startswith("```"):
        # Drop the opening fence line (``` or ```json) and any closing fence.
        t = re.sub(r"^```[a-zA-Z0-9]*\s*", "", t)
        t = re.sub(r"\s*```$", "", t.strip())
    t = t.strip()
    if t.lower().startswith("json"):
        t = t[4:].lstrip()
    return t.strip()


def _extract_json_object(text: str) -> dict[str, object] | None:
    """Parse the first JSON object out of ``text`` tolerantly."""
    cleaned = _strip_json_fences(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Fall back to the first {...} span (the model may add stray prose).
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


def _propose_sources(
    intent: str, seeds: list[dict[str, str]], required_fields: list[str] | None = None
) -> list[dict[str, str]]:
    """Ask the LLM for candidate sources; return a list of {kind,ref,access_python}."""
    resp = chat_with_fallback(
        _build_propose_messages(intent, seeds, required_fields),
        default_backend="dartmouth",
        fallback_backends=["local"],
        model=_MODEL,
    )
    obj = _extract_json_object(resp.text)
    if not obj:
        return []
    raw = obj.get("sources")
    if not isinstance(raw, list):
        return []
    out: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind") or "").strip()
        ref = str(item.get("ref") or "").strip()
        snippet = str(item.get("access_python") or "")
        if kind in {"pypi_package", "data_url"} and ref and snippet.strip():
            out.append({"kind": kind, "ref": ref, "access_python": snippet})
    return out


# ---------------------------------------------------------------------------
# Step 3 — HARD verification.
# ---------------------------------------------------------------------------


def _pip_spec_to_name(ref: str) -> str:
    """Strip a version/extras spec from a pip requirement → bare package name.

    e.g. ``database-knotinfo==1.0`` → ``database-knotinfo``;
    ``foo[bar]>=2`` → ``foo``.
    """
    name = re.split(r"[<>=!~\[ ;]", ref.strip(), maxsplit=1)[0]
    return name.strip()


def _module_name(ref: str) -> str:
    """Best-effort import name for a pip package (``-`` → ``_``)."""
    return _pip_spec_to_name(ref).replace("-", "_")


def _make_venv(venv_dir: Path) -> Path:
    """Create a fresh venv in ``venv_dir``; return its python executable path."""
    subprocess.run(
        [sys.executable, "-m", "venv", str(venv_dir)],
        check=True,
        capture_output=True,
        timeout=_VENV_CREATE_TIMEOUT,
    )
    py = venv_dir / "bin" / "python"
    if not py.exists():  # Windows layout (not expected on this platform).
        py = venv_dir / "Scripts" / "python.exe"
    return py


def _pip_install(py: Path, name: str) -> tuple[bool, str]:
    """``pip install -q <name>`` in the venv. Return (ok, stderr)."""
    try:
        proc = subprocess.run(
            [str(py), "-m", "pip", "install", "-q", name],
            capture_output=True,
            text=True,
            timeout=_PIP_INSTALL_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return False, "pip install timed out"
    return proc.returncode == 0, proc.stderr or proc.stdout


def _run_snippet(py: Path, snippet: str) -> tuple[int, str, str]:
    """Run ``snippet`` via ``<py> -c <snippet>``. Return (returncode, out, err)."""
    try:
        proc = subprocess.run(
            [str(py), "-c", snippet],
            capture_output=True,
            text=True,
            timeout=_SNIPPET_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return 1, "", "snippet execution timed out"
    return proc.returncode, proc.stdout, proc.stderr


def _introspect_package(py: Path, ref: str) -> str:
    """Return the installed package's real top-level exports + submodules, and —
    best-effort — the keys/shape of one sample record loaded via the first
    callable top-level export.

    Surfacing a sample record's real keys is what stops the LLM from inventing a
    filter key (e.g. ``crossing_number``) that doesn't match the data and zeroing
    out the count. The sample probe is wrapped so it never breaks introspection.
    """
    mod = _module_name(ref)
    probe = (
        f"import {mod} as M, pkgutil\n"
        "top = [n for n in dir(M) if not n.startswith('_')]\n"
        "print('top:', top)\n"
        "print('submods:', [m.name for m in pkgutil.iter_modules(M.__path__)] "
        "if hasattr(M, '__path__') else [])\n"
        "# Best-effort: call the first callable top-level export and inspect one record.\n"
        "for n in top:\n"
        "    fn = getattr(M, n)\n"
        "    if callable(fn):\n"
        "        try:\n"
        "            data = list(fn())\n"
        "        except Exception:\n"
        "            continue\n"
        "        print('callable:', n, 'len:', len(data))\n"
        "        if data:\n"
        "            rec = data[1] if len(data) > 1 else data[0]\n"
        "            keys = list(rec.keys()) if isinstance(rec, dict) else type(rec).__name__\n"
        "            print('sample_keys:', keys[:30] if isinstance(keys, list) else keys)\n"
        "        break\n"
    )
    rc, out, err = _run_snippet(py, probe)
    if rc == 0:
        return out.strip()
    return f"(introspection failed: {err.strip() or out.strip()})"


_REPAIR_SYSTEM = """\
You fix a broken python snippet that must load REAL data from an \
already-installed package and print results.

You are given: the pip package name, its ACTUAL importable exports/submodules, \
a sample record's real keys (when available), the previous (broken) snippet, \
and the exact failure (stderr and/or why the output was rejected).

Output ONLY the corrected python snippet — NO prose, NO markdown fences, NO \
explanation.

The corrected snippet MUST:
- be fully self-contained (all imports inside it),
- use the package's REAL exports (shown to you) — do not invent attributes; if \
the top-level export is a function, CALL it (e.g. `list(link_list())`),
- load the FULL dataset/census and print exactly one line `RECORDS=<count>` \
with a NON-ZERO count equal to the number of loaded records,
- NOT apply value filters (crossing-number, etc.) that can shrink the count to \
zero — load EVERYTHING; the goal is to prove the data loads, not to subset it. \
A previous attempt that printed RECORDS=0 was filtering on a key/format that \
did not match the real records — remove such filters,
- optionally also print one line `FIELDS=<comma-separated real field names>` \
taken from a sample record's keys,
- FAIL loudly (raise) if the API is wrong — never hide it behind \
`getattr(...,[])`, try/except, or RECORDS=0."""


def _repair_snippet(
    *, ref: str, exports: str, broken: str, stderr: str, reason: str, stdout: str
) -> str | None:
    """Ask the LLM to FIX the snippet given real exports + the exact failure.

    Passes BOTH the stderr (for raises) AND the gate's rejection ``reason`` +
    a stdout tail (for the silent ``RECORDS=0`` / missing-marker case, where
    stderr is empty) so the model can see WHY the run was rejected.
    """
    user = (
        f"pip package: {ref}\n\n"
        f"actual exports/submodules:\n{exports}\n\n"
        f"previous broken snippet:\n{broken}\n\n"
        f"rejection reason: {reason}\n\n"
        f"stdout (tail):\n{stdout.strip()[-800:]}\n\n"
        f"stderr (tail):\n{stderr.strip()[-1200:]}\n\n"
        "Return ONLY the corrected snippet."
    )
    resp = chat_with_fallback(
        [
            ChatMessage(role="system", content=_REPAIR_SYSTEM),
            ChatMessage(role="user", content=user),
        ],
        default_backend="dartmouth",
        fallback_backends=["local"],
        model=_MODEL,
    )
    fixed = _strip_code_fences(resp.text)
    return fixed or None


def _strip_code_fences(text: str) -> str:
    """Strip ```...``` fences (optionally ```python) around a code snippet."""
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z0-9]*\s*\n?", "", t)
        t = re.sub(r"\n?```\s*$", "", t)
    return t.strip()


_SAMPLE_KEYS_RE = re.compile(r"sample_keys:\s*(\[[^\]]*\])")


def _introspected_sample_keys(py: Path, ref: str) -> list[str]:
    """Real keys of one sample record (from package introspection) — used to
    score field coverage WITHOUT relying on the recipe printing a FIELDS line."""
    m = _SAMPLE_KEYS_RE.search(_introspect_package(py, ref))
    if not m:
        return []
    try:
        import ast

        val = ast.literal_eval(m.group(1))
        return [str(x) for x in val] if isinstance(val, list) else []
    except (ValueError, SyntaxError):
        return []


def _finalize_source(
    ref: str, snippet: str, gate: GateResult, py: Path,
    required_fields: list[str] | None,
) -> VerifiedSource:
    """Build a VerifiedSource. Field coverage uses the recipe's FIELDS line if it
    printed one, else the package's REAL introspected record keys — so coverage
    doesn't hinge on the LLM remembering to emit FIELDS (a rich source like
    database-knotinfo must not be rejected merely because its recipe omitted it)."""
    fields = gate.sample_fields
    if required_fields and not fields:
        fields = _introspected_sample_keys(py, ref)
    return VerifiedSource(
        kind="pypi_package", ref=ref, access_python=snippet,
        record_count=gate.record_count, sample_fields=fields,
        field_coverage=field_coverage(fields, required_fields or []),
    )


def _verify_pypi_package(
    proposal: dict[str, str], *, repair_rounds: int, deadline: float,
    required_fields: list[str] | None = None,
) -> VerifiedSource | None:
    """Install a proposed pip package in a fresh venv and gate its recipe,
    repairing the recipe up to ``repair_rounds`` times. Returns a
    VerifiedSource on success, else None. Never raises on candidate failure.
    """
    ref = proposal["ref"]
    name = _pip_spec_to_name(ref)
    snippet = proposal["access_python"]
    with tempfile.TemporaryDirectory(prefix="llmxive-disc-") as tmp:
        try:
            py = _make_venv(Path(tmp) / "venv")
        except (subprocess.SubprocessError, OSError):
            return None
        ok, _install_err = _pip_install(py, name)
        if not ok:
            # Not a real installable package → reject (a hallucinated name).
            return None
        rc, out, err = _run_snippet(py, snippet)
        gate = parse_records_gate(rc, out, err)
        if gate.verified:
            return _finalize_source(ref, snippet, gate, py, required_fields)
        # Repair loop: introspect the REAL exports and ask the LLM to fix it.
        exports = _introspect_package(py, ref)
        for _ in range(max(0, repair_rounds)):
            if time.monotonic() > deadline:
                break
            fixed = _repair_snippet(
                ref=ref, exports=exports, broken=snippet,
                stderr=err, reason=gate.reason or "rejected", stdout=out,
            )
            if not fixed or fixed.strip() == snippet.strip():
                # No new/changed recipe to try → the model is stuck; stop early
                # rather than burning identical rounds.
                break
            snippet = fixed
            rc, out, err = _run_snippet(py, snippet)
            gate = parse_records_gate(rc, out, err)
            if gate.verified:
                return _finalize_source(ref, snippet, gate, py, required_fields)
        return None


def _verify_data_url(
    proposal: dict[str, str], *, required_fields: list[str] | None = None
) -> VerifiedSource | None:
    """Verify a data URL by STREAMING + PARSING a real sample (no venv).

    Symmetric with :func:`_verify_pypi_package`'s records gate: a URL qualifies
    only if a downloaded sample both sniffs as a known dataset format AND parses
    into ``record_count > 0`` real records (via
    :func:`llmxive.librarian.dataset_resolver.sample_records`). A URL that merely
    "sniffs parseable" but yields zero countable records is REJECTED — a format
    sniff is a PROXY, not a verification. ``field_coverage`` is computed from the
    sample's REAL parsed field names against the caller's ``required_fields`` (so
    a URL with the wrong schema loses to a richer source and, if it's the best
    candidate, is rejected by the caller's coverage gate) — never the old
    ``1.0`` free pass when no fields were requested.
    """
    ref = proposal["ref"]
    if not ref.lower().startswith(("http://", "https://")):
        return None
    sr = sample_records(ref)
    if not sr.parsed or sr.record_count <= 0:
        return None
    return VerifiedSource(
        kind="data_url", ref=ref, access_python=proposal["access_python"],
        record_count=sr.record_count, sample_fields=list(sr.fields),
        field_coverage=field_coverage(sr.fields, required_fields or []),
    )


# ---------------------------------------------------------------------------
# Public entry point.
# ---------------------------------------------------------------------------

# Overall wall-clock cap for one discovery call (venv + installs + LLM repairs).
_TOTAL_BUDGET_S = 900


def discover_data_source(
    intent: str, *, required_fields: list[str] | None = None,
    max_sources: int = 3, repair_rounds: int = 3,
) -> VerifiedSource | None:
    """Discover and HARD-verify a real, programmatic data source for ``intent``.

    Web-searches for seeds, asks the LLM to propose sources, then verifies each
    (capped at ``max_sources``) for real — installing pip packages in an
    ephemeral venv and gating their access recipe (with a bounded ``repair_rounds``
    introspect-and-fix loop) or sniffing data URLs.

    When ``required_fields`` is given, a source must not only LOAD records but
    contain (most of) those fields — the richest-covering verified source wins,
    and one covering fewer than :data:`_MIN_FIELD_COVERAGE` of them is rejected
    (a name-only census is the WRONG dataset even though it loads records).
    Returns the best :class:`VerifiedSource`, or ``None`` if nothing qualifies.

    Never raises on a single-candidate failure — it moves on to the next.
    """
    deadline = time.monotonic() + _TOTAL_BUDGET_S
    seeds = _web_search_seeds(intent)
    try:
        proposals = _propose_sources(intent, seeds, required_fields)
    except Exception:
        proposals = []
    verified: list[VerifiedSource] = []
    for proposal in proposals[: max(1, max_sources)]:
        if time.monotonic() > deadline:
            break
        try:
            if proposal["kind"] == "pypi_package":
                result = _verify_pypi_package(
                    proposal, repair_rounds=repair_rounds, deadline=deadline,
                    required_fields=required_fields,
                )
            else:
                result = _verify_data_url(proposal, required_fields=required_fields)
        except Exception:
            # A single candidate blowing up must never abort discovery.
            continue
        if result is None:
            continue
        verified.append(result)
        # A fully-covering source (or no field requirement) is ideal — stop early
        # rather than spend the budget verifying further candidates.
        if result.field_coverage >= 0.999:
            break
    if not verified:
        return None
    # Pick the richest source: most required-field coverage, then most records.
    verified.sort(key=lambda v: (v.field_coverage, v.record_count), reverse=True)
    best = verified[0]
    if required_fields and best.field_coverage < _MIN_FIELD_COVERAGE:
        logger.warning(
            "discovery: best source %r covers only %.0f%% of required fields "
            "(< %.0f%%) — rejecting as wrong-schema",
            best.ref, best.field_coverage * 100, _MIN_FIELD_COVERAGE * 100,
        )
        return None
    return best


__all__ = [
    "GateResult",
    "VerifiedSource",
    "discover_data_source",
    "field_coverage",
    "parse_records_gate",
]
