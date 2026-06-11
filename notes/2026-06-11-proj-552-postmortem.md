# PROJ-552 post-mortem: pipeline-induced non-convergence, not a flawed premise

**Question** (maintainer, 2026-06-11): did PROJ-552 ("Quantifying the
complexity of knot diagrams") fail for real scientific reasons, or did the
pipeline steer a sound project into the kickback cap?

**Verdict: the premise is scientifically sound and the project should have
proceeded.** The cap exhaustion was caused by two structural pipeline
defects (now fixed as spec-023 defects #14 and #15) plus the earlier
reviser-output defects (#11–#13). No panel ever disputed the core idea.

## Evidence

### The science itself held up

- The panel ACCEPTED the substance: in the final clean run
  (`convergence_trail/plan-017.jsonl`), all 24 round-1 concerns were
  addressed by real revisions and **passed** their re-review in round 2.
- The genuinely scientific concerns that arose later (hyperbolic-vs-torus
  proportion unquantified in the power analysis; which tests N≥5000
  applies to; exploratory-construct vs confirmatory-correlation wording)
  are ordinary, addressable review feedback — none is a premise-killer.
- The one factual error (spec.md: "49 prime knots at crossing number 13";
  true value 9988 per OEIS A002863 — 49 is the n=9 count) was caught by
  the pipeline's own claims layer: plan.md and research.md carry the
  VERIFIED 9988 with the source URL. The knowledge to fix the spec existed
  inside the project for days.

### Defect #14 — kickback routing could never repair the root cause

The final unresolved concern set was dominated by **spec.md defects**
(the 49-vs-9988 error, three reviewers flagging it independently; missing
percentage values). The plan panel's reviser is structurally FORBIDDEN
from editing spec.md (it rejects writes outside the plan-artifact set —
correctly). The designed remedy was the kickback: "Routing to 'clarified'
with full provenance so the next worker can address the root cause."

But `to_stage: clarified` means *stage = clarified*, whose agent is the
**planner** (`STAGE_TO_AGENT[CLARIFIED] = "planner"`). Every kickback
re-ran the plan against the same defective spec; no spec-editing agent
ever ran. The whole routing table had this off-by-one (the to_stage names
were chosen as "the stage whose artifact needs fixing", but the graph
dispatches the NEXT agent): plan→"clarified" (should be "specified"),
tasks→"planned" (should be "clarified"), and the paper-side equivalents.
Four kicks → cap → human escalation. **Fixed**: routing maps corrected +
lifecycle transitions added + `test_kickback_routing_semantics.py`.

### Defect #15 — the claim-strip pass mutilated the documents

spec 020's deterministic "guarantee" pass (`strip_empirical_values`)
BARE-DELETED empirical tokens, leaving broken prose that reviewers were
right to flag:

- spec.md acceptance scenario: "**Then** of records have crossing number…"
  (a percentage was deleted mid-sentence); SC-006: "of knots with
  computable invariants…"
- plan.md's own CRITICAL correction note was mutilated into nonsense:
  "spec.md states 'Prime knots at a specific crossing number' but OEIS
  A002863 shows Prime knots at a specific crossing number" — both numbers
  stripped, including the VERIFIED 9988 sitting next to its source URL.

So each cycle: reviewers flag the broken placeholders → the reviser
restores values → the strip pass deletes them again on render. Unwinnable.
**Fixed**: verified-facts values (the project's `verified_facts.yaml`) are
exempt; unverified values defer to a grammatical sanctioned `[deferred]`
marker; the shared panel-review block now instructs panels not to flag the
marker. (`test_planning_strip_defers_grammatically.py`.)

### Compounding defects (#11–#13, fixed earlier on 2026-06-11)

Two of the four counted kickbacks were degraded by the reviser-output
defects: the backend-chain outage misclassification (#11), the
single-malformed-reply panel abort (#12), and the load-dependent
zero-artifact replies (#13) burned panel runs and kept concerns alive that
revisions would otherwise have settled.

## Disposition

PROJ-552's kickback count and `human_input_needed` state were produced by
the defects above, not by unresolvable content. With #11–#15 fixed, the
honest course is the one the panel itself asked for: **re-run the spec
stage** (clarifier + spec panel, which CAN fix the 49→9988 error and the
mutilated sentences using the verified facts already on file), then re-run
plan. The maintainer escalation record is answered by this post-mortem;
the resume routes the project to `specified` as the human action the gate
requested.
