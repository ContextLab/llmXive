"""State-artifact reader pre-check (issue #1139, anti-pattern 1).

Anti-pattern 1 ("dead-end verified artifact") is a stage that COMPUTES/persists a
durable state artifact that NOTHING downstream reads — so the work is thrown away
(the ``resolved_datasets.yaml`` case: written 676 times, read by nobody). This guard
makes that class of defect a CI failure instead of a latent dead-end.

Rule: **every fixed-name artifact a non-test source module WRITES under
``state/`` or ``.specify/memory/`` must also be READ by non-test source** — a
writer with no reader (its own store's ``load`` counts; only-test readers do not)
is a dead-end and fails the check.

The analysis is AST dataflow, associating each write/read verb with the SPECIFIC
artifact basename it touches (so a module that writes ``a.yaml`` and separately
reads ``b.yaml`` does not falsely count as reading ``a.yaml``):

* Module-level ``NAME = "foo.yaml"`` constants and same-module path helpers
  (functions that ``return <path built from a basename>``) are resolved, so
  ``(dir / _CACHE_NAME).write_text(...)`` and ``_cache_path(...).read_text()``
  both resolve to the basename.
* Local variables are tracked within each function: ``p = dir / "x.yaml"`` then
  ``p.write_text(...)`` associates the write with ``x.yaml``.
* Per-project files with DYNAMIC names (``f"{project_id}.json"``) carry no fixed
  basename, so they are naturally out of scope — always read by their own
  store's ``load``.
* A basename is IN SCOPE only if it is written on a path that references a
  ``state`` / ``.specify`` / ``memory`` segment (machine state, not content
  artifacts like ``spec.md`` or prompt files).

Artifacts intentionally consumed OUTSIDE non-test Python (the web dashboard, git,
humans) are listed in :data:`ALLOWLIST` with a justification. Exits 1 with one
line per dead-end.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from llmxive.config import repo_root as _repo_root

_SOURCE_ROOTS = ("src/llmxive", "agents")
_ARTIFACT_SUFFIXES = (".yaml", ".yml", ".json", ".md")
_STATE_TOKENS = {"state", ".specify", "memory", ".specify/memory"}

#: Method names that READ a path (receiver is the path expression).
_READ_METHODS = {"read_text", "read_bytes", "exists", "is_file", "glob", "rglob",
                 "iterdir", "open"}
#: Method names that WRITE a path (receiver is the path expression).
_WRITE_METHODS = {"write_text", "write_bytes"}
#: Free functions that WRITE, path = first positional arg.
_WRITE_FUNCS = {"atomic_write_text", "atomic_write_text_cas"}
#: Free functions that READ, path = first positional arg (``open(path)``).
_READ_FUNCS = {"open"}

ALLOWLIST: dict[str, str] = {
    # A human-readable consolidated peer-review artifact committed to git (222
    # files under projects/**/paper/) and read by maintainers/authors. It is a
    # RENDERED VIEW, not a pipeline input: the underlying action-item DATA is
    # threaded forward from the review records (paper/reviews/*) in-memory to the
    # review PDF (paper_reprocess.preprint_pdf.build_peer_review_tex) and to the
    # dashboard via web/data/projects.json's `action_items` field. So the writer
    # is NOT a dead-end — its consumer is human/git, not non-test src.
    "action_items.md": (
        "human-readable committed peer-review artifact; action-item data is "
        "threaded forward via review records -> review PDF + dashboard JSON"
    ),
    # The dashboard data file: consumed by the web dashboard (web/js/app.js,
    # web/js/dialog.js) and committed to docs/data/. No Python consumer by design
    # (web_data + status_reporter GENERATE it).
    "projects.json": "dashboard data file consumed by web/js + committed docs/",
    # The Kaggle kernel spec that offload.dispatch writes and PUSHES; the Kaggle
    # API/CLI is the consumer (issue #367 GPU offload), not non-test src.
    "kernel-metadata.json": "Kaggle kernel spec consumed by the Kaggle API on push",
    # Read by the implementer via `round_dir.glob('*.md')` (spec-012 auto-revisions
    # round contract, agents/implementer.py ~L2208) — consumed by a directory glob,
    # so it is never named literally for a by-name static reader to see.
    "analyze-report.md": "read by implementer via round_dir.glob('*.md') (spec-012)",
    # Human reproduction guide for a reprocessed code paper; surfaced as a project
    # artifact link in web/data/projects.json (dashboard), read by humans.
    "reproduction.md": "human reproduction guide; surfaced as a dashboard artifact",
    # Documented human-facing deliverable of the arXiv/reprocess intake bundle
    # (paper_reprocess/__init__ lists it); the actionable code-resource data is
    # threaded via metadata.json (consumed by paper_reprocess/classify.py).
    "external_resources.md": (
        "documented human-facing intake deliverable; code-resource data threaded "
        "via metadata.json (consumed by classify.py)"
    ),
    # Intentional provenance/historical marker, EXPLICITLY documented at
    # pipeline/graph.py ~L1696 ("left in place as a historical artifact; it does
    # not override the default stage transition"). Authoritative state is the
    # stage transition; the sentinel is a committed git provenance record.
    "research_question_validated.yaml": (
        "intentional historical provenance marker (documented graph.py ~L1696)"
    ),
    # Sibling provenance marker to research_question_validated.yaml: a committed
    # git record of the idea selection + timestamp. Selection is authoritative via
    # the stage transition; no code consumer by design.
    "idea_selected.yaml": (
        "provenance/selection marker committed to git; selection authoritative via "
        "the stage transition (sibling of research_question_validated.yaml)"
    ),
}


def _is_test_path(p: Path) -> bool:
    parts = set(p.parts)
    return "tests" in parts or p.name.startswith("test_") or "__pycache__" in parts


def _basename_if_artifact(value: str) -> str | None:
    if value.lower().endswith(_ARTIFACT_SUFFIXES):
        name = Path(value).name
        # must have a real stem before the extension (excludes bare ".json"/"*.json")
        if name and not name.startswith("*") and "." in name and name.split(".")[0]:
            return name
    return None


class _ModuleScan:
    """Resolves artifact basenames touched by write/read verbs in one module."""

    def __init__(self, tree: ast.Module):
        self.tree = tree
        self.consts: dict[str, str] = {}       # NAME -> basename
        self.helpers: dict[str, set[str]] = {}  # func name -> basenames it returns
        self.mentions: set[str] = set()         # every artifact basename referenced
        self.state_tokens_present = False
        self.writes: set[str] = set()
        self.reads: set[str] = set()
        self.write_is_state: dict[str, bool] = {}
        self.read_wrappers: set[str] = set()   # fns that read their first arg
        self._collect_consts_and_helpers()
        self._detect_read_wrappers()
        self._walk_functions()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                b = _basename_if_artifact(node.value)
                if b:
                    self.mentions.add(b)
        self.mentions |= set(self.consts.values())

    # ---- pass 1: module constants + path-helper return basenames ---------- #
    def _collect_consts_and_helpers(self) -> None:
        for node in self.tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) \
                    and isinstance(node.value.value, str):
                b = _basename_if_artifact(node.value.value)
                if b:
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            self.consts[t.id] = b
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                returned: set[str] = set()
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Return) and sub.value is not None:
                        returned |= self._expr_basenames(sub.value, {})
                if returned:
                    self.helpers[node.name] = returned

    # ---- detect custom read-wrapper functions (``_read_optional(path)``) --- #
    def _detect_read_wrappers(self) -> None:
        """A function that applies a READ verb to its FIRST parameter is a read
        wrapper (e.g. ``_read_optional(path)`` → ``path.read_text()``); a call to
        it consumes the artifact passed in. Same-module detection only."""
        for node in ast.walk(self.tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.args.args:
                continue
            first = node.args.args[0].arg
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) \
                        and sub.func.attr in _READ_METHODS:
                    if any(isinstance(n, ast.Name) and n.id == first
                           for n in ast.walk(sub.func.value)):
                        self.read_wrappers.add(node.name)
                        break
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) \
                        and sub.func.id in _READ_FUNCS and sub.args \
                        and any(isinstance(n, ast.Name) and n.id == first
                                for n in ast.walk(sub.args[0])):
                    self.read_wrappers.add(node.name)
                    break

    # ---- resolve the artifact basenames a path expression refers to ------- #
    def _expr_basenames(self, expr: ast.AST, locals_: dict[str, set[str]]) -> set[str]:
        out: set[str] = set()
        for node in ast.walk(expr):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                b = _basename_if_artifact(node.value)
                if b:
                    out.add(b)
            elif isinstance(node, ast.Name):
                if node.id in self.consts:
                    out.add(self.consts[node.id])
                if node.id in locals_:
                    out |= locals_[node.id]
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                    and node.func.id in self.helpers:
                out |= self.helpers[node.func.id]
        return out

    @staticmethod
    def _expr_has_state(expr: ast.AST) -> bool:
        for node in ast.walk(expr):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                    and node.value in _STATE_TOKENS:
                return True
        return False

    # ---- pass 2: flow-insensitive dataflow over the WHOLE module --------- #
    def _walk_functions(self) -> None:
        # Local-var -> basenames bindings, collected module-wide and regardless of
        # nesting (writes/reads inside if/for/with/try blocks must be seen). Two
        # passes so a binding that depends on a later-collected one still resolves.
        # A var reused across functions unions its basenames — a safe
        # over-approximation (it can only ADD read/write associations, never hide
        # a real dead-end).
        locals_: dict[str, set[str]] = {}
        for _ in range(2):
            for node in ast.walk(self.tree):
                if isinstance(node, ast.Assign):
                    bn = self._expr_basenames(node.value, locals_)
                    if bn:
                        for t in node.targets:
                            if isinstance(t, ast.Name):
                                locals_.setdefault(t.id, set()).update(bn)
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call):
                self._classify_call(node, locals_)

    def _classify_call(self, call: ast.Call, locals_: dict[str, set[str]]) -> None:
        func = call.func
        if isinstance(func, ast.Attribute):
            recv = func.value
            if func.attr in _WRITE_METHODS:
                for b in self._expr_basenames(recv, locals_):
                    self.writes.add(b)
                    self.write_is_state[b] = self.write_is_state.get(b, False) or \
                        self._path_is_state(recv, locals_)
            elif func.attr in _READ_METHODS:
                self.reads |= self._expr_basenames(recv, locals_)
        elif isinstance(func, ast.Name):
            if func.id in _WRITE_FUNCS and call.args:
                bns = self._expr_basenames(call.args[0], locals_)
                for b in bns:
                    self.writes.add(b)
                    self.write_is_state[b] = self.write_is_state.get(b, False) or \
                        self._path_is_state(call.args[0], locals_)
            elif func.id in _READ_FUNCS and call.args:
                self.reads |= self._expr_basenames(call.args[0], locals_)
            elif func.id in self.read_wrappers and call.args:
                self.reads |= self._expr_basenames(call.args[0], locals_)

    def _path_is_state(self, expr: ast.AST, locals_: dict[str, set[str]]) -> bool:
        """True if the write path references a state/.specify/memory segment.

        Checks the expression itself and, when it is a bare Name bound earlier,
        the whole module text as a fallback (a store module that writes under
        ``state/`` almost always references the token somewhere)."""
        if self._expr_has_state(expr):
            return True
        # bare local var whose binding expr referenced state
        return self.state_tokens_present


def main() -> int:
    repo = _repo_root()
    writers: dict[str, set[str]] = {}
    precise_readers: dict[str, set[str]] = {}
    state_scoped: set[str] = set()
    # (rel, basenames-mentioned, has-any-read-verb) per file, for the lenient pass.
    file_info: list[tuple[str, set[str], bool]] = []

    _READ_MARKERS = (
        ".read_text(", ".read_bytes(", "safe_load", "json.load", ".exists(",
        ".is_file(", ".glob(", ".rglob(", ".iterdir(", "open(",
    )

    files: list[Path] = []
    for root in _SOURCE_ROOTS:
        base = repo / root
        if base.is_dir():
            files.extend(p for p in base.rglob("*.py") if not _is_test_path(p))

    for f in files:
        if f.name == "state_readers.py":
            continue
        try:
            text = f.read_text(encoding="utf-8")
            tree = ast.parse(text)
        except (OSError, SyntaxError):
            continue
        scan = _ModuleScan(tree)
        scan.state_tokens_present = any(tok in text for tok in _STATE_TOKENS)
        rel = str(f.relative_to(repo))
        for b in scan.writes:
            writers.setdefault(b, set()).add(rel)
            if scan.write_is_state.get(b) or scan.state_tokens_present:
                state_scoped.add(b)
        for b in scan.reads:
            precise_readers.setdefault(b, set()).add(rel)
        file_info.append((rel, set(scan.mentions), any(m in text for m in _READ_MARKERS)))

    def _has_reader(b: str) -> bool:
        # Precise dataflow read anywhere → definitely consumed.
        if precise_readers.get(b):
            return True
        # Lenient cross-module fallback: a NON-writer module that names this
        # artifact AND has a read verb is almost certainly a reader whose exact
        # path the dataflow could not trace (e.g. a cross-module loader). Only a
        # self-only artifact — named by no module other than its writer(s) — has
        # to prove a precise read; that is the true dead-end case.
        w = writers.get(b, set())
        return any(b in mentions and has_read and rel not in w
                   for rel, mentions, has_read in file_info)

    dead_ends: list[tuple[str, list[str]]] = []
    for b in sorted(state_scoped):
        if b in ALLOWLIST:
            continue
        if writers.get(b) and not _has_reader(b):
            dead_ends.append((b, sorted(writers[b])))

    print(f"state-readers-check: {len(state_scoped)} state artifact(s) written by "
          f"non-test src; {len(ALLOWLIST)} allow-listed; {len(dead_ends)} dead-end(s).")
    if dead_ends:
        for b, wf in dead_ends:
            print(
                f"state-readers-check: DEAD-END artifact {b!r} — written by "
                f"{', '.join(wf)} but read by no non-test source module.",
                file=sys.stderr,
            )
        print(
            "Fix each: thread the value forward through an existing reader (SSoT), "
            "add the missing consumer, delete the unused write, or (if a real "
            "external reader exists) add it to ALLOWLIST with a justification.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
