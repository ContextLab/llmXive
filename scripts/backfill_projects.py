"""Backfill state/projects/ from projects/ dirs and open GitHub issues.

Run from repo root:
    python scripts/backfill_projects.py [--dry-run]

For each projects/PROJ-*/ directory missing a state/projects/<id>.yaml:
    create a Project record at stage=brainstormed with the dir's idea
    file as the title hint.

For each open GitHub issue labeled 'idea' that doesn't already correspond
to a project on disk:
    allocate a new PROJ-### id, create state/projects/<id>.yaml +
    projects/<id>/idea/<slug>.md with the cleaned issue body.

Cleans up noisy issue titles ('Certainly! Here is...' etc.) by extracting
the first plausible title line from the body.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from llmxive.state import project as project_store  # noqa: E402
from llmxive.types import Project, Stage  # noqa: E402

NOISY_PREFIXES = (
    "Certainly!", "Sure!", "Here is", "Here's", "Title:",
    "Research Idea:", "Idea:", "Project:", "**",
)


def clean_title(raw: str, body: str = "") -> str:
    """Strip leading filler tokens, take first reasonable line, cap at 80 chars."""
    t = (raw or "").strip()
    # Drop leading conversational fluff.
    for _ in range(3):
        for prefix in NOISY_PREFIXES:
            if t.startswith(prefix):
                t = t[len(prefix):].strip(" :*\"'")
        if t and not any(t.startswith(p) for p in NOISY_PREFIXES):
            break
    # Strip surrounding quotes / asterisks.
    t = re.sub(r'^[\*"\']+|[\*"\']+$', '', t).strip()
    # If still suspicious, look in body.
    if not t or len(t) < 8 or t.endswith("..."):
        # Try first H1 in body, then first non-empty line.
        if body:
            for line in body.splitlines():
                line = line.strip()
                if line.startswith("# "):
                    cand = line[2:].strip()
                    if 8 <= len(cand) <= 200:
                        t = cand
                        break
            else:
                for line in body.splitlines():
                    line = line.strip(" *_-")
                    if 8 <= len(line) <= 200 and not line.startswith("```"):
                        t = line
                        break
    # Truncate to ≤ 80 chars at a word boundary.
    if len(t) > 80:
        t = t[:80].rsplit(" ", 1)[0]
    return t.strip() or "Untitled idea"


def slug_from_title(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s[:40] or "idea"


def next_id(existing: set[str], slug: str, *, start: int = 1) -> str:
    """Allocate the next free PROJ-NNN-<slug>.

    Picks the lowest unused integer N (across ALL existing slugs) so that
    every project gets a unique numeric prefix.
    """
    used_nums: set[int] = set()
    for pid in existing:
        m = re.match(r"^PROJ-(\d+)-", pid)
        if m:
            used_nums.add(int(m.group(1)))
    n = start
    while True:
        if n not in used_nums:
            pid = f"PROJ-{n:03d}-{slug}"
            return pid
        n += 1


def guess_field(title: str, body: str) -> str:
    blob = (title + " " + body).lower()
    keywords = {
        "biology": ["gene", "protein", "cell", "neuron", "rna", "dna", "biolog"],
        "chemistry": ["catalyst", "molecul", "reaction", "chemis", "synthes", "solvent"],
        "physics": ["quantum", "phonon", "atomic", "physic", "particle"],
        "computer science": ["algorithm", "transformer", "neural network", "llm", "compil", "operating sys"],
        "materials science": ["material", "alloy", "crystal", "phase", "lattice"],
        "neuroscience": ["brain", "cortex", "hippocamp", "neur", "memory"],
        "psychology": ["behav", "cognit", "psycholog", "decision-mak"],
        "statistics": ["bayes", "regress", "predict", "statistic", "infer"],
        "energy systems": ["solar", "battery", "energy", "grid", "wind"],
        "robotics": ["robot", "autonomous", "manipulat", "navigation"],
    }
    for field, kws in keywords.items():
        if any(kw in blob for kw in kws):
            return field
    return "general"


def write_idea_md(repo: Path, pid: str, slug: str, title: str, field: str,
                   body: str, github_issue_url: str | None) -> Path:
    idea_dir = repo / "projects" / pid / "idea"
    idea_dir.mkdir(parents=True, exist_ok=True)
    p = idea_dir / f"{slug}.md"
    front = [
        "---",
        f"field: {field}",
        f"keywords: [{field}]",
    ]
    if github_issue_url:
        front.append(f"github_issue: {github_issue_url}")
    front.append("---")
    content = "\n".join(front) + f"\n\n# {title}\n\n"
    if body:
        content += body.strip() + "\n"
    p.write_text(content, encoding="utf-8")
    return p


def project_for_dir(repo: Path, pid: str, *, dry: bool, now: datetime) -> bool:
    """Ensure state/projects/<pid>.yaml exists for a projects/<pid>/ dir."""
    state_path = repo / "state" / "projects" / f"{pid}.yaml"
    if state_path.exists():
        return False
    pdir = repo / "projects" / pid
    # Find an idea file; if none, write a stub from dir name.
    idea_md = next(iter((pdir / "idea").glob("*.md")), None) if (pdir / "idea").exists() else None
    if idea_md is None:
        # Some legacy dirs have no idea/; synthesize from dir name.
        title = pid.split("-", 2)[-1].replace("-", " ").title()
        slug = slug_from_title(title)
        write_idea_md(repo, pid, slug, title, "general", "", None)
    else:
        text = idea_md.read_text(encoding="utf-8", errors="replace")
        # Pull title from first H1 if present.
        m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        title = m.group(1).strip() if m else pid.split("-", 2)[-1].replace("-", " ").title()
    title = clean_title(title)
    field = guess_field(title, idea_md.read_text(errors="replace") if idea_md else "")
    project = Project(
        id=pid,
        title=title,
        field=field,
        current_stage=Stage.BRAINSTORMED,
        points_research={},
        points_paper={},
        created_at=now,
        updated_at=now,
        artifact_hashes={},
    )
    if dry:
        print(f"[dry] would create state/projects/{pid}.yaml ({title!r})")
    else:
        project_store.save(project, repo_root=repo)
        print(f"[backfill-dir] {pid} ({title!r})")
    return True


_FIELD_RE = re.compile(r"\*\*Field\*\*:\s*(.+)")
_TITLE_RES = [
    re.compile(r"\*\*Research Idea:?\*\*[:\s]*\"?([^\"\n]+?)\"?\s*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"\*\*Title\*\*:?[:\s]*\"?([^\"\n]+?)\"?\s*$", re.MULTILINE | re.IGNORECASE),
    # Old llmXive automation often wrote `**Description**: Title: "Foo"`
    # or `**Description**: Research Idea: Foo`.
    re.compile(r"\bTitle:\s*\"([^\"\n]+)\"", re.IGNORECASE),
    re.compile(r"\bTitle:\s*([^\n]+)", re.IGNORECASE),
    re.compile(r"\bResearch Idea:\s*([^\n]+)", re.IGNORECASE),
]
_DESC_RE = re.compile(
    r"\*\*Description\*\*:\s*(.+?)(?=\n\*\*[A-Z]|\n---|\Z)",
    re.IGNORECASE | re.DOTALL,
)


def _parse_legacy_metadata(body: str) -> dict:
    """Extract structured fields from llmXive-automation idea bodies."""
    out: dict[str, str] = {}
    fm = _FIELD_RE.search(body or "")
    if fm:
        out["field"] = fm.group(1).strip().rstrip(".").lower()
    for rx in _TITLE_RES:
        m = rx.search(body or "")
        if m:
            cand = m.group(1).strip(' *"\'')
            if 8 <= len(cand) <= 200:
                out["title"] = cand
                break
    dm = _DESC_RE.search(body or "")
    if dm:
        desc = dm.group(1).strip()
        for prefix in ("Certainly!", "Sure!", "Here is", "Here's"):
            if desc.startswith(prefix):
                desc = desc[len(prefix):].lstrip(" ,:.!\n")
        # Strip leading "**Research Idea:** ..." line if it duplicates the title.
        for rx in _TITLE_RES:
            desc = rx.sub("", desc, count=1).strip()
        out["description"] = desc
    return out


def project_for_issue(repo: Path, issue: dict, *, existing_ids: set[str], dry: bool, now: datetime) -> bool:
    """Create a brand-new Project + idea file for an open GitHub idea-issue.

    Parses legacy llmXive automation metadata (**Field**, **Research Idea**,
    **Description**) when present.
    """
    title_raw = issue["title"]
    body = issue.get("body") or ""
    meta = _parse_legacy_metadata(body)
    title = clean_title(meta.get("title") or title_raw, body)
    field = meta.get("field") or guess_field(title, body)
    if not field or len(field) > 40:
        field = guess_field(title, body)
    idea_body = meta.get("description") or body

    slug = slug_from_title(title)
    pid = next_id(existing_ids, slug)
    existing_ids.add(pid)
    issue_url = f"https://github.com/ContextLab/llmXive/issues/{issue['number']}"
    if dry:
        print(f"[dry] would import #{issue['number']} -> {pid}  ({field}) {title!r}")
        return True
    write_idea_md(repo, pid, slug, title, field, idea_body, issue_url)
    project = Project(
        id=pid,
        title=title,
        field=field,
        current_stage=Stage.BRAINSTORMED,
        points_research={},
        points_paper={},
        created_at=now,
        updated_at=now,
        artifact_hashes={},
    )
    project_store.save(project, repo_root=repo)
    print(f"[backfill-issue #{issue['number']}] {pid} ({title!r})")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-issues", action="store_true")
    args = ap.parse_args()
    now = datetime.now(UTC)
    repo = REPO

    # Step 1: every projects/PROJ-*/ dir without state.
    print("=== Step 1: backfill projects/ dirs ===")
    new_dirs = 0
    for pdir in sorted((repo / "projects").glob("PROJ-*")):
        if pdir.is_dir():
            if project_for_dir(repo, pdir.name, dry=args.dry_run, now=now):
                new_dirs += 1
    print(f"  added {new_dirs} state files for existing project dirs.\n")

    if args.skip_issues:
        return 0

    # Step 2: every open idea-labeled GitHub issue without a corresponding project.
    print("=== Step 2: import idea-labeled GitHub issues ===")
    proc = subprocess.run(
        ["gh", "issue", "list", "--state", "open", "--limit", "100",
         "--json", "number,title,body,labels"],
        capture_output=True, text=True, check=True,
    )
    issues = json.loads(proc.stdout)
    idea_issues = [
        i for i in issues
        if any(lbl["name"] == "idea" for lbl in i.get("labels", []))
    ]
    existing_ids = {p.stem for p in (repo / "state" / "projects").glob("PROJ-*.yaml")}
    # Track which issue numbers already have a state record (via idea front-matter).
    already = set()
    for state_file in (repo / "state" / "projects").glob("PROJ-*.yaml"):
        pid = state_file.stem
        for md in (repo / "projects" / pid / "idea").glob("*.md") if (repo / "projects" / pid / "idea").exists() else []:
            text = md.read_text(errors="replace")
            m = re.search(r"github_issue:\s*https://github.com/ContextLab/llmXive/issues/(\d+)", text)
            if m:
                already.add(int(m.group(1)))
    new_issues = 0
    for issue in idea_issues:
        if issue["number"] in already:
            continue
        if project_for_issue(repo, issue, existing_ids=existing_ids, dry=args.dry_run, now=now):
            new_issues += 1
    print(f"  imported {new_issues} new idea-issues.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
