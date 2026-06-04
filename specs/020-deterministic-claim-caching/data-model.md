# Phase 1 Data Model: Deterministic Claim Caching + Planning-Stage Reference-Only Verification

Entities here are mostly **existing** structures (specs 016–019); this document records the fields
that matter for spec 020 and the **changes** to identity, lifecycle, and persistence. New fields are
marked **NEW**; behavioral changes are marked **CHANGE**.

---

## Entity: Claim

The detected assertion. Existing dataclass at
[claims/models.py:40-58](../../src/llmxive/claims/models.py#L40-L58).

| Field | Type | Role in spec 020 |
|-|-|-|
| `claim_id` | str (`c_` + 8 hex of SHA256 over kind+canonical+context) | Text-hash identity. **CHANGE**: no longer the *reuse/freeze* key — demoted to a within-document span handle. |
| `kind` | `ClaimKind` | The planning gate axis: `CITATION` ⇒ verify; low-level ⇒ strip/smooth in planning, verify+freeze elsewhere. |
| `raw_text` / `canonical` / `context` | str | Source span + normalized forms. |
| `artifact_path` | str | Which artifact the claim came from. |
| `status` | `ClaimStatus` | Lifecycle (below). VERIFIED ⇒ frozen/immutable. |
| `resolved_value` | str \| None | The verified value. **CHANGE**: excluded from the fill cache key (FR-012); carried in the doc as a placeholder, not baked into prose (FR-007). |
| `evidence` | str \| None | Source quote / provenance. |
| `source_hash` | str \| None | Source identity used for freeze invalidation (FR-010); set by spec 016 FR-015. |
| `subject_key` (derived) | str (via `canonical.subject_key(claim)`) | **The freeze/reuse identity** (FR-009). Value-independent: excludes asserted/resolved digits, keeps qualifier digits + subject keywords. |

### `ClaimKind` (taxonomy — unchanged enum, reused as the gate)
[models.py:11-18](../../src/llmxive/claims/models.py#L11-L18):
`NUMERIC, MAGNITUDE, RELATIONAL, CAUSAL, ENTITY_FACT, CITATION, RESULT`.
- **Reference class** = `{CITATION}` → resolvability-checked everywhere (incl. planning).
- **Low-level class** = `{NUMERIC, MAGNITUDE, RELATIONAL, CAUSAL, ENTITY_FACT}` → planning:
  strip/smooth (no fetch/ground/kickback); paper/research/impl: full verify + freeze.
- `RESULT` follows the low-level class for planning gating (a stated result is an empirical value).

### `ClaimStatus` (lifecycle — unchanged enum, new immutability rule)
[models.py:21-26](../../src/llmxive/claims/models.py#L21-L26):
`PENDING, VERIFIED, REFUTED, NOT_ENOUGH_INFO, UNRESOLVABLE`.

**CHANGE — freeze rule (FR-010, FR-011)**: once a `(kind, subject_key)` record reaches `VERIFIED`, it
is **immutable**. Transitions out of VERIFIED are allowed **only** when `source_hash` changes
(genuine source change). A transient failure or a later-round re-extraction landing `PENDING` MUST
NOT transition a VERIFIED record back to PENDING/NOT_ENOUGH_INFO.

```text
PENDING ──resolve──▶ VERIFIED ──(frozen; immutable unless source_hash changes)──▶ VERIFIED
   │                    ▲                                                            │
   │                    └────────────── source_hash changed ───────────────────────┘
   ├──refuted──▶ REFUTED
   ├──no evidence──▶ NOT_ENOUGH_INFO
   └──unresolvable reference──▶ UNRESOLVABLE  (references only — blocks advancement, fail-closed)
```

---

## Entity: Verified store (frozen source of truth)

The git-tracked registry. Existing at `state/claims/<PROJECT-ID>.yaml`, read/written by
[state/claims.py:65-93](../../src/llmxive/state/claims.py#L65-L93) (`load`, `upsert`, `get`).

| Aspect | Today | spec 020 |
|-|-|-|
| Location | `state/claims/<PROJECT-ID>.yaml` (git-tracked) | unchanged — this is the single frozen source of truth (FR-013) |
| Record key | `claim_id` (text hash), dedup on upsert | **NEW lookup** `load_verified_by_subject(project_id, repo_root) -> dict[(kind, subject_key) -> Claim]` over VERIFIED records |
| Freeze dependency | partially relies on gitignored grounding-cache | **CHANGE**: freezing depends only on this registry; grounding-cache is a within-run optimization only |
| Persistence guarantee | YAML committed | unchanged — survives clean checkout (SC-004) |

**Invariant**: for a given `(kind, subject_key)` there is at most one VERIFIED record; its
`resolved_value` is the frozen value returned by every later lookup until `source_hash` changes.

---

## Entity: Placeholder

The durable token standing in for a verified claim in the **canonical stored** document.

| Property | Value |
|-|-|
| Token form | the existing pointer `{{claim:c_XXXXXXXX}}` ([pointer.py](../../src/llmxive/claims/pointer.py)) |
| In canonical stored doc | **present and durable** — `strip_claim_artifacts` MUST preserve it (FR-007) |
| In rendered view | replaced by `resolved_value` from the frozen store, deterministically, at review time + publish (FR-008) |
| Re-extractability | none — the stored form carries the token, never the literal value, so it is never re-detected as a new claim (SC-007) |

**Distinction**: `[UNRESOLVED-CLAIM: id — reason]` markers remain **transient** and are still stripped
each round; only the `{{claim:id}}` *verified* pointer becomes durable.

---

## Entity: Stage class

Selects the verification regime. Derived from the speckit `stage_label` string.

| Stage class | `stage_label` values | Claim-layer behavior |
|-|-|-|
| **planning** | `spec`, `clarify`, `plan`, `tasks` | references verified (fail-closed); low-level claims stripped/smoothed (no fetch/ground/kickback) |
| **full** | `paper_*` (paper/research/impl), `None`/unknown (fail-safe) | all kinds verified + frozen (Part B) |

Predicate: **NEW** `claims/stage.py::is_planning_stage(stage_label: str | None) -> bool`
(`True` iff `stage_label in {"spec","clarify","plan","tasks"}`). Single SSoT for the classification.

> The idea/flesh_out stages keep their current behavior (clarification Q1) — they are outside the
> speckit `stage_label` set and so fall into neither planning nor a changed path here.

---

## Entity: Strip/smooth transform

The planning-stage operation replacing a detected low-level claim with a higher-level statement.

| Property | Value |
|-|-|
| Home | **NEW** `claims/smooth.py::strip_and_smooth(passage, claim, *, backend, model) -> str` |
| Input | the passage span carrying the low-level claim + the `Claim` |
| Step 1 | LLM rewrite (via `reasoning_chat`) → claim-free higher-level statement preserving intent + citations |
| Step 2 | re-detect guard: re-run claim detection; if a low-level claim with the same `subject_key` remains → |
| Step 3 | deterministic fallback: remove the asserting clause/sentence span (no LLM) |
| Postcondition | output contains **zero** detectable low-level claims (idempotent; SC-001a) |
| Preserves | citations, research question, method, surrounding non-claim content (FR-002c) |

---

## Relationships

```text
SlashCommandContext.stage_label ──is_planning_stage()──▶ Stage class
        │
        ▼
process_document(text, …, stage_label)
        │
        ├─ planning ─▶ CITATION → reference validator (fail-closed)         [FR-004]
        │             low-level → strip_and_smooth() ─▶ claim-free passage  [FR-002a/b/c, FR-003]
        │
        └─ full ─────▶ all kinds → resolve()
                          │
                          ├─ frozen lookup by (kind, subject_key) in state/claims/   [FR-009/010/011]
                          │     └─ VERIFIED & source_hash unchanged ⇒ adopt value, NO re-resolution
                          └─ else fill_claim() [value-independent cache key, FR-012] ⇒ upsert VERIFIED

render(text, claims)        ─▶ canonical stored form WITH durable {{claim:id}} placeholders  [FR-007]
render_view(text, registry) ─▶ reviewer/publish form WITH values substituted from frozen store [FR-008]
```
