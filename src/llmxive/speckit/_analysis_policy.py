"""Policy identity for reusable task analysis, including the code actually loaded."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from llmxive.speckit.slash_command import SlashCommandContext


def _deployed_source_root() -> Path:
    # Data checkouts may carry a frozen source copy while the runner imports a
    # separate platform. Hash the loaded package too, not just ctx's data root.
    return Path(__file__).resolve().parents[1]


def analysis_policy_fingerprint(ctx: SlashCommandContext) -> str:
    policy = {
        "model": ctx.default_model,
        "backend": ctx.default_backend.value,
        "fallbacks": [backend.value for backend in ctx.fallback_backends],
        "prompt_version": ctx.prompt_version,
        "flags": {key: value for key, value in os.environ.items()
                  if key.startswith("LLMXIVE_") and not any(
                      secret in key for secret in ("TOKEN", "SECRET", "KEY", "PASSWORD"))},
    }
    digest = hashlib.sha256(b"task-review-policy-v1\0")
    digest.update(json.dumps(policy, sort_keys=True).encode() + b"\0")
    deployed = _deployed_source_root()
    for path in sorted(deployed.rglob("*.py")):
        if path.is_file():
            digest.update(path.relative_to(deployed).as_posix().encode() + b"\0")
            digest.update(path.read_bytes() + b"\0")
    return digest.hexdigest()
