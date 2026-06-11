"""paper_publisher agent (spec 013 / US6, FR-021..FR-033).

Deterministic (no-LLM) agent. Picks projects at `paper_accepted`,
registers a real DOI via Zenodo, recompiles the PDF with the final
byline + post-paper appendix, transitions to `posted`.

Contract: specs/013-paper-revision-implementer/contracts/publisher-agent.md
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import yaml

from llmxive.agents.base import Agent, AgentContext
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.config import repo_root as _repo_root
from llmxive.pipeline import post_paper_appendix
from llmxive.pipeline import zenodo as zenodo_module
from llmxive.pipeline.authors import list_authors
from llmxive.state import project as project_state
from llmxive.state import publication as pub_state
from llmxive.state import revision_history as rh_state
from llmxive.state import runlog
from llmxive.types import (
    AuthorEntry,
    BackendName,
    DOIVersion,
    Outcome,
    Publication,
    RunLogEntry,
    Stage,
    VolumeIssue,
)

_PUBLISH_BLOCKED_AFTER = 5  # FR-030


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def resolve_badge(rounds_data: Sequence[object]) -> str:
    """FR-022: determine the `\\paperstatus{...}` value at publication.

    - if `paper/revision_history.yaml` is missing OR rounds == [] OR all
      rounds had 0 successful tasks: `"Auto-Reviewed | Published"`
    - if ≥1 round had ≥1 successful task: `"Auto-Reviewed | Auto-Revised | Published"`
    """
    if not rounds_data:
        return "Auto-Reviewed | Published"
    for r in rounds_data:
        if hasattr(r, "tasks_done"):
            td: object = r.tasks_done
        elif isinstance(r, dict):
            td = r.get("tasks_done", 0)
        else:
            td = 0
        if isinstance(td, (int, float)) and td > 0:
            return "Auto-Reviewed | Auto-Revised | Published"
    return "Auto-Reviewed | Published"


def _inject_paper_macros(
    source_dir: Path,
    *,
    status: str,
    doi: str,
    volume: str,
    issue: str,
) -> None:
    """Inject or update `\\paperstatus{}`, `\\paperdoi{}`,
    `\\papervolume{}`, `\\paperissue{}` in the primary tex's preamble
    (before `\\begin{document}`)."""
    primary = _find_primary_tex(source_dir)
    if primary is None:
        return
    text = primary.read_text(encoding="utf-8")

    def set_macro(text: str, name: str, value: str) -> str:
        pat = re.compile(r"\\" + name + r"\s*\{[^}]*\}")
        line = f"\\{name}{{{value}}}"
        if pat.search(text):
            return pat.sub(lambda _m: line, text, count=1)
        # Insert before \begin{document}.
        return text.replace(r"\begin{document}", f"{line}\n\\begin{{document}}", 1)

    text = set_macro(text, "paperstatus", status)
    text = set_macro(text, "paperdoi", doi)
    text = set_macro(text, "papervolume", volume)
    text = set_macro(text, "paperissue", issue)
    primary.write_text(text, encoding="utf-8")


def _find_primary_tex(source_dir: Path) -> Path | None:
    for tex in sorted(source_dir.rglob("*.tex")):
        try:
            head = tex.read_text(encoding="utf-8", errors="ignore")[:4000]
        except OSError:
            continue
        if "\\documentclass" in head:
            return tex
    return None


def _compile_full(source_dir: Path) -> tuple[bool, bytes | None]:
    """Full lualatex → bibtex → lualatex → lualatex sequence for the
    publisher's final compile."""
    primary = _find_primary_tex(source_dir)
    if primary is None:
        return False, None
    stem = primary.stem

    def _run(cmd: list[str]) -> int:
        proc = subprocess.run(
            cmd, cwd=source_dir, capture_output=True, text=True, timeout=600.0,
        )
        return proc.returncode

    if _run(["lualatex", "-interaction=nonstopmode", primary.name]) != 0:
        return False, None
    _run(["bibtex", stem])  # bibtex's return code is unreliable; rely on next pass
    _run(["lualatex", "-interaction=nonstopmode", primary.name])
    if _run(["lualatex", "-interaction=nonstopmode", primary.name]) != 0:
        return False, None
    pdf = source_dir / f"{stem}.pdf"
    if not pdf.is_file():
        return False, None
    return True, pdf.read_bytes()


def _append_appendix_input(source_dir: Path, appendix_tex_rel: str) -> None:
    """Insert `\\input{<appendix_tex_rel>}` before `\\end{document}` in the
    primary tex. Idempotent — no-op if the input line is already there."""
    primary = _find_primary_tex(source_dir)
    if primary is None:
        return
    text = primary.read_text(encoding="utf-8")
    marker = f"\\input{{{appendix_tex_rel}}}"
    if marker in text:
        return
    text = text.replace(r"\end{document}", f"{marker}\n\\end{{document}}", 1)
    primary.write_text(text, encoding="utf-8")


def _draft_ledger_path(paper_dir: Path) -> Path:
    """Recovery ledger for the in-flight Zenodo deposition (FR-020
    idempotence): written immediately after draft creation so a crash at
    ANY later point — including after the remote publish succeeded — can
    resume the SAME deposition instead of minting a second DOI."""
    return paper_dir / ".zenodo_draft.yaml"


def _read_draft_ledger(paper_dir: Path) -> dict | None:
    p = _draft_ledger_path(paper_dir)
    if not p.is_file():
        return None
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) and data.get("deposition_id") else None


def _write_draft_ledger(
    paper_dir: Path, *, deposition_id: int, doi: str, environment: str
) -> None:
    _draft_ledger_path(paper_dir).write_text(
        yaml.safe_dump(
            {
                "deposition_id": deposition_id,
                "doi": doi,
                "environment": environment,
                "created_at": datetime.now(UTC).isoformat(),
            }
        ),
        encoding="utf-8",
    )


def _publish_failure_counter_path(repo_root: Path, project_id: str) -> Path:
    return repo_root / "state" / f"{project_id}.publisher.yaml"


def _bump_failure_counter(
    repo_root: Path, project_id: str, *, failed: bool,
) -> int:
    p = _publish_failure_counter_path(repo_root, project_id)
    state: dict[str, object] = {}
    if p.is_file():
        try:
            state = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            state = {}
    _cf = state.get("consecutive_failures", 0)
    n = int(_cf) if isinstance(_cf, (int, float, str)) else 0  # yaml value is numeric
    n = n + 1 if failed else 0
    state["consecutive_failures"] = n
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
    return n


def _build_citation_string(
    authors: list[AuthorEntry], title: str, year: int, vol_issue: str, doi: str,
) -> str:
    """FR-026: human-readable citation. Original authors then 'et al.' if
    >5, then comma-separated LLM contributors."""
    human_names = [a.name for a in authors if a.kind == "human"]
    llm_names = [a.name for a in authors if a.kind == "llm"]
    if len(human_names) > 5:
        humans = ", ".join(human_names[:3]) + ", …"
    else:
        humans = ", ".join(human_names)
    llm = ", ".join(llm_names)
    revised = f" Revised by: {llm}." if llm else ""
    return (
        f"{humans}. {year}. *{title}*. llmXive **{vol_issue}**. "
        f"doi:{doi}.{revised}"
    )


class PaperPublisher(Agent):
    """Deterministic publisher. Single `run()` per scheduler tick, no LLM
    calls — every step is filesystem + HTTP I/O against Zenodo."""

    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:
        return [ChatMessage(role="user", content="(deterministic agent — unused)")]

    def handle_response(self, ctx: AgentContext, response: ChatResponse) -> list[str]:
        return []

    def run(self, ctx: AgentContext) -> RunLogEntry:
        started = datetime.now(UTC)
        outcome = Outcome.SUCCESS
        failure_reason: str | None = None
        outputs: list[str] = []
        backend_used = BackendName.DARTMOUTH
        model_used = "deterministic-no-llm"
        repo = _repo_root()
        ended = started  # default; reassigned on success

        try:
            project = project_state.load(ctx.project_id, repo_root=repo)
            if project is None:
                raise FileNotFoundError(f"no project state for {ctx.project_id}")
            # Spec 015 T035 / FR-036 + FR-054: publisher runs at PAPER_ACCEPTED OR
            # AWAITING_PUBLICATION_SIGNOFF, and refuses to mint a DOI unless the
            # maintainer sign-off has been recorded. Defense-in-depth alongside the
            # graph gate: no Zenodo DOI is minted without explicit
            # `llmxive project publish-approve`.
            if project.current_stage not in (
                Stage.PAPER_ACCEPTED, Stage.AWAITING_PUBLICATION_SIGNOFF,
            ):
                outcome = Outcome.SKIPPED
                failure_reason = (
                    f"current_stage={project.current_stage.value} "
                    f"(expected paper_accepted or awaiting_publication_signoff); no-op"
                )
                ended = datetime.now(UTC)
                return self._emit_run_log(
                    ctx, started, ended, outcome, failure_reason, outputs,
                    backend_used, model_used,
                )
            from llmxive.speckit._publication_signoff import read_signoff
            project_memory_dir = repo / "projects" / project.id / ".specify" / "memory"
            signoff = read_signoff(project_memory_dir)
            if signoff is None:
                outcome = Outcome.SKIPPED
                failure_reason = (
                    "awaiting manual maintainer DOI sign-off (FR-054); "
                    "run `llmxive project publish-approve <PROJ-ID> --who X --what Y`"
                )
                ended = datetime.now(UTC)
                return self._emit_run_log(
                    ctx, started, ended, outcome, failure_reason, outputs,
                    backend_used, model_used,
                )

            paper_dir = repo / "projects" / project.id / "paper"
            source_dir = paper_dir / "source"
            metadata_path = paper_dir / "metadata.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.is_file() else {}

            # Spec 023 / FR-020 idempotence check 1: a publication.yaml
            # with a minted DOI but a non-POSTED stage means a prior run
            # crashed between mint and the state write. CONVERGE — never
            # mint again.
            prior_pub = pub_state.load(project.id, repo_root=repo)
            if prior_pub is not None and prior_pub.doi:
                ended = datetime.now(UTC)
                project_state.update(
                    project.id,
                    {
                        "current_stage": Stage.POSTED.value,
                        "updated_at": ended.isoformat(),
                    },
                    repo_root=repo,
                )
                _draft_ledger_path(paper_dir).unlink(missing_ok=True)
                outputs.append(f"projects/{project.id}/paper/publication.yaml")
                failure_reason = (
                    f"already published (doi={prior_pub.doi}); converged "
                    "state to posted without re-minting"
                )
                return self._emit_run_log(
                    ctx, started, ended, outcome, failure_reason, outputs,
                    backend_used, model_used,
                )

            # FR-024: derive volume/issue from acceptance time.
            accepted_at = project.updated_at  # last advancement
            vi = VolumeIssue.from_datetime(accepted_at)

            # FR-022: resolve status badge.
            hist = rh_state.load(project.id, repo_root=repo)
            badge = resolve_badge(hist.rounds)

            # FR-027: detect re-publication via existing zenodo_id.
            existing_zenodo_id = metadata.get("zenodo_id")
            is_republication = bool(existing_zenodo_id)

            # Decide environment (production by default; sandbox via env var).
            import os
            use_sandbox = os.environ.get("LLMXIVE_ZENODO_ENV") == "sandbox"
            client = zenodo_module.ZenodoClient(sandbox=use_sandbox)

            # Build Zenodo metadata block.
            authors = list_authors(metadata_path)
            zenodo_meta = self._build_zenodo_metadata(
                title=str(metadata.get("title") or project.title),
                authors=authors,
                description=str(metadata.get("abstract") or ""),
                publication_date=accepted_at.strftime("%Y-%m-%d"),
                project_id=project.id,
            )

            # Spec 023 / FR-020 idempotence check 2: a prior run may have
            # created (or even PUBLISHED) a deposition and then crashed
            # before the local state write. The recovery ledger
            # (paper/.zenodo_draft.yaml, written immediately after draft
            # creation) lets us RESUME that deposition instead of minting
            # a second DOI.
            resumed_published: zenodo_module.PublishedDeposition | None = None
            draft = None
            ledger = _read_draft_ledger(paper_dir)
            if ledger and ledger.get("environment") == (
                "sandbox" if use_sandbox else "production"
            ):
                try:
                    raw = client.get_deposition(int(ledger["deposition_id"]))
                except zenodo_module.ZenodoAPIError:
                    raw = None
                if raw is not None and raw.get("submitted"):
                    # Already published remotely — adopt it, do NOT re-mint.
                    resumed_published = zenodo_module.PublishedDeposition(
                        deposition_id=int(raw["id"]),
                        doi=raw.get("doi", "") or str(ledger.get("doi") or ""),
                        doi_url=raw.get("doi_url")
                        or f"https://doi.org/{raw.get('doi', '')}",
                        concept_doi=raw.get("conceptdoi"),
                        raw=raw,
                    )
                elif raw is not None:
                    links = raw.get("links") or {}
                    prereserve = (raw.get("metadata") or {}).get("prereserve_doi") or {}
                    draft = zenodo_module.Deposition(
                        deposition_id=int(raw["id"]),
                        doi=prereserve.get("doi") or str(ledger.get("doi") or ""),
                        bucket_url=links.get("bucket", ""),
                        publish_url=links.get("publish", ""),
                        raw=raw,
                    )
            if resumed_published is None and draft is None:
                # Create draft (pre-reserves DOI) — new deposition for first
                # publication; new version for re-publication.
                if is_republication:
                    draft = client.new_version(int(existing_zenodo_id or 0))
                else:
                    draft = client.create_deposition(zenodo_meta)
            if resumed_published is not None:
                doi = resumed_published.doi
            else:
                doi = draft.doi
                _write_draft_ledger(
                    paper_dir,
                    deposition_id=draft.deposition_id,
                    doi=doi,
                    environment="sandbox" if use_sandbox else "production",
                )
            if not doi:
                raise RuntimeError("Zenodo did not return a pre-reserved DOI")

            # Generate post-paper appendix tex fragment.
            appendix_path = source_dir / "_llmxive_appendix.tex"
            post_paper_appendix.render_to_file(
                paper_dir.parent, appendix_path, project_id=project.id,
            )
            _append_appendix_input(source_dir, "_llmxive_appendix.tex")

            # Inject macros into preamble.
            _inject_paper_macros(
                source_dir, status=badge, doi=doi, volume=vi.volume, issue=vi.issue,
            )

            # Final compile.
            ok, pdf_bytes = _compile_full(source_dir)
            if not ok or pdf_bytes is None:
                raise RuntimeError("final paper compile failed")

            # Replace paper/pdf/main.pdf.
            out_pdf = paper_dir / "pdf" / "main.pdf"
            out_pdf.parent.mkdir(parents=True, exist_ok=True)
            out_pdf.write_bytes(pdf_bytes)
            outputs.append(str(out_pdf.relative_to(repo)))

            # Upload + publish (skipped when resuming an already-published
            # deposition — FR-020 idempotence).
            if resumed_published is not None:
                published = resumed_published
            else:
                client.upload_file(draft.bucket_url, "main.pdf", pdf_bytes)
                published = client.publish(draft.deposition_id)
            doi = published.doi  # canonical after publish (may match prereserve)
            doi_url = published.doi_url
            concept_doi = published.concept_doi

            # Write publication.yaml.
            ended = datetime.now(UTC)
            doi_version = DOIVersion(
                doi=doi,
                version_index=(len(metadata.get("doi_versions") or []) + 1),
                published_at=ended,
                pdf_sha256=_sha256(pdf_bytes),
            )
            existing_versions = []
            if is_republication:
                # Carry forward versions from the prior publication.yaml.
                prior = pub_state.load(project.id, repo_root=repo)
                if prior:
                    existing_versions = list(prior.doi_versions)
            all_versions = [*existing_versions, doi_version]
            review_summary = self._summarize_reviews(paper_dir, hist)
            citation = _build_citation_string(
                authors, str(metadata.get("title") or project.title),
                ended.year, vi.display, doi,
            )
            pub = Publication(
                project_id=project.id,
                title=str(metadata.get("title") or project.title),
                volume=vi.volume,
                issue=vi.issue,
                display_volume_issue=vi.display,
                doi=doi,
                doi_url=doi_url,
                concept_doi=concept_doi,
                doi_versions=all_versions,
                zenodo_id=published.deposition_id,
                zenodo_environment="sandbox" if use_sandbox else "production",
                citation_string=citation,
                authors_at_publication=authors,
                accepted_at=accepted_at,
                published_at=ended,
                review_summary=review_summary,
            )
            pub_state.save(project.id, pub, repo_root=repo)
            outputs.append(f"projects/{project.id}/paper/publication.yaml")
            # Publication recorded — the recovery ledger has served its
            # purpose (FR-020 idempotence).
            _draft_ledger_path(paper_dir).unlink(missing_ok=True)

            # Reset failure counter on success.
            _bump_failure_counter(repo, project.id, failed=False)

            # Stage → posted (FR-021).
            project_state.update(
                project.id,
                {
                    "current_stage": Stage.POSTED.value,
                    "updated_at": ended.isoformat(),
                },
                repo_root=repo,
            )

        except Exception as exc:
            # FR-030: failure → bump counter; on 5th → publish_blocked.
            n = _bump_failure_counter(repo, ctx.project_id, failed=True)
            outcome = Outcome.FAILED
            failure_reason = f"{type(exc).__name__}: {exc}"
            ended = datetime.now(UTC)
            if n >= _PUBLISH_BLOCKED_AFTER:
                try:
                    project_state.update(
                        ctx.project_id,
                        {
                            "current_stage": Stage.PUBLISH_BLOCKED.value,
                            "updated_at": ended.isoformat(),
                        },
                        repo_root=repo,
                    )
                    failure_reason = (
                        f"{failure_reason} [transitioned to publish_blocked "
                        f"after {n} consecutive failures]"
                    )
                except Exception:
                    pass
        # Emit exactly once. A ``return`` in ``finally`` previously swallowed
        # the early SKIPPED returns above and the FAILED path here, double-
        # appending run-log entries (B012). Agents never propagate — failures
        # are reported via outcome=FAILED so the cron sweep continues.
        return self._emit_run_log(
            ctx, started, ended, outcome, failure_reason, outputs,
            backend_used, model_used,
        )

    # --- Helpers --------------------------------------------------------

    def _build_zenodo_metadata(
        self,
        *,
        title: str,
        authors: list[AuthorEntry],
        description: str,
        publication_date: str,
        project_id: str,
    ) -> dict[str, object]:
        creators: list[dict[str, str]] = []
        for a in authors:
            entry: dict[str, str] = {"name": a.name}
            if a.affiliation:
                entry["affiliation"] = a.affiliation
            creators.append(entry)
        if not creators:
            creators = [{"name": "llmXive Pipeline"}]
        github_url = (
            f"https://github.com/ContextLab/llmXive/tree/main/projects/{project_id}/"
        )
        return {
            "metadata": {
                "upload_type": "publication",
                "publication_type": "article",
                "title": title,
                "creators": creators,
                "description": description or f"llmXive paper {project_id}.",
                "publication_date": publication_date,
                "keywords": ["llmXive", "automated peer review"],
                "related_identifiers": [
                    {
                        "relation": "isSupplementTo",
                        "identifier": github_url,
                        "resource_type": "software",
                    },
                ],
                "notes": (
                    f"Reviewed and revised by llmXive. "
                    f"Project: {github_url}"
                ),
                "prereserve_doi": True,
            }
        }

    def _summarize_reviews(self, paper_dir: Path, hist: object) -> dict[str, int]:
        reviews_dir = paper_dir / "reviews"
        n_reviewers = 0
        if reviews_dir.is_dir():
            n_reviewers = sum(1 for _ in reviews_dir.glob("paper_reviewer*.md"))
        rounds = hist.rounds if hasattr(hist, "rounds") else []
        n_done = sum(r.tasks_done for r in rounds)
        n_failed = sum(r.tasks_failed for r in rounds)
        return {
            "num_reviewers": n_reviewers,
            "num_revision_rounds": len(rounds),
            "num_action_items_addressed": int(n_done),
            "num_action_items_failed": int(n_failed),
        }

    def _emit_run_log(
        self,
        ctx: AgentContext,
        started: datetime,
        ended: datetime,
        outcome: Outcome,
        failure_reason: str | None,
        outputs: list[str],
        backend_used: BackendName,
        model_used: str,
    ) -> RunLogEntry:
        entry = RunLogEntry(
            run_id=ctx.run_id,
            entry_id=str(uuid4()),
            agent_name=self.name,
            project_id=ctx.project_id,
            task_id=ctx.task_id,
            inputs=ctx.inputs,
            outputs=outputs,
            backend=backend_used,
            model_name=model_used,
            prompt_version=self.entry.prompt_version,
            started_at=started,
            ended_at=ended,
            outcome=outcome,
            failure_reason=failure_reason,
            cost_estimate_usd=0.0,
        )
        runlog.append_entry(entry)
        return entry
