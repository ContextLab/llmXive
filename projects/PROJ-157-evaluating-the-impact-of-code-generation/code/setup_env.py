"""
setup_env.py
----------------
Deterministic environment setup script.

This script performs three actions:
1. Pins random seeds for the standard libraries used throughout the
   project (Python ``random``, ``numpy`` and, if available, ``torch``).
2. Retrieves the immutable Docker image digest for the deterministic
   image ``gcc:13.2-bullseye`` via the Docker Hub Registry HTTP API,
   handling the token authentication flow required by Docker Hub.
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
# 2. Retrieve Docker image digest via Docker Hub Registry API
# ----------------------------------------------------------------------
DOCKER_IMAGE = "gcc:13.2-bullseye"

def _fetch_auth_token(repository: str) -> str:
    """
    Obtain a Bearer token for accessing a public Docker Hub repository.

    Parameters
    ----------
    repository: str
        Repository name in the form ``library/gcc`` (no tag).

    Returns
    -------
    str
        The access token to be used in the Authorization header.

    Raises
    ------
    RuntimeError
        If the token cannot be retrieved.
    """
    token_url = (
        "https://auth.docker.io/token"
        "?service=registry.docker.io"
        f"&scope=repository:{repository}:pull"
    )
    log.debug("Requesting Docker Hub auth token for %s", repository)
    resp = requests.get(token_url, timeout=30)
    try:
        resp.raise_for_status()
    except Exception as exc:
        raise RuntimeError(f"Failed to obtain Docker Hub token: {exc}") from exc

    data = resp.json()
    token = data.get("token") or data.get("access_token")
    if not token:
        raise RuntimeError("Docker Hub token response missing token field")
    return token

def _fetch_docker_digest(image: str) -> str:
    """
    Retrieve the immutable digest for a public Docker image using the
    Docker Hub Registry HTTP API, handling token authentication.

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
    repo, tag = image.split(":")
    # Official images are under the ``library`` namespace.
    if "/" not in repo:
        repo = f"library/{repo}"
    manifest_url = f"https://registry-1.docker.io/v2/{repo}/manifests/{tag}"
    headers = {
        "Accept": "application/vnd.docker.distribution.manifest.v2+json"
    }
    # First obtain an auth token for the repository.
    token = _fetch_auth_token(repo)
    headers["Authorization"] = f"Bearer {token}"
    log.info("Requesting Docker manifest for %s", image)
    response = requests.get(manifest_url, headers=headers, timeout=30)
    try:
        response.raise_for_status()
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch manifest for {image}: {exc}") from exc

    digest = response.headers.get("Docker-Content-Digest")
    if not digest:
        raise RuntimeError(
            f"Docker-Content-Digest header missing in response for {image}"
        )
    return digest

try:
    docker_digest = _fetch_docker_digest(DOCKER_IMAGE)
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