# Contract: librarian JSON output — delta for spec 006

**Base contract**: `specs/005-librarian-agent/contracts/librarian-json-output.md` — the full `LibrarianResult` JSON schema. **Unchanged** except for the one addition below.

**Module**: `src/llmxive/agents/librarian.py` — `LibrarianResult.to_dict()`

## The one new field: `math_classifier`

The top-level JSON gains exactly one new key, `math_classifier`, alongside the existing `relevance_judge`, `extracted_queries`, `per_query_hit_count`, `pdf_sample` audit fields:

```jsonc
{
  "schema_version": "1.0.0",
  "librarian_prompt_version": "1.6.0",          // bumped from 1.5.0 by this amendment
  "term_input": { "raw": "...", "normalized": "..." },
  "context": { "field": "mathematics", "idea_body_excerpt": "...", "target_n": 5 },
  "outcome": "success | success_after_expansion | exhausted | failed",
  "verified_citations": [ /* <VerifiedCitation>, unchanged shape; a theoremsearch-sourced
                             one has verification_log.backend == "theoremsearch" */ ],
  "verification_failures": [ /* unchanged */ ],
  "expansion": null | { /* unchanged */ },
  "pdf_sample": { /* unchanged */ },
  "relevance_judge": { /* unchanged */ },
  "extracted_queries": [ /* unchanged */ ],
  "per_query_hit_count": { /* unchanged */ },

  "math_classifier": {                          // NEW (spec 006)
    "invoked": true | false,                    // false  ⇔ field=="mathematics" trigger (classifier not called)
    "verdict": true | false | null,             // null   ⇔ not invoked, OR classifier call failed
    "error":   "<message>" | null               // non-null ⇔ classifier call failed
  },

  "started_at": "...", "ended_at": "...", "duration_seconds": 42.1,
  "cache_status": "miss | hit | refreshed_after_ttl"
}
```

### `math_classifier` value table

| Scenario | `invoked` | `verdict` | `error` |
|-|-|-|-|
| `field == "mathematics"` (TheoremSearch queried unconditionally; classifier skipped) | `false` | `null` | `null` |
| non-math field; classifier verdict served from the per-project cache | `true` | `true` / `false` | `null` |
| non-math field; classifier ran, returned a parseable verdict | `true` | `true` / `false` | `null` |
| non-math field; classifier ran, response unparseable (fail-open to non-math) | `true` | `false` | `null` |
| non-math field; classifier backend call failed (fail-open to non-math) | `true` | `null` | `"<exception message>"` |

(Note: a `verdict == false` from a successful-but-non-math classifier call is indistinguishable in the JSON from a `verdict == false` from an unparseable response — both are `{"invoked": true, "verdict": false, "error": null}`. The unparseable case is distinguished only by the stderr diagnostic. This is acceptable: downstream consumers only care "was TheoremSearch queried?" which is `invoked && verdict` OR `field == "mathematics"`.)

## Identifying TheoremSearch-sourced citations

A verified citation in `verified_citations` is identifiable as TheoremSearch-sourced by its `verification_log` recording the candidate's `backend == "theoremsearch"` (the verification log already records the candidate's backend in spec 005). Its `primary_pointer` is a normal arXiv short ID; its bibliographic info comes from the arXiv API (resolved via `ArxivClient.get_by_id`). Otherwise it is byte-for-byte the same shape as an arXiv-sourced verified citation.

## What is NOT changed

- No change to `verified_citations` / `verification_failures` / `expansion` / `pdf_sample` / `relevance_judge` / `extracted_queries` / `per_query_hit_count` shapes.
- No change to the verification chain (URL-resolves → title-overlap ≥0.7 → summary-grounding ≥0.5 → relevance judge).
- No change to `outcome` semantics, `cache_status` semantics, or the result-cache key (`sha256(normalized_term)`).
- `schema_version` stays `1.0.0` — the `math_classifier` addition is backward-compatible (a consumer that ignores unknown top-level keys is unaffected). `librarian_prompt_version` bumps to `1.6.0` (separate from `schema_version`; it tracks the prompt/behavior surface, and the new classifier LLM call is a behavior change → invalidates the result cache).

## Test obligations

- The cross-domain coverage test (9 fields) asserts every result has a `math_classifier` key with the correct shape; for `field == "mathematics"` it asserts `{"invoked": false, "verdict": null, "error": null}`; for other fields it asserts `invoked == true` and `verdict in (true, false)` (or `verdict is null` with a non-null `error` if the classifier happened to fail that run — tolerated).
- The PROJ-261 / PROJ-262 re-validation asserts the `math_classifier` field is present and that those (non-math) projects either had the classifier return `false` (so TheoremSearch wasn't queried — expected, they're CS/chemistry questions) — i.e. no behavior regression from the new field.
