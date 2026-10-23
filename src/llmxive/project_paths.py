"""Resolve generated artifact references consistently for implementation and review."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

# --- Artifact-path detection (the deterministic evidence a task line references) ---
#
# Broadened well beyond the original code/data/figures/results/outputs roots so
# scaffolding / config / test tasks are judged from real files, not prose.
#: Directory-rooted artifact paths with a real dotted extension.
_ROOTED_PATH_RE = re.compile(
    r"(?<![\w./-])((?:projects/[\w.-]+|code|data|figures|results|outputs?|src|tests?|scripts|config|configs|"
    r"notebooks|docs|assets|models|reports|paper|contracts|state|specs)/[\w./-]+\.\w+)"
)
#: Bare (optionally path-prefixed) build/config filenames a task may reference.
_CONFIG_FILE_RE = re.compile(
    r"\b((?:[\w./-]+/)?(?:pyproject\.toml|setup\.cfg|setup\.py|"
    r"requirements(?:-[\w.]+)?\.txt|environment\.ya?ml|tox\.ini|noxfile\.py|"
    r"conftest\.py|pytest\.ini|mkdocs\.ya?ml|Makefile|Dockerfile))\b"
)
#: Generic config-extension files (…toml/…cfg/…yaml/…ini) referenced under the project.
_CONFIG_EXT_RE = re.compile(r"(?<![\w./-])((?:[\w./-]+/)?[\w.-]+\.(?:toml|cfg|ya?ml|ini))\b")
_SPEC_DOC_RE = re.compile(r"\b((?:specs/[\w./-]+/)?(?:plan|spec|tasks|research|quickstart|data-model)\.md)\b")
_DIRECTORY_PATH_RE = re.compile(
    r"(?<![\w./-])((?:projects/[\w.-]+|code|data|figures|results|outputs?|src|tests?|"
    r"scripts|config|configs|notebooks|docs|assets|models|reports|paper|contracts|state|specs)"
    r"/(?:[\w.-]+/)*)(?![\w-]|\.\w)"
)


#: A rooted artifact path written as a PATTERN: ``data/counts_N{N}_p{p}.csv``,
#: ``figures/<model>_loss.png``, ``data/raw/*.json``. `_ROOTED_PATH_RE` cannot
#: match these (its path class has no braces), so a task that produces a family
#: of files named none of them as far as the evidence collector could tell.
_PATTERN_PATH_RE = re.compile(
    r"(?<![\w./-])((?:code|data|figures|results|outputs?|src|tests?|scripts|docs|models|reports|"
    r"paper|contracts)/[\w./-]*(?:\{[^{}\s`]{1,32}\}|<[\w-]{1,32}>|\*)[\w./{}<>*-]*\.\w+)"
)
_PLACEHOLDER_RE = re.compile(r"\{[^{}]*\}|<[\w-]+>|\*+")


def declared_patterns(task_text: str) -> list[tuple[str, str]]:
    """``(pattern as written, glob)`` for every templated artifact path in a task.

    Measured 2026-10-11: 211 of 734 project task lists name outputs this way.
    Each placeholder becomes ``*``; the glob never crosses a directory unless
    the task wrote a ``/`` there itself.
    """
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for m in _PATTERN_PATH_RE.finditer(task_text):
        written = m.group(1)
        if written in seen or ".." in Path(written).parts:
            continue
        seen.add(written)
        out.append((written, _PLACEHOLDER_RE.sub("*", written)))
    return out


def resolve_pattern(project_dir: Path, glob: str, *, limit: int = 500) -> list[Path]:
    """Files inside the project matching ``glob``, sorted. Never leaves the project.

    A pattern that names a source/test path is also tried under ``code/``, the
    same shorthand :func:`resolve_project_path` honours for literal paths.
    """
    root = project_dir.resolve()
    bases = [root]
    if Path(glob).parts[:1] in (("src",), ("test",), ("tests",), ("scripts",)):
        bases.append(root / "code")
    for base in bases:
        found = sorted(
            p for p in base.glob(glob)
            if p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(root)
        )
        if found:
            return found[:limit]
    return []


def declared_paths(task_text: str) -> list[str]:
    """Every artifact path a task line references (rooted paths + build/config
    files), de-duplicated in first-seen order."""
    out: list[str] = []
    seen: set[str] = set()
    matches = sorted(
        (m for rx in (_ROOTED_PATH_RE, _CONFIG_FILE_RE, _CONFIG_EXT_RE, _SPEC_DOC_RE,
                      _DIRECTORY_PATH_RE)
         for m in rx.finditer(task_text)),
        key=lambda m: (m.start(1), -m.end(1)),
    )
    end = -1
    for m in matches:
        # A repo-rooted spec path must not also consume an evidence slot as
        # the bare basename matched by the spec-document pattern.
        if m.start(1) < end:
            continue
        end = m.end(1)
        rel = m.group(1)
        if rel not in seen:
            seen.add(rel)
            out.append(rel)
    return out


_NAMED_FILE_RE = re.compile(
    r"`((?:[\w.-]+/)*[\w.-]+\.(?:md|py|sh|txt|csv|tsv|json|png|pdf|svg|tex|bib|ipynb))`")


def declared_existing_files(project_dir: Path, task_text: str) -> list[str]:
    """Backticked file paths in a task that ARE files in the project.

    :func:`declared_paths` needs a directory name from its list or a config
    filename, so "add a `README.md` entry at the project root" and a table
    written to `tables/extra/tv_long.md` declared nothing. A backticked name is
    ambiguous text (`scipy.stats`, `json.dump`, a path in another project), so
    this never reports one as missing: only a real, regular, in-project file
    counts, and only when :func:`declared_paths` has not already found it.
    """
    known = set(declared_paths(task_text))
    root = project_dir.resolve()
    out: list[str] = []
    for match in _NAMED_FILE_RE.finditer(task_text):
        name = match.group(1)
        if name in known or name in out or ".." in Path(name).parts:
            continue
        # No component may be a link: the file must be the project's own.
        steps = [project_dir.joinpath(*Path(name).parts[:i + 1]) for i in range(len(Path(name).parts))]
        if any(step.is_symlink() for step in steps):
            continue
        if steps[-1].is_file() and steps[-1].resolve().is_relative_to(root):
            out.append(name)
    return out


def resolve_project_path(project_dir: Path, rel: str) -> Path | None:
    """Resolve declared paths within this project, including its code layout.

    Generated tasks use both repo-rooted paths and paths relative to ``code/``.
    An explicit repo-rooted path is exact; shorthand prefers the project root
    and only falls back to code/ for source, test, and build/config paths.
    """
    relative = Path(rel)
    if relative.is_absolute() or ".." in relative.parts:
        return None
    explicit = relative.parts[:1] == ("projects",)
    if explicit:
        if len(relative.parts) < 2 or relative.parts[1] != project_dir.name:
            return None
        relative = Path(*relative.parts[2:])
    root = project_dir.resolve()
    path = root / relative
    if not path.resolve().is_relative_to(root):
        return None
    if (not path.exists() and len(relative.parts) >= 3 and relative.parts[0] == "specs"
            and not (root / "specs" / relative.parts[1] / "spec.md").is_file()):
        # The implementer canonicalizes invented feature slugs on write. Read
        # the same authoritative feature, without aliasing an existing feature.
        # A scaffold-only directory is not a feature: setup tasks often create
        # an invented slug's contracts/ before artifact writes canonicalize it.
        from llmxive.state.project import feature_dir_for
        feature = feature_dir_for(project_dir, track="research")
        if feature is not None:
            path = feature.joinpath(*relative.parts[2:])
    elif not explicit and not path.exists() and relative.parts[:1] == ("contracts",):
        # Spec Kit contract paths are relative to the active feature. Never
        # borrow a contract for an explicit repo-rooted or existing root path.
        from llmxive.state.project import feature_dir_for
        feature = feature_dir_for(project_dir, track="research")
        if feature is not None:
            path = feature / relative
    elif not explicit and not path.exists() and "/" not in rel and _SPEC_DOC_RE.fullmatch(rel):
        from llmxive.state.project import feature_dir_for
        feature = feature_dir_for(project_dir, track="research")
        if feature is not None:
            path = feature / rel
    elif not explicit and not path.exists() and (
        relative.parts[:1] in (("src",), ("test",), ("tests",), ("scripts",))
        or (len(relative.parts) == 1 and (
            _CONFIG_FILE_RE.fullmatch(rel) or _CONFIG_EXT_RE.fullmatch(rel)
        ))
    ):
        path = root / "code" / relative
        if not path.exists() and len(relative.parts) == 1:
            # A task that names a contract by its bare file name
            # (`summary.schema.yaml`) means the active feature's contract: the
            # planner writes contracts nowhere else. Batch 4 (2026-10-12): the
            # verifier was told both schemas were MISSING four times, the task
            # went unverifiable, and the implementer wrote a second copy that
            # then disagreed with the first.
            from llmxive.state.project import feature_dir_for
            feature = feature_dir_for(project_dir, track="research")
            if feature is not None and (feature / "contracts" / relative).is_file():
                path = feature / "contracts" / relative
    if not path.resolve().is_relative_to(root):
        return None
    return path.resolve()


def casefold_write_conflict(project_dir: Path, target: Path) -> Path | None:
    """Reject a new filename spelling that aliases an existing project path.

    Check each existing path component before writing, on case-sensitive hosts
    too. Existing exact spellings remain editable; historical collisions require
    their separate provenance audit rather than an arbitrary winning variant.
    """
    current = project_dir
    for part in target.relative_to(project_dir).parts:
        if part == "..":
            current = current.parent
            continue
        if current.is_dir():
            entries = list(current.iterdir())
            exact = next((entry for entry in entries if entry.name == part), None)
            if exact is None:
                folded = unicodedata.normalize("NFD", part).casefold()
                conflict = next((entry for entry in entries
                                 if unicodedata.normalize("NFD", entry.name).casefold() == folded), None)
                if conflict is not None:
                    return conflict
        current = current / part
    return None
