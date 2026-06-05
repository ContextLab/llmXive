"""PlanReviser + PaperPlanReviser — R2 for the plan convergence units (T056).

The plan stage edits MULTIPLE artifacts (plan.md + research.md + data-model.md
+ quickstart.md + contracts/*) instead of one spec.md, so these revisers use
a `updated_artifacts: {path: text}` map in the JSON contract rather than the
single `new_spec_md` field used by the spec revisers.

Both revisers share the same shape; the differences are:

* Reviser  ↦ system prompt              ↦ source spec key
* Planner  ↦ ``agents/prompts/planner.md`` ↦ ``specs/<feature>/spec.md``
* PaperPlanner ↦ ``agents/prompts/paper_planner.md`` ↦ ``paper/specs/<slug>/spec.md``

Overflow routing (FR-006): when the bundle exceeds the token budget, the
SOURCE spec (research or paper) + comments_block are routed through
``tools.summarize.summarize``. Plan artifacts themselves are NEVER
summarized — the reviser must see the full text it's editing.

Deterministic guards (artifact-set-complete, URL-reachability,
data-model↔contracts alignment, Constitution-Check) stay as a pre-filter
that runs BEFORE the panel — they are not the reviser's job. The reviser
addresses panel concerns that the deterministic guards couldn't catch
(methodology, spec_coverage, data_resources, plan_consistency lenses).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage
from llmxive.tools.summarize import summarize

from ..types import Concern, ConcernResponse
from ._reviser_response import (
    RESPONSE_FORMAT_BLOCK,
    build_concern_responses,
    parse_reviser_response,
)
from ._self_consistency import (
    invoke_reviser_backend,
    run_with_self_consistency,
)
from .spec_reviser import (
    _DEFAULT_INPUT_TOKEN_BUDGET,
    _approx_tokens,
)

# Artifact path-suffix patterns that mark "plan-stage" artifacts the reviser
# may edit. These match the 5 design docs the planner step produces.
_PLAN_ARTIFACT_SUFFIXES: tuple[str, ...] = (
    "plan.md",
    "research.md",
    "data-model.md",
    "quickstart.md",
)


def _is_plan_artifact(key: str, *, paper: bool) -> bool:
    """A key counts as a plan-stage artifact iff it ends in one of the 5
    design-doc names AND its side (paper vs research) matches the reviser."""
    is_paper_side = key.startswith("paper/") or "/paper/" in key
    if paper != is_paper_side:
        return False
    if "/contracts/" in key or key.startswith("contracts/"):
        return True
    return any(key.endswith(s) for s in _PLAN_ARTIFACT_SUFFIXES)


def _feature_dirs_of(valid_paths: set[str]) -> set[str]:
    """The feature dir(s) the existing plan artifacts live in.

    A NEW plan artifact is accepted only inside one of these dirs — so the
    reviser may add a ``contracts/<name>.schema.yaml`` next to the existing
    plan files, but never write to ``src/``, ``tests/``, or a different
    ``specs/NNN`` dir. For a ``.../specs/002-x/contracts/foo.schema.yaml`` path
    the feature dir is ``.../specs/002-x``; for ``.../specs/002-x/plan.md`` it
    is the file's parent, also ``.../specs/002-x``.
    """
    dirs: set[str] = set()
    for p in valid_paths:
        if "/contracts/" in p:
            dirs.add(p.split("/contracts/", 1)[0])
        elif "/" in p:
            dirs.add(p.rsplit("/", 1)[0])
    return dirs


def _is_source_spec(key: str, *, paper: bool) -> bool:
    """The spec.md that the plan is built FROM (research-side or paper-side
    depending on the reviser). NOT a plan artifact."""
    if paper:
        return (
            key.endswith("paper/spec.md")
            or ("paper/specs/" in key and key.endswith("spec.md"))
        )
    is_paper_side = key.startswith("paper/") or "/paper/" in key
    return (not is_paper_side) and key.endswith("spec.md")


class _AbstractPlanReviser:
    """Base implementation shared by PlanReviser + PaperPlanReviser.

    Subclasses set ``name``, ``_system_prompt_path``, and ``_is_paper_side``;
    everything else is shared.
    """

    name = "abstract_plan_reviser"
    _system_prompt_path = ""
    _is_paper_side = False

    def __init__(
        self,
        *,
        backend: Any,
        repo_root: Path,
        project_id: str,
        model: str | None = None,
        token_budget: int = _DEFAULT_INPUT_TOKEN_BUDGET,
        summarize_cache_dir: Path | None = None,
    ) -> None:
        self._backend = backend
        self._repo_root = Path(repo_root)
        self._project_id = project_id
        self._model = model
        self._token_budget = token_budget
        self._summarize_cache_dir = (
            Path(summarize_cache_dir)
            if summarize_cache_dir is not None
            else self._repo_root / ".llmxive" / "summarize_cache"
        )

    # --- public API ---------------------------------------------------------

    def revise(
        self, artifacts: dict[str, str], concerns: list[Concern]
    ) -> tuple[dict[str, str], list[ConcernResponse]]:
        plan_artifacts = self._extract_plan_artifacts(artifacts)
        if not plan_artifacts:
            raise ValueError(
                f"{type(self).__name__}.revise: no plan-stage artifacts "
                f"found in artifacts dict (keys={list(artifacts)!r}). "
                "Expected at least one of: "
                f"{', '.join(_PLAN_ARTIFACT_SUFFIXES)} or contracts/*."
            )
        source_spec = self._extract_source_spec(artifacts)
        constitution = artifacts.get("__constitution__", "")
        comments_block = artifacts.get("__comments_block__", "")

        # Overflow: source spec + comments may be large. Plan artifacts
        # (what we're editing) stay verbatim. Constitution stays verbatim
        # (it's small and load-bearing for every panel concern).
        approx_total = (
            sum(_approx_tokens(t) for t in plan_artifacts.values())
            + _approx_tokens(source_spec)
            + _approx_tokens(comments_block)
            + _approx_tokens(constitution)
        )
        if approx_total > self._token_budget:
            if source_spec:
                source_spec = summarize(
                    source_spec,
                    goal=(
                        "extract every FR/SC id verbatim, every constraint, "
                        "every named dataset, and the exact research question"
                    ),
                    model=self._model or "qwen3.5-122b",
                    token_budget=max(3_000, self._token_budget // 3),
                    cache_dir=self._summarize_cache_dir,
                )
            if comments_block:
                comments_block = summarize(
                    comments_block,
                    goal=(
                        "extract every reviewer concern, requested change, "
                        "and the FR/SC ids each refers to"
                    ),
                    model=self._model or "qwen3.5-122b",
                    token_budget=max(1_500, self._token_budget // 6),
                    cache_dir=self._summarize_cache_dir,
                )

        def _run_pass(
            extra_instructions: str = "",
        ) -> tuple[dict[str, str], list[ConcernResponse]]:
            messages = self._build_messages(
                plan_artifacts=plan_artifacts,
                source_spec=source_spec,
                constitution=constitution,
                comments_block=comments_block,
                concerns=concerns,
                extra_instructions=extra_instructions,
            )
            response_text = self._call_backend(messages)
            updates, responses = self._parse_response(
                response_text, concerns, list(plan_artifacts.keys())
            )
            new_artifacts = dict(artifacts)
            new_artifacts.update(updates)
            return new_artifacts, responses

        # FR-011 self-consistency pass: first pass + ONE corrective re-pass.
        return run_with_self_consistency(
            backend=self._backend,
            model=self._model,
            repo_root=self._repo_root,
            concerns=concerns,
            first_pass=_run_pass(),
            redo=_run_pass,
            stage_label="plan",  # spec 020 FR-001: planning → references-only + strip/smooth
        )

    # --- internal helpers ---------------------------------------------------

    def _extract_plan_artifacts(self, artifacts: dict[str, str]) -> dict[str, str]:
        return {
            k: v
            for k, v in artifacts.items()
            if _is_plan_artifact(k, paper=self._is_paper_side)
        }

    def _extract_source_spec(self, artifacts: dict[str, str]) -> str:
        for k, v in artifacts.items():
            if _is_source_spec(k, paper=self._is_paper_side):
                return v
        return ""

    def _build_messages(
        self,
        *,
        plan_artifacts: dict[str, str],
        source_spec: str,
        constitution: str,
        comments_block: str,
        concerns: list[Concern],
        extra_instructions: str = "",
    ) -> list[ChatMessage]:
        system_text = render_prompt(
            self._system_prompt_path,
            {"project_id": self._project_id},
            repo_root=self._repo_root,
        )
        plan_block = "\n\n".join(
            f"## {path}\n\n{text}" for path, text in plan_artifacts.items()
        )
        concern_list = "\n".join(
            f"- [concern {c.id}] severity={c.severity.value} reviewer={c.reviewer} "
            f"location={c.location or '(unstated)'}\n  {c.text}"
            for c in concerns
        ) or "(no panel concerns this round)"
        artifact_paths = "\n".join(f"- {p}" for p in plan_artifacts)

        user_text = (
            "# Source spec (what the plan must satisfy)\n\n"
            f"{source_spec or '(no source spec supplied)'}\n\n"
            "# Constitution (per-project SSoT principles — FR-030)\n\n"
            f"{constitution or '(no constitution supplied)'}\n\n"
            "# Current plan-stage artifacts\n\n"
            f"{plan_block}\n\n"
            "# Panel concerns to address (R1 output)\n\n"
            f"{concern_list}\n\n"
            "# Recent reviewer / personality comments\n\n"
            f"{comments_block or '(no recent comments)'}\n\n"
            "# Task\n\n"
            "Revise the plan-stage artifacts to address every panel concern. "
            "Emit one artifact block per file you change; omit unchanged files. "
            "The paths you may emit MUST match these inputs exactly:\n"
            f"{artifact_paths}\n\n"
            "- If a concern is rooted in the source spec (not the plan), "
            "describe what's needed in `response` and set `what_changed` to "
            "'spec-root cause; flagged for kickback'.\n\n"
            + RESPONSE_FORMAT_BLOCK
        )

        # Trustworthiness Phase 2: feed canonical verified facts back to the
        # plan reviser. Pure addition — empty when no facts exist.
        from llmxive.claims.verified_facts_prompt import (
            load_verified_facts,
            project_dir_for,
            render_verified_facts_block,
        )
        artifact_hint = next(iter(plan_artifacts), None)
        verified_facts_block = render_verified_facts_block(
            load_verified_facts(
                project_dir_for(
                    self._repo_root,
                    self._project_id,
                    artifact_path=artifact_hint,
                )
            )
        )
        if verified_facts_block:
            user_text += "\n\n" + verified_facts_block

        user_text += extra_instructions

        return [
            ChatMessage(role="system", content=system_text),
            ChatMessage(role="user", content=user_text),
        ]

    def _call_backend(self, messages: list[ChatMessage]) -> str:
        return invoke_reviser_backend(self, messages)

    def _parse_response(
        self,
        response_text: str,
        concerns: list[Concern],
        valid_paths: list[str],
    ) -> tuple[dict[str, str], list[ConcernResponse]]:
        try:
            raw_updates, responses_raw = parse_reviser_response(
                response_text, expected_artifacts=valid_paths
            )
        except RuntimeError as exc:
            raise RuntimeError(
                f"{type(self).__name__}: backend did not return parseable JSON: "
                f"{exc}; first 200 chars: {response_text[:200]!r}"
            ) from exc

        if not raw_updates:
            raise RuntimeError(
                f"{type(self).__name__}: response JSON has no usable "
                "'updated_artifacts' map; got: 0 artifacts"
            )
        valid_set = set(valid_paths)
        # The reviser may legitimately ADD a NEW plan artifact (e.g. a
        # contracts/<name>.schema.yaml a panel concern asked for) — not only
        # edit the pre-existing files. Allow a path that is itself a plan-stage
        # artifact AND lives inside the SAME feature dir as the existing plan
        # artifacts. Writes OUTSIDE that dir (src/, tests/, the source spec, a
        # different specs/NNN dir) are still rejected. Restricting to only the
        # pre-existing file set wrongly hard-failed a valid revision and
        # escalated the whole plan panel to a human (PROJ-552 composite-score).
        feature_dirs = _feature_dirs_of(valid_set)
        updates: dict[str, str] = {}
        rejected: list[str] = []
        for path, text in raw_updates.items():
            if not isinstance(text, str):
                rejected.append(str(path))
            elif path in valid_set:
                updates[path] = text
            elif _is_plan_artifact(path, paper=self._is_paper_side) and any(
                path.startswith(d + "/") for d in feature_dirs
            ):
                updates[path] = text  # NEW plan artifact within the feature dir
            else:
                rejected.append(str(path))
        if rejected:
            # Honest reporting — don't silently drop attempts to write
            # outside the declared plan-artifact set / feature dir.
            raise RuntimeError(
                f"{type(self).__name__}: response tried to write artifacts "
                f"outside the plan set: {rejected!r}. Valid: {sorted(valid_set)!r}"
            )

        responses = build_concern_responses(responses_raw, concerns)
        return updates, responses


class PlanReviser(_AbstractPlanReviser):
    """R2 reviser for the research-plan convergence unit (FR-027)."""

    name = "planner"
    _system_prompt_path = "agents/prompts/planner.md"
    _is_paper_side = False


class PaperPlanReviser(_AbstractPlanReviser):
    """R2 reviser for the paper-plan convergence unit (FR-028)."""

    name = "paper_planner"
    _system_prompt_path = "agents/prompts/paper_planner.md"
    _is_paper_side = True


__all__ = ["PaperPlanReviser", "PlanReviser"]
