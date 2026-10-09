"""Explicit HF pilot operations; credentials come only from CI env or Keychain."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys

import requests
from huggingface_hub import HfApi

ORG = "contextlab"
GROUP = "6ac8defed831a06784773cfd"
REPO = "contextlab/llmxive-artifacts"


def token() -> str:
    value = os.environ.get("HF_TOKEN", "").strip()
    if value:
        return value
    if sys.platform == "darwin":
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-s",
                "llmxive-huggingface",
                "-a",
                "jeremyrmanning",
                "-w",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    raise RuntimeError(
        "Set HF_TOKEN from a repository secret or use the llmxive-huggingface Keychain item"
    )


def request(method: str, path: str, **kwargs):
    response = requests.request(
        method,
        "https://huggingface.co" + path,
        headers={"Authorization": "Bearer " + token()},
        timeout=30,
        **kwargs,
    )
    if not response.ok:
        # Never dump request headers, credentials, or provider error payloads.
        raise RuntimeError(f"HF request failed with HTTP {response.status_code}")
    return response.json()


def cpu_probe() -> dict:
    """One bounded job, no retries, public ports, or credentials in its container."""
    program = (
        "import hashlib,json; "
        "values=[sum(__import__('math').gcd(k,n)==1 for k in range(1,n+1)) for n in range(1,101)]; "
        "assert sum(values)==3044; "
        "print(json.dumps({'probe':'totient-1-through-100','sum':sum(values),"
        "'sha256':hashlib.sha256(json.dumps(values).encode()).hexdigest()}))"
    )
    return request(
        "POST",
        f"/api/jobs/{ORG}",
        json={
            "dockerImage": "python:3.11-slim",
            "command": ["python", "-c", program],
            "flavor": "cpu-basic",
            "timeoutSeconds": 120,
            "attempts": 1,
            "resourceGroupId": GROUP,
            "labels": {"project": "llmxive", "purpose": "pilot"},
        },
    )


def storage_probe() -> dict:
    api = HfApi(token=token())
    info = api.repo_info(REPO, repo_type="dataset")
    if not info.private:
        raise RuntimeError("Pilot storage must remain private")
    data = json.dumps(
        {"probe": "llmxive-storage-roundtrip", "schema_version": 1}, sort_keys=True
    ).encode()
    commit = api.upload_file(
        path_or_fileobj=data,
        path_in_repo="pilot/storage-probe.json",
        repo_id=REPO,
        repo_type="dataset",
        commit_message="Verify private pilot artifact storage",
    )
    url = f"https://huggingface.co/datasets/{REPO}/resolve/{commit.oid}/pilot/storage-probe.json"
    downloaded = requests.get(url, headers={"Authorization": "Bearer " + token()}, timeout=30)
    if downloaded.status_code != 200 or downloaded.content != data:
        raise RuntimeError("Private storage round trip did not preserve bytes")
    anonymous = requests.get(url, timeout=30)
    if anonymous.status_code not in (401, 403, 404):
        raise RuntimeError(
            "Private artifact unexpectedly accessible or anonymous check inconclusive"
        )
    return {
        "repo": REPO,
        "private": True,
        "revision": commit.oid,
        "sha256": hashlib.sha256(data).hexdigest(),
        "anonymous_status": anonymous.status_code,
    }


def inference_probe() -> dict:
    """Small explicit alternate-model check, billed only to the pilot group."""
    model = "moonshotai/Kimi-K3:together"
    response = requests.post(
        "https://router.huggingface.co/v1/chat/completions",
        headers={"Authorization": "Bearer " + token(), "X-HF-Bill-To": GROUP},
        json={
            "model": model,
            "messages": [
                {"role": "user", "content": 'Return only this JSON object: {"hf_pilot": "ok"}.'}
            ],
            "max_tokens": 256,
            "stream": False,
        },
        timeout=90,
    )
    if not response.ok:
        raise RuntimeError(f"HF inference failed with HTTP {response.status_code}")
    result = response.json()
    content = result["choices"][0]["message"].get("content") or ""
    if not content.strip():
        raise RuntimeError("HF model returned no usable text")
    if json.loads(content) != {"hf_pilot": "ok"}:
        raise RuntimeError("HF model did not satisfy the probe response contract")
    return {
        "requested_model": model,
        "model": result.get("model"),
        "usage": result.get("usage"),
        "content": content,
        "resource_group": GROUP,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation", choices=["storage-probe", "cpu-probe", "inference-probe", "job-status"]
    )
    parser.add_argument("--job-id")
    args = parser.parse_args()
    if args.operation == "storage-probe":
        result = storage_probe()
    elif args.operation == "inference-probe":
        result = inference_probe()
    elif args.operation == "cpu-probe":
        job = cpu_probe()
        result = {k: job.get(k) for k in ("id", "status", "resourceGroupId", "timeout", "flavor")}
    else:
        if not args.job_id or not args.job_id.isalnum():
            parser.error("job-status requires an alphanumeric --job-id")
        job = request("GET", f"/api/jobs/{ORG}/{args.job_id}")
        result = {
            k: job.get(k)
            for k in ("id", "status", "resourceGroupId", "durations", "timeout", "flavor")
        }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # SDK exceptions can contain server payloads. Print only deliberate errors.
        print(str(exc) if type(exc) is RuntimeError else type(exc).__name__, file=sys.stderr)
        raise SystemExit(1) from None
