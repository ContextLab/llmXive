"""Brainstorm / Flesh-Out / Idea-Selector agent classes.

These three agents drive the idea-generation phase of the pipeline:

    brainstormed       → flesh_out (writes a richer idea body in projects/<id>/idea/)
    flesh_out_complete → project_initializer
    project_initialized → idea_selector → specifier (next pass)

For minimum-viable execution they each just persist the LLM's output
into a stable artifact; advanced behavior (lit-search, duplicate-check,
selection ranking) is left to future iterations.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from llmxive.agents.base import Agent, AgentContext
from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.types import AgentRegistryEntry


def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40] or "idea"


class _IdeaPhaseAgent(Agent):
    """Shared scaffolding for idea-phase agents.

    Each subclass overrides `prompt_path` and `_persist`. The default
    `build_messages` just renders the system prompt with project metadata
    and asks the LLM for free-form Markdown back; `handle_response`
    routes to the subclass's `_persist`.
    """

    prompt_path: str = ""

    def __init__(self, registry_entry: AgentRegistryEntry) -> None:
        super().__init__(registry_entry)

    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:
        repo = Path(__file__).resolve().parent.parent.parent.parent
        system = render_prompt(
            self.prompt_path,
            {
                "project_id": ctx.project_id,
                "title": ctx.metadata.get("title", ""),
                "field": ctx.metadata.get("field", ""),
            },
            repo_root=repo,
        )
        # Existing idea body (if any) gets handed to the LLM as context.
        # spec 003 / D13: filter out diagnostic-artifact files
        # (research_question_validation.md, etc.) so the validator and
        # flesh_out don't accidentally read their own / each other's
        # output as the canonical idea body. Sort alphabetically for
        # deterministic selection when multiple legitimate idea files
        # exist (none should, but be safe).
        idea_body = ""
        idea_dir = repo / "projects" / ctx.project_id / "idea"
        if idea_dir.exists():
            for md in sorted(idea_dir.glob("*.md")):
                if md.name in {"research_question_validation.md"}:
                    continue
                idea_body = md.read_text(encoding="utf-8", errors="replace")
                break
        user_parts: list[str] = []
        if ctx.metadata.get("title"):
            user_parts.append(f"# Title\n\n{ctx.metadata['title']}")
        if ctx.metadata.get("field"):
            user_parts.append(f"# Field\n\n{ctx.metadata['field']}")
        if idea_body:
            user_parts.append(f"# Current idea note\n\n{idea_body}")
        user = "\n\n".join(user_parts) + "\n\n# Task\n\nReturn the requested Markdown."
        return [
            ChatMessage(role="system", content=system),
            ChatMessage(role="user", content=user),
        ]

    def _persist(self, ctx: AgentContext, response: ChatResponse) -> list[str]:
        raise NotImplementedError

    def handle_response(self, ctx: AgentContext, response: ChatResponse) -> list[str]:
        return self._persist(ctx, response)


class BrainstormAgent(_IdeaPhaseAgent):
    """Stage owner: brainstormed (initial seeding only).

    The brainstorm agent is invoked when the user (or the cron job)
    explicitly seeds a new idea. The LLM proposes a 2-4 sentence
    research idea, persisted to projects/<id>/idea/<slug>.md.
    """

    prompt_path = "agents/prompts/brainstorm.md"

    def _persist(self, ctx: AgentContext, response: ChatResponse) -> list[str]:
        repo = Path(__file__).resolve().parent.parent.parent.parent
        title = ctx.metadata.get("title", ctx.project_id)
        slug = _slugify(title)
        idea_dir = repo / "projects" / ctx.project_id / "idea"
        idea_dir.mkdir(parents=True, exist_ok=True)
        target = idea_dir / f"{slug}.md"
        body = response.text.strip() or "(brainstorm produced empty output)"
        front = (
            "---\n"
            f"field: {ctx.metadata.get('field', 'general')}\n"
            f"submitter: agent:brainstorm\n"
            "---\n\n"
            f"# {title}\n\n"
            f"{body}\n"
        )
        target.write_text(front, encoding="utf-8")
        return [str(target.relative_to(repo))]


class FleshOutAgent(_IdeaPhaseAgent):
    """Stage owner: brainstormed → flesh_out_complete.

    Takes a brainstorm-stage idea and expands it into a richer note
    (research question, motivation, related work, expected results,
    methodology sketch). Overwrites the existing idea/<slug>.md.
    """

    prompt_path = "agents/prompts/flesh_out.md"

    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:
        messages = super().build_messages(ctx)
        repo = Path(__file__).resolve().parent.parent.parent.parent
        # spec 003 / D12: forward any [REVISED] hint from a prior
        # research_question_validator iteration so this re-run actually
        # adopts the revised question instead of regenerating the rejected
        # one. The validator persists its output to
        # idea/research_question_validation.md alongside the idea Markdown.
        validation_md = (
            repo / "projects" / ctx.project_id / "idea" / "research_question_validation.md"
        )
        if validation_md.exists():
            v_text = validation_md.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"\[REVISED\]\s*(.+?)\s*\[/REVISED\]", v_text, re.DOTALL)
            if m:
                revised_q = m.group(1).strip()
                hint_block = (
                    "# PRIOR VALIDATION FEEDBACK\n\n"
                    "A prior research_question_validator iteration flagged the\n"
                    "previous research question and proposed a defensible reframing.\n"
                    "You MUST adopt or improve on the [REVISED] question below — do\n"
                    "NOT regenerate the previous question:\n\n"
                    f"[REVISED]\n{revised_q}\n[/REVISED]\n"
                )
                last = messages[-1]
                messages[-1] = ChatMessage(
                    role=last.role,
                    content=last.content + "\n\n" + hint_block,
                )
        # Augment the user prompt with a real lit-search result block so
        # the LLM grounds its "Related work" section on actual papers
        # instead of hallucinating URLs that 404 (PROJ-006 spec.md was
        # citing non-existent worldagroforestry.org/...).
        title = ctx.metadata.get("title", "")
        field = ctx.metadata.get("field", "")
        query = " ".join(filter(None, [title, field]))
        if query:
            try:
                import sys as _sys
                from pathlib import Path as _Path
                _repo = _Path(__file__).resolve().parent.parent.parent.parent
                if str(_repo) not in _sys.path:
                    _sys.path.insert(0, str(_repo))
                from agents.tools.lit_search import lit_search
                papers = lit_search(query=query, max_results=8)
            except Exception as exc:  # pragma: no cover — defensive
                papers = []
                print(f"[flesh_out] lit_search failed: {exc!r}")
            if papers:
                lines = ["# Verified literature search results (use ONLY these URLs)"]
                for p in papers:
                    yr = f" ({p.year})" if p.year else ""
                    lines.append(f"- [{p.title}{yr}]({p.source_url}) — {p.abstract[:200]}")
                lit_block = "\n".join(lines)
                # Append to the last user message.
                last = messages[-1]
                messages[-1] = ChatMessage(
                    role=last.role,
                    content=last.content + "\n\n" + lit_block + "\n",
                )
        return messages

    # spec 003 / D13: diagnostic artifacts that share idea_dir with the
    # canonical idea file but MUST NOT be picked as the overwrite target.
    _DIAGNOSTIC_ARTIFACT_NAMES: frozenset[str] = frozenset({
        "research_question_validation.md",
        # citation_resolution.json is .json so already excluded by *.md, but
        # if the resolver ever switches output format, keep this list
        # explicit.
    })

    def _persist(self, ctx: AgentContext, response: ChatResponse) -> list[str]:
        repo = Path(__file__).resolve().parent.parent.parent.parent
        title = ctx.metadata.get("title", ctx.project_id)
        idea_dir = repo / "projects" / ctx.project_id / "idea"
        idea_dir.mkdir(parents=True, exist_ok=True)
        # Find existing idea file (preserve filename if present). Filter
        # out diagnostic artifacts that happen to share the *.md extension
        # — D13 from spec 003: alphabetical ordering picked
        # research_question_validation.md before the canonical slug-named
        # file and clobbered the validator's output.
        existing = next(
            (p for p in sorted(idea_dir.glob("*.md"))
             if p.name not in self._DIAGNOSTIC_ARTIFACT_NAMES),
            None,
        )
        if existing is not None:
            target = existing
            # Preserve original front-matter.
            cur = existing.read_text(encoding="utf-8", errors="replace")
            front = ""
            if cur.startswith("---"):
                try:
                    end = cur.index("---", 3)
                    front = cur[: end + 3] + "\n\n"
                except ValueError:
                    pass
        else:
            target = idea_dir / f"{_slugify(title)}.md"
            front = (
                "---\n"
                f"field: {ctx.metadata.get('field', 'general')}\n"
                f"submitter: agent:flesh_out\n"
                "---\n\n"
            )
        body = response.text.strip()
        if not body:
            raise RuntimeError("Flesh-Out returned an empty body")
        # Strip ```markdown / ```md fences if present.
        if body.startswith("```"):
            lines = body.splitlines()
            if lines and lines[0].lstrip("`").lower() in {"", "markdown", "md"}:
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            body = "\n".join(lines).strip()
        # If the body already starts with a `# Title` heading, don't
        # double-add one. The LLM tends to repeat the title; honor
        # whichever variant it produced.
        if not body.startswith("# "):
            body = f"# {title}\n\n{body}"
        target.write_text(front + body + "\n", encoding="utf-8")

        # Scope check: if the LLM declared the idea out-of-scope per
        # the brainstorm/flesh-out scope constraints, write a sentinel
        # so the dispatcher rolls the project back to BRAINSTORMED.
        # The Brainstorm agent will then propose a different idea on
        # the next cycle.
        body_lower = body.lower()
        if (
            "verdict: rejected" in body_lower
            or "out of scope" in body_lower
            or "out-of-scope" in body_lower
            or "exceeds gha" in body_lower
            or "exceeds github actions" in body_lower
        ):
            scope_marker = (
                repo / "projects" / ctx.project_id / ".specify" / "memory" / "scope_rejected.yaml"
            )
            scope_marker.parent.mkdir(parents=True, exist_ok=True)
            from datetime import datetime, timezone as _tz
            scope_marker.write_text(
                f"reason: flesh-out judged idea out of GHA-feasible scope\n"
                f"detected_at: {datetime.now(_tz.utc).isoformat()}\n",
                encoding="utf-8",
            )
            print(f"[flesh_out] {ctx.project_id} marked OUT-OF-SCOPE")
        return [str(target.relative_to(repo))]


class IdeaSelectorAgent(_IdeaPhaseAgent):
    """Stage owner: project_initialized → specified (selects which idea to advance).

    Currently a no-op pass-through: the project-initializer already
    advances each project individually, so the selector just signals
    "this idea is selected" by writing a sentinel file. Future versions
    will rank multiple fleshed-out ideas and pick the highest-scoring.
    """

    prompt_path = "agents/prompts/idea_selector.md"

    def _persist(self, ctx: AgentContext, response: ChatResponse) -> list[str]:
        repo = Path(__file__).resolve().parent.parent.parent.parent
        target = (
            repo
            / "projects"
            / ctx.project_id
            / ".specify"
            / "memory"
            / "idea_selected.yaml"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            f"selected: true\nselected_at: {datetime.now(timezone.utc).isoformat()}\n",
            encoding="utf-8",
        )
        return [str(target.relative_to(repo))]


class ResearchQuestionValidatorAgent(_IdeaPhaseAgent):
    """Stage owner: flesh_out_complete → validated | validator_revise | validator_rejected.

    Audits a fleshed-out idea for research-question quality (phenomenon-vs-method,
    circularity, triviality, narrowing) before idea_selector promotes it. Writes
    the validation block to ``idea/research_question_validation.md`` and a sentinel
    file under ``.specify/memory/`` that the pipeline graph consumes to decide the
    next stage transition.

    Three sentinel outcomes:
      - ``research_question_validated.yaml`` → Stage.VALIDATED
      - ``research_question_revise.yaml`` → Stage.VALIDATOR_REVISE (rolled back to
        flesh_out_in_progress on the next tick)
      - ``research_question_rejected.yaml`` → Stage.VALIDATOR_REJECTED (rolled back
        to brainstormed on the next tick)
    """

    prompt_path = "agents/prompts/research_question_validator.md"

    def _persist(self, ctx: AgentContext, response: ChatResponse) -> list[str]:
        repo = Path(__file__).resolve().parent.parent.parent.parent
        idea_dir = repo / "projects" / ctx.project_id / "idea"
        idea_dir.mkdir(parents=True, exist_ok=True)

        body = response.text.strip()
        if not body:
            raise RuntimeError("Research-question validator returned an empty body")
        # Strip ```markdown / ```md fences if present.
        if body.startswith("```"):
            lines = body.splitlines()
            if lines and lines[0].lstrip("`").lower() in {"", "markdown", "md"}:
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            body = "\n".join(lines).strip()

        target = idea_dir / "research_question_validation.md"
        target.write_text(body + "\n", encoding="utf-8")

        verdict = self._extract_verdict(body)
        revised_question = self._extract_revised_question(body)
        memory_dir = repo / "projects" / ctx.project_id / ".specify" / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc).isoformat()

        outputs: list[str] = [str(target.relative_to(repo))]

        if verdict == "validated":
            sentinel = memory_dir / "research_question_validated.yaml"
            sentinel.write_text(f"validated: true\nvalidated_at: {now}\n", encoding="utf-8")
            outputs.append(str(sentinel.relative_to(repo)))
        elif verdict == "validator_revise":
            sentinel = memory_dir / "research_question_revise.yaml"
            content = f"revise: true\nflagged_at: {now}\n"
            if revised_question:
                # Escape any quotes in the revised question for valid YAML.
                escaped = revised_question.replace('"', '\\"')
                content += f'revised_question: "{escaped}"\n'
            sentinel.write_text(content, encoding="utf-8")
            outputs.append(str(sentinel.relative_to(repo)))
        elif verdict == "validator_rejected":
            sentinel = memory_dir / "research_question_rejected.yaml"
            sentinel.write_text(f"rejected: true\nflagged_at: {now}\n", encoding="utf-8")
            outputs.append(str(sentinel.relative_to(repo)))
        else:
            # Defensive: if the LLM produced an unparseable verdict, treat as
            # revise so we don't silently advance a flawed project.
            sentinel = memory_dir / "research_question_revise.yaml"
            sentinel.write_text(
                f"revise: true\nflagged_at: {now}\n"
                f"reason: validator output verdict could not be parsed\n",
                encoding="utf-8",
            )
            outputs.append(str(sentinel.relative_to(repo)))
            print(
                f"[research_question_validator] {ctx.project_id} verdict unparseable; "
                f"defaulting to validator_revise"
            )

        return outputs

    @staticmethod
    def _extract_verdict(body: str) -> str | None:
        """Find the final `**Verdict**: <one of three>` line.

        Per the prompt contract, the overall verdict is the LAST `**Verdict**`
        line in the document.
        """
        candidates = re.findall(
            r"\*\*Verdict\*\*\s*:\s*(validated|validator_revise|validator_rejected)",
            body,
        )
        return candidates[-1] if candidates else None

    @staticmethod
    def _extract_revised_question(body: str) -> str | None:
        """Find the [REVISED]...[/REVISED] block, if any."""
        m = re.search(r"\[REVISED\]\s*(.+?)\s*\[/REVISED\]", body, re.DOTALL)
        return m.group(1).strip() if m else None


__all__ = [
    "BrainstormAgent",
    "FleshOutAgent",
    "IdeaSelectorAgent",
    "ResearchQuestionValidatorAgent",
]
