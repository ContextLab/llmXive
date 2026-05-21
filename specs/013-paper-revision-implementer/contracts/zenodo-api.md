# Contract — Zenodo REST API integration

## Base URLs

| Environment | Base URL | DOI prefix | Token source |
|-|-|-|-|
| Production | `https://zenodo.org/api` | `10.5281/zenodo.<n>` | `~/.config/llmxive/credentials.toml::[zenodo].api_token` or `ZENODO_API_TOKEN` |
| Sandbox (tests) | `https://sandbox.zenodo.org/api` | `10.5072/zenodo.<n>` | `~/.config/llmxive/credentials.toml::[zenodo_sandbox].api_token` or `ZENODO_SANDBOX_API_TOKEN` |

## Authentication

All requests carry `Authorization: Bearer <token>`. Tokens require
scopes `deposit:write` + `deposit:actions`.

## Operations

### O1 — Create a new deposition with a pre-reserved DOI

```http
POST {BASE}/deposit/depositions
Content-Type: application/json

{
  "metadata": {
    "upload_type": "publication",
    "publication_type": "article",
    "title": "<paper title>",
    "creators": [{"name": "<Last, First>", "affiliation": "<institution>"}, ...],
    "description": "<paper abstract>",
    "publication_date": "YYYY-MM-DD",
    "keywords": ["<kw1>", ...],
    "related_identifiers": [
      {"relation": "isSupplementTo", "identifier": "<github project URL>", "resource_type": "software"}
    ],
    "notes": "Reviewed and revised by llmXive. See: <dashboard project URL>",
    "prereserve_doi": true
  }
}
```

**Response 201**:
```json
{
  "id": 1234567,
  "doi_url": "https://doi.org/...",
  "metadata": {
    "prereserve_doi": {"doi": "10.5281/zenodo.1234567", "recid": 1234567}
  },
  "links": {
    "bucket": "https://zenodo.org/api/files/<uuid>",
    "publish": "https://zenodo.org/api/deposit/depositions/1234567/actions/publish",
    ...
  }
}
```

**Capture**: `id`, `metadata.prereserve_doi.doi`, `links.bucket`,
`links.publish`.

### O2 — Upload the PDF

```http
PUT {bucket}/main.pdf
Content-Type: application/octet-stream

<binary PDF bytes>
```

**Response 200**: file metadata. No usable IDs to capture.

### O3 — Publish the deposition

```http
POST {BASE}/deposit/depositions/{id}/actions/publish
```

**Response 202** (Accepted): deposition is now publicly visible and the
DOI is registered with DataCite.

```json
{
  "id": 1234567,
  "doi": "10.5281/zenodo.1234567",
  "doi_url": "https://doi.org/10.5281/zenodo.1234567",
  "conceptdoi": "10.5281/zenodo.1234566",
  "state": "done",
  ...
}
```

**Capture**: `doi`, `doi_url`, `conceptdoi`.

### O4 — Create a new version of an existing deposition (re-publication)

```http
POST {BASE}/deposit/depositions/{existing_id}/actions/newversion
```

**Response 201**:
```json
{
  "id": <old_id>,
  "links": {
    "latest_draft": "https://zenodo.org/api/deposit/depositions/<new_id>"
  }
}
```

**Capture**: `<new_id>` from `links.latest_draft`. Then fetch the new
draft via `GET {BASE}/deposit/depositions/<new_id>` to read the new
`prereserve_doi` and `bucket`. Upload + publish as O2 + O3.

## Client module location

`src/llmxive/pipeline/zenodo.py`:

```python
class ZenodoClient:
    def __init__(self, *, sandbox: bool = False):
        self.base = "https://sandbox.zenodo.org/api" if sandbox else "https://zenodo.org/api"
        self.token = load_zenodo_token(sandbox=sandbox)

    def create_deposition(self, metadata: ZenodoMetadata) -> Deposition: ...
    def upload_file(self, bucket: str, name: str, content: bytes) -> None: ...
    def publish(self, deposition_id: int) -> PublishedDeposition: ...
    def new_version(self, deposition_id: int) -> Deposition: ...
```

Each method raises `ZenodoAPIError(status_code, message)` on non-2xx
responses. The publisher agent catches this and applies the FR-030 retry
policy.

## Real-call test

`tests/real_call/test_publisher_zenodo_sandbox.py` (gated on
`LLMXIVE_REAL_TESTS=1`):

1. Build a minimal fixture project at `paper_accepted` with a 1-page PDF.
2. Run the publisher pointed at Zenodo Sandbox.
3. Assert: the DOI returned begins with `10.5072/zenodo.`, the
   `publication.yaml` is written, `metadata.json::doi` is mirrored,
   the project transitions to `posted`, and an `HTTP HEAD` on the DOI
   URL returns 200/302 (DOI resolves).

## Cost & rate-limit notes

- Free for research use.
- Documented rate limit: 5,000 requests/hour per token (more than
  enough for llmXive's expected volume of <100 publications/month).
- No per-deposition fee; no upload-size fee under 50 GB.
