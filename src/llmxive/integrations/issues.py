"""GitHub issue lifecycle hooks for the agentic pipeline.

Two responsibilities:

  1. close_issue_for_project(project) -> None
     Called when a project transitions to POSTED. Closes the linked
     GitHub issue (if any) with a completion comment that links to the
     posted PDF + the project YAML.

  2. comment_on_artifact_added(project, artifact_kind, path) -> None
     Called when a new artifact is committed. Posts a short comment to
     the linked GitHub issue announcing the new artifact + a blob URL.

The link between a project and its GitHub issue is stored in the idea
file's front-matter as `github_issue: <url>`. If no issue is linked,
all hooks are no-ops.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import yaml

from llmxive.types import Project

_BLOB_BASE = "https://github.com/ContextLab/llmXive/blob/main"


def _issue_number_for(repo: Path, project: Project) -> int | None:
    """Return the GitHub issue number from the idea file's front-matter.

    Looks for `github_issue: https://github.com/ContextLab/llmXive/issues/<N>`
    or `github_issue: <N>` in the YAML front-matter of any
    projects/<id>/idea/*.md file.
    """
    pdir = repo / "projects" / project.id
    idea_dir = pdir / "idea"
    if not idea_dir.is_dir():
        return None
    for md in idea_dir.glob("*.md"):
        text = md.read_text(encoding="utf-8", errors="replace")
        if not text.startswith("---"):
            continue
        try:
            end = text.index("---", 3)
            front = yaml.safe_load(text[3:end]) or {}
        except (ValueError, yaml.YAMLError):
            continue
        v = front.get("github_issue")
        if v is None:
            continue
        if isinstance(v, int):
            return int(v)
        m = re.search(r"/issues/(\d+)", str(v)) or re.match(r"^(\d+)$", str(v).strip())
        if m:
            return int(m.group(1))
    return None


def _gh_available() -> bool:
    return shutil.which("gh") is not None


def _gh(*args: str) -> tuple[int, str, str]:
    proc = subprocess.run(["gh", *args], capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def close_issue_for_project(repo: Path, project: Project, *, dry_run: bool = False) -> int | None:
    """Close the linked issue with a completion comment. Returns issue number, or None."""
    issue_num = _issue_number_for(repo, project)
    if issue_num is None or not _gh_available():
        return None
    pdir = project.id
    pdf_path = next(iter((repo / "projects" / pdir / "paper" / "pdf").glob("*.pdf")), None) if (repo / "projects" / pdir / "paper" / "pdf").exists() else None
    yaml_url = f"{_BLOB_BASE}/state/projects/{pdir}.yaml"
    pdf_url = f"{_BLOB_BASE}/{pdf_path.relative_to(repo).as_posix()}" if pdf_path else None
    body_lines = [
        "## ✅ Posted",
        "",
        f"Project **{project.id}** has completed both review gates and is now posted.",
        "",
        f"- Project state: [{pdir}.yaml]({yaml_url})",
    ]
    if pdf_url:
        body_lines.append(f"- Final paper: [{pdf_path.name}]({pdf_url})")
    body_lines += [
        "",
        "Full artifact log: <https://context-lab.com/llmXive/#paper>",
    ]
    body = "\n".join(body_lines)
    if dry_run:
        print(f"[dry] would close issue #{issue_num} with body:\n{body}")
        return issue_num
    _gh("issue", "comment", str(issue_num), "--body", body)
    _gh("issue", "close", str(issue_num), "--reason", "completed")
    return issue_num


def comment_on_artifact_added(
    repo: Path, project: Project, artifact_kind: str, path: str, *, dry_run: bool = False
) -> int | None:
    """Post an artifact-added comment to the linked issue. Returns issue number, or None."""
    issue_num = _issue_number_for(repo, project)
    if issue_num is None or not _gh_available():
        return None
    blob = f"{_BLOB_BASE}/{path.lstrip('/')}"
    body = (
        f"📦 **{artifact_kind}** added to **{project.id}** (now at stage `{project.current_stage.value}`)\n\n"
        f"- [{path}]({blob})\n\n"
        f"Stage history: <https://context-lab.com/llmXive/>"
    )
    if dry_run:
        print(f"[dry] would comment on issue #{issue_num}:\n{body}")
        return issue_num
    _gh("issue", "comment", str(issue_num), "--body", body)
    return issue_num


__all__ = [
    "close_issue_for_project",
    "comment_on_artifact_added",
]
