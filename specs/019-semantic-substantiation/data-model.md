# Phase 1 Data Model: Semantic Substantiation for the Claim-Fill Layer

This feature adds behavior, not persisted schema. The "entities" are the in-memory
types the gate reasons over. No migration, no new stored fields.

## Existing types consumed (unchanged)

### `Claim` (`claims/models.py`)
Relevant fields: `kind: ClaimKind`, `raw_text: str`, `canonical: str`,
`resolved_value: str | None`. The gate reads `kind`, `raw_text`/`canonical`
(for the pre-guard and `subject_keywords`); it never mutates the claim.

### `FetchedSource` (`fill/models.py`)
Frozen value object: `channel: str`, `source_id: str`, `url: str`,
`title: str | None`, `text: str`, `authority: int`. The gate reads `channel`
(→ STRUCTURED/PROSE) and `text` (the prose body). Unchanged.

### `Verdict` (`grounding/entailment.py`)
`status: Literal["grounded","contradicted","not_found"]`, `evidence: str`,
`note: str`. The gate accepts iff `status == "grounded"`. Unchanged.

## New conceptual entities (in-memory, no persistence)

### ChannelKind classification
- **Representation**: not a stored type — a pure predicate pair over the existing
  `channel` string: `is_structured(channel) -> bool`, `is_prose(channel) -> bool`.
- **STRUCTURED** = `{constants, oeis, wikidata}` (subject↔value link inherent).
- **PROSE** = complement (`wikipedia, theorem, paper`, and any unknown channel —
  fail-closed).
- **Invariant**: `is_structured(c) == (not is_prose(c))` for all `c`;
  `is_prose("<unknown>") is True`.

### `_SourceDoc` (adapter, `fill/relevance.py`)
- **Fields**: `full_text: str`, `abstract: str = ""`.
- **Purpose**: the minimal object `assess` reads (`doc.full_text or doc.abstract`).
  Built from `FetchedSource.text`. Frozen dataclass, slots. Not persisted.

### RelevanceDecision (transient)
- The boolean outcome of `prose_substantiated(...)`: `True` only when the
  deterministic subject-keyword co-occurrence pre-filter passes AND `assess`
  returns `grounded`. Any failure/error → `False` (fail-closed). Not stored;
  it gates whether `extract_value` returns the candidate.

## State transitions (claim resolution, with the new gate)

```text
unresolved claim
  │  fill_claim()
  ├─ claim-kind pre-guard (NEW): bound/percent OR digit-less numeric?
  │     └─ yes → BLOCKED (no fetch)                         [FR-002/FR-003]
  ├─ fetch candidates per channel
  ├─ extract_value() per source → _accept(candidate, source, claim) (NEW chokepoint)
  │     ├─ present_in_source fails → reject (as today)      [FR-009 unchanged]
  │     ├─ STRUCTURED channel → accept on present_in_source  [FR-004 exempt]
  │     └─ PROSE channel:
  │           ├─ subject-keyword co-occurrence fails → reject (no LLM) [FR-005]
  │           └─ assess != grounded (incl. error) → reject   [FR-006/FR-010]
  ├─ surviving candidates → conflict.choose (UNCHANGED)      [FR-008 by construction]
  └─ no survivors → BLOCKED via [UNRESOLVED-CLAIM:] marker    [FR-008/FR-010]
```

## Validation rules

- A PROSE candidate is admitted **iff** literal presence ∧ keyword co-occurrence
  ∧ `assess == grounded`. (All three; any failure rejects.)
- A STRUCTURED candidate is admitted **iff** literal presence (today's behavior,
  unmodified).
- The exact-count path (`number_substantiated`) is never altered — it is the
  first conjunct, not replaced.
