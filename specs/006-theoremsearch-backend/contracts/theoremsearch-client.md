# Contract: `TheoremSearchClient.search()`

**Module**: `src/llmxive/librarian/theoremsearch.py` (NEW)
**Consumed by**: `LibrarianAgent.invoke()` (via the `_theoremsearch_candidates(term)` helper in `src/llmxive/agents/librarian.py`)
**Peer of**: `SemanticScholarClient` (`search.py`), `ArxivClient` (`search.py`) — same role: a `Candidate`-producing backend client.

## Signature

```python
class TheoremSearchClient:
    API_URL = "https://api.theoremsearch.com/search"

    def __init__(self, *, min_interval_seconds: float = 2.0, arxiv_client: "ArxivClient | None" = None) -> None: ...

    def search(self, term: str, *, limit: int = 10) -> list[Candidate]: ...
```

- `min_interval_seconds`: self-imposed rate limit (TheoremSearch documents none). Same token-bucket / inter-request-sleep pattern as `ArxivClient` (`min_interval_seconds=5.0` there; 2.0 here because TheoremSearch is one call per librarian invocation, not per-query). Implementation may use a `threading.Lock` + last-call timestamp like `ArxivClient._wait_for_slot`.
- `arxiv_client`: the `ArxivClient` used to resolve arXiv IDs → full bibliographic records. `None` → construct a fresh one (but callers should pass the librarian's shared instance so its rate limiter is respected globally).

## Behavior

1. POST `{"query": term, "limit": limit}` to `API_URL` (JSON body, `Content-Type: application/json`), with a sane timeout (e.g. 30s). On HTTP error (non-2xx), network error, timeout, or non-JSON response → raise `TransientBackendError` (the existing `llmxive.backends.base.TransientBackendError`, or whatever the codebase uses for "this backend is unavailable; fall through"). **Do not** raise `PermanentBackendError` — a 4xx from TheoremSearch is still "treat it as down."
2. Parse `response.json()["theorems"]` (a list). If absent or not a list → raise `TransientBackendError`.
3. Sort the hits by `score` descending; iterate (the `limit` request param already bounds the count, but be defensive).
4. For each hit:
   - Read `hit["paper"]`. If `paper["source"] != "arXiv"` → **skip** (logged at debug — non-arXiv sources are Spec B / #114).
   - `raw_id = paper["paper_id"]`; `arxiv_id = re.sub(r"v\d+$", "", raw_id)`. If `arxiv_id` doesn't look like an arXiv ID (modern `\d{4}\.\d{4,5}` or old-style `[a-z\-]+(\.[A-Z]{2})?/\d{7}`) → skip (logged at debug).
   - `cand = arxiv_client.get_by_id(arxiv_id)`. If `None` → skip (logged at warning — "TheoremSearch hit's arXiv ID didn't resolve: <arxiv_id>").
   - Re-tag: `cand = dataclasses.replace(cand, backend="theoremsearch")` (keep `primary_pointer` = the resolver-normalized short ID, so dedup against an arXiv-search-sourced copy works).
   - Append `cand` to the result list, de-duplicating by `cand.primary_pointer` *within this call* (two hits pointing to the same paper → one `Candidate`).
5. Return the list (may be empty — zero usable arXiv hits is a normal outcome).

## Caller contract (`_theoremsearch_candidates` in `librarian.py`)

```python
def _theoremsearch_candidates(term: str, *, arxiv_client) -> list[Candidate]:
    try:
        return TheoremSearchClient(arxiv_client=arxiv_client).search(term)
    except TransientBackendError as exc:
        LOGGER.warning("[theoremsearch] backend unavailable; skipping: %s", exc)
        return []
```

→ the librarian **never aborts** because TheoremSearch is down (FR-A06).

## What this contract does NOT do

- It does not call any TheoremSearch endpoint other than `POST /search`.
- It does not consume the theorem `body`/`slogan`/`theorem_type` (Spec B / #114).
- It does not handle non-arXiv sources (Spec B / #114).
- It does not change the librarian's verification chain, dedup logic, or output schema (the `Candidate`s it returns flow through the existing pipeline unchanged).

## Test obligations (→ `tests/phase2/test_theoremsearch.py`)

- **Parser, recorded response** (no network): given a recorded `/search` JSON with a mix of arXiv and ProofWiki hits → returns only the arXiv ones as `Candidate(backend="theoremsearch", ...)`; ProofWiki hits skipped; version suffix stripped; two hits → same paper → one `Candidate`.
- **`get_by_id` returns None** → that hit produces no candidate (the rest still do).
- **Real-API smoke** (gated on network reachability): `TheoremSearchClient().search("sharp bound spectral gap random regular graphs", limit=5)` → returns ≥1 `Candidate` with `backend="theoremsearch"` and a resolving arXiv ID. (Skipped if the API is unreachable — documented skip reason, like the existing arXiv-429 handling.)
- **Forced-unreachable host** → `search()` raises `TransientBackendError`; `_theoremsearch_candidates` returns `[]`.
