# Quickstart — Pipeline Convergence Protocol

How to exercise each deliverable with **real** calls/inputs (Const. III). Real-model tests require `LLMXIVE_REAL_TESTS=1` and a Dartmouth key (`~/.config/llmxive/credentials.toml` or env via `llmxive.credentials.load_dartmouth_key`).

## 0. Environment

```bash
pip install -e .                      # editable install
python -m llmxive.checks.backends     # confirms free-model backend reachable
export LLMXIVE_REAL_TESTS=1           # enable real-call tests
export LLMXIVE_INSPECTION_DIR=$PWD/specs/015-pipeline-convergence-protocol/inspections  # capture per-agent I/O
```

## 1. Summarizer (`summarize`/`desummarize`) — validate FIRST

```python
from llmxive.tools.summarize import summarize, desummarize
# Real over-budget artifact (e.g. a large plan.md or a multi-section paper)
reduced = summarize(open("big_plan.md").read(), goal="preserve every FR/SC/task id verbatim",
                    model="qwen.qwen3.5-122b", cache_dir=".summaries")
# Every critical id must round-trip:
restored = desummarize(reduced)            # recursively pages content back in
```
- Unit/edge: `pytest tests/unit/test_summarize_edge_cases.py` (7 edge cases: atomic-unit splitting, cross-chunk refs, cross-chunk logic, numbers, ordering, output cut-off, recursion loss).
- Real fidelity: `pytest tests/real_call/test_summarize_fidelity.py` (real qwen calls; asserts 100% verbatim recovery of URLs/DOIs/ids/numbers and same critical verdicts on reduced vs full form).

## 2. Single-step convergence

```python
from llmxive.convergence.engine import run_convergence
from llmxive.convergence.reviewspecs import reviewspec_for
result = run_convergence(reviewspec_for("clarified"), project, max_rounds=3)  # the Spec step
assert result.converged is (result.kickback is None)   # honest reporting (FR-016)
```
- `pytest tests/integration/test_convergence_spec_step.py` — drives the Spec panel on a real project; asserts structured concerns in R1, per-concern change-log in R2, anchored R3, and converge-or-kickback.

## 3. Triage (advisory human/personality reviews)

```python
from llmxive.convergence.triage import triage
rec = triage(review_text, stage_context="planned")
# off-topic/unsafe -> rec.preserved is False, mapped_lenses == []
```
- `pytest tests/integration/test_triage.py` — feeds high-quality / low-quality / off-topic / unsafe reviews; asserts only quality+safe+on-topic ones reach a lens and the publication log.

## 4. Differential calibration (per panel, per domain)

```bash
python -m llmxive.calibration.differential --stage planned --domain chemistry
# writes specs/015-.../calibration/<stage>/<domain>/adjudication.md for manual review
```
- Asserts the injected flaw is caught by the expected lens (and absent in the clean run); surfaces extra findings for **manual adjudication** (Claude pre-evaluates; maintainer spot-checks). Repeat for all 9 fields; tune sensitivity from the reports; validate the held-out field with un-tuned prompts.

## 5. End-to-end traversal (one domain)

```bash
# Drive a real high-quality project through every stage to posted.
python -m llmxive.cli step --project PROJ-261-... --until posted
# At paper_accepted the publisher halts at awaiting_publication_signoff and writes pending_publication.yaml.
# Maintainer inspects, then:
llmxive publish-approve PROJ-261-...     # records publication_signoff.yaml; only then is the real DOI minted
```
- `pytest tests/e2e/test_domain_traversal.py` (real, repeated for noise-robustness): a golden project per domain reaches `posted` with a real DOI (post sign-off), compiled PDF, and `publication.yaml`; a weak project is rejected/kicked back. **This pauses for the manual DOI sign-off (FR-054).**

## 6. Living-document discussion

```bash
# Post an on-topic comment to a posted project, then run the batched recompile.
python -m llmxive.cli discussion-recompile --project PROJ-261-...
# Adds/updates a Discussion section; on material PDF change, halts for sign-off before minting a version DOI.
```

## 7. Full verification (Stage 5 gate)

```bash
ruff check . && mypy src/llmxive
pytest tests/unit tests/contract tests/integration -q
LLMXIVE_REAL_TESTS=1 pytest tests/real_call tests/e2e -q   # real calls; long-running
python -m llmxive.checks.prompts        # prompt registry integrity
```
Then re-walk `spec.md` (every FR/SC) and `tasks.md` (every `[X]`) per the execute skill's Stage-5 protocol; record manual QC co-evaluation results.

## Status

`specs/015-pipeline-convergence-protocol/STATUS.md` is the live progress doc (FR-052): per-workstream status with direct file references, updated as work proceeds so any agent/sub-agent can read current state.
