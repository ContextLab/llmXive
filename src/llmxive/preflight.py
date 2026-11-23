"""Fail-fast preamble (T013).

Runs as the first step of every scheduled workflow. Validates:
  * at least one usable model provider is configured: the Dartmouth key, or
    both HF_TOKEN and LLMXIVE_HF_BILL_TO
  * required CLI tools (git, pdflatex, uv/uvx) are on PATH
  * agent registry parses and validates against its schema
  * every prompt template referenced by the registry exists
  * Dartmouth + HF endpoints respond to a list_models() probe (when keys
    are present)

It then prints a model-selection report (``selection_report``): which backends
are reachable, the funded allowance, the leaderboard's freshness and coverage,
and the top candidate for each requirement profile. The report is built from one
``runtime_snapshot()`` (catalog, leaderboard and ledger reads only; no chat
request, no reservation, no ledger write) and never prints a rating, a token or
a bill-to id.

Per Constitution Principle V, exits non-zero on any failure with a
precondition-specific message.
"""

from __future__ import annotations

import os
import shutil
import sys

from llmxive import credentials as cred_mod
from llmxive.agents import registry as registry_loader
from llmxive.config import about_page_published, all_keys
from llmxive.config import repo_root as _repo_root
from llmxive.contract_validate import list_contracts
from llmxive.model_selection.policy import FUNDED_POLICY, FundedPolicy
from llmxive.model_selection.profiles import PROFILES, build_requirement
from llmxive.model_selection.select import select
from llmxive.model_selection.snapshot import runtime_snapshot
from llmxive.model_selection.strength import repo_of
from llmxive.model_selection.types import (
    CallBudget,
    ModelUnavailable,
    RuntimeSnapshot,
    Track,
    worst_case_usd,
)

REQUIRED_TOOLS = ["git"]
OPTIONAL_TOOLS = ["pdflatex", "uvx", "uv", "pipx"]
OPTIONAL_SECRETS = [
    "DARTMOUTH_API_KEY",
    "GITHUB_TOKEN",
    "LLMXIVE_HF_BILL_TO",
    "LLMXIVE_FUNDED_LEDGER_ANCHOR",
]

#: Nominal per-call budget used only to rank candidates and price them for display.
_REPORT_BUDGET = CallBudget(8_000, 4_096)


class PreflightError(RuntimeError):
    pass


def _check_tools() -> list[str]:
    missing: list[str] = []
    for tool in REQUIRED_TOOLS:
        if not shutil.which(tool):
            missing.append(tool)
    return missing


def _dartmouth_configured() -> tuple[bool, list[str]]:
    """Dartmouth key via env -> credentials file. Second item: problems found."""
    if os.environ.get(cred_mod.DARTMOUTH_KEY_NAME):
        return True, []
    try:
        if cred_mod.load_dartmouth_key(prompt_if_missing=False):
            return True, []
    except PermissionError as exc:
        return False, [str(exc)]
    return False, []


def _hf_configured() -> tuple[bool, list[str]]:
    """Hugging Face pair: a token (env or Keychain) AND the bill-to variable.
    Second item: the names of whichever half is missing (never values)."""
    missing = []
    if not cred_mod.load_hf_token():
        missing.append("HF_TOKEN")
    if not os.environ.get("LLMXIVE_HF_BILL_TO", "").strip():
        missing.append("LLMXIVE_HF_BILL_TO")
    return not missing, missing


def _check_secrets() -> tuple[list[str], list[str]]:
    """At least one usable model provider is required: the Dartmouth key, or the
    Hugging Face pair (``HF_TOKEN`` + ``LLMXIVE_HF_BILL_TO``). Returns
    ``(failures, info)``; messages carry names only, never values."""
    dartmouth, problems = _dartmouth_configured()
    hf, hf_missing = _hf_configured()
    if not dartmouth and not hf:
        detail = f" ({'; '.join(problems)})" if problems else ""
        hf_detail = f"; Hugging Face is missing {hf_missing}" if len(hf_missing) < 2 else ""
        return [
            "no usable model provider: set DARTMOUTH_CHAT_API_KEY (env or credentials "
            f"file){detail}, or both HF_TOKEN and LLMXIVE_HF_BILL_TO{hf_detail}"
        ], []
    if dartmouth and not hf:
        return [], [f"providers: dartmouth configured; huggingface not configured (missing {hf_missing})"]
    if hf and not dartmouth:
        return [], ["providers: huggingface configured; dartmouth not configured (DARTMOUTH_CHAT_API_KEY unset)"]
    return [], ["providers: dartmouth and huggingface configured"]


def _check_registry() -> list[str]:
    issues: list[str] = []
    try:
        reg = registry_loader.load()
    except FileNotFoundError as exc:
        return [f"agent registry: {exc}"]
    except Exception as exc:
        return [f"agent registry parse failure: {exc}"]
    repo = _repo_root()
    for agent in reg.agents:
        prompt = repo / agent.prompt_path
        if not prompt.exists():
            issues.append(f"agent {agent.name}: prompt missing at {agent.prompt_path}")
    return issues


def _check_contracts() -> list[str]:
    try:
        list_contracts()
    except Exception as exc:
        return [f"contracts dir unreadable: {exc}"]
    return []


def _check_about_page() -> list[str]:
    """Soft check — warn (return as info, do not fail) when about page
    has not yet published thresholds. T130 publishes them."""
    info: list[str] = []
    for key in all_keys():
        if not about_page_published(key):
            info.append(f"config {key}: using default (about page not yet authoritative)")
    return info


def _source_of(snap: RuntimeSnapshot, component: str) -> str:
    prov = snap.sources.get(component)
    return prov.source if prov is not None else "unavailable"


def _leaderboard_line(snap: RuntimeSnapshot) -> str:
    covered: dict[Track, set[str]] = {"reasoning": set(), "coding": set()}
    published = []
    for model_id, scores in snap.scores.items():
        for track in covered:
            score = scores.for_track(track)
            if score is not None:
                covered[track].add(repo_of(model_id))
                published.append(score.publish_date)
    latest = max(published).isoformat() if published else "n/a"
    return (
        f"leaderboard: {_source_of(snap, 'leaderboard')}, published {latest}, "
        f"reasoning {len(covered['reasoning'])} models, coding {len(covered['coding'])} models"
    )


def selection_report(
    snap: RuntimeSnapshot, *, funded_policy: FundedPolicy | None = None
) -> list[str]:
    """Lines describing what a run would use: backend reachability, funded
    allowance, leaderboard freshness/coverage and each profile's top candidate.

    Pure: reads only ``snap``. Prints model ids, counts, dates and dollar amounts,
    never a leaderboard rating."""
    fpol = funded_policy if funded_policy is not None else FUNDED_POLICY
    lines = [
        f"backends: dartmouth={_source_of(snap, 'catalog')} "
        f"huggingface={_source_of(snap, 'hf_catalog')} local={_source_of(snap, 'local')}"
    ]
    fund = snap.funded
    if fund is None:
        lines.append("funded allowance: unavailable")
    else:
        lines.append(
            f"funded allowance: ${fund.monthly_usd:.2f}/month, spent ${fund.spent_month_usd:.2f} "
            f"this month, ${fund.available_usd:.2f} available now ({fund.epoch})"
        )
    lines.append(_leaderboard_line(snap))
    for name, prof in PROFILES.items():
        label = f"top candidate [{name}] {prof.track}/{prof.strength}"
        try:
            chain = select(build_requirement(name, _REPORT_BUDGET), snap, funded_policy=fpol)
        except ModelUnavailable as exc:
            reason = " ".join(str(exc).split())[:120]
            lines.append(f"{label}: none — {reason}")
            continue
        top = chain.candidates[0]
        worst = worst_case_usd(top.pricing, _REPORT_BUDGET)
        cost = f"${worst:.4f}" if worst is not None else "unknown"
        lines.append(
            f"{label}: {top.model_ref.model_id} "
            f"({top.model_ref.backend}, {top.cost_class}, worst case {cost})"
        )
    return lines


def main() -> int:
    failures: list[str] = []
    info: list[str] = []

    missing_tools = _check_tools()
    if missing_tools:
        failures.append(f"required tools missing on PATH: {missing_tools}")
    for opt in OPTIONAL_TOOLS:
        if not shutil.which(opt):
            info.append(f"optional tool not on PATH: {opt}")

    secret_failures, secret_info = _check_secrets()
    failures.extend(secret_failures)
    info.extend(secret_info)
    for opt in OPTIONAL_SECRETS:
        if not os.environ.get(opt):
            info.append(f"optional secret not set: {opt}")

    failures.extend(_check_registry())
    failures.extend(_check_contracts())
    info.extend(_check_about_page())
    if not failures:  # fail fast (FR-024): never spend network time on a run that cannot start
        try:
            info.extend(selection_report(runtime_snapshot()))
        except Exception as exc:  # informational: never change preflight's outcome
            info.append(f"selection report unavailable: {type(exc).__name__}")

    for line in info:
        print(f"[preflight] info: {line}")
    if failures:
        for line in failures:
            print(f"[preflight] FAIL: {line}", file=sys.stderr)
        return 1
    print("[preflight] OK — ready to run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["PreflightError", "main", "selection_report"]
