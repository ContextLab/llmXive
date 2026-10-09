"""Resolve generated artifact references consistently for implementation and review."""

from __future__ import annotations

import re
from pathlib import Path

# --- Artifact-path detection (the deterministic evidence a task line references) ---
#
# Broadened well beyond the original code/data/figures/results/outputs roots so
# scaffolding / config / test tasks are judged from real files, not prose.
#: Directory-rooted artifact paths with a real dotted extension.
_ROOTED_PATH_RE = re.compile(
    r"(?<![\w./-])((?:projects/[\w.-]+|code|data|figures|results|outputs|src|tests?|scripts|config|configs|"
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
    r"(?<![\w./-])((?:projects/[\w.-]+|code|data|figures|results|outputs|src|tests?|"
    r"scripts|config|configs|notebooks|docs|assets|models|reports|paper|contracts|state|specs)"
    r"/(?:[\w.-]+/)*)(?![\w-]|\.\w)"
)


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
    if not path.resolve().is_relative_to(root):
        return None
    return path.resolve()
