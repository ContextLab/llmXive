"""
setup_env.py
----------------
Deterministic environment setup script.

This script performs three actions:
1. Pins random seeds for the standard libraries used throughout the
   project (Python ``random``, ``numpy`` and, if available, ``torch``).
2. Retrieves the immutable Docker image digest for the deterministic
   image ``gcc:13.2``. It first attempts to obtain the digest
   via the local Docker daemon (Docker SDK). If the Docker daemon is
   unavailable (e.g., in CI environments without Docker), it falls back
   to the Docker Hub Registry HTTP API.
3. Writes a JSON configuration file ``data/env_config.json`` that
   captures the seed values and Docker image information for downstream
   reproducibility checks.
"""

import json
import random
from pathlib import Path

import numpy as np
import requests
import docker

from llmxive_toolkit import paths, get_logger
from code.seed_config import PROJECT_SEED, pin_seeds

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Docker Image Configuration
# ----------------------------------------------------------------------
DOCKER_IMAGE = "gcc:13.2"

def _fetch_docker_digest_via_docker(image: str) -> str:
    client = docker.from_env()
    repository, tag = image.split(":")
    try:
        log.info("Pulling Docker image %s", image)
        client.images.pull(repository, tag=tag)
    except Exception as exc:
        raise RuntimeError(f"Failed to pull Docker image {image}: {exc}") from exc

    try:
        image_obj = client.images.get(f"{repository}:{tag}")
    except Exception as exc:
        raise RuntimeError(f"Failed to get Docker image {image} after pull: {exc}") from exc

    repo_digests = image_obj.attrs.get("RepoDigests")
    if not repo_digests:
        raise RuntimeError(f"No RepoDigests found for image {image}")
    
    digest_entry = repo_digests[0]
    if "@" not in digest_entry:
        raise RuntimeError(f"Unexpected RepoDigest format: {digest_entry}")
    _, digest = digest_entry.split("@", 1)
    return digest

def _fetch_docker_digest_via_registry(image: str) -> str:
    repository, tag = image.split(":")
    token_url = (
        "https://auth.docker.io/token"
        f"?service=registry.docker.io&scope=repository:library/{repository}:pull"
    )
    log.info("Requesting Docker Hub auth token for %s", repository)
    token_resp = requests.get(token_url, timeout=30)
    if not token_resp.ok:
        raise RuntimeError(
            f"Failed to obtain Docker Hub token: {token_resp.status_code} {token_resp.reason}"
        )
    token = token_resp.json().get("token")
    if not token:
        raise RuntimeError("Docker Hub token response missing 'token' field")

    manifest_url = f"https://registry-1.docker.io/v2/library/{repository}/manifests/{tag}"
    headers = {
        "Accept": "application/vnd.docker.distribution.manifest.v2+json",
        "Authorization": f"Bearer {token}",
    }
    log.info("Fetching Docker manifest via registry API: %s", manifest_url)
    manifest_resp = requests.get(manifest_url, headers=headers, timeout=30)
    if not manifest_resp.ok:
        raise RuntimeError(
            f"Failed to fetch manifest for {image} from Docker Hub: "
            f"{manifest_resp.status_code} {manifest_resp.reason}"
        )
    digest = manifest_resp.headers.get("Docker-Content-Digest")
    if not digest:
        raise RuntimeError(
            f"Docker-Content-Digest header missing in response for {image}"
        )
    return digest

def main():
    # 1. Pin random seeds
    pin_seeds()

    # torch is optional
    torch_available = False
    try:
        import torch
        torch.manual_seed(PROJECT_SEED)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        torch_available = True
    except Exception as exc:
        log.warning("Torch not available; skipping torch seed configuration: %s", exc)

    # 2. Retrieve Docker image digest
    try:
        docker_digest = _fetch_docker_digest_via_docker(DOCKER_IMAGE)
        log.info("Docker image digest retrieved via local daemon: %s", docker_digest)
    except Exception as exc_docker:
        log.warning("Docker SDK method failed (%s). Falling back to registry API.", exc_docker)
        try:
            docker_digest = _fetch_docker_digest_via_registry(DOCKER_IMAGE)
            log.info("Docker image digest retrieved via registry API: %s", docker_digest)
        except Exception as exc_registry:
            log.error("Failed to obtain Docker image digest via both methods: %s", exc_registry)
            raise RuntimeError("Cannot determine Docker image digest; aborting environment setup.") from exc_registry

    # 3. Write environment configuration JSON
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

if __name__ == "__main__":
    main()