"""Project-owned revision artifacts, with read compatibility for older checkouts."""
from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path


def project_control_dir(repo: Path, project_id: str) -> Path:
    if not re.fullmatch(r"PROJ-[A-Za-z0-9][A-Za-z0-9_-]*", project_id):
        raise ValueError(f"invalid project namespace: {project_id!r}")
    root = repo / "projects" / project_id
    path = root / ".specify"
    expected = repo.resolve() / "projects" / project_id
    if not path.resolve().is_relative_to(expected):
        raise ValueError("project control directory escapes its project")
    return path


def revision_base(repo: Path, project_id: str) -> Path:
    base = project_control_dir(repo, project_id) / "auto-revisions"
    if not base.resolve().is_relative_to(project_control_dir(repo, project_id).resolve()):
        raise ValueError("revision directory escapes its project")
    return base


def legacy_revision_base(repo: Path, project_id: str) -> Path:
    project_control_dir(repo, project_id)  # validate namespace, including traversal
    base = repo / "specs" / "auto-revisions" / project_id
    expected = repo.resolve() / "specs" / "auto-revisions" / project_id
    if not base.resolve().is_relative_to(expected):
        raise ValueError("legacy revision directory escapes its namespace")
    return base


def revision_bases(repo: Path, project_id: str) -> list[Path]:
    """Canonical first; legacy rounds remain readable until an explicit reset."""
    base = revision_base(repo, project_id)
    bases = [base]
    if not (base / ".legacy-retired").exists():
        bases.append(legacy_revision_base(repo, project_id))
    return bases


def round_numbers(repo: Path, project_id: str) -> list[int]:
    return sorted({
        int(match.group(1))
        for base in revision_bases(repo, project_id) if base.is_dir()
        for path in base.iterdir()
        if path.is_dir() and (match := re.fullmatch(r"round-(\d+)", path.name))
    })


def revision_round(repo: Path, project_id: str, number: int) -> Path:
    if number < 1:
        raise ValueError("revision rounds are one-indexed")
    base = revision_base(repo, project_id)
    path = base / f"round-{number}"
    if not path.resolve().is_relative_to(base.resolve()):
        raise ValueError("revision round escapes its project")
    return path


def prepare_revision_round(repo: Path, project_id: str, number: int) -> Path:
    """Keep legacy retry inputs beside a newly project-local implementer log.

    A log alone must not shadow the old directory's tasks on the next retry.
    Preserve existing canonical edits; copy only missing work-spec documents.
    """
    target = revision_round(repo, project_id, number)
    if (target.parent / ".legacy-retired").exists():
        return target
    legacy_base = legacy_revision_base(repo, project_id)
    legacy = legacy_base / f"round-{number}"
    if not legacy.exists():
        return target
    if (legacy.is_symlink() or not legacy.resolve().is_relative_to(legacy_base.resolve())
            or any(p.is_symlink() for p in legacy.rglob("*"))):
        raise ValueError(f"unsafe legacy work-spec source: {legacy}")
    names = ("spec.md", "plan.md", "tasks.md", "analyze-report.md", "result.yaml")
    for name in names:
        if (target / name).is_symlink():
            raise ValueError(f"symlink in canonical work spec: {target / name}")
    copies = [(legacy / name, target / name) for name in names
              if (legacy / name).is_file() and not (target / name).exists()]
    if copies:
        target.mkdir(parents=True, exist_ok=True)
        for source, destination in copies:
            shutil.copy2(source, destination, follow_symlinks=False)
    return target


def resolve_revision_path(repo: Path, project_id: str, relative: str) -> Path:
    """Resolve a historical pointer without rewriting the original provenance."""
    path = Path(relative)
    legacy = Path("specs") / "auto-revisions" / project_id
    canonical = revision_base(repo, project_id)
    if path.is_relative_to(legacy):
        suffix = path.relative_to(legacy)
        replacement = canonical / suffix
        if replacement.exists() or (canonical / ".legacy-retired").exists():
            path = replacement
        else:
            path = repo / path
    else:
        path = repo / path
    allowed = [canonical, legacy_revision_base(repo, project_id)]
    if not any(path.resolve().is_relative_to(base.resolve()) for base in allowed):
        raise ValueError(f"revision pointer escapes {project_id}: {relative!r}")
    return path


def archive_revision_cycle(repo: Path, project_id: str) -> Path:
    """Reset the bounded round budget, preserving the old cycle inside the project.

    Legacy directories are copied, never deleted by a research run. A marker
    prevents their old round numbers from consuming the new cycle's budget.
    """
    control = project_control_dir(repo, project_id)
    archives = control / "revision-archives"
    if not archives.resolve().is_relative_to(control.resolve()):
        raise ValueError("revision archive directory escapes its project")
    canonical = revision_base(repo, project_id)
    legacy = legacy_revision_base(repo, project_id)
    use_legacy = legacy.is_dir() and not (canonical / ".legacy-retired").exists()
    sources = [canonical] + ([legacy] if use_legacy else [])
    history = repo / "projects" / project_id / "paper" / "revision_history.yaml"
    counter = repo / "state" / f"{project_id}.implementer.yaml"
    # Validate every source BEFORE moving any of them. In particular, copytree
    # must never follow a historical symlink and import unrelated file bytes.
    for source in sources:
        if source.is_symlink() or (source.is_dir() and any(p.is_symlink() for p in source.rglob("*"))):
            raise ValueError(f"symlink in revision archive source: {source}")
    for path, boundary in (
        (history, repo.resolve() / "projects" / project_id),
        (counter, repo.resolve() / "state"),
    ):
        if path.is_symlink() or not path.resolve().is_relative_to(boundary):
            raise ValueError(f"revision history source escapes its boundary: {path}")
    archives.mkdir(parents=True, exist_ok=True)
    archive = Path(tempfile.mkdtemp(prefix="cycle-", dir=archives))
    if use_legacy:
        shutil.copytree(legacy, archive / "legacy-auto-revisions", symlinks=True)
    if canonical.is_dir():
        canonical.rename(archive / "auto-revisions")
    for path in (history, counter):
        if path.is_file():
            path.rename(archive / path.name)
    canonical.mkdir(parents=True, exist_ok=True)
    (canonical / ".legacy-retired").write_text(
        f"Prior cycle preserved at {archive.relative_to(repo)}\n", encoding="utf-8"
    )
    return archive
