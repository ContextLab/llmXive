# Contract: Librarian JSON output schema

**Module**: `src/llmxive/agents/librarian.py` (returned by `LibrarianAgent.handle_response`)
**Consumed by**: `flesh_out`'s rewired path, `reference_validator`'s rewired logic, `tests/phase1/citation_resolver.py` shim, future paper-side agents per FR-022
**Schema base**: data-model.md E5 (LibrarianResult)

## Top-level JSON shape

```json
{
  "schema_version": "1.0.0",
  "librarian_prompt_version": "1.0.0",
  "term_input": {
    "raw": "transformer attention mechanisms",
    "normalized": "transformer attention mechanisms"
  },
  "context": {
    "field": "computer science",
    "idea_body_excerpt": "<first 1000 chars or null>",
    "target_n": 5
  },
  "outcome": "success | success_after_expansion | exhausted | failed",
  "verified_citations": [<VerifiedCitation>, ...],
  "verification_failures": [<VerificationFailure>, ...],
  "expansion": null | {<expansion-record>},
  "pdf_sample": {
    "sampled_count": 1,
    "sample_size_target": 1,
    "sampled_pointers": ["10.xxxx/yyyy"]
  },
  "started_at": "2026-05-06T10:30:00Z",
  "ended_at": "2026-05-06T10:30:42Z",
  "duration_seconds": 42.1,
  "cache_status": "miss | hit | refreshed_after_ttl"
}
```

## VerifiedCitation sub-schema

```json
{
  "primary_pointer": "10.5555/abc.def" | "1706.03762" | "https://example.org/path",
  "bibliographic_info": {
    "title": "Attention Is All You Need",
    "authors": ["Ashish Vaswani", "Noam Shazeer", "..."],
    "year": 2017,
    "venue": "NeurIPS"
  },
  "summary": "<≤500 words; faithful to fetched content>",
  "summary_grounded_pdf": true | false | null,
  "verification_log": {
    "url_resolves": true,
    "final_url": "https://...",
    "redirect_chain": ["https://doi.org/10.../...", "https://..."],
    "http_status": 200,
    "title_token_overlap_score": 0.95,
    "summary_grounding_score": 0.78,
    "pdf_sample_score": 0.82,
    "verified_at": "2026-05-06T10:30:30Z"
  }
}
```

## VerificationFailure sub-schema

```json
{
  "candidate": {
    "backend": "semantic_scholar" | "arxiv",
    "primary_pointer": "<...>",
    "claimed_title": "<...>",
    "claimed_authors": ["..."],
    "claimed_year": null,
    "claimed_venue": null,
    "claimed_abstract": null
  },
  "reason": "url_not_resolves | title_mismatch | summary_not_grounded | summary_not_grounded_pdf | paywall_partial | timeout",
  "details": "title-token-overlap was 0.42 against fetched-title 'Different Paper'",
  "failed_at": "2026-05-06T10:30:25Z"
}
```

## Expansion sub-schema

Populated only when `outcome` is `success_after_expansion` or `exhausted`.

```json
{
  "original_term": "ablation density LLM perplexity",
  "expanded_terms_ranked": [
    [1, "code clone density LLM"],
    [2, "redundant code language model perplexity"],
    [...]
  ],
  "per_term_hit_count": {
    "ablation density LLM perplexity": 0,
    "code clone density LLM": 2,
    "redundant code language model perplexity": 3
  },
  "total_queries_issued": 22
}
```

## Field-level validation rules

| Field | Type | Required | Validation |
|-|-|-|-|
| `schema_version` | string | yes | semver; must match the librarian's published schema version |
| `librarian_prompt_version` | string | yes | semver; matches `agents/registry.yaml` `librarian.prompt_version` at invocation time |
| `term_input.raw` | string | yes | non-empty; ≤500 chars |
| `term_input.normalized` | string | yes | derived per E1 normalization rules |
| `context.field` | string \| null | yes | one of `agents/registry.yaml` default fields, or null |
| `context.target_n` | int | yes | ≥1; default 5 |
| `outcome` | enum | yes | one of {`success`, `success_after_expansion`, `exhausted`, `failed`} |
| `verified_citations` | list | yes | length ≤ 50; each item validates against VerifiedCitation sub-schema |
| `verification_failures` | list | yes | each item validates against VerificationFailure sub-schema |
| `expansion` | object \| null | yes | non-null iff outcome is `success_after_expansion` or `exhausted` |
| `pdf_sample.sampled_count` | int | yes | ≥ ceiling(0.10 * len(verified_citations)) with min 1, when len > 0 |
| `pdf_sample.sample_size_target` | int | yes | matches the formula above |
| `pdf_sample.sampled_pointers` | list[string] | yes | length == sampled_count; each is a primary_pointer present in verified_citations |
| `cache_status` | enum | yes | one of {`miss`, `hit`, `refreshed_after_ttl`} |
| `started_at`, `ended_at` | ISO-8601 UTC | yes | end ≥ start; duration ≤ 600s (FR-010 / Q4 budget) |

## Cross-field invariants

- `outcome == "success"` ⇒ `len(verified_citations) >= context.target_n` AND `expansion is None`
- `outcome == "success_after_expansion"` ⇒ `len(verified_citations) >= context.target_n` AND `expansion is not None`
- `outcome == "exhausted"` ⇒ `len(verified_citations) < context.target_n` AND `expansion is not None`
- `outcome == "failed"` ⇒ `len(verified_citations) == 0` AND populated `verification_failures` OR a top-level `failure_reason` field
- For every citation in `verified_citations`: `verification_log.url_resolves == True` AND `verification_log.title_token_overlap_score >= 0.7`
- For at least `pdf_sample.sample_size_target` citations: `verification_log.pdf_sample_score is not None` AND `summary_grounded_pdf in {True, False}` (not None)

## Failure modes the schema records

| Failure | Where it appears | Caller's response |
|-|-|-|
| Backend unreachable | `outcome: "failed"` + verification_failures empty | Treat as `TransientBackendError` (per Constitution V); retry per existing router policy |
| All candidates fail verification | `outcome: "failed"` + populated verification_failures | Caller decides whether to expand search or give up |
| Expansion exhausted | `outcome: "exhausted"` + partial verified_citations | Caller (per Q3) decides whether to triage or fall through to gap-analysis-as-feature |
| Per-citation timeout | citation appears in verification_failures with `reason: "timeout"` | Other citations may still verify; caller proceeds with partial result |
| PDF inaccessible (paywall) | citation appears in verified_citations with `summary_grounded_pdf: null` + verification_log.pdf_sample_score: null | Caller treats as abstract-level-verified-only |

## Example minimum-passing output

```json
{
  "schema_version": "1.0.0",
  "librarian_prompt_version": "1.0.0",
  "term_input": {"raw": "transformer attention", "normalized": "transformer attention"},
  "context": {"field": "computer science", "idea_body_excerpt": null, "target_n": 1},
  "outcome": "success",
  "verified_citations": [{
    "primary_pointer": "1706.03762",
    "bibliographic_info": {"title": "Attention Is All You Need", "authors": ["Vaswani et al."], "year": 2017, "venue": "NeurIPS"},
    "summary": "Introduces the transformer architecture...",
    "summary_grounded_pdf": true,
    "verification_log": {
      "url_resolves": true, "final_url": "https://arxiv.org/abs/1706.03762", "redirect_chain": [],
      "http_status": 200, "title_token_overlap_score": 1.0, "summary_grounding_score": 0.85,
      "pdf_sample_score": 0.82, "verified_at": "2026-05-06T10:30:30Z"
    }
  }],
  "verification_failures": [],
  "expansion": null,
  "pdf_sample": {"sampled_count": 1, "sample_size_target": 1, "sampled_pointers": ["1706.03762"]},
  "started_at": "2026-05-06T10:30:00Z", "ended_at": "2026-05-06T10:30:42Z", "duration_seconds": 42.1,
  "cache_status": "miss"
}
```
