# Full-Text Claim Grounding — Design

_Date: 2026-05-29 · Branch: `015-pipeline-convergence-protocol` · Spec 015 / issue #239, Part-7 quality lineage (F-18 → F-19 → this)._

## 1. Problem

The convergence reviser (and any doc-producing agent) can attach a **fabricated or incorrect factual claim to a citation** and have the panel pass it. The PROJ-552 trail showed this concretely: a reviewer wrongly called the (correct) count `9,988` "implausibly high"; the reviser "resolved" it by fabricating a wrong number (`1,296`) plus a free-text citation ("Kauffman & Lambropoulou 2004"), and the panel passed it.

Two prior layers exist:

- **F-18** (`citation_guard`, committed `9e0cef8c`/`e9d13b3e`): verifies a reference *resolves* (DOI/arXiv/URL exists, registrar-agnostic) and rewrites unresolvable ones `[UNVERIFIED: …]`, which **hard-block advancement** (F-18c) at 3 gate sites.
- **F-19 v1** (`grounding_guard`, uncommitted): extracts source-attributed claims and grounds them — but only against the **abstract**, and only for **arXiv** sources (DOI/URL stubbed).

**Neither verifies the bar the maintainer actually requires:** that *the specific claim is substantiated by the full text of the cited paper* — the numbers match and the concept is conveyed accurately. "The paper exists" (F-18) and "the abstract overlaps" (F-19 v1) are both insufficient. arXiv-only retrieval is a critical gap.

This design adds a **full-text claim-grounding capability** that retrieves a cited paper's full text from many open-access sources and uses an LLM entailment check to decide whether the source substantiates the claim.

## 2. Decisions (maintainer-confirmed)

1. **Grounding method = hybrid:** mechanically locate candidate passages in the full text, then LLM-entailment-check those passages (`grounded | contradicted | not_found`). Matches the "numbers match, concept conveyed accurately" bar; bounding the LLM to relevant passages keeps cost sane on long papers.
2. **Retrieval = open-access-first cascade with abstract fallback:** try multiple OA sources for full text; if only an abstract is reachable, the claim passes **only** if its number AND concept are fully present in the abstract; otherwise FLAG. No paywall scraping.
3. **Placement = reviser chokepoint every revision round + persistent cache** keyed by `(source-id, claim-hash)`, so cost scales with *new distinct claims*, not rounds/stages/projects.
4. **Unreadable/unresolvable/free-text-only source = FLAG** (carried from F-18/F-19: a resolvable-but-unreadable source still flags; the reference existing is not enough).
5. **Scope = Approach A:** a standalone `llmxive.grounding` service reusing `pdf_sample`/`verify` helpers; the librarian is **untouched** (it keeps its own abstract + 10%-PDF-sample flow) but the service is designed so the librarian *could* adopt it later.

## 3. Architecture

New package `src/llmxive/grounding/`. The existing F-19 `agents/grounding_guard.py` keeps its **extraction** (`CitedClaim`) and **pure rewriter** (`apply_grounding_verdicts`, `[UNVERIFIED]` marker → F-18c hard-block) front-ends; only its `ground_claim`/`_fetch_source_text` internals are swapped to call the new service.

| Unit | Responsibility | Interface (sketch) | Depends on |
|-|-|-|-|
| `grounding/full_text.py` | OA-first retrieval cascade | `retrieve(kind, value, *, timeout) -> RetrievedDoc` | `pdf_sample._download_pdf` + new full-text extractor; `verify.resolve_reference`; S2 client; Unpaywall; html-to-text |
| `grounding/entailment.py` | passage location + 1 LLM entailment call | `assess(claim, doc, *, backend, model) -> Verdict` | `number_appears_in`, `jaccard_tokens`, backend |
| `grounding/cache.py` | persistent full-text + verdict caches | `get/put_fulltext(...)`, `get/put_verdict(...)` | `librarian.cache` SHA-256 keying; `state/grounding-cache/` |
| `grounding/service.py` | orchestrator | `ground_cited_claim(claim, *, backend, model, repo_root) -> GroundingVerdict` | the three above |

`RetrievedDoc = {kind, value, tier, full_text: str|None, abstract: str|None, title: str|None, final_url: str, readable: bool, error: str|None}` where `readable = bool(full_text or abstract)`.

`Verdict = {status: "grounded"|"contradicted"|"not_found", evidence: str, note: str}`.

### Service control flow (`ground_cited_claim`)
1. **Verdict cache hit?** → return it.
2. **classify source** (reuse F-19 `classify_source`): free-text / no resolvable id → FLAG.
3. **`resolve_reference`** exists? no → FLAG.
4. **retrieve** full text (full-text cache → cascade).
5. **not readable** → FLAG.
6. **locate passages + entailment** (`assess`).
7. **policy**: `grounded`→OK · `contradicted`/`not_found`→FLAG · abstract-only source OK only if `assess` on the abstract is `grounded`.
8. **write verdict cache**; return `GroundingVerdict(ok, reason)`.

## 4. Retrieval cascade (`full_text.py`) — first tier yielding full text wins

1. **arXiv** → `https://arxiv.org/pdf/<id>` via `pdf_sample._download_pdf` + new full-text extractor; abstract via `verify._fetch_from_arxiv`.
2. **DOI → Unpaywall** → `https://api.unpaywall.org/v2/<doi>?email=<UNPAYWALL_EMAIL>` → `best_oa_location.url_for_pdf` (fallback `.url`) → download + extract. _(Verified 2026-05-29: response carries `is_oa`, `best_oa_location.url_for_pdf`.)_ Skipped if no email configured.
3. **DOI/arXiv → Semantic Scholar** → `/paper/DOI:<doi>?fields=openAccessPdf,abstract,title,externalIds` → `openAccessPdf.url` → download; capture `abstract` for fallback.
4. **Preprint URL patterns** — bioRxiv/medRxiv `…/content/<doi>vN.full.pdf`; OSF/PsyArXiv `https://osf.io/<id>/download`; Zenodo records files API (`/api/records/<id>` → `files[].links.self`).
5. **Direct URL** → GET; `application/pdf` → extract; HTML → strip-to-text.
6. **Abstract-only fallback** — if no full text but an abstract was obtained (S2/arXiv/Crossref), return `RetrievedDoc(full_text=None, abstract=…, readable=True)`.

New helper: a **full-text PDF extractor** (extend `pdf_sample`: extract all pages, not the 1000-word sample), with a sane char cap (e.g. ~200k) so passage-location, not the whole doc, drives LLM input. HTML→text via stdlib `html.parser` (no new heavy dep) or an existing dependency if already present.

## 5. Grounding (`entailment.py`) — hybrid

- **Locate passages:** collect windows around every occurrence of the claim's number (all equivalent forms from `number_appears_in`) plus the top sentence-windows ranked by salient-token overlap with the claim. Cap to ~3–5 windows of bounded length so the LLM call is cheap and focused even on a 30-page paper. If the claim has no number, use token-overlap windows only.
- **LLM entailment:** one call — system+user prompt with the verbatim claim and the candidate passages → strict reply `{status: grounded|contradicted|not_found, evidence_quote}`. Reasoning-safe `max_tokens` (mirror F-13's 131072). Parse strictly; unparseable/empty → treat as error (retry once, then FLAG).
- **Verdict → policy** (in `service`): `grounded`→OK; `contradicted`→FLAG (the `1,296` case: source says otherwise); `not_found`→FLAG. Abstract-only source: run `assess` against the abstract; OK only if `grounded`, else FLAG.

## 6. Cache (`cache.py`)

Under `state/grounding-cache/` (transient, kept out of commits like `librarian-cache`):
- **Full-text cache:** key = normalized source-id → `{tier, full_text|abstract, title, fetched_at}`. Avoids re-downloading the same paper for different claims/rounds. TTL ≈ 90 d.
- **Verdict cache:** key = `sha256(source-id + normalized-claim-text + number)` → `{status, ok, reason, evidence, assessed_at}`. TTL ≈ 30 d.
- Corrupt/expired entry → ignore + refetch (no crash). Reuses `librarian.cache`'s SHA-256 key helper.

## 7. Wiring, config, error handling

- `grounding_guard.ground_claim` delegates to `grounding.service.ground_cited_claim`. F-18 marker + F-18c hard-block unchanged. `LLMXIVE_GROUNDING_GUARD` env-gate unchanged (on in `cli.run`, off in the offline gate so the ~50 call-count reviser tests stay valid).
- **Config:** `UNPAYWALL_EMAIL` (default `llmxive@gmail.com`; tier-2 skipped if explicitly unset/empty); existing `SEMANTIC_SCHOLAR_API_KEY`; new `state/grounding-cache/` dir.
- **No silent pass / fail-loud:** every network step bounded-timeout; a tier error → try the next tier; all tiers fail → `readable=False` → FLAG; entailment error → one retry → FLAG. A verification that itself failed is **never** read as "grounded."

## 8. Testing (real calls; no mocks of external services)

**Real-call** (gated `LLMXIVE_REAL_TESTS=1`):
- arXiv full text grounds a real stated result; fabricated number vs the same paper → `contradicted`/`not_found` → FLAG.
- Real OA DOI via Unpaywall **and** via S2 `openAccessPdf` → full text grounds a real claim.
- bioRxiv/medRxiv/OSF/Zenodo each retrieve readable text (live ids confirmed in-run, never hardcoded unverified).
- Direct HTML URL → text extracted + grounds.
- Abstract-only DOI (no OA full text): claim-in-abstract → OK; claim-not-in-abstract → FLAG.
- Cache: second call for the same `(source, claim)` returns without re-fetching (instrumented).

**Offline** (real fixtures, no external mocks): passage-location, verdict-policy, cache round-trip (real tmp files), PDF/HTML text extraction on local sample files, `classify_source` edge cases.

**Gates:** offline standard gate stays green (guard env-gated off there); heavy tests behind `LLMXIVE_REAL_TESTS`. ruff + mypy clean.

## 9. Out of scope (YAGNI)

- Refactoring the librarian's own citation verification onto this service (future; the seam is left clean).
- Paywalled/publisher-HTML scraping.
- Verifying *uncited* factual claims (the scope guard only grounds claims explicitly attributed to a source; bare design numbers are never touched).
- **F-19 runs only at the reviser chokepoint, not at initial stage production.** A number fabricated in the *first* draft with zero revision rounds is not grounded by F-19 (the grounding pass only fires on a revise). F-18 still catches unresolvable references in that case; full first-draft grounding is future work.
- **`_preprint_pdf_urls` only tries the `v1` preprint version** (e.g. `…v1.full.pdf`). Later revisions (`v2`+) of a bioRxiv/medRxiv/OSF preprint are not attempted; the other OA tiers (Unpaywall/S2) may still resolve them.

## 10. Status of prior work

F-19 v1 (`grounding_guard.py`, prompt block, `_self_consistency` hook, `cli` env flag, its unit + real-call tests) is **uncommitted on disk** and becomes the front-end (extraction + rewriter + env-gate) for this service. Its abstract-only `_fetch_source_text`/`ground_claim` internals are replaced by `grounding.service`. The F-19 v1 work + this service land together.
