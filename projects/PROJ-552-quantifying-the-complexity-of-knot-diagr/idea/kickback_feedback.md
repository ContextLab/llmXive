# Downstream review concerns (address in this revision)

A downstream convergence panel kicked this project back to the idea stage,
and the maintainer has reviewed the escalation and made the scope decision
the panel kept requesting. You MUST apply this decision to the idea —
especially the research question and `Methodology sketch` — exactly as
stated, not merely re-state the prior idea.

**Why it was kicked back**: the spec panel's scope/scientific-soundness
reviewers repeatedly flagged (concerns scope-03fd3302, scope-2b46267f,
scope-8deb7e69, scope-77778c77) that operationalizing "hyperbolic volume"
silently restricts the population from "prime knots" to "hyperbolic prime
knots", and that the added invariants / composite score exceed the idea's
stated methodology.

## MAINTAINER DECISION (apply verbatim — this resolves the scope dispute)

1. **Restate the research question over HYPERBOLIC prime knots.**
   Hyperbolic volume is mathematically defined ONLY for hyperbolic knots
   (torus and satellite knots have no hyperbolic structure), so the
   restriction is forced by the invariant itself, not a scope drift. The
   research question becomes: "To what extent do crossing number and braid
   index jointly predict the hyperbolic volume of HYPERBOLIC prime knots,
   and does this relationship differ systematically between alternating
   and non-alternating classes?" State explicitly in the motivation that
   the overwhelming majority of prime knots at ≤13 crossings are
   hyperbolic (per Thurston's classification; torus/satellite knots are
   rare at low crossing number), and require the analysis to REPORT the
   exact excluded count as a dataset statistic.
2. **Drop the composite complexity score and the additional invariants
   (arc index, Seifert circle count, bridge number) from Phase 1
   entirely.** The core study is: crossing number + braid index →
   hyperbolic volume, stratified by alternating/non-alternating. Mention
   additional invariants only under "Future work", not in the methodology
   sketch, so the spec stops re-acquiring them.
3. Keep the validated-scope split exactly as already converged:
   data availability ≤13 crossings, validated completeness ≤10, 11–13
   exploratory with qualified conclusions.
