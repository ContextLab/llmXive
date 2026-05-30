# Quickstart: Per-Claim Verification Modes

## What it does

The claim verifier picks the right check per claim: **exact-count** (literal, unchanged), **approximate-constant** (π/e correct to stated precision — multiple roundings valid), **computational** (evaluate "1+2=1", "1>2", "5 km = 5000 m" — catch them as *wrong*, not just unsourceable), or **source-fact** (search + ground). It also corrects wrong **superlatives** (largest planet Saturn→Jupiter) and **relations** (capital of Australia Sydney→Canberra). Constants come from `math`/`scipy.constants` (deterministic, zero-network); computations from `sympy` (the evaluator computes, never the LLM).

## Prerequisites

- Python 3.11; `pip install -e .` (now pulls `sympy`; `scipy` already present).
- Dartmouth key for the ambiguous-case classifier + expression locator + superlative/relational search.
- `LLMXIVE_REAL_TESTS=1` for real-call tests; the constants/compute/rounding paths run offline.

## Verify the headline behaviors

```bash
# deterministic — no network/LLM
python -m pytest tests/unit/test_verify_constants.py tests/unit/test_verify_approximate.py tests/unit/test_verify_compute.py -q
# real-call (search-based + LLM classifier)
LLMXIVE_REAL_TESTS=1 python -m pytest tests/real_call/test_compute_real.py tests/real_call/test_verify_pi_e_real.py tests/real_call/test_fill_superlative_real.py tests/real_call/test_fill_relational_real.py -q
```
Asserts: "π is 3.14" / "π is about 3" / "π is 3.14159" all VERIFIED; "π is 3.15" / "e is 2.5" REFUTED+corrected; "1 plus 1 is 2" VERIFIED, "1 plus 2 is 1" REFUTED→3, "1 is larger than 2" REFUTED; "9,988 prime knots" still VERIFIED (no regression); "largest planet is Saturn"→Jupiter; "capital of Australia is Sydney"→Canberra.

## Use programmatically

```python
from llmxive.verify import mode, compute, approximate, constants
mode.select_mode(claim)                  # "computational" for "1 plus 2 is 1"
compute.verify_computational(claim, backend=be, model=None, repo_root=root).computed   # "3"
constants.true_value("pi")               # 3.141592653589793
approximate.is_valid_rounding(3.14, 3.141592653589793, decimals=2, hedge=False)   # True
```
In the pipeline these run automatically inside `claims/resolve.py` (the verifier selects the mode; computational/approximate don't search; exact/source do).

## Safety invariant

A computed/constant value is a **deterministic authority** (sympy/`math`/CODATA), never model memory: the evaluator computes and the library holds the constant; the LLM only *locates* the expression/subject. An unparseable computational claim falls back to source verification or blocks — never guessed.

## Offline gate

```bash
python -m pytest tests/contract tests/integration tests/unit -q -p no:cacheprovider \
  --deselect tests/unit/test_audit_pdf.py::TestPdfAuditorOnLivePdfs
```

## SC map

SC-001 approx π/e roundings · SC-002 9,988 no-regress · SC-003 constants zero-network · SC-004 superlative · SC-005 relational · SC-006 no model-memory · SC-007 no over-correction · SC-008 magnitude/relational · SC-009 computational examples · SC-010 evaluator-computes-not-LLM.
