# Phase 1 Contracts: Claim-Verification Layer

Module-level contracts (this is a Python library + pipeline, not a network API). Each contract names the module, its public functions with signatures, and the behavioral guarantee a test asserts. Reused symbols are referenced, not redefined.

## `state/claims.py` — Claim Registry store

```python
def load(project_id: str, *, repo_root: Path | None = None) -> list[Claim]
def save(project_id: str, claims: list[Claim], *, repo_root: Path | None = None) -> Path
def upsert(project_id: str, claim: Claim, *, repo_root: Path | None = None) -> None   # replace by claim_id
def get(project_id: str, claim_id: str, *, repo_root: Path | None = None) -> Claim | None
```
**Guarantees**: round-trips through `state/claims/<PROJECT-ID>.yaml`; `upsert` is replace-by-`claim_id` (no duplicates); missing file → `[]`. Mirrors `state/citations.py`.

## `claims/models.py` — entities

```python
class ClaimKind(str, Enum): NUMERIC; MAGNITUDE; RELATIONAL; CAUSAL; ENTITY_FACT; CITATION; RESULT
class ClaimStatus(str, Enum): PENDING; VERIFIED; REFUTED; NOT_ENOUGH_INFO; UNRESOLVABLE
@dataclass(frozen=True) class Verdict: status: ClaimStatus; value: str | None; evidence: dict | None; resolver: str | None
@dataclass class Claim: ...  # fields per data-model.md
def compute_claim_id(kind: ClaimKind, canonical: str, context: str) -> str   # "c_" + sha256[:8]
```
**Guarantees**: `compute_claim_id` is stable + deterministic for identical inputs and differs when any of `(kind, canonical, context)` differ.

## `claims/extract.py` — extraction

```python
def extract_claims(text: str, *, artifact_path: str, backend, model: str | None, repo_root: Path) -> list[Claim]
```
**Guarantees**: returns only check-worthy, externally-attributable or result claims; does NOT return design choices / thresholds / subjective statements (SC-007). Each returned Claim has `status=PENDING` and a populated `kind`, `raw_text`, `canonical`, `context`. Real LLM call (no mock) in real-call tests.

## `claims/classify.py` — taxonomy

```python
def classify(raw_text: str, canonical: str) -> ClaimKind
```
**Guarantees**: assigns one of the 7 kinds; superlative/comparative wording → `MAGNITUDE`; SPO/relation wording → `RELATIONAL`; "X causes/leads to Y" → `CAUSAL`; an internal metric phrased as a produced result → `RESULT`.

## `claims/pointer.py` — substitution + render (PURE)

```python
def to_pointer(claim_id: str) -> str                                   # "{{claim:<id>}}"
def substitute_pointers(text: str, spans: list[tuple[str, str]]) -> str # raw span -> pointer, idempotent
def render(text: str, claims_by_id: dict[str, Claim]) -> tuple[str, GateReport]  # pointer -> resolved_value or marker
```
**Guarantees**: pure (no IO); `pointer.py` defines its OWN `{{claim:<id>}}` regex (`\{\{\s*claim:(?P<id>c_[0-9a-f]{8})\s*\}\}`) — it does NOT call `agents/prompts.py::substitute`, whose `_TOKEN_RE` excludes the colon; `render` substitutes the registry's `resolved_value` for `VERIFIED` claims and the unified marker for any non-verified claim; round-trip `substitute → render` of an all-verified set reproduces verified values; the model's original numerals never reappear for verified claims.

## `claims/resolve.py` + `claims/triple.py` — resolvers

```python
def select_resolver(kind: ClaimKind) -> Callable[..., Verdict]   # PURE dispatch (testable without backends/mocks)
def resolve(claim: Claim, *, backend, model: str | None, repo_root: Path) -> Verdict   # dispatch via select_resolver
# triple.py
def decompose_triple(text: str) -> tuple[str, str, str]          # PURE: subject, relation, object
def check_ordering(candidates: list, claim: str) -> bool          # PURE: candidate set + ordering, no IO
def resolve_relational(triple: str, *, backend, model, repo_root) -> Verdict
def resolve_superlative(claim: Claim, *, backend, model, repo_root) -> Verdict   # retrieve candidate set → check_ordering
```
**Guarantees**: numeric/citation delegate to `librarian.verify.resolve_reference` + `grounding.service.ground_cited_claim` (incl. `number_substantiated` gate); superlative retrieves the candidate set and checks ordering (not single-statement entailment); causal returns `NOT_ENOUGH_INFO` unless a citable source supports it; verdicts are cached via `grounding/cache.py`; `NOT_ENOUGH_INFO` stays distinct from `REFUTED`.

## `results/receipt.py` + `results/harness.py` — execution receipts

```python
# receipt.py
@dataclass(frozen=True) class Receipt: ...   # fields per data-model.md
def sign_receipt(payload: dict, *, key: bytes) -> str          # hmac-sha256 hexdigest
def verify_receipt(receipt: Receipt, *, key: bytes) -> bool    # hmac.compare_digest
def load_signing_key() -> bytes                                # process-local secret; NEVER passed to a model
# harness.py
def mint_receipt(*, value, kind, producer: dict, inputs: dict, env_sha: str, captured: dict, repo_root, project_id) -> Receipt
def result_backed(value: str, project_id: str, *, repo_root) -> Receipt | None  # value matches a verified receipt
```
**Guarantees**: `mint_receipt` is only ever called by the harness (implementation/analysis stage), never from an agent/LLM path; `verify_receipt` fails on any field mutation; a result claim resolves only when `result_backed` returns a receipt with matching `output_sha256` AND `verify_receipt` passes; `load_signing_key` resolves outside model context (env/credentials, like the Dartmouth key).

## `claims/gate.py` — unified marker + block

```python
CLAIM_MARKER_PREFIX = "[UNRESOLVED-CLAIM:"
def mark_unresolved(text: str, claim: Claim, reason: str) -> str
def has_unresolved_claims(text: str) -> bool
def find_unresolved_claims(text: str) -> list[str]
```
**Guarantees**: API mirrors F-18's `has_unverified_markers`/`find_unverified_markers` so `convergence/engine.py` detects claim blocks the same way it detected `[UNVERIFIED]`. Replaces the F-18 marker (FR-019).

## `claims/service.py` — orchestrator (extract→register→substitute→resolve→render)

```python
def process_document(text: str, *, artifact_path: str, project_id: str, backend, model, repo_root) -> tuple[str, list[Claim], GateReport]
```
**Guarantees**: runs the full loop; persists claims to the registry; returns the rendered document (verified values or markers) + the claim list + a gate report indicating whether any unresolved claim blocks advancement. Idempotent across rounds via the verified-value cache.

## `claims/migrate.py` — one-time migration

```python
def migrate_unverified_markers(*, repo_root: Path, dry_run: bool = False) -> list[Path]
```
**Guarantees**: rewrites residual `[UNVERIFIED: …]` markers in tracked artifacts to `[UNRESOLVED-CLAIM: …]`, seeds registry entries as `NOT_ENOUGH_INFO`; returns the changed files; run once.

## Integration contracts (modifications to existing modules)

- `speckit/slash_command.py::_validate_artifact_citations(ctx, outputs)` — additionally runs `claims.service.process_document` on each `.md`/`.tex` artifact; blocks + records claims.
- `convergence/revisers/_self_consistency.py::run_with_self_consistency(...)` — runs the claim layer on revised artifacts each round (earliest interception).
- `convergence/engine.py` — `_unverified_marker_concerns()` (or a sibling) synthesizes a blocking SCIENCE-severity concern when `has_unresolved_claims` is true (FR-017).
- `pipeline/_kickback.py` + `pipeline/graph.py` — the `CONVERGENCE_KICKBACK_CAP` human-escalation terminal is repointed: an unresolved-claim kickback routes to the librarian/implementation stage for an automated retry (FR-013/014).
