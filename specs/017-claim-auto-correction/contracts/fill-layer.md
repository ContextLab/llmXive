# Phase 1 Contracts: Authoritative-Fill Layer

Module-level contracts (Python library + pipeline). Each names the module, its public functions with signatures, and the behavioral guarantee a test asserts. Reused spec-016/librarian/grounding symbols are referenced, not redefined.

## `fill/models.py` — entities

```python
@dataclass(frozen=True) class FetchedSource: channel:str; source_id:str; url:str; title:str|None; text:str; authority:int
@dataclass(frozen=True) class FillProvenance: value:str; source_id:str; url:str; quote:str; channel:str; conflicts:list[dict]
@dataclass(frozen=True) class FillResult: status:str; value:str|None; provenance:FillProvenance|None; channels_tried:list[str]; reason:str
```
**Guarantees**: pure data; `FillResult.status in {"filled","blocked"}`; a `filled` result always has non-null `value` + `provenance`.

## `fill/subject_query.py` — derive the search subject (PURE + optional LLM)

```python
def subject_query(claim: Claim, *, backend=None, model=None, repo_root=None) -> str
def strip_asserted_value(raw_text: str, value: str | None) -> str   # PURE
```
**Guarantees**: `strip_asserted_value` removes the asserted value/number but keeps subject + qualifiers (pure, deterministic, testable offline); `subject_query` falls back to `strip_asserted_value` when no backend.

## `fill/channels/` — source channels (each → fetched, resolvable sources)

```python
# channels/__init__.py
AUTHORITY: dict[str, int]                      # oeis<wikidata<wikipedia<theorem<paper (lower = higher authority)
def channels_for(kind: ClaimKind, *, math: bool) -> list[Channel]   # v1 routing (numeric/entity only)
# each channel module exposes:
def search_and_fetch(query: str, claim: Claim, *, timeout: float = 30.0) -> list[FetchedSource]
# oeis.py also:
def fetch_bfile(a_number: str, *, timeout: float = 20.0) -> dict[int, int]   # {n: value} from b-file (REAL http)
def a_numbers_in(text: str) -> list[str]                                     # PURE: find A###### in text
```
**Guarantees**: each `search_and_fetch` returns only sources it actually fetched (non-empty `text`, resolvable `url`); a channel HTTP failure returns `[]` (never raises into the resolver — mirrors `_theoremsearch_candidates`); OEIS uses the **b-file** endpoint (search API is Cloudflare-blocked — research D1), so `fetch_bfile("A002863")[13] == 9988` (real-call); `papers.py`/`theorem.py` adapt librarian `Candidate`s to `FetchedSource` via `grounding.full_text.retrieve`.

## `fill/extract.py` — extract candidate value + present-in-source gate (the trust boundary)

```python
def extract_value(source: FetchedSource, claim: Claim, *, backend, model, repo_root) -> str | None
def present_in_source(value: str, source: FetchedSource, kind: ClaimKind) -> bool   # deterministic gate
```
**Guarantees**: `present_in_source` for numeric delegates to `grounding.service.number_substantiated(value, source.text)`; for entity it is a normalized located-in-text check; `extract_value` returns a candidate ONLY if it passes `present_in_source` (the LLM is a locator, never a source) — a value not in `source.text` yields `None` (FR-003 / SC-002).

## `fill/conflict.py` — channel-priority + record (FR-008, PURE)

```python
def choose(candidates: list[tuple[FetchedSource, str]]) -> tuple[FetchedSource, str, list[dict]]
```
**Guarantees**: given `(source, value)` pairs from multiple channels, returns the highest-authority source's value plus the `conflicts` list of the lower-authority disagreeing `{value, source_id, url, channel}`; never drops a conflict; deterministic by `AUTHORITY`.

## `fill/citation_repair.py` — repair the citation to the source (FR-007, PURE rewriter)

```python
def repair_citation(text: str, *, claim: Claim, provenance: FillProvenance) -> str
```
**Guarantees**: rewrites/annotates the citation adjacent to the claim's value so the doc cites the authoritative fill source (e.g. `(OEIS A002863, oeis.org/A002863)`); reuses `agents/citation_guard.py` occurrence regexes; idempotent; if no adjacent citation, appends an inline one; never touches unrelated prose.

## `fill/service.py` — orchestrator

```python
def fill_claim(claim: Claim, *, backend, model, repo_root) -> FillResult
```
**Guarantees**: runs subject_query → channels_for(kind) search_and_fetch → **cross-channel OEIS enrichment** (extract A-numbers from discovery channels' fetched text via `oeis.a_numbers_in`, fetch their b-files, add as higher-authority sources) → extract_value (with present-in-source gate) per source → conflict.choose → FillResult(filled, value, provenance) or FillResult(blocked, reason). The bounded channel list is the per-attempt budget (FR-011): each channel tried once, then blocked. Caches by (claim canonical, channel) via grounding cache. Only attempts numeric/entity kinds in v1; returns `blocked` for others. Never returns a `filled` value absent from a fetched source.

## Integration contracts (modifications)

- `claims/resolve.py::resolve_numeric_or_citation` + `resolve_entity_fact`: when `LLMXIVE_CLAIM_FILL=1` and the resolver would return `NOT_ENOUGH_INFO`/`REFUTED`, call `fill.service.fill_claim`; on `filled`, return `Verdict(VERIFIED, value=<corrected>, evidence={filled:true, fill:{…}}, resolver="fill:<channel>")`; on `blocked`, return the original Verdict unchanged. Never fill a RESULT-kind claim (FR-010).
- `claims/service.py::process_document`: after `render`, for each claim whose `evidence.filled` is true, call `fill.citation_repair.repair_citation` on the rendered text so the corrected value is cited to its fill source.
- `cli.py::run`: `os.environ.setdefault("LLMXIVE_CLAIM_FILL", "1")` (one line; mirrors `LLMXIVE_CLAIM_LAYER`).
