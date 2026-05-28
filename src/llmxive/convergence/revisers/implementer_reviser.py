"""ImplementerReviser — R2 for the research-implement convergence unit (T058).

Implements the new ``implementer`` revise behavior the design SSoT calls for
(spec 015 step 6 + discrepancy #1):

* Takes the CURRENT code/data artifacts + the 8-panel's R1 concerns and
  produces revised code artifacts + a per-concern change-log. The existing
  ``implementer.py`` Mode-A authoring (pick next ``[ ]`` task + write its
  artifact) stays in place — that drives the FIRST pass before R1. This
  reviser drives the in-loop revisions that today don't exist (the panel
  flags concerns → today's code immediately kicks back to an earlier stage).
* Filesystem re-verification (issue #49): after the LLM proposes edits,
  the reviser runs :func:`verify_task_assertions` against the revised
  tasks artifact + the project's filesystem. Any task whose deliverable
  is still missing post-revise → an explicit "<unverified-by-filesystem>"
  entry is added to the engine's response log so R3 sees it (no silent
  acceptance of "I edited the file" claims).

Overflow routing (FR-006): code/data artifacts can be many MB. The
reviser routes BIG artifacts (over a per-artifact size threshold) through
``tools.summarize`` for the LLM's view, but the FULL contents are still
written back when the LLM emits edits — summarization is for the
*prompt*, not the output.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage
from llmxive.tools.summarize import summarize

from ..types import Concern, ConcernResponse
from .spec_reviser import (
    _DEFAULT_INPUT_TOKEN_BUDGET,
    _approx_tokens,
    _strip_json_fences,
)

# Per-artifact threshold above which we summarize for the prompt. This is
# a heuristic — a 4k-token file is small enough to send in full; bigger
# files get summarized to fit in the bundle.
_PER_ARTIFACT_SUMMARIZE_THRESHOLD_TOKENS = 4_000


# --- code-artifact discovery ---------------------------------------------


def _is_code_artifact(key: str) -> bool:
    """A repo-relative key that looks like project code / data / tests.

    Heuristic: anything under ``code/``, ``data/``, ``tests/``, or ``src/``
    in the project tree is code-side. Excludes spec/tasks/plan markdown
    (those have their own revisers) and dot-prefixed artifacts.
    """
    if key.startswith(".") or "/." in key:
        return False
    if "/paper/" in key or key.startswith("paper/"):
        return False
    if key.endswith((".md",)) and "/code/" not in key and not key.startswith("code/"):
        # markdowns under code/ ARE code-side (READMEs etc.); pure-doc
        # markdowns are not.
        return False
    parts_starts = ("code/", "data/", "tests/", "src/", "scripts/")
    return any(key.startswith(p) or f"/{p}" in key for p in parts_starts)


# --- filesystem re-verification (#49) ------------------------------------


_TASK_LINE_RE = re.compile(
    r"^- \[(?P<status>[ Xx])\]\s+(?P<id>T\d+[a-z]?)(?P<rest>.*)$",
    re.MULTILINE,
)
# Loose path detector: a file-ish token with a directory separator AND a
# known extension OR a leading "tests/"/"src/"/"code/"/"data/" segment.
_FILELIKE_RE = re.compile(
    r"`([A-Za-z0-9_./\-]+(?:\.(?:py|md|txt|csv|json|yaml|yml|sh|ipynb|cpp|c|h|hpp|js|ts|tsx|toml|cfg))[A-Za-z0-9_./\-]*)`"
)


def verify_task_assertions(
    tasks_text: str, *, repo_root: Path
) -> list[tuple[str, str]]:
    """Walk the completed (``[X]``) tasks in ``tasks_text`` and check whether
    every backtick-quoted file path each task names actually exists on
    disk under ``repo_root``.

    Returns a list of ``(task_id, missing_path)`` for unverified items —
    paths the task claims to have created/edited that don't exist. Empty
    list = every checked-off task's filesystem assertions hold.

    This is the implementation of discrepancy #49 the spec calls out:
    today the implementer marks tasks ``[X]`` without proving the
    deliverable landed; the panel's `filesystem_hygiene` lens + this
    helper close that gap.
    """
    repo = Path(repo_root)
    unverified: list[tuple[str, str]] = []
    for m in _TASK_LINE_RE.finditer(tasks_text):
        if m.group("status") not in ("X", "x"):
            continue
        task_id = m.group("id")
        rest = m.group("rest")
        for pm in _FILELIKE_RE.finditer(rest):
            cand = pm.group(1)
            # Strip a leading slash or `./` for repo-relative resolution.
            cand_clean = cand.lstrip("/").removeprefix("./")
            if not (repo / cand_clean).exists():
                unverified.append((task_id, cand_clean))
    return unverified


# --- ImplementerReviser ---------------------------------------------------


class ImplementerReviser:
    """R2 reviser for the research-implement convergence unit (FR-027)."""

    name = "implementer"
    _system_prompt_path = "agents/prompts/implementer_research.md"

    def __init__(
        self,
        *,
        backend: Any,
        repo_root: Path,
        project_id: str,
        project_root: Path | None = None,
        model: str | None = None,
        token_budget: int = _DEFAULT_INPUT_TOKEN_BUDGET,
        summarize_cache_dir: Path | None = None,
    ) -> None:
        self._backend = backend
        # ``repo_root`` is for prompt-file lookup (``agents/prompts/*.md``)
        # and lives in the llmXive repo. ``project_root`` is where the
        # implementer's deliverables actually land — for in-repo projects
        # under ``projects/<id>/`` it differs from the repo root. Tests
        # let these diverge so prompt loading uses the real repo while
        # filesystem assertions check a tmp_path tree.
        self._repo_root = Path(repo_root)
        self._project_root = Path(project_root) if project_root is not None else self._repo_root
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
        code_artifacts = {k: v for k, v in artifacts.items() if _is_code_artifact(k)}
        if not code_artifacts:
            raise ValueError(
                "ImplementerReviser.revise: no code-side artifacts found "
                f"(keys={list(artifacts)!r}). Expected at least one path "
                "under code/, data/, tests/, src/, or scripts/."
            )
        tasks_text = artifacts.get("__tasks_md__", "")
        spec_text = artifacts.get("__spec_md__", "")
        plan_text = artifacts.get("__plan_md__", "")
        constitution = artifacts.get("__constitution__", "")
        analyze_report = artifacts.get("__analyze_report__", "")
        comments_block = artifacts.get("__comments_block__", "")

        # Per-artifact summarization for the PROMPT view. The reviser only
        # SEES summaries for big files, but it can still write FULL new
        # contents (the LLM is instructed below to emit complete file
        # bodies for each edited path).
        view_artifacts = {
            k: self._artifact_view(k, v) for k, v in code_artifacts.items()
        }

        # Outer-bundle overflow: the non-code context can balloon too.
        approx_total = (
            sum(_approx_tokens(t) for t in view_artifacts.values())
            + _approx_tokens(tasks_text)
            + _approx_tokens(spec_text)
            + _approx_tokens(plan_text)
            + _approx_tokens(constitution)
            + _approx_tokens(analyze_report)
            + _approx_tokens(comments_block)
        )
        if approx_total > self._token_budget:
            if spec_text:
                spec_text = summarize(
                    spec_text,
                    goal="preserve every FR/SC id verbatim + every constraint",
                    model=self._model or "qwen3.5-122b",
                    token_budget=max(2_000, self._token_budget // 6),
                    cache_dir=self._summarize_cache_dir,
                )
            if plan_text:
                plan_text = summarize(
                    plan_text,
                    goal="preserve every plan element + every method choice",
                    model=self._model or "qwen3.5-122b",
                    token_budget=max(2_000, self._token_budget // 6),
                    cache_dir=self._summarize_cache_dir,
                )
            if comments_block:
                comments_block = summarize(
                    comments_block,
                    goal="extract every reviewer concern + every requested change",
                    model=self._model or "qwen3.5-122b",
                    token_budget=max(1_500, self._token_budget // 8),
                    cache_dir=self._summarize_cache_dir,
                )

        messages = self._build_messages(
            view_artifacts=view_artifacts,
            tasks_text=tasks_text,
            spec_text=spec_text,
            plan_text=plan_text,
            constitution=constitution,
            analyze_report=analyze_report,
            comments_block=comments_block,
            concerns=concerns,
        )
        response_text = self._call_backend(messages)
        updates, responses = self._parse_response(
            response_text, concerns, valid_paths=list(code_artifacts.keys()),
        )

        updated = dict(artifacts)
        updated.update(updates)

        # Filesystem re-verification (#49): if the engine passed a tasks_md
        # AND a real project root resolves, check that every [X] task's
        # named paths exist post-revise. Unverified items become synthetic
        # responses so R3 sees the failure.
        if tasks_text and self._project_root.exists():
            unverified = verify_task_assertions(
                tasks_text, repo_root=self._project_root,
            )
            for task_id, missing_path in unverified:
                responses.append(
                    ConcernResponse(
                        concern_id=f"<filesystem-unverified:{task_id}>",
                        response=(
                            f"Task {task_id} is marked complete but the "
                            f"deliverable `{missing_path}` does not exist "
                            f"on disk under {self._project_root}."
                        ),
                        what_changed="<filesystem-unverified>",
                        artifacts_changed=[],
                    )
                )

        return updated, responses

    # --- internal helpers ---------------------------------------------------

    def _artifact_view(self, key: str, text: str) -> str:
        """Return a possibly-summarized view of the artifact for the prompt.
        Big files get summarized; small files stay verbatim."""
        if _approx_tokens(text) <= _PER_ARTIFACT_SUMMARIZE_THRESHOLD_TOKENS:
            return text
        return summarize(
            text,
            goal=(
                "preserve every function/class signature verbatim, every "
                "imported symbol, every public API, and the exact location "
                "of TODO/FIXME/XXX comments"
            ),
            model=self._model or "qwen3.5-122b",
            token_budget=_PER_ARTIFACT_SUMMARIZE_THRESHOLD_TOKENS,
            cache_dir=self._summarize_cache_dir,
        )

    def _build_messages(
        self,
        *,
        view_artifacts: dict[str, str],
        tasks_text: str,
        spec_text: str,
        plan_text: str,
        constitution: str,
        analyze_report: str,
        comments_block: str,
        concerns: list[Concern],
    ) -> list[ChatMessage]:
        system_text = render_prompt(
            self._system_prompt_path,
            {"project_id": self._project_id},
            repo_root=self._repo_root,
        )
        concern_list = "\n".join(
            f"- [concern {c.id}] severity={c.severity.value} reviewer={c.reviewer} "
            f"location={c.location or '(unstated)'}\n  {c.text}"
            for c in concerns
        ) or "(no panel concerns this round)"
        artifact_block = "\n\n".join(
            f"## {path}\n\n```\n{text}\n```"
            for path, text in view_artifacts.items()
        )
        artifact_paths = "\n".join(f"- {p}" for p in view_artifacts)

        user_text = (
            "# Spec (constraints the code must satisfy)\n\n"
            f"{spec_text or '(no spec supplied)'}\n\n"
            "# Plan (methodology + plan elements)\n\n"
            f"{plan_text or '(no plan supplied)'}\n\n"
            "# Tasks (what the implementer has been doing)\n\n"
            f"{tasks_text or '(no tasks supplied)'}\n\n"
            "# Constitution (FR-030)\n\n"
            f"{constitution or '(no constitution supplied)'}\n\n"
            "# Current code/data artifacts (your editable scope)\n\n"
            f"{artifact_block or '(no artifacts)'}\n\n"
            "# Analyze report (current code-quality scan)\n\n"
            f"{analyze_report or '(no analyze report)'}\n\n"
            "# Panel concerns to address (R1 output)\n\n"
            f"{concern_list}\n\n"
            "# Recent reviewer / personality comments\n\n"
            f"{comments_block or '(no recent comments)'}\n\n"
            "# Task\n\n"
            "Return a single JSON document with this exact shape:\n\n"
            "```json\n"
            "{\n"
            '  "updated_artifacts": {\n'
            '    "<artifact_path>": "<the FULL new file contents>"\n'
            "  },\n"
            '  "responses": [\n'
            '    {"concern_id": "<id>",\n'
            '     "response": "<how you addressed this concern>",\n'
            '     "what_changed": "<concrete diff summary + which files>",\n'
            '     "artifacts_changed": ["<artifact paths actually edited>"]}\n'
            "  ]\n"
            "}\n"
            "```\n\n"
            "Rules:\n"
            "- `updated_artifacts` MUST contain the FULL new contents of "
            "  every file you change (not patches). Omit unchanged files.\n"
            "- The paths you may emit MUST match these inputs exactly:\n"
            f"{artifact_paths}\n"
            "- Every panel concern MUST have one entry in `responses`.\n"
            "- Code-class concerns are fixed in-loop. Methodology- or "
            "  science-class concerns are described in `response` with "
            "  `what_changed` tagged 'methodology-root cause; flagged "
            "  for kickback' (the engine will route them to the right "
            "  earlier stage).\n"
            "- Real-only (Constitution V): do NOT introduce mocks, fake "
            "  fallbacks, or paid-only model calls. If a concern would "
            "  require those, leave the code unchanged and explain why "
            "  in `response`.\n"
        )

        return [
            ChatMessage(role="system", content=system_text),
            ChatMessage(role="user", content=user_text),
        ]

    def _call_backend(self, messages: list[ChatMessage]) -> str:
        if self._model is not None:
            response = self._backend.chat(messages, model=self._model)
        else:
            response = self._backend.chat(messages)
        return getattr(response, "text", "") or ""

    def _parse_response(
        self,
        response_text: str,
        concerns: list[Concern],
        valid_paths: list[str],
    ) -> tuple[dict[str, str], list[ConcernResponse]]:
        payload = _strip_json_fences(response_text)
        try:
            obj = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"ImplementerReviser: backend did not return parseable JSON: "
                f"{exc}; first 200 chars: {response_text[:200]!r}"
            ) from exc

        raw_updates = obj.get("updated_artifacts")
        if not isinstance(raw_updates, dict):
            raise RuntimeError(
                "ImplementerReviser: response JSON has no usable "
                f"'updated_artifacts' map; got: {type(raw_updates).__name__}"
            )
        valid_set = set(valid_paths)
        updates: dict[str, str] = {}
        rejected: list[str] = []
        for path, text in raw_updates.items():
            if path in valid_set and isinstance(text, str):
                updates[path] = text
            else:
                rejected.append(str(path))
        if rejected:
            raise RuntimeError(
                "ImplementerReviser: response tried to write artifacts "
                f"outside the declared code set: {rejected!r}. "
                f"Valid: {sorted(valid_set)!r}"
            )

        responses_raw = obj.get("responses") or []
        by_id: dict[str, dict[str, Any]] = {}
        for r in responses_raw:
            if isinstance(r, dict) and isinstance(r.get("concern_id"), str):
                by_id[r["concern_id"]] = r

        responses: list[ConcernResponse] = []
        for c in concerns:
            r = by_id.get(c.id)
            if r is None:
                responses.append(
                    ConcernResponse(
                        concern_id=c.id,
                        response="<missing>",
                        what_changed="reviser produced no response for this concern",
                        artifacts_changed=[],
                    )
                )
                continue
            responses.append(
                ConcernResponse(
                    concern_id=c.id,
                    response=str(r.get("response", "")).strip() or "<empty>",
                    what_changed=str(r.get("what_changed", "")).strip() or "<empty>",
                    artifacts_changed=[
                        str(x) for x in (r.get("artifacts_changed") or [])
                    ],
                )
            )
        return updates, responses


__all__ = ["ImplementerReviser", "verify_task_assertions"]
