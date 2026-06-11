"""Zenodo REST API client for paper publication (spec 013 / FR-025..FR-031).

Implements the four operations the publisher agent needs:

  O1  create_deposition(metadata)     — POST /deposit/depositions
  O2  upload_file(bucket, name, bytes)— PUT to bucket URL
  O3  publish(deposition_id)          — POST /actions/publish (DOI activates)
  O4  new_version(deposition_id)      — POST /actions/newversion (FR-027)

Contract: specs/013-paper-revision-implementer/contracts/zenodo-api.md
Authentication: `llmxive.credentials.load_zenodo_token(sandbox=...)`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests  # type: ignore[import-untyped]  # no stubs; types-requests not installed

from llmxive.credentials import load_zenodo_token

PRODUCTION_BASE = "https://zenodo.org/api"
SANDBOX_BASE = "https://sandbox.zenodo.org/api"


class ZenodoAPIError(RuntimeError):
    """Raised on any non-2xx response from Zenodo. Carries the status
    code and the API's error message so the publisher's retry/back-off
    logic (FR-030) can decide whether to retry."""

    def __init__(self, status_code: int, message: str):
        super().__init__(f"Zenodo API error {status_code}: {message}")
        self.status_code = status_code
        self.message = message


@dataclass(frozen=True)
class Deposition:
    """A Zenodo deposition (may be unpublished draft or published)."""

    deposition_id: int
    doi: str                 # pre-reserved DOI; final after publish()
    bucket_url: str          # URL for file uploads
    publish_url: str         # URL to POST to for publishing
    raw: dict[str, Any]      # full response body for debug


@dataclass(frozen=True)
class PublishedDeposition:
    """Result of publish(): the deposition is now live and DOI active."""

    deposition_id: int
    doi: str
    doi_url: str
    concept_doi: str | None
    raw: dict[str, Any]


class ZenodoClient:
    """Stateless HTTP client. Token resolution happens once at init.

    Usage:
        client = ZenodoClient(sandbox=True)
        dep = client.create_deposition({"metadata": {...}})
        client.upload_file(dep.bucket_url, "main.pdf", pdf_bytes)
        pub = client.publish(dep.deposition_id)
    """

    def __init__(self, *, sandbox: bool = False, timeout: float = 60.0):
        self.sandbox = sandbox
        self.base = SANDBOX_BASE if sandbox else PRODUCTION_BASE
        self.token = load_zenodo_token(sandbox=sandbox)
        self.timeout = timeout

    def _headers(self, *, json_body: bool = True) -> dict[str, str]:
        h = {"Authorization": f"Bearer {self.token}"}
        if json_body:
            h["Content-Type"] = "application/json"
        return h

    def _raise_for_status(self, r: requests.Response) -> None:
        if 200 <= r.status_code < 300:
            return
        try:
            body = r.json()
            msg = body.get("message") or body
        except Exception:
            msg = r.text[:500]
        raise ZenodoAPIError(r.status_code, str(msg))

    def create_deposition(self, metadata: dict[str, Any]) -> Deposition:
        """O1 — Create a draft deposition with a pre-reserved DOI.

        `metadata` MUST follow Zenodo's schema; at minimum it should
        contain `metadata.title`, `metadata.upload_type`,
        `metadata.creators`, `metadata.publication_date`, and
        `metadata.prereserve_doi: true` (added if missing).
        """
        body = {"metadata": dict(metadata.get("metadata", metadata))}
        body["metadata"].setdefault("prereserve_doi", True)
        r = requests.post(
            f"{self.base}/deposit/depositions",
            headers=self._headers(),
            json=body,
            timeout=self.timeout,
        )
        self._raise_for_status(r)
        data = r.json()
        prereserve = (data.get("metadata") or {}).get("prereserve_doi") or {}
        doi = prereserve.get("doi") or ""
        links = data.get("links") or {}
        return Deposition(
            deposition_id=int(data["id"]),
            doi=doi,
            bucket_url=links.get("bucket", ""),
            publish_url=links.get("publish", ""),
            raw=data,
        )

    def upload_file(self, bucket_url: str, name: str, content: bytes) -> None:
        """O2 — Upload `content` to `bucket_url/<name>` (PUT).

        Zenodo's newer file API uses the bucket URL pattern. The legacy
        files-as-form-data API is intentionally unused here for clarity.
        """
        if not bucket_url:
            raise ZenodoAPIError(0, "empty bucket_url; call create_deposition first")
        r = requests.put(
            f"{bucket_url.rstrip('/')}/{name}",
            headers={"Authorization": f"Bearer {self.token}"},
            data=content,
            timeout=self.timeout,
        )
        self._raise_for_status(r)

    def publish(self, deposition_id: int) -> PublishedDeposition:
        """O3 — Publish a draft deposition. After this returns, the DOI
        is registered with DataCite and the deposition is publicly
        visible."""
        r = requests.post(
            f"{self.base}/deposit/depositions/{deposition_id}/actions/publish",
            headers=self._headers(json_body=False),
            timeout=self.timeout,
        )
        self._raise_for_status(r)
        data = r.json()
        return PublishedDeposition(
            deposition_id=int(data["id"]),
            doi=data.get("doi", ""),
            doi_url=data.get("doi_url") or f"https://doi.org/{data.get('doi', '')}",
            concept_doi=data.get("conceptdoi"),
            raw=data,
        )

    def new_version(self, deposition_id: int) -> Deposition:
        """O4 — Create a new VERSION of an existing published deposition.
        Returns the new draft (different deposition_id) with a fresh
        pre-reserved DOI. Upload the revised PDF + call publish() on
        the new id to register the new version. The original DOI keeps
        resolving to the prior PDF."""
        r = requests.post(
            f"{self.base}/deposit/depositions/{deposition_id}/actions/newversion",
            headers=self._headers(json_body=False),
            timeout=self.timeout,
        )
        self._raise_for_status(r)
        data = r.json()
        latest_draft = ((data.get("links") or {}).get("latest_draft", ""))
        if not latest_draft:
            raise ZenodoAPIError(
                r.status_code, "newversion response missing links.latest_draft"
            )
        # Fetch the new draft to get its bucket + publish_url + prereserve_doi.
        new_id = int(latest_draft.rstrip("/").rsplit("/", 1)[-1])
        r2 = requests.get(
            f"{self.base}/deposit/depositions/{new_id}",
            headers=self._headers(json_body=False),
            timeout=self.timeout,
        )
        self._raise_for_status(r2)
        d2 = r2.json()
        prereserve = (d2.get("metadata") or {}).get("prereserve_doi") or {}
        links = d2.get("links") or {}
        return Deposition(
            deposition_id=new_id,
            doi=prereserve.get("doi") or "",
            bucket_url=links.get("bucket", ""),
            publish_url=links.get("publish", ""),
            raw=d2,
        )

    def get_deposition(self, deposition_id: int) -> dict[str, Any]:
        """Fetch a deposition's raw record (draft or published).

        Used by the publisher's resume path (spec 023 / FR-020
        idempotence): a crash between ``publish()`` and the local state
        write must NOT mint a second DOI — the recovery ledger's
        deposition is fetched and inspected (``submitted`` → already
        published; reuse its DOI) instead of creating a new one."""
        r = requests.get(
            f"{self.base}/deposit/depositions/{deposition_id}",
            headers=self._headers(json_body=False),
            timeout=self.timeout,
        )
        self._raise_for_status(r)
        return r.json()

    def delete_draft(self, deposition_id: int) -> None:
        """Convenience: delete an unpublished draft (e.g., during tests).
        Zenodo prohibits deleting published depositions; this is a no-op
        on publishables and raises if Zenodo refuses."""
        r = requests.delete(
            f"{self.base}/deposit/depositions/{deposition_id}",
            headers=self._headers(json_body=False),
            timeout=self.timeout,
        )
        self._raise_for_status(r)
