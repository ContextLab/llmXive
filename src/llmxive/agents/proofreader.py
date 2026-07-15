"""Proofreader-Agent (T087).

Reads the assembled paper LaTeX source and emits a flag list. An
empty flag list is a precondition for `paper_complete` (per FR-007's
proofreader-flag-list-empty rule).

A "clean" verdict is BOUND to the exact paper source it was computed
against (a SHA-256 of the concatenated ``paper/source/**/*.tex``), the
verifier version that produced it, and a freshness TTL. ``proofreader_clean``
re-derives the CURRENT source hash and only reports clean when the stored
verdict still matches — existence of a stored "clean" is NOT proof the
current source is clean. Any drift (source edited, verifier bumped, verdict
expired) is treated as stale and forces a bounded re-proofread rather than a
silent pass (issue #1139 D13 — presence must never be mistaken for a fresh
verified verdict).
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path

import yaml

from llmxive.agents.base import Agent, AgentContext
from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.config import repo_root as _repo_root
from llmxive.speckit.yaml_extract import parse_yaml_lenient

#: Bump when the proofreader's flagging logic changes materially — a stored
#: verdict produced by an older verifier is treated as stale (re-proofread).
PROOFREADER_VERIFIER_VERSION = "proofreader/1"

#: A stored "clean" verdict older than this is treated as stale even when the
#: source is byte-identical, bounding how long a cached PASS is trusted.
#: Generous by design (proofreading is re-run cheaply each paper round).
PROOFREADER_VERDICT_TTL = timedelta(days=30)


def _read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _concat_paper_source(paper_source_dir: Path) -> str:
    if not paper_source_dir.is_dir():
        return ""
    out: list[str] = []
    for tex in sorted(paper_source_dir.rglob("*.tex")):
        rel = tex.relative_to(paper_source_dir).as_posix()
        body = tex.read_text(encoding="utf-8", errors="ignore")
        out.append(f"=== {rel} ===\n{body}\n")
    return "\n".join(out)


def _source_hash(paper_source_dir: Path) -> str:
    """SHA-256 of the concatenated paper source — the input a proofreader verdict
    is bound to. Identical between store (``handle_response``) and check
    (``proofreader_clean``) so a source edit provably invalidates a stored verdict.
    """
    return hashlib.sha256(
        _concat_paper_source(paper_source_dir).encode("utf-8")
    ).hexdigest()


class ProofreaderAgent(Agent):
    """Handles [kind:proofread] tasks. Also runs as a precondition gate."""

    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:
        repo = _repo_root()
        project_dir = repo / "projects" / ctx.project_id
        paper_dir = project_dir / "paper"
        source_dir = paper_dir / "source"

        body = _concat_paper_source(source_dir)
        constitution = paper_dir / ".specify" / "memory" / "constitution.md"
        paper_constitution = _read_optional(constitution)

        system = render_prompt(
            "agents/prompts/proofreader.md",
            {"project_id": ctx.project_id},
            repo_root=repo,
        )
        user = (
            f"# Paper source\n\n{body}\n\n"
            f"# Paper constitution\n\n{paper_constitution}\n\n"
            "# Task\n\nReturn the YAML flag list per the contract."
        )
        return [
            ChatMessage(role="system", content=system),
            ChatMessage(role="user", content=user),
        ]

    def handle_response(self, ctx: AgentContext, response: ChatResponse) -> list[str]:
        repo = _repo_root()
        try:
            doc = parse_yaml_lenient(response.text)
        except yaml.YAMLError as exc:
            raise RuntimeError(f"Proofreader-Agent returned invalid YAML: {exc}") from exc
        if not isinstance(doc, dict):
            raise RuntimeError("Proofreader YAML must be a mapping")

        # BIND the verdict to the exact source it was computed against, the
        # verifier version, and a wall-clock timestamp. proofreader_clean
        # re-derives the source hash and refuses to report clean when any of
        # these drift — so a "clean" verdict cannot survive a later source edit.
        source_dir = repo / "projects" / ctx.project_id / "paper" / "source"
        doc["source_hash"] = _source_hash(source_dir)
        doc["verifier_version"] = PROOFREADER_VERIFIER_VERSION
        doc["verified_at"] = datetime.now(UTC).isoformat()

        # Persist the flag list under the project's paper memory so the
        # paper_complete gate can read it.
        flags_path = (
            repo
            / "projects"
            / ctx.project_id
            / "paper"
            / ".specify"
            / "memory"
            / "proofreader_flags.yaml"
        )
        flags_path.parent.mkdir(parents=True, exist_ok=True)
        flags_path.write_text(yaml.safe_dump(doc, sort_keys=True), encoding="utf-8")
        return [str(flags_path.relative_to(repo))]


def proofreader_clean(
    project_id: str,
    *,
    repo_root: Path | None = None,
    now: datetime | None = None,
) -> bool:
    """Return True iff a FRESH proofreader verdict certifies the CURRENT source.

    "Fresh" is a positive gate — all of the following must hold:

    * the stored verdict is ``clean`` with an empty flag list;
    * the stored ``source_hash`` equals the hash of the CURRENT
      ``paper/source/**/*.tex`` (a source edit after proofreading invalidates
      the verdict — the D13 staleness fix);
    * the stored ``verifier_version`` matches the current verifier; and
    * the verdict has not aged past :data:`PROOFREADER_VERDICT_TTL`.

    Any drift (or a legacy record written before verdicts were bound to a
    source hash) is treated as STALE and reported NOT clean, so the
    paper_complete gate re-runs a bounded proofread rather than trusting a
    cached PASS on existence alone.
    """
    repo = repo_root or _repo_root()
    flags_path = (
        repo
        / "projects"
        / project_id
        / "paper"
        / ".specify"
        / "memory"
        / "proofreader_flags.yaml"
    )
    if not flags_path.exists():
        return False
    try:
        doc = yaml.safe_load(flags_path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return False
    if not isinstance(doc, dict):
        return False
    flags = doc.get("flags") or []
    if doc.get("verdict") != "clean" or flags:
        return False

    # The verdict must still describe the source in front of us, must have been
    # produced by the current verifier, and must not have expired. Otherwise it
    # is stale — re-proofread rather than silently pass.
    source_dir = repo / "projects" / project_id / "paper" / "source"
    if doc.get("source_hash") != _source_hash(source_dir):
        return False
    if doc.get("verifier_version") != PROOFREADER_VERIFIER_VERSION:
        return False
    verified_at_raw = doc.get("verified_at")
    if not verified_at_raw:
        return False
    try:
        verified_at = datetime.fromisoformat(str(verified_at_raw))
    except ValueError:
        return False
    if verified_at.tzinfo is None:
        verified_at = verified_at.replace(tzinfo=UTC)
    current = now or datetime.now(UTC)
    if current - verified_at > PROOFREADER_VERDICT_TTL:
        return False
    return True


__all__ = ["ProofreaderAgent", "proofreader_clean"]
