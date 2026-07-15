"""Deterministic anti-fabrication gate (PROJ-604).

A project's analysis can RUN and write real *files* while its reported numbers are
FABRICATED — drawn from ``random.*`` with a range hand-tuned to a paper's claim,
forced by a tautological constant, or openly labelled "simulated metrics" because
the real computation could not run on the CPU CI. The execution gate's bar is
only "the code ran and a file appeared", and the harness-receipt layer proves an
artifact's *provenance* (which run produced it), NOT that its numbers are real —
so a fabricated benchmark sails through to ``research_complete`` and only the
(non-deterministic) LLM review panel catches it.

This module is the missing DETERMINISTIC check: it scans the analysis CODE and the
produced RESULT files for unambiguous fabrication signals and reports findings the
caller turns into a hard gate failure (``ok=False`` → kickback to implementation).

Design for HIGH PRECISION (must not block honest work):
- It targets the *output/metric* being faked, not the mere presence of randomness
  or the word "simulation" — a legitimate Monte-Carlo simulation, a synthetic
  *input* dataset, a random seed, a bootstrap CI, or a train/test split are all
  fine and are NOT flagged.
- It fires only on explicit self-declarations that the reported metrics are
  simulated/placeholder/hardcoded, or on a reported number assigned *directly*
  from an RNG draw (no real computation between the RNG and the written result).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

# --- Self-declared fabrication of the OUTPUT / METRICS ----------------------
# Each pattern targets a claim that the RESULT itself is fake — NOT a legitimate
# "simulation" *method* or "synthetic *input* data". Honest analysis code/results
# do not describe their own headline numbers this way.
_FAKE_METRIC_PHRASES = (
    # "simulated metrics", "simulated result(s)", "simulated speedup/throughput/..."
    r"simulat(?:ed|e\s+the)\s+(?:metric|result|number|speedup|throughput|latency|"
    r"accuracy|score|benchmark|performance|measurement)",
    # "we cannot/can't run the actual ... so we simulate/approximate/fake ..."
    r"(?:can(?:not|'t)|could\s*n(?:ot|'t)|unable\s+to)\s+run\s+the\s+(?:actual|real)"
    r"[^.\n]{0,80}(?:simulat|approximat|fake|placeholder|mock)",
    # placeholder / mock / fake / dummy / hardcoded value standing in for a metric
    r"(?:placeholder|mock|fake|dummy|hard[\s-]?coded)\s+(?:metric|result|number|"
    r"value|speedup|throughput|accuracy|score|measurement|data\s+point)",
    # an "arbitrary" scaling/constant used to manufacture a reported quantity
    r"arbitrary\s+(?:scaling|constant|factor|value|number)",
    # a range/number chosen to reproduce the paper's claim rather than measured
    r"(?:tuned|chosen|set|adjusted)\s+to\s+(?:match|reproduce|hit)\s+the\s+paper",
    r"to\s+match\s+the\s+paper'?s?\s+(?:claim|reported|number|result)",
    # explicit "not a real measurement/experiment"
    r"not\s+(?:a\s+)?real\s+(?:measurement|experiment|computation|benchmark)",
    # a results-metadata field openly declaring the run is a simulation of metrics
    r"\bsimulated\s+metrics\b",
)
_FAKE_METRIC_RE = re.compile("|".join(_FAKE_METRIC_PHRASES), re.IGNORECASE)

# Modules whose direct draw, used as a value, is an RNG (not real computation).
_RNG_ROOTS = {"random", "np", "numpy"}
# Attribute paths that are RNG draws: random.uniform, np.random.normal, etc.
_RNG_DRAW_FUNCS = {
    "uniform", "random", "randint", "randrange", "gauss", "normalvariate",
    "normal", "randn", "rand", "choice", "triangular", "betavariate",
    "lognormvariate", "expovariate", "standard_normal",
}
# Result/metric-ish names: when an RNG draw is assigned to (or returned as) one of
# these, the reported number IS the random draw.
_METRIC_NAME_RE = re.compile(
    r"speedup|throughput|latency|accuracy|score|fps|memory|mem_|"
    r"reduction|improvement|gain|ratio|perf|time_ms|metric|result",
    re.IGNORECASE,
)
_RESULT_SINK_RE = re.compile(r"to_csv|to_json|to_parquet|json\.dump|savefig|DataFrame")


def _is_rng_call(node: ast.AST) -> bool:
    """True iff ``node`` is a direct RNG draw like ``random.uniform(...)`` or
    ``np.random.normal(...)`` — a value with NO real computation behind it."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    # x.y(...) — attribute call
    if isinstance(func, ast.Attribute) and func.attr in _RNG_DRAW_FUNCS:
        root = func.value
        # random.uniform / np.random.normal / numpy.random.rand
        if isinstance(root, ast.Name) and root.id in _RNG_ROOTS:
            return True
        if isinstance(root, ast.Attribute) and root.attr == "random":
            base = root.value
            if isinstance(base, ast.Name) and base.id in _RNG_ROOTS:
                return True
    return False


def scan_text_for_fabrication(text: str, *, source: str) -> list[str]:
    """Findings where ``text`` self-declares its OUTPUT/METRICS are fabricated.

    Usable on any stage artifact (spec/plan/tasks prose, analysis code comments,
    or produced result files) — the same deterministic signal at every stage."""
    out: list[str] = []
    for m in _FAKE_METRIC_RE.finditer(text or ""):
        snippet = text[max(0, m.start() - 30): m.end() + 30].replace("\n", " ").strip()
        out.append(f"{source}: self-declared fabricated metric — “…{snippet}…”")
    return out


def _scan_code_rng_metrics(code_text: str, *, source: str) -> list[str]:
    """Findings where a REPORTED metric is assigned/returned directly from an RNG
    draw — the number itself IS random, with no real computation behind it."""
    out: list[str] = []
    try:
        tree = ast.parse(code_text)
    except SyntaxError:
        return out

    # A function whose body is essentially `return <rng draw>` is a fabricator
    # primitive (PROJ-604's `simulate_gemm_throughput`). Record its name.
    fabricator_funcs: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for sub in ast.walk(node):
                if isinstance(sub, ast.Return) and sub.value is not None and _is_rng_call(sub.value):
                    fabricator_funcs.add(node.name)
                    out.append(
                        f"{source}: function `{node.name}` returns a bare RNG draw "
                        f"(line {sub.lineno}) — a reported value computed from no real input"
                    )
                    break

    # An assignment whose RHS is a direct RNG draw OR a call to a fabricator
    # function (one that returns a bare RNG draw), AND whose target name looks like
    # a metric: `speedup = random.uniform(1.6, 2.3)` or
    # `speedup = simulate_gemm_throughput(...)` (PROJ-604).
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        rhs = node.value
        from_rng = _is_rng_call(rhs)
        from_fab = (
            isinstance(rhs, ast.Call)
            and isinstance(rhs.func, ast.Name)
            and rhs.func.id in fabricator_funcs
        )
        if not (from_rng or from_fab):
            continue
        for tgt in node.targets:
            name = getattr(tgt, "id", None)
            if name and _METRIC_NAME_RE.search(name):
                how = "an RNG draw" if from_rng else f"fabricator `{rhs.func.id}()`"
                out.append(
                    f"{source}: metric `{name}` assigned from {how} (line {node.lineno})"
                )
    return out


#: Directory names that hold INSTALLED dependencies / build / cache artifacts —
#: NOT the project's own authored analysis. Scanning them flags THIRD-PARTY library
#: docstrings/comments ("…tries to simulate the result…", "Arbitrary values…") as
#: fabrication — 143 false positives from a single ``code/.venv`` (PIL, pytest, …)
#: that wrongly fail the execution gate for essentially every project with a venv.
_SKIP_DIR_PARTS = frozenset({
    ".venv", "venv", "env", ".env", "virtualenv", "site-packages", "dist-packages",
    "__pycache__", "node_modules", ".git", ".tox", ".nox", ".mypy_cache",
    ".pytest_cache", ".ipynb_checkpoints", "dist", "build", ".eggs", ".cache",
    "external",  # vendored ORIGINAL repo of a reprocessed paper (not our analysis)
})


def _skip_path(p: Path) -> bool:
    """True if ``p`` is NOT the project's own ANALYSIS code/output: installed
    third-party deps, build/cache artifacts, OR test code. Test files legitimately
    use synthetic/random fixtures and assert on stub values — that is unit testing,
    not a fabricated RESEARCH result (the produced data/ + analysis code are still
    scanned), so flagging them is a false positive."""
    if any(part in _SKIP_DIR_PARTS or part.endswith(".egg-info") for part in p.parts):
        return True
    if "tests" in p.parts or "test" in p.parts:
        return True
    name = p.name
    return name == "conftest.py" or name.startswith("test_") or name.endswith("_test.py")


def find_code_fabrication(project_dir: Path) -> list[str]:
    """Scan a project's analysis code (``code/**/*.py``) for fabrication signals."""
    out: list[str] = []
    code_dir = project_dir / "code"
    if not code_dir.is_dir():
        return out
    for py in sorted(code_dir.rglob("*.py")):
        if _skip_path(py):
            continue
        try:
            text = py.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = py.relative_to(project_dir).as_posix()
        out += scan_text_for_fabrication(text, source=rel)
        out += _scan_code_rng_metrics(text, source=rel)
    return out


def find_result_fabrication(project_dir: Path) -> list[str]:
    """Scan a project's PRODUCED result files (data/ + figures-adjacent summaries)
    for self-declared fabrication of the reported numbers."""
    out: list[str] = []
    for sub in ("data", "results", "outputs"):
        d = project_dir / sub
        if not d.is_dir():
            continue
        for f in sorted(d.rglob("*")):
            if _skip_path(f):
                continue
            if f.suffix.lower() not in (".json", ".csv", ".md", ".txt", ".yaml", ".yml"):
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            # Only the header/metadata of a big CSV matters (the column-level fake
            # is caught in code); cap the read for huge files.
            out += scan_text_for_fabrication(
                text[:20000], source=f.relative_to(project_dir).as_posix()
            )
    return out


# --- Synthetic INPUT data -----------------------------------------------------
# Generating fake INPUT data is acceptable ONLY when the project EXPLICITLY calls
# for it (e.g. a simulation study, a synthetic-benchmark paper). For a project
# meant to produce REAL-WORLD insights, substituting synthetic/fake/dummy data
# for the real dataset means the "findings" are not real — the analysis must use
# the real data (download a small real sample) or, if genuinely infeasible on the
# CPU runner, ESCALATE (GPU offload), never fall back to invented data. Detected
# by the code's OWN label (the code_adapter is told to label synthetic data
# clearly), so this is high-precision and never fires on real-data analysis,
# bootstrap resampling, seeds, or noise injection.
_SYNTHETIC_DATA_RE = re.compile(
    # synthetic/fake/… optionally one intervening word, then a data noun:
    # "synthetic data", "synthetic sampled input data", "fake input samples".
    r"\b(?:synthetic|fake|dummy|mock|simulated|randomly[\s-]generated)\s+(?:\w+\s+)?"
    r"(?:data|dataset|datasets|input|inputs|sample|samples|examples?|records?|corpus|table)\b"
    r"|\bgenerate[ds]?\s+(?:\w+\s+){0,2}synthetic\b",
    re.IGNORECASE,
)

# The synthetic-phrase core (shared with _SYNTHETIC_DATA_RE's first alternative).
_SYNTH_PHRASE = (
    r"(?:synthetic|fake|dummy|mock|simulated|randomly[\s-]generated)\s+(?:\w+\s+)?"
    r"(?:data|dataset|datasets|input|inputs|sample|samples|examples?|records?|corpus|table)"
)
# An AVOIDANCE construct: a negation/refusal cue governing the synthetic phrase —
# "avoid fake data", "rather than synthetic data", "do NOT fall back to synthetic
# data", "no synthetic data". Such code is REFUSING to fabricate, not doing it; the
# gate wrongly blocked live projects (PROJ-306, PROJ-606) whose comments said exactly
# that. The bridge between cue and phrase is bounded AND punctuation-free
# (``[^.,;:\n]{0,24}?``): a comma or clause break severs a wrongful attachment, so
# "the real data was not available, so we use synthetic data" (genuine fabrication
# with an unrelated nearby "not") STAYS flagged, and "Instead of the real dataset, we
# generate 200 synthetic rows" keeps its "instead of" bound to the real dataset. Fail
# closed: only a cue clearly attached to the synthetic phrase clears it.
_AVOIDANCE_RE = re.compile(
    r"(?:avoid(?:s|ing|ed)?|without|rather\s+than|instead\s+of|refus\w*|prohibit\w*|"
    r"forbid\w*|never|don'?t|does\s*n'?t|do(?:es)?\s+not|\bnot\b|\bno\b)"
    r"[^.,;:\n]{0,24}?" + _SYNTH_PHRASE,
    re.IGNORECASE,
)


def _synthetic_data_authorized(project_dir: Path) -> bool:
    """True iff the project's ORIGINAL research intent explicitly calls for
    synthetic or simulated data (the research question is about it).

    Scans the ``idea/`` dir ONLY — the genuine, pre-implementation intent.
    Deliberately NOT the spec/plan/tasks: those are BACK-FILLED from the code for
    reprocessed papers, so they mention synthetic data merely BECAUSE the code
    uses it (circular self-authorization). A real-world-insight project's idea
    never frames itself around synthetic data, so synthetic data in its code is an
    unauthorized shortcut, not the design."""
    d = project_dir / "idea"
    if not d.is_dir():
        return False
    for f in d.rglob("*.md"):
        try:
            if _SYNTHETIC_DATA_RE.search(f.read_text(encoding="utf-8", errors="ignore")):
                return True
        except OSError:
            continue
    return False


def find_synthetic_data_use(project_dir: Path) -> list[str]:
    """Findings where the project's code/results use SYNTHETIC input data (by the
    code's own label). The caller suppresses these when the spec authorizes it."""
    out: list[str] = []
    for sub in ("code", "data", "results", "outputs"):
        d = project_dir / sub
        if not d.is_dir():
            continue
        for f in sorted(d.rglob("*")):
            if _skip_path(f):
                continue
            if f.suffix.lower() not in (".py", ".json", ".csv", ".md", ".txt", ".yaml", ".yml"):
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            scanned = text[:40000]
            avoided = [a.span() for a in _AVOIDANCE_RE.finditer(scanned)]
            for m in _SYNTHETIC_DATA_RE.finditer(scanned):
                # Skip a phrase the code is REFUSING (its match falls inside an
                # avoidance construct — "avoid fake data", "not … synthetic data").
                if any(lo <= m.start() < hi for lo, hi in avoided):
                    continue
                snippet = text[max(0, m.start() - 25): m.end() + 25].replace("\n", " ").strip()
                out.append(
                    f"{f.relative_to(project_dir).as_posix()}: synthetic/fake INPUT data "
                    f"not authorized by the spec — “…{snippet}…”"
                )
    return out


def find_fabrication(project_dir: Path) -> list[str]:
    """All deterministic fabrication findings for a project's analysis + results.

    A NON-EMPTY return means the reported results are fabricated/simulated rather
    than measured (or rest on unauthorized synthetic data) — the caller must FAIL
    the execution gate and kick the project back to implementation rather than let
    it reach research_complete."""
    findings = find_code_fabrication(project_dir) + find_result_fabrication(project_dir)
    # Synthetic INPUT data is fabrication UNLESS the project explicitly requires it.
    if not _synthetic_data_authorized(project_dir):
        findings += find_synthetic_data_use(project_dir)
    return findings
