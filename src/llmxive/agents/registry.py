"""Agent registry loader (T025).

Reads agents/registry.yaml, validates against contracts/agent-registry,
and exposes get(name) and list().
"""

from __future__ import annotations

from pathlib import Path

import yaml

from llmxive.contract_validate import validate
from llmxive.types import AgentRegistry, AgentRegistryEntry


def _registry_path() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent / "agents" / "registry.yaml"


def load(*, repo_root: Path | None = None) -> AgentRegistry:
    path = (repo_root / "agents" / "registry.yaml") if repo_root else _registry_path()
    if not path.exists():
        raise FileNotFoundError(f"agent registry not found at {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    validate("agent-registry", raw)
    return AgentRegistry.model_validate(raw)


def get(name: str, *, repo_root: Path | None = None) -> AgentRegistryEntry:
    reg = load(repo_root=repo_root)
    for agent in reg.agents:
        if agent.name == name:
            return agent
    raise KeyError(f"agent {name!r} not in registry at {_registry_path()}")


def list_names(*, repo_root: Path | None = None) -> list[str]:
    return [a.name for a in load(repo_root=repo_root).agents]


__all__ = ["load", "get", "list_names"]
