# Quickstart: Semantic Substantiation Acceptance Matrix

How to exercise spec 019's behavior end-to-end. The offline suite proves the
deterministic layers; the real-call matrix proves the semantic gate against the
live (free) Dartmouth backend — the only honest signal (Constitution III).

## Offline gate (no key required)

```bash
cd /Users/jmanning/llmXive
python -m pytest tests/contract tests/integration tests/unit -q \
  -p no:cacheprovider \
  --deselect tests/unit/test_audit_pdf.py::TestPdfAuditorOnLivePdfs
```
Expected: full green, including the must-not-regress suites
`tests/unit/test_grounding_service.py`, `tests/unit/test_fill_extract_gate.py`,
`tests/unit/test_claim_resolve_dispatch.py`,
`tests/integration/test_exact_count_no_regress.py`, plus the new
`test_fill_channels_kind.py`, `test_fill_relevance.py`,
`test_fill_claimkind_preguard.py`.

## Real-call acceptance matrix (live backend)

Requires `LLMXIVE_REAL_TESTS=1` and a Dartmouth key (resolved via
`llmxive.credentials.load_dartmouth_key()` — never read `os.environ` directly;
the models used are free).

```bash
cd /Users/jmanning/llmXive
LLMXIVE_REAL_TESTS=1 python -m pytest \
  tests/real_call/test_semantic_substantiation.py \
  tests/real_call/test_grounding_entailment.py -q -p no:cacheprovider
```

The matrix asserts (each a Success Criterion):

| Case | Input | Channel | Expected | SC |
|-|-|-|-|-|
| NEGATIVE (the bug) | crossing-number bound vs Wikipedia "Almoravid dynasty" ("about 6 generations") | PROSE | fill BLOCKED; `6` never returned | SC-001 |
| POSITIVE exact-count | "9,988 prime knots at 13 crossings" via OEIS b-file | STRUCTURED | still fills `9988` (gate skipped) | SC-002 |
| POSITIVE constant | `π ≈ 3.14159` | STRUCTURED | still fills | SC-003 |
| POSITIVE prose | "the capital of France is Paris" | PROSE | `assess=grounded`; keeps `Paris` | SC-004 |
| CONTRADICTED | "the capital of Australia is Sydney" | PROSE | `assess=contradicted`; never `Sydney` | SC-005 |
| BOUND pre-guard | "braid index ≤ crossing number for most knots" | — | BLOCKED before any fetch | SC-006 |

## Manual one-shot smoke (the headline bug)

```bash
cd /Users/jmanning/llmXive
LLMXIVE_REAL_TESTS=1 python - <<'PY'
from pathlib import Path
from llmxive.fill.relevance import prose_substantiated, _SourceDoc
from llmxive.fill.models import FetchedSource
from llmxive.claims.models import Claim, ClaimKind, ClaimStatus
from llmxive.backends.dartmouth import DartmouthBackend

backend = DartmouthBackend()
# A knot crossing-number claim vs an unrelated Almoravid-dynasty body that
# merely contains "about 6 generations".
claim = Claim(
    claim_id="t", kind=ClaimKind.NUMERIC,
    raw_text="the trefoil knot has crossing number 6",
    canonical="the trefoil knot has crossing number 6",
    context="", artifact_path="", source_type="external",
    status=ClaimStatus.PENDING, resolved_value=None, evidence=None,
    resolver=None, attempts=0, updated_at="",
)
src = FetchedSource(
    channel="wikipedia", source_id="Almoravid_dynasty",
    url="https://en.wikipedia.org/wiki/Almoravid_dynasty", title="Almoravid dynasty",
    text="The Almoravid dynasty ... lasted about 6 generations ...", authority=3,
)
ok = prose_substantiated("6", src, claim, backend=backend, model=None, repo_root=None)
print("prose_substantiated ->", ok, "(MUST be False — coincidental match)")
assert ok is False
PY
```
Expected: `prose_substantiated -> False` (the keyword pre-filter alone rejects it —
"crossing"/"trefoil"/"knot" do not co-occur with the `6` — so no LLM call is even
needed).

## What MUST NOT change

- `grounding/service.number_substantiated` and `grounding_guard.number_appears_in`
  (the exact-count literal gate) — byte-for-byte.
- `grounding/entailment.assess` and `Verdict` — reused as-is.
- `claims/canonical` keyword logic — only renamed to public `subject_keywords`.
