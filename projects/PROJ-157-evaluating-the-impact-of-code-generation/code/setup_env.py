"""
setup_env.py
----------------
Deterministic environment setup script.

This script performs three actions:
1. Pins random seeds for the standard libraries used throughout the
   project (Python ``random``, ``numpy`` and, if available, ``torch``).
2. Retrieves the immutable Docker image digest for the deterministic
   image ``gcc:13.2-bullseye`` using the local Docker daemon (via the
   Docker SDK). This avoids reliance on the Docker Hub Registry API,
   which may return 404 for certain multi‑arch manifests.
3. Writes a JSON configuration file ``data/env_config.json`` that
   captures the seed values and Docker image information for downstream
   reproducibility checks (as required by task T000).

The script is intended to be run as a stand‑alone entry point:
    python code/setup_env.py

It writes its output using the ``llmxive_toolkit.paths`` helpers,
which automatically create the target directories.
"""

import json
import random
from pathlib import Path

import numpy as np
import requests
import docker

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# 1. Pin random seeds
# ----------------------------------------------------------------------
PROJECT_SEED = 20231027

random.seed(PROJECT_SEED)
np.random.seed(PROJECT_SEED)

# ``torch`` is optional – the project may not require it at this stage.
try:
    import torch

    torch.manual_seed(PROJECT_SEED)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch_available = True
except Exception as exc:  # pragma: no cover – torch may be missing
    log.warning("Torch not available; skipping torch seed configuration: %s", exc)
    torch_available = False

# ----------------------------------------------------------------------
# 2. Retrieve Docker image digest via local Docker daemon
# ----------------------------------------------------------------------
DOCKER_IMAGE = "gcc:13.2-bullseye"

def _fetch_docker_digest_via_docker(image: str) -> str:
    """
    Retrieve the immutable digest for a Docker image using the local Docker
    daemon. This pulls the image if it is not already present.

    Parameters
    ----------
    image: str
        Image name with tag, e.g. ``gcc:13.2-bullseye``.

    Returns
    -------
    str
        The digest string (e.g. ``sha256:<hash>``).

    Raises
    ------
    RuntimeError
        If the digest cannot be obtained.
    """
    client = docker.from_env()
    repository, tag = image.split(":")
    try:
        # Pull the image to ensure it is present locally.
        log.info("Pulling Docker image %s", image)
        client.images.pull(repository, tag=tag)
    except Exception as exc:
        raise RuntimeError(f"Failed to pull Docker image {image}: {exc}") from exc

    try:
        image_obj = client.images.get(f"{repository}:{tag}")
    except Exception as exc:
        raise RuntimeError(f"Failed to get Docker image {image} after pull: {exc}") from exc

    # RepoDigests is a list like ["gcc@sha256:abcd..."]
    repo_digests = image_obj.attrs.get("RepoDigests")
    if not repo_digests:
        raise RuntimeError(f"No RepoDigests found for image {image}")
    # Take the first digest entry.
    digest_entry = repo_digests[0]
    # The entry format is "<repository>@sha256:<hash>"
    if "@" not in digest_entry:
        raise RuntimeError(f"Unexpected RepoDigest format: {digest_entry}")
    _, digest = digest_entry.split("@", 1)
    return digest

try:
    docker_digest = _fetch_docker_digest_via_docker(DOCKER_IMAGE)
    log.info("Docker image digest retrieved: %s", docker_digest)
except Exception as exc:
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