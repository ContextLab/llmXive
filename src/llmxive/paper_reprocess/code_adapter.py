"""CPU-adaptation step for the code-included ingested-paper branch (spec 024).

An externally-ingested paper that ships code is vendored as a submodule and the
back-fill sets up the execution gate to RUN it (see
:mod:`llmxive.paper_reprocess.branch_code`). But that shipped code is almost
always GPU-heavy and/or large-scale and cannot run on the project's free CI
(2 CPU cores, ~7 GB RAM, NO GPU). The execution gate then has nothing real to
run and stalls.

This module is the PROACTIVE fix: ONE free-model LLM call (the ``code_adapter``
agent, prompt at ``agents/prompts/code_adapter.md``) reads the vendored repo and
emits a SIMPLIFIED, CPU-runnable adaptation under the project's ``code/`` dir
plus a ``quickstart.md`` whose ``python`` run-commands invoke it. The adaptation
writes real artifacts to ``data/``/``figures/`` so the execution gate can verify
a meaningful, scaled-down version of the paper's core result.

The single LLM call reuses the SAME backend/model/router the brainstorm /
flesh_out / planner agents use (resolved from ``agents/registry.yaml`` via
:mod:`llmxive.agents.registry`), so this step inherits the free-model guarantee
and the Dartmouth credit guard. The response is split with the SAME multi-file
splitter the planner uses (``speckit.plan_cmd._split_multi_file``) — no bespoke
parser.

ROBUST BY DESIGN: this is an OPTIONAL proactive improvement. Any failure (LLM
error, empty/garbled response, no ``code/`` files produced) is logged and yields
``[]`` — the caller leaves the existing external-pointing quickstart in place and
the execution fix-loop converges residual issues. :func:`adapt_code` NEVER raises.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Cap the total source context fed to the LLM so the prompt fits comfortably
# inside the reasoning model's input/output budget (the prompt also carries the
# paper summary + file tree). ~14K chars of source leaves ample room.
_MAX_SOURCE_CHARS = 14_000
# Per-file excerpt cap so one giant file cannot swallow the whole budget.
_MAX_PER_FILE_CHARS = 5_000
# How many extra (non-entry) .py files to include, largest-first.
_MAX_EXTRA_FILES = 6

# Skip dirs mirror branch_code._SKIP_DIRS (vendored deps / VCS / caches).
_SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", ".mypy_cache",
              ".pytest_cache", ".ipynb_checkpoints", "build", "dist", ".eggs"}

# We accept (write) only these output paths from the split response.
_QUICKSTART_NAME = "quickstart.md"


def adapt_code(
    pdir: Path,
    *,
    repo_root: Path,
    paper_summary: str,
    submodule_abs: Path,
    file_tree: str,
    entry_scripts: list[str],
) -> list[str]:
    """Produce a CPU-runnable adaptation of the vendored repo under ``pdir``.

    Reads the most-relevant source from ``submodule_abs`` (the entry scripts +
    the largest other ``.py`` files, truncated to a budget), asks the
    ``code_adapter`` agent to emit a simplified CPU adaptation, splits the
    response with the planner's multi-file splitter, and writes every ``code/**``
    file, ``quickstart.md``, and ``code/README.md`` under ``pdir`` (creating
    dirs). Paths that escape ``pdir`` (``..``/absolute) are IGNORED.

    Returns the list of written rel paths (relative to ``pdir``). On ANY failure
    — LLM error, empty/garbled response, or no ``code/`` files produced — logs a
    warning and returns ``[]`` (the caller keeps the external-pointing
    quickstart). NEVER raises.
    """
    try:
        excerpts = _collect_source_excerpts(submodule_abs, entry_scripts)
        response = _call_adapter(
            repo_root=repo_root,
            paper_summary=paper_summary,
            file_tree=file_tree,
            entry_scripts=entry_scripts,
            source_excerpts=excerpts,
        )
        files = _split_response(response)
        # Syntax-validate the produced scripts; an LLM syntax error makes the
        # adaptation un-runnable AND breaks requirements detection (PROJ-576).
        # Retry ONCE with the errors fed back; keep the parseable result.
        errs = _syntax_errors(files)
        if errs:
            logger.info("%s: code_adapter retrying after syntax error(s): %s",
                        pdir.name, "; ".join(errs.values())[:200])
            retry = _call_adapter(
                repo_root=repo_root, paper_summary=paper_summary,
                file_tree=file_tree, entry_scripts=entry_scripts,
                source_excerpts=excerpts,
                feedback="Syntax errors to fix:\n" + "\n".join(errs.values()),
            )
            retry_files = _split_response(retry)
            if retry_files and not _syntax_errors(retry_files):
                files = retry_files
        written = _write_adaptation(pdir, files)
    except Exception as exc:  # noqa: BLE001 — proactive step; never break back-fill
        logger.warning("%s: code_adapter failed (%s); keeping external quickstart",
                        pdir.name, exc)
        return []

    if not written:
        logger.warning("%s: code_adapter produced no usable files; keeping "
                        "external quickstart", pdir.name)
        return []
    # Declare the adapted code's third-party deps in code/requirements.txt so the
    # execution venv installs them on the FIRST run. The LLM is unreliable about
    # emitting requirements.txt (PROJ-577: produced it one run, omitted it the
    # next → ModuleNotFoundError in a fresh venv). Reuse the production self-heal's
    # STATIC import scan + import→pip mapping (SSoT) — failures=[] runs only the
    # scan, declaring the whole third-party stack in one pass.
    try:
        from llmxive.execution.stage import _declare_missing_imports

        _declare_missing_imports(pdir, [])
        req_rel = "code/requirements.txt"
        if (pdir / req_rel).is_file() and req_rel not in written:
            written.append(req_rel)
            written.sort()
    except Exception as exc:  # noqa: BLE001 — best-effort; the fix-loop still heals deps
        logger.warning("%s: code_adapter requirements generation failed (%s)",
                        pdir.name, exc)
    return written


# --------------------------------------------------------------------------- #
# Source collection (deterministic)
# --------------------------------------------------------------------------- #
def _collect_source_excerpts(
    submodule_abs: Path, entry_scripts: list[str]
) -> list[tuple[str, str]]:
    """Return ``[(relpath, truncated_source), ...]`` for the entry scripts plus
    the largest other ``.py`` files, capped at ``_MAX_SOURCE_CHARS`` total."""
    selected: list[str] = []
    seen: set[str] = set()

    # 1) Entry scripts first (the runnable surface the adaptation mirrors).
    for rel in entry_scripts:
        if rel not in seen and (submodule_abs / rel).is_file():
            selected.append(rel)
            seen.add(rel)

    # 2) The largest remaining .py files (most likely to hold the core logic).
    extras: list[tuple[int, str]] = []
    for path in submodule_abs.rglob("*.py"):
        rel = path.relative_to(submodule_abs)
        if any(part in _SKIP_DIRS for part in rel.parts):
            continue
        relstr = str(rel)
        if relstr in seen:
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        extras.append((size, relstr))
    extras.sort(reverse=True)
    for _size, relstr in extras[:_MAX_EXTRA_FILES]:
        selected.append(relstr)
        seen.add(relstr)

    out: list[tuple[str, str]] = []
    total = 0
    for relstr in selected:
        try:
            text = (submodule_abs / relstr).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if len(text) > _MAX_PER_FILE_CHARS:
            text = text[:_MAX_PER_FILE_CHARS].rstrip() + "\n# … (truncated)\n"
        if total + len(text) > _MAX_SOURCE_CHARS:
            remaining = _MAX_SOURCE_CHARS - total
            if remaining < 400:  # not enough room for a useful excerpt
                break
            text = text[:remaining].rstrip() + "\n# … (truncated)\n"
        out.append((relstr, text))
        total += len(text)
        if total >= _MAX_SOURCE_CHARS:
            break
    return out


# --------------------------------------------------------------------------- #
# The single LLM call (free model, shared router) — mirrors
# branch_nocode._propose_extension exactly.
# --------------------------------------------------------------------------- #
def _call_adapter(
    *,
    repo_root: Path,
    paper_summary: str,
    file_tree: str,
    entry_scripts: list[str],
    source_excerpts: list[tuple[str, str]],
    feedback: str = "",
) -> str:
    """ONE real LLM call: hand the paper + repo tree + key source to the
    ``code_adapter`` agent and return its raw multi-file response text."""
    from llmxive.agents import registry as registry_loader
    from llmxive.backends.base import ChatMessage
    from llmxive.backends.router import chat_with_fallback
    from llmxive.credentials import load_dartmouth_key

    # Resolve the Dartmouth key the SSoT way (never read os.environ directly);
    # populate the env the langchain client reads so the dartmouth backend works.
    key = load_dartmouth_key(prompt_if_missing=False)
    if key:
        import os

        os.environ.setdefault("DARTMOUTH_CHAT_API_KEY", key)

    # The agent registry + prompts are PLATFORM config (``agents/`` at the
    # llmXive root), NOT under the project's ``repo_root`` — resolve them from the
    # platform root (like branch_nocode) so this works in hermetic runs too, not
    # only when repo_root happens to equal the platform root.
    from llmxive.config import repo_root as _platform_root

    _plat = _platform_root()
    entry = registry_loader.get("code_adapter")
    system = (_plat / entry.prompt_path).read_text(encoding="utf-8")

    entry_block = "\n".join(f"- `{s}`" for s in entry_scripts[:15]) or "(none detected)"
    source_block = "\n\n".join(
        f"--- {rel} ---\n{text.rstrip()}" for rel, text in source_excerpts
    ) or "(no source excerpts available)"
    user = (
        "## PAPER\n\n"
        f"{paper_summary}\n\n"
        "## REPO TREE\n\n"
        f"```\n{file_tree}\n```\n\n"
        "## ENTRY SCRIPTS\n\n"
        f"{entry_block}\n\n"
        "## KEY SOURCE EXCERPTS\n\n"
        f"{source_block}\n"
    )
    if feedback:
        user += (
            "\n## FIX REQUIRED\n\nYour previous attempt had errors. Regenerate ALL "
            "files in the SAME multi-file format, with these fixed:\n\n"
            f"{feedback}\n"
        )

    response = chat_with_fallback(
        [ChatMessage(role="system", content=system), ChatMessage(role="user", content=user)],
        default_backend=entry.default_backend.value,
        fallback_backends=[b.value for b in entry.fallback_backends],
        model=entry.default_model,
        max_tokens=8192,
    )
    return (response.text or "").strip()


# --------------------------------------------------------------------------- #
# Split + write (deterministic, unit-testable without a network)
# --------------------------------------------------------------------------- #
def _split_response(response: str) -> dict[str, str]:
    """Split the LLM reply into ``{relpath: content}`` using the SAME multi-file
    splitter the planner uses (SSoT)."""
    if not response:
        return {}
    from llmxive.speckit.plan_cmd import _split_multi_file

    return _split_multi_file(response)


def _is_safe_rel(rel: str) -> bool:
    """True if ``rel`` is a project-relative path that does NOT escape ``pdir``
    (no absolute path, no ``..`` component)."""
    p = Path(rel)
    if p.is_absolute():
        return False
    return not any(part == ".." for part in p.parts)


def _is_accepted(rel: str) -> bool:
    """Accept only the adaptation outputs we write: any ``code/**`` file, the
    top-level ``quickstart.md``, or ``code/README.md`` (the latter is a ``code/``
    file, so covered by the prefix)."""
    norm = Path(rel).as_posix()
    return norm == _QUICKSTART_NAME or norm.startswith("code/")


def _syntax_errors(files: dict[str, str]) -> dict[str, str]:
    """Return ``{code/*.py path: error}`` for any produced script that does not
    parse. An LLM SyntaxError (PROJ-576: a dict written with ``[]``) makes the
    adaptation un-runnable AND breaks the import scan, so we retry the agent once
    with these fed back."""
    import ast

    errs: dict[str, str] = {}
    for rel, content in files.items():
        r = Path(rel).as_posix()
        if r.startswith("code/") and r.endswith(".py"):
            try:
                ast.parse(content)
            except SyntaxError as exc:
                errs[r] = f"{r}: line {exc.lineno}: {exc.msg}"
    return errs


def _normalize_quickstart_text(text: str) -> str | None:
    """Ensure the quickstart's python run-commands sit inside a ```bash fence the
    execution gate can parse. Returns the (possibly-rewritten) text, or ``None``
    if there are no runnable python commands at all (an unusable run-book)."""
    from llmxive.execution.analysis_runner import extract_run_commands

    if extract_run_commands(text):
        return text  # already has fenced, parseable python commands
    cmds = [
        ln.strip()
        for ln in text.splitlines()
        if ln.strip().startswith(("python ", "python3 "))
    ]
    if not cmds:
        return None
    return "# Quickstart\n\n```bash\n" + "\n".join(cmds) + "\n```\n"


def _write_adaptation(pdir: Path, files: dict[str, str]) -> list[str]:
    """Write each accepted, in-tree file under ``pdir``. Returns written rel
    paths. A response with no ``code/*.py`` file is rejected (returns ``[]``):
    a quickstart with nothing to run is not a usable adaptation."""
    accepted: dict[str, str] = {}
    for rel, content in files.items():
        rel = rel.strip()
        if not rel:
            continue
        if not _is_safe_rel(rel):
            logger.warning("%s: code_adapter ignoring out-of-tree path %r", pdir.name, rel)
            continue
        if not _is_accepted(rel):
            continue
        accepted[Path(rel).as_posix()] = content

    has_code_py = any(r.startswith("code/") and r.endswith(".py") for r in accepted)
    has_quickstart = _QUICKSTART_NAME in accepted
    if not (has_code_py and has_quickstart):
        return []
    # The LLM sometimes emits the run-book commands as bare lines instead of in a
    # ```bash fence, which the execution gate's ``extract_run_commands`` can't
    # parse (PROJ-577 v1: a real, runnable adaptation that never ran because of
    # this). Normalize so the python commands are always fenced; reject the
    # adaptation if there is nothing runnable.
    qs_norm = _normalize_quickstart_text(accepted[_QUICKSTART_NAME])
    if qs_norm is None:
        logger.warning(
            "%s: code_adapter quickstart has no runnable python commands", pdir.name
        )
        return []
    accepted[_QUICKSTART_NAME] = qs_norm

    written: list[str] = []
    for rel, content in accepted.items():
        target = pdir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        body = content if content.endswith("\n") else content + "\n"
        target.write_text(body, encoding="utf-8")
        written.append(rel)
    return sorted(written)


__all__ = ["adapt_code"]
