"""Paths a PROJECT may not own — deterministic containment, no model call.

A project owns ``projects/<id>/`` and what the lifecycle puts there: ``idea/``,
``specs/``, ``code/``, ``data/``, ``figures/``, ``paper/``, ``reviews/``,
``.specify/``. It does NOT own the platform's directories, and a directory with
a platform name INSIDE a project is a SHADOW of canonical state that something
will later read as if it were the real thing.

Observed (PROJ-9999 totient canary, 2026-10-10, step 15). A generated task,
``code/run_t004_finalize.py``, was authored to record artifact hashes "into
state/projects/PROJ-9999-totient-canary.yaml". It ran with the project as its
working directory, so that resolved to
``projects/PROJ-9999-totient-canary/state/projects/PROJ-9999-totient-canary.yaml``
— a shadow. Canonical ``state/projects/<id>.yaml`` still read
``artifact_hashes: {}``. Eight minutes later the JSON was regenerated, so the
shadow's recorded hash went stale, and the task verifier — which resolves every
path named in a task relative to the project directory — read the shadow,
compared its stale hash to the live file, rejected the task, exhausted the
round cap and kicked the whole project back to ``clarified``. Two runs in a row
ended that way.

``#1553`` already refuses control-file rewrites in artifacts the implementer
writes DIRECTLY; it says so explicitly: it "does not provide OS isolation
against arbitrary executed scripts". This is that uncovered path — a shadow
written at runtime by the project's own script — so the containment is enforced
where the shadow is READ and where a run's feedback is written, not only where
artifacts are declared.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath

#: Top-level names a project genuinely cannot own. Deliberately SHORT.
#:
#: ``src``, ``agents``, ``eval``, ``tests``, ``scripts`` and ``docs`` are all
#: excluded: a research project legitimately has a `code/src/` package, an
#: `agents/` module for a multi-agent simulation, its own `eval/` scripts, and
#: so on — and a task names such a path relative to `code/`, so the verifier
#: resolves `src/utils/sieve.py` against both the project root and `code/`.
#: Listing them produced a false positive that broke the already-fixed
#: false-missing-file rejection (tests/unit/test_task_verifier.py
#: ::test_verification_reads_repo_rooted_and_code_relative_files).
#:
#: What remains is the pair no analysis has any business writing: canonical
#: machine state, and workflow definitions.
PLATFORM_OWNED_ROOTS: tuple[str, ...] = (
    "state",
    ".github",
)


def platform_shadow(rel: str) -> str | None:
    """The platform-owned root that ``rel`` shadows, or ``None``.

    ``rel`` is a project-relative path as a task or run-book names it. An
    absolute path, or one escaping the project with ``..``, is reported against
    the root it starts with so a caller never silently accepts it.
    """
    text = str(rel).strip().replace("\\", "/")
    if not text:
        return None
    while text.startswith("./"):
        text = text[2:]
    pure = PurePosixPath(text)
    parts = tuple(p for p in pure.parts if p not in (".", "/"))
    if not parts:
        return None
    for owned in PLATFORM_OWNED_ROOTS:
        owned_parts = tuple(PurePosixPath(owned).parts)
        if parts[: len(owned_parts)] == owned_parts:
            return owned
    return None


def is_project_dir(project_dir: Path) -> bool:
    """Whether ``project_dir`` is a ``projects/<id>`` directory.

    The containment rule applies to a PROJECT. The same verifier also runs over
    the platform's own Spec Kit features, where a task naming ``src/llmxive/...``
    is entirely legitimate, so the rule must not fire there.
    """
    try:
        return Path(project_dir).parent.name == "projects"
    except (OSError, ValueError):  # pragma: no cover - defensive
        return False


def shadow_dirs(project_dir: Path) -> list[str]:
    """Platform-owned directories that exist INSIDE ``project_dir``, sorted.

    What a finished run is checked against: a script that wrote canonical state
    project-locally leaves the directory behind even when no task declared it.
    """
    root = Path(project_dir)
    found: list[str] = []
    for owned in PLATFORM_OWNED_ROOTS:
        if (root / owned).exists():
            found.append(owned)
    return sorted(found)


def shadow_feedback(project_dir: Path) -> str:
    """Feedback naming each shadow found, or ``""`` when there is none."""
    found = shadow_dirs(project_dir)
    if not found:
        return ""
    lines = [
        "## Platform-owned paths written inside the project",
        "",
        "A script in this project created "
        + ", ".join(f"`{name}/`" for name in found)
        + " inside the project directory. Those names belong to the platform, "
        "and a copy of them here is a SHADOW: the verifier resolves the paths a "
        "task names relative to this project, so it reads the shadow instead of "
        "canonical state and rejects work on the strength of a stale record.",
        "",
        "Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do "
        "not record artifact hashes, run state or project status yourself — the "
        "platform owns `state/` and derives hashes at verification time. Delete "
        "the directories listed above and drop whatever step created them.",
    ]
    return "\n".join(lines)


__all__ = [
    "PLATFORM_OWNED_ROOTS",
    "is_project_dir",
    "platform_shadow",
    "shadow_dirs",
    "shadow_feedback",
]


def project_dir_of(path: str | Path) -> Path | None:
    """The ``projects/<id>`` directory a path lies in, read from the path alone."""
    parts = Path(path).parts
    for index in range(len(parts) - 2, -1, -1):
        if parts[index] == "projects":
            return Path(*parts[: index + 2])
    return None


def platform_path_tasks(text: str) -> list[tuple[str, str, str]]:
    """``(task id, path, platform root)`` for each unfinished task naming a path
    the platform owns."""
    from llmxive.project_paths import declared_paths
    from llmxive.speckit.task_lines import TASK_LINE_RE, mask_fenced_code, task_continuation

    lines = mask_fenced_code(text).split("\n")
    found = []
    for index, line in enumerate(lines):
        task = TASK_LINE_RE.fullmatch(line)
        if not task or task.group("status") in "Xx":
            continue
        for path in declared_paths(line + task_continuation(lines, index)):
            owned = platform_shadow(path)
            if owned:
                found.append((task.group("id"), path, owned))
    return found


def refuse_platform_path_tasks(text: str, project_dir: Path | None) -> None:
    """Raise ``TaskFormatError`` for a project task list that writes a
    platform-owned path.

    The task verifier rejects every attempt at such a task whatever was
    produced, so once it is in the list no amount of implementation finishes it
    (batch 3, 2026-10-11: one task asking for ``.github/workflows/ci.yml`` took
    22 verifier rounds and 39 implementer replies before the whole project was
    re-planned). Refusing the list where it is written sends the reason to the
    tasker instead. Does nothing outside a ``projects/<id>`` directory.
    """
    from llmxive.speckit.task_lines import TaskFormatError

    if project_dir is None or not is_project_dir(project_dir):
        return
    offending = platform_path_tasks(text)
    if offending:
        raise TaskFormatError(
            "Task(s) write a path the platform owns: "
            + "; ".join(f"{tid} `{path}` (inside `{owned}/`)" for tid, path, owned in offending[:8])
            + ". A project can only write inside its own directories (code/, src/, "
            "scripts/, tests/, data/, figures/, results/, paper/); it cannot add "
            "workflow files or platform state. Rewrite each of these tasks to produce "
            "a project-owned file instead (for a CI step, a script under `scripts/` or "
            "`code/` that runs the same commands), and make the plan and quickstart "
            "name that file."
        )
