# Phase 1 Contracts: Internal Claim-Layer Interfaces (spec 020)

This is an internal library + CLI; the "contracts" are the **function signatures and behavioral
guarantees** that change. Each contract names the canonical home (one location, Principle I),
the signature, preconditions/postconditions, and the FR + acceptance scenario it satisfies.
NEW = new symbol; CHANGE = modified behavior of an existing symbol.

---

## C1 — Stage classification (NEW) — `claims/stage.py`

```python
PLANNING_STAGE_LABELS: frozenset[str] = frozenset({"spec", "clarify", "plan", "tasks"})

def is_planning_stage(stage_label: str | None) -> bool:
    """True iff stage_label denotes a planning stage (specify/clarify/plan/tasks)."""
```

- **Post**: `None`/unknown ⇒ `False` (fail-safe to full verification). Pure, deterministic.
- **Satisfies**: FR-001. Single SSoT for the planning/full distinction.

---

## C2 — Stage-aware document processing (CHANGE) — `claims/service.py::process_document`

```python
def process_document(
    text: str, *, artifact_path: str, project_id: str,
    backend, model, repo_root,
    stage_label: str | None = None,          # NEW (default None ⇒ today's full-verify behavior)
) -> tuple[str, list[Claim], GateReport]:
```

- **Pre**: existing.
- **Post (planning, `is_planning_stage(stage_label)`)**:
  - CITATION claims are still registered + resolvability-checked (reference path); an unresolvable
    citation still produces a blocking signal (FR-004).
  - low-level claims (NUMERIC/MAGNITUDE/RELATIONAL/CAUSAL/ENTITY_FACT/RESULT) are **not** fetched,
    filled, or grounded; **no** `[UNRESOLVED-CLAIM:]` marker is emitted for them; instead each is
    passed to `strip_and_smooth` and replaced in `text` (FR-002, FR-002a, FR-003).
  - returned `GateReport` carries **no** kickback attributable to a low-level claim (FR-003).
- **Post (full, default/paper)**: unchanged coverage; Part-B freeze applies (C5).
- **Backward-compat**: existing callers that omit `stage_label` get identical behavior to today.
- **Satisfies**: FR-001/002/003; US1 scenarios 1,3,4,5.

---

## C3 — Strip/smooth transform (NEW) — `claims/smooth.py::strip_and_smooth`

```python
def strip_and_smooth(passage: str, claim: Claim, *, backend, model) -> str:
    """Replace the low-level assertion in `passage` with a claim-free higher-level statement,
    preserving citations and surrounding content. Guaranteed claim-free output."""
```

- **Pre**: `claim.kind` is a low-level kind; `passage` contains the claim span.
- **Post**:
  1. result is produced by an LLM rewrite (`reasoning_chat`), else
  2. if the re-detect guard finds a low-level claim with `claim`'s `subject_key` ⇒ deterministic
     clause removal is applied;
  3. **invariant**: `extract_claims(result)` yields no low-level claim with that `subject_key`
     (idempotent / SC-001a); citations in `passage` are present in `result` unchanged (FR-002c).
- **Idempotence**: `strip_and_smooth(strip_and_smooth(p, c), c) == strip_and_smooth(p, c)` (no-op on
  already-smoothed text — FR-002b).
- **Satisfies**: FR-002a/b/c; US1 scenarios 1,2,5; SC-001, SC-001a.

---

## C4 — Frozen subject-keyed lookup (NEW) — `state/claims.py::load_verified_by_subject`

```python
def load_verified_by_subject(
    project_id: str, repo_root,
) -> dict[tuple[ClaimKind, str], Claim]:
    """Map (kind, subject_key) -> the VERIFIED Claim, from state/claims/<PROJECT-ID>.yaml."""
```

- **Post**: only `status == VERIFIED` records with a non-empty `subject_key` are included; at most
  one per key (invariant from the data model).
- **Satisfies**: FR-009, FR-013; backing for C5.

---

## C5 — Freeze on resolution (CHANGE) — `claims/service.py::resolve_registered_claims` + `claims/resolve.py`

- **CHANGE (reuse key)**: reuse is keyed by `(kind, subject_key)` via `load_verified_by_subject`
  ([service.py:92](../../src/llmxive/claims/service.py#L92) currently keys by `claim_id`). A new claim
  whose `(kind, subject_key)` matches a VERIFIED record **adopts** that record's `resolved_value`,
  `evidence`, `source_hash`, and VERIFIED status with **no** call to `resolve()` (FR-009, FR-010).
- **CHANGE (immutability)**: the self-heal re-resolution
  ([service.py:94-107](../../src/llmxive/claims/service.py#L94-L107)) MUST skip any claim whose
  `(kind, subject_key)` is VERIFIED in the registry, **unless** `source_hash` differs. A transient
  resolver failure MUST NOT overwrite or downgrade a VERIFIED record (FR-011).
- **Post**: across ≥3 rounds, a once-verified fact yields the same value with zero re-resolutions
  (SC-003); a clean-checkout re-run reads the frozen value with zero cold re-resolutions (SC-004);
  a transient failure never re-opens a VERIFIED record (US2 scenario 4).
- **Satisfies**: FR-009/010/011; US2 scenarios 1,3,4.

---

## C6 — Durable placeholder vs rendered view (CHANGE + NEW) — `claims/pointer.py`, `claims/extract.py`

- **CHANGE — `pointer.py::render(text, claims_by_id) -> tuple[str, GateReport]`**: for a VERIFIED
  claim it now emits the **durable placeholder** `{{claim:c_XXXXXXXX}}` in the canonical stored form
  instead of baking `resolved_value` into prose (FR-007). `[UNRESOLVED-CLAIM:]` markers for
  non-VERIFIED claims are unchanged (still transient).
- **CHANGE — `extract.py::strip_claim_artifacts(text) -> str`**: MUST **preserve** durable
  `{{claim:id}}` pointers that correspond to a registered claim; it still removes
  `[UNRESOLVED-CLAIM:]` markers and orphan/stray pointers (FR-007).
- **NEW — `pointer.py::render_view(text, registry_by_id) -> str`**: substitute each durable
  placeholder with its VERIFIED `resolved_value` from the frozen store, deterministically. Called at
  review time (artifact handed to the panel) and for the published artifact (FR-008).
- **Post**: a stored canonical doc round-trips the convergence loop with **no** verified value baked
  into prose (SC-007); the rendered view is human-readable and reviewer-judgeable (FR-008).
- **Satisfies**: FR-007, FR-008; US2 scenario 2; SC-007.

---

## C7 — Value-independent fill/verification cache key (CHANGE) — `fill/service.py`, `fill/subject_query.py`, `grounding/cache.py`

- **CHANGE — `fill/service.py::_cache_key_parts`** ([L115-130](../../src/llmxive/fill/service.py#L115-L130)):
  drop `claim.resolved_value` from the returned key tuple; key on the value-excluded subject identity.
- **CHANGE — fingerprint**: the fill key uses a value-excluded fingerprint (exclude the asserted
  value token; keep qualifier numbers), consistent with `subject_key`’s exclusion rule, rather than
  `fact_fingerprint`’s all-numeric-tokens set ([subject_query.py:176-180](../../src/llmxive/fill/subject_query.py#L176-L180)).
- **CHANGE — `grounding/cache.py` verdict key** ([L71-80](../../src/llmxive/grounding/cache.py#L71-L80)):
  the `number` (asserted value) component is dropped from the cache key.
- **Post**: a PENDING phrasing ("49") and a VERIFIED phrasing ("9,988") of the **same** fact compute
  the **same** key and hit the same entry (FR-012), so the freeze is not defeated by a cold cache.
- **Satisfies**: FR-012; reinforces SC-003/SC-004.

---

## C8 — Planning short-circuit in the fill gate (CHANGE) — `fill/service.py`, `fill/channels/__init__.py`

- **CHANGE — `channels_for(kind, *, math, stage_label=None)`**
  ([channels/__init__.py:44](../../src/llmxive/fill/channels/__init__.py#L44)): when
  `is_planning_stage(stage_label)`, return **no** channels for low-level kinds (nothing to fetch).
- **CHANGE — fill gate** ([fill/service.py:307-311](../../src/llmxive/fill/service.py#L307-L311)):
  in a planning stage, a low-level claim short-circuits before any external fetch (FR-002).
- **Satisfies**: FR-002 (no fetch/locator/ground in planning); defense-in-depth with C2.

---

## C9 — Threading the stage into the speckit layer (CHANGE) — `speckit/`

- **CHANGE — `SlashCommandContext`** gains `stage_label: str | None`; populated by each command from
  the value it already passes to `_stage_panel` (`"spec"`/`"clarify"`/`"plan"`/`"tasks"`/`"paper_*"`).
- **CHANGE — `_validate_artifact_citations`** ([slash_command.py:207,286](../../src/llmxive/speckit/slash_command.py#L207))
  forwards `stage_label=ctx.stage_label` into `process_document`.
- **CHANGE — `_stage_panel.py`**: the artifact handed to the review panel is the **rendered view**
  (`render_view`) so reviewers judge values, while the stored artifact keeps placeholders (FR-008).
- **Unchanged**: `agents/reference_validator.py` and `state/citations/` (the reference gate already
  runs per artifact and is stage-agnostic — it correctly keeps gating in planning, FR-004).
- **Satisfies**: FR-001, FR-004, FR-008; US1 scenario 3.

---

## C10 — Template & prompt guidance (CHANGE) — docs/templates (FR-006)

Edit the producing guidance (no code contract; behavioral guidance) in the shared templates, the
speckit SKILL.md files, the data-resources panel prompt, and the per-project PROJ-552 template copies,
to state research-question + method + references and **defer specific empirical values** to
implementation. **Satisfies**: FR-006; US3 scenario 1; SC-006 (prevention half).

---

## Contract test matrix (→ quickstart.md for commands)

| Contract | Offline test | Real-call test |
|-|-|-|
| C1 | `is_planning_stage` truth table | — |
| C2/C8 | planning skips low-level (no fetch attempted; no marker) | planning doc w/ wrong number ⇒ no fetch/ground/kickback |
| C3 | strip/smooth idempotence + claim-free guarantee + citation preserved (fallback path forced) | LLM rewrite on real prose ⇒ claim-free, grammatical |
| C4/C5 | frozen lookup reuse; transient failure doesn't re-open VERIFIED | rephrase across 3 rounds ⇒ same value, 0 re-resolutions |
| C6 | stored form keeps `{{claim:id}}`; `render_view` substitutes; round-trip no bake-in | — |
| C7 | PENDING vs VERIFIED phrasing ⇒ same cache key | — |
| C9 | ctx threads stage; reference validator still invoked in planning | fabricated DOI in planning ⇒ blocks |
| (no-regress) | `test_exact_count_no_regress`, `test_claim_*`, `test_fill_*` green | paper-stage 9,988 + constant + entity fact verify + freeze (SC-005) |
