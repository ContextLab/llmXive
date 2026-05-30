# Phase 1 Data Model: Claim-Verification Layer

Two persistent stores, both following the existing `state/citations.py` convention (flat YAML, `load`/`save`/`upsert`, `repo_root`-aware via `llmxive.config.repo_root()`).

## Entity: Claim

`state/claims/<PROJECT-ID>.yaml` — a flat list of Claim records.

| Field | Type | Notes |
|-|-|-|
| `claim_id` | str | `c_<sha8>` — stable hash of normalized `(kind, canonical, context)`. Identity key. |
| `kind` | enum `ClaimKind` | `numeric \| magnitude \| relational \| causal \| entity_fact \| citation \| result` |
| `raw_text` | str | verbatim span as the agent wrote it |
| `canonical` | str | normalized assertion; for `relational` a `subject \| relation \| object` triple string; for `numeric` a `metric(args)=value` form |
| `context` | str | surrounding anchor text used to re-locate the span across rounds |
| `artifact_path` | str | repo-relative path of the document the claim came from |
| `source_type` | enum | `external \| result \| pending` |
| `status` | enum `ClaimStatus` | `pending \| verified \| refuted \| not_enough_info \| unresolvable` |
| `resolved_value` | str \| null | the value rendered into the doc once verified |
| `evidence` | map \| null | `{ source_id, url_or_receipt, quote, score }` — provenance of the resolution |
| `resolver` | str \| null | `librarian \| grounding \| triple \| result_receipt` |
| `attempts` | int | automated re-resolution attempts (bounded by retry budget) |
| `updated_at` | str (ISO) | last mutation time (stamped by caller, not in pure logic) |

**State transitions**: `pending → (verified | refuted | not_enough_info)`. `not_enough_info → pending` on auto-route retry (until budget). `verified → pending` (cache invalidation) when the underlying source/receipt hash changes (FR-015). `refuted`/budget-exhausted `not_enough_info → unresolvable` (terminal block; doc stays blocked).

**Validation**:
- `claim_id` MUST equal the recomputed hash of `(kind, canonical, context)` (tamper/skew check).
- `status == verified` REQUIRES non-null `resolved_value` AND non-null `evidence`.
- `source_type == result` REQUIRES the resolver to be `result_receipt` and a matching receipt to exist.
- A `verified` claim's `resolved_value` is the ONLY thing rendered; the model's `raw_text` value is never trusted.

## Entity: Claim Registry

The per-project set of Claims = the file `state/claims/<PROJECT-ID>.yaml`. Single source of truth from which documents render. Operations: `load(project_id)`, `save(project_id, claims)`, `upsert(project_id, claim)` (replace-by-`claim_id`), `get(project_id, claim_id)`.

## Entity: Claim Pointer

In-document reference `{{claim:<claim_id>}}`. NOTE: the existing `agents/prompts.py` `_TOKEN_RE` matches only `[a-z_][a-z0-9_]*` token names (no colon), so `claims/pointer.py` defines its OWN regex `\{\{\s*claim:(?P<id>c_[0-9a-f]{8})\s*\}\}` in the same `{{…}}` style rather than calling `substitute()`. `render(text, claims_by_id)` swaps each pointer for the registry's `resolved_value`. A pointer whose claim is not `verified` renders the **unified claim-marker** (see Gate) instead of a value, which the gate detects.

## Entity: Execution Receipt

`state/results/<PROJECT-ID>/<result_id>.yaml` — minted by the harness, NEVER an LLM.

| Field | Type | Notes |
|-|-|-|
| `result_id` | str | `r_<sha8>` |
| `value` | str/num | scalar value, or a pointer to a table/figure artifact |
| `kind` | enum | `scalar \| table \| figure` |
| `producer` | map | `{ script_path, code_sha, entrypoint, seed }` |
| `inputs` | map | `{ dataset_id, data_sha256, params }` |
| `env_sha` | str | lockfile/environment hash |
| `captured` | map | `{ stdout_path, return_repr }` |
| `output_sha256` | str | hash of the produced value/artifact |
| `created_at` | str (ISO) | mint time |
| `hmac` | str | `hmac.new(key, canonical_payload, sha256).hexdigest()` over all fields above; `key` never in any model context |

**Validation**:
- `verify_receipt(receipt, key)` recomputes the HMAC over the canonicalized payload and compares with `hmac.compare_digest`; mismatch → invalid (block).
- A result claim resolves ONLY if a receipt exists whose `output_sha256` matches the cached/re-verified run AND `verify_receipt` passes (FR-009).
- No field may be mutated after signing without re-minting (any edit invalidates the HMAC).

## Entity: Result Store

The per-project set of receipts under `state/results/<PROJECT-ID>/`. Receipts are first-class sources: a downstream claim may set `source_type: result` and cite `result:<result_id>` exactly as it would a DOI (FR-010).

## Entity: Resolver

A per-kind strategy `resolve(claim) -> Verdict`. `Verdict = { status: verified|refuted|not_enough_info, value, evidence, resolver }`.

| kind | resolver | mechanism |
|-|-|-|
| `numeric`, `citation` | `librarian`/`grounding` | `resolve_reference` existence + `ground_cited_claim` content/number gate |
| `magnitude` (superlative/comparative) | `triple` | retrieve full candidate set → compute ordering → verify |
| `relational` | `triple` | subject–relation–object → retrieve citable source → entailment |
| `causal` | `grounding` | require a citable supporting source; never model inference; else `not_enough_info` |
| `entity_fact` | `grounding` | authoritative reference entailment |
| `result` | `result_receipt` | matching signed receipt (above) |

## Unified marker (replaces F-18 `[UNVERIFIED:`)

Single constant `CLAIM_MARKER_PREFIX = "[UNRESOLVED-CLAIM:"` in `claims/gate.py` (SSoT). `has_unresolved_claims(text)` / `find_unresolved_claims(text)` mirror the F-18 predicate API so `convergence/engine.py` and the chokepoint detect blocks uniformly. `migrate.py` rewrites any residual `[UNVERIFIED: …]` to this marker.
