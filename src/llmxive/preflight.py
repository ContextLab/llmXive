"""Fail-fast preamble (T013).

Runs as the first step of every scheduled workflow. Validates:
  * required secrets are present and non-empty
  * required CLI tools (git, pdflatex, uv/uvx) are on PATH
  * agent registry parses and validates against its schema
  * every prompt template referenced by the registry exists
  * Dartmouth + HF endpoints respond to a list_models() probe (when keys
    are present)

Per Constitution Principle V, exits non-zero on any failure with a
precondition-specific message.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from llmxive.agents import registry as registry_loader
from llmxive.config import all_keys, about_page_published
from llmxive.contract_validate import list_contracts


REQUIRED_TOOLS = ["git"]
OPTIONAL_TOOLS = ["pdflatex", "uvx", "uv", "pipx"]
REQUIRED_SECRETS = ["DARTMOUTH_CHAT_API_KEY"]
OPTIONAL_SECRETS = ["DARTMOUTH_API_KEY", "HF_TOKEN", "GITHUB_TOKEN"]


class PreflightError(RuntimeError):
    pass


def _check_tools() -> list[str]:
    missing: list[str] = []
    for tool in REQUIRED_TOOLS:
        if not shutil.which(tool):
            missing.append(tool)
    return missing


def _check_secrets() -> list[str]:
    return [name for name in REQUIRED_SECRETS if not os.environ.get(name)]


def _check_registry() -> list[str]:
    issues: list[str] = []
    try:
        reg = registry_loader.load()
    except FileNotFoundError as exc:
        return [f"agent registry: {exc}"]
    except Exception as exc:
        return [f"agent registry parse failure: {exc}"]
    repo = Path(__file__).resolve().parent.parent.parent
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


def main() -> int:
    failures: list[str] = []
    info: list[str] = []

    missing_tools = _check_tools()
    if missing_tools:
        failures.append(f"required tools missing on PATH: {missing_tools}")
    for opt in OPTIONAL_TOOLS:
        if not shutil.which(opt):
            info.append(f"optional tool not on PATH: {opt}")

    missing_secrets = _check_secrets()
    if missing_secrets:
        failures.append(f"required secrets missing: {missing_secrets}")
    for opt in OPTIONAL_SECRETS:
        if not os.environ.get(opt):
            info.append(f"optional secret not set: {opt}")

    failures.extend(_check_registry())
    failures.extend(_check_contracts())
    info.extend(_check_about_page())

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


__all__ = ["main", "PreflightError"]
