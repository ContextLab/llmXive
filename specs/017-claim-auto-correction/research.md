# Phase 0 Research: Authoritative-Fill / Claim Auto-Correction

Clarifications (FR-008 conflict, FR-015 scope, channels, fill-output) were resolved in `/speckit-clarify`. This file records the **source-channel reachability research** (done live, 2026-05-30) that de-risks the new integrations, plus the extraction/citation-repair/gating decisions. Every external endpoint below was probed with a real HTTP client before being committed to the design (FR-013, Constitution II).

## D1 — OEIS access: search is Cloudflare-blocked; the b-file is reachable (VERIFIED)

- **Decision**: Use OEIS as a **confirmation channel by A-number** via the **b-file** endpoint `https://oeis.org/A<NNNNNN>/b<NNNNNN>.txt` (plain `n value` lines). Do NOT depend on the OEIS search API for subject→A-number discovery.
- **Evidence (live)**: `GET https://oeis.org/search?q=id:A002863&fmt=json` and `&fmt=text` and `/A002863/list` all return **HTTP 403** behind a Cloudflare "Just a moment…" challenge. But `GET https://oeis.org/A002863/b002863.txt` returns **HTTP 200** plain text containing `13 9988` — confirming **A002863 ("Number of prime knots with n crossings") a(13) = 9988**, the headline value.
- **Rationale**: OEIS is the highest-authority source for integer-sequence/combinatorial counts, but its searchable surface is bot-protected. The A-number is reliably surfaced by Wikipedia (D2) and frequently appears in the claim's own cited prose; given an A-number + the crossing index, the b-file deterministically yields the value. This keeps OEIS as the top-authority *value confirmation* without fighting Cloudflare.
- **Alternatives rejected**: scraping the Cloudflare-challenged HTML (fragile, against the site's intent); a paid OEIS mirror (none; Constitution IV).

## D2 — Wikipedia is the reachable discovery + value channel (VERIFIED)

- **Decision**: Wikipedia (`en.wikipedia.org/w/api.php`) is the primary **discovery** channel for reference/encyclopedic facts and a **value** source: `action=query&list=search` to find articles, then `action=query&prop=extracts&explaintext=1` to fetch plain-text article content.
- **Evidence (live)**: search `prime knots number by crossing` → `["Prime knot", "Crossing number (knot theory)", "71 knot"]`. The **Knot theory** and **Knot tabulation** article extracts contain **both `9988` and `A002863`**. So a Wikipedia fetch both yields the value (present-in-source gate passes on 9988) AND surfaces the OEIS A-number for D1 confirmation.
- **Rationale**: Wikipedia's API is open, fast, no auth, no Cloudflare; its prose carries the value and usually cites the primary source (OEIS A-number, a paper DOI). It is the bridge from a natural-language claim subject to a resolvable primary source.

## D3 — Wikidata for relational/entity facts (VERIFIED, but v1 scope note)

- **Decision**: Wikidata (`www.wikidata.org/w/api.php?action=wbsearchentities` → entity API) for set/relational + entity facts (subject–relation–object). In v1 (numeric + entity per FR-015), Wikidata backs **entity/definitional** fills; relational fills are the fast-follow.
- **Evidence (live)**: `wbsearchentities&search=France` → `[(Q142, "France"), …]` (HTTP 200, no auth). Entity claims (statements P-values) are fetchable + structured.

## D4 — Channel authority order + conflict policy (FR-008)

- **Decision**: Fixed channel-authority order, highest first: **OEIS (b-file, for the matching A-number) > Wikidata (structured statement) > Wikipedia (article prose) > theorem search (paper) > paper search**. On disagreement, take the highest-authority channel's value and **record the competing value(s) + sources** in provenance.
- **Rationale**: clarified FR-008 = channel-priority + record. Curated reference outranks paper search; within curated, a primary structured source (OEIS sequence, Wikidata statement) outranks encyclopedic prose. Conflicts on stable reference facts are rare; recording them keeps the layer honest (never silently settle a contested value).

## D5 — Value extraction + the present-in-source safety gate (the trust boundary)

- **Decision**: For each fetched source, locate the candidate value **in the fetched text**, then gate on literal presence:
  - **Numeric**: an LLM extractive-QA step ("from THIS source text only, what is the value of `<quantity>`? quote it") proposes a value; then `grounding.service.number_substantiated(value, fetched_text)` (the spec-016 deterministic gate) MUST confirm it is literally present. Absent → reject the candidate. This makes the LLM a *locator*, never a *source* — the value must exist in fetched text.
  - **Entity/definitional**: extract the answer term, then require it to appear in the fetched text (a deterministic substring/normalized-match check + `grounding.entailment.assess` for support). Absent → reject.
- **Rationale**: FR-003/SC-002 — zero fills from model memory. The deterministic presence check is the non-negotiable gate; the LLM only points at where the value is, the gate confirms it's really there.
- **Alternatives rejected**: trusting an LLM-returned value without the presence gate (this is the exact fabrication failure mode we are fixing).

## D6 — Subject-query derivation

- **Decision**: Derive the search query from the claim by stripping the asserted value, keeping the subject + qualifiers (e.g., claim "27,635 prime knots at 13 crossings" → query "number of prime knots at 13 crossings"). Reuse `librarian/query_extractor.extract_queries` where useful; a small deterministic strip + an LLM rephrase fallback otherwise. Route math-classified claims (via `librarian/math_classifier.classify`) to the theorem channel additionally.
- **Rationale**: reuse existing query machinery; keep the subject intact so search recall is high while the (to-be-corrected) value is removed.

## D7 — Citation repair (FR-007)

- **Decision**: On a successful fill, repair the surrounding citation to the authoritative fill source: locate the claim span (already pointer-substituted by spec 016) and replace/annotate the adjacent citation with the fill source (e.g., `(OEIS A002863, oeis.org/A002863)` or the Wikipedia/Wikidata URL). Reuse `agents/citation_guard.py` occurrence regexes (`_doi_occurrence_re`, `_md_link_occurrence_re`, `_bare_url_occurrence_re`) + `reference_validator.extract_citations` to find and rewrite the nearby citation; if none is adjacent, append the source as an inline citation. This runs in `claims/service.process_document` after render, for claims whose verdict came from a fill.
- **Rationale**: clarified "value + repair citation" — the corrected value and its citation are fixed together so the document is self-consistent.

## D8 — Env gating + entrypoint

- **Decision**: The fill is gated by `LLMXIVE_CLAIM_FILL=1` (mirrors `LLMXIVE_CLAIM_LAYER` / `LLMXIVE_GROUNDING_GUARD`): OFF by default so the offline unit suite stays network-free; `cli.run` sets it for real pipeline runs (one-line `os.environ.setdefault`). The `resolve.py` wire-in checks the flag before attempting a fill.
- **Rationale**: matches the established spec-016/F-19 pattern; keeps the ~1500-test offline gate green and network-free.

## D9 — Reuse map (from the Explore pass; exact symbols)

| Need | Reuse | Symbol(s) |
|-|-|-|
| wire-in (numeric) | `claims/resolve.py` | `resolve_numeric_or_citation` NEI branches (lines 89/125/127) |
| wire-in (entity) | `claims/resolve.py` | `resolve_entity_fact` NEI branches (lines 287/321) |
| HTTP retry/rate-limit | `librarian/search.py` | `_retry_request(method,url,*,headers,params,timeout,max_attempts)`, `_TokenBucket`, `USER_AGENT` |
| paper channel | `librarian/search.py` | `SemanticScholarClient.search_papers`, `ArxivClient.search/get_by_id`, `merge_candidates`, `Candidate` |
| theorem channel | `librarian/theoremsearch.py` + `math_classifier.py` | `TheoremSearchClient.search(term)`, `classify(...)->MathClassifierResult` |
| subject query | `librarian/query_extractor.py` | `extract_queries(...)` |
| fetch source text | `grounding/full_text.py` | `retrieve(kind,value,*,timeout)->RetrievedDoc(.readable)` |
| presence gate | `grounding/service.py` | `number_substantiated(number,doc_text)` |
| entailment | `grounding/entailment.py` | `assess(...)`, `locate_passages(...)` |
| cache | `grounding/cache.py` | `get/put_fulltext`, `get/put_verdict` (TTL + atomic) |
| registry | `state/claims.py` | `load/save/upsert/get` |
| render verified value | `claims/pointer.py` / `claims/service.py` | `render`, `process_document`, `resolve_registered_claims` |
| citation repair | `agents/citation_guard.py` / `reference_validator.py` | occurrence regexes, `extract_citations` |

## D10 — Testing (real-call, no mocks; FR-013)

- **Real-call** (`LLMXIVE_REAL_TESTS=1` + Dartmouth key + network): OEIS b-file fetch confirms 9988 (A002863); Wikipedia discovery+value for the knot count; Wikidata entity fill; a no-source claim correctly blocks (no fabricated fill); end-to-end on the chokepoint: 27,635 → sourced 9,988 with OEIS/Wikipedia citation, never 27,635.
- **Offline pure-logic**: subject-query derivation, the present-in-source gate decision, conflict/authority ordering, citation-repair rewriting (given fixed source + claim), per-channel response parsing on captured fixtures (the *parsing*, not the network).
- **No mocks** of search/retrieval/extraction (constitution III). Any endpoint/value entering code is verified first (OEIS b-file, Wikipedia/Wikidata APIs all verified above).

**Output**: all decisions resolved with live evidence; no NEEDS CLARIFICATION remain. Proceed to Phase 1.
