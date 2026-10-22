"""
setup_env.py
----------------
Deterministic environment setup script.

This script performs three actions:
1. Pins random seeds for the standard libraries used throughout the
   project (Python ``random``, ``numpy`` and, if available, ``torch``).
2. Pulls the deterministic Docker image ``gcc:13.2-bullseye`` and records
   its immutable content digest.
3. Writes a JSON configuration file ``data/env_config.json`` that captures
   the seed values and Docker image information for downstream reproducibility
   checks (as required by task T000).

The script is intended to be run as a stand‑alone entry point:
    python code/setup_env.py

It writes its output using the ``llmxive_toolkit.paths`` helpers, which
automatically create the target directories.
"""

import json
import random
from pathlib import Path

import numpy as np

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# 1. Pin random seeds
# ----------------------------------------------------------------------
# A single, project‑wide seed is defined.  All libraries that rely on a
# random number generator are seeded using this value.
PROJECT_SEED = 20231027

random.seed(PROJECT_SEED)
np.random.seed(PROJECT_SEED)

# ``torch`` is optional – the project may not require it at this stage.
try:
    import torch

    torch.manual_seed(PROJECT_SEED)
    # Ensure deterministic behaviour on CPU/GPU (even though we run CPU‑only)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch_available = True
except Exception as exc:  # pragma: no cover – torch may be missing
    log.warning("Torch not available; skipping torch seed configuration: %s", exc)
    torch_available = False

# ----------------------------------------------------------------------
# 2. Pull deterministic Docker image and obtain its content digest
# ----------------------------------------------------------------------
# The plan specifies the exact Docker image tag to use.  We retrieve the
# immutable digest (e.g. ``sha256:<hash>``) via the Docker SDK.  The digest
# is recorded so that later verification steps can compare it against the
# value stored in ``plan.md``.
DOCKER_IMAGE = "gcc:13.2-bullseye"

try:
    import docker

    client = docker.from_env()
    log.info("Pulling Docker image %s …", DOCKER_IMAGE)
    image = client.images.pull(DOCKER_IMAGE)
    # ``RepoDigests`` is a list like
    # ["gcc@sha256:<digest>", "gcc:13.2-bullseye@sha256:<digest>"]
    repo_digests = image.attrs.get("RepoDigests", [])
    if not repo_digests:
        raise RuntimeError("No RepoDigests found for image")
    # Prefer the entry that includes the tag we asked for.
    digest_entry = next(
        (d for d in repo_digests if DOCKER_IMAGE.split(":")[0] in d),
        repo_digests[0],
    )
    # Extract the ``sha256:…`` part.
    docker_digest = digest_entry.split("@")[1]
    log.info("Docker image digest: %s", docker_digest)
except Exception as exc:
    # The task explicitly forbids silent fall‑backs; we raise to surface the
    # problem to the execution harness.
    log.error("Failed to obtain Docker image digest: %s", exc)
    raise

# ----------------------------------------------------------------------
# 3. Write environment configuration JSON
# ----------------------------------------------------------------------
env_config = {
    "seed": PROJECT_SEED,
    "libraries": {
        "random": PROJECT_SEED,
        "numpy": PROJECT_SEED,
        "torch": PROJECT_SEED if torch_available else None,
    },
    "docker_image": DOCKER_IMAGE,
    "docker_digest": docker_digest,
}

out_path = paths.data("env_config.json")
out_path.parent.mkdir(parents=True, exist_ok=True)
with out_path.open("w", encoding="utf-8") as fp:
    json.dump(env_config, fp, indent=2, sort_keys=True)

log.info("Wrote environment configuration to %s", out_path)
