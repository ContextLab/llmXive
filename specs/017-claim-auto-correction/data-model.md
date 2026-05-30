# Phase 1 Data Model: Authoritative-Fill

The fill layer is mostly **transient** (a fill attempt produces a corrected value + provenance that is written onto the existing spec-016 `Claim`). New dataclasses live in `src/llmxive/fill/models.py`; the persisted state is the spec-016 `Claim` (its `resolved_value`, `evidence`, `source_hash`).

## Entity: FetchedSource

A resolvable source whose text was actually retrieved by a channel. Produced by every channel client; consumed by extraction.

| Field | Type | Notes |
|-|-|-|
| `channel` | str | `oeis \| wikipedia \| wikidata \| paper \| theorem` |
| `source_id` | str | stable identifier: OEIS A-number, Wikidata Q-id, Wikipedia title, DOI/arXiv id |
| `url` | str | resolvable URL (e.g. `https://oeis.org/A002863`, article URL) |
| `title` | str \| null | human title |
| `text` | str | the fetched text the value must be located in (article extract, b-file lines, entity statements) |
| `authority` | int | channel authority rank (lower = higher authority; see conflict.py) |

**Validation**: `text` non-empty (an unreadable/empty source is discarded, never used for a fill); `url` must resolve (the channel only returns sources it fetched).

## Entity: FillProvenance

Recorded on a corrected claim so the value is traceable and re-checkable (FR-004). Stored inside the spec-016 `Claim.evidence` (a dict), so no schema change to the registry.

| Field | Type | Notes |
|-|-|-|
| `filled` | bool | true → this claim's value came from a fill |
| `value` | str | the corrected value, **located in** `source.text` |
| `source_id` | str | the chosen source's id |
| `url` | str | the chosen source's resolvable URL |
| `quote` | str | the supporting passage/number from the source text |
| `channel` | str | which channel supplied it |
| `conflicts` | list | competing `{value, source_id, url, channel}` from lower-authority channels (FR-008); empty if none |

Persisted shape (inside `Claim.evidence`):
```yaml
evidence:
  filled: true
  fill:
    value: "9988"
    source_id: "A002863"
    url: "https://oeis.org/A002863"
    quote: "13 9988"
    channel: "oeis"
    conflicts: []
```

## Entity: FillResult

The terminal outcome of one fill attempt (transient; drives the Verdict the resolver returns).

| Field | Type | Notes |
|-|-|-|
| `status` | enum | `filled \| blocked` |
| `value` | str \| null | the corrected value when `filled` |
| `provenance` | FillProvenance \| null | present when `filled` |
| `channels_tried` | list[str] | for observability/logging |
| `reason` | str | why blocked (no source found / value not present in any source) |

**Mapping to spec-016 Verdict**: `filled` → `Verdict(status=VERIFIED, value=<corrected>, evidence={filled:true, fill:{…}}, resolver="fill:<channel>")`; `blocked` → the original NEI/REFUTED Verdict is returned unchanged (claim stays blocked).

## Entity: Source Channel (behavioral)

A channel is a callable `search_and_fetch(subject_query, claim) -> list[FetchedSource]`. The registry (`channels/__init__.py`) holds the ordered channel list + the authority ranks. v1 routing:
- **numeric** claim → OEIS (if an A-number is discoverable from the claim/Wikipedia) + Wikipedia + paper (+ theorem if math-classified).
- **entity/definitional** claim → Wikidata + Wikipedia + paper.
- **magnitude/relational** → DEFERRED in v1 (no fill; stays blocked).

## State transitions (on the spec-016 Claim)

A claim entering the fill step is `NOT_ENOUGH_INFO` or `REFUTED` (from the check-only resolver). After a fill:
- **filled** → `VERIFIED`, `resolved_value = <corrected>`, `evidence.fill = {…}`, `source_hash` set from the fill source (so spec-016 reuse/invalidation applies); the citation is repaired in the rendered doc.
- **blocked** → unchanged (stays NEI/REFUTED → spec-016 renders the `[UNRESOLVED-CLAIM:]` marker + gate).

**Reuse/invalidation (FR-009)**: a filled claim is cached (grounding cache + the registry entry); reused across rounds/documents without re-searching; invalidated when the fill source's content hash changes (spec-016 `source_hash` mechanism, extended to fill sources).

## Validation rules (the safety invariants)

1. A `FillResult.filled` REQUIRES `number_substantiated(value, source.text)` is true (numeric) or the value is located in `source.text` (entity) — **no fill whose value is absent from fetched text** (FR-003 / SC-002).
2. A fill source MUST be resolvable (the channel fetched it); a non-resolvable/free-text reference is never a fill source.
3. An external fill MUST NOT override a receipt-backed internal result (FR-010): the resolver only attempts a fill on external NEI/REFUTED, never on a RESULT-kind claim.
4. v1 attempts fills only for `numeric` and `entity_fact` kinds; other kinds skip the fill (stay blocked) — never silently "filled" (FR-015).
