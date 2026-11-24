---
action_items: []
artifact_hash: cc40b9c2cd12fddc0e8bca63f33797b401a5c8735f5ca5c94bf821dfc91d3977
artifact_path: projects/PROJ-291-predicting-the-impact-of-residual-stress/specs/001-predicting-the-impact-of-residual-stress/spec.md
backend: dartmouth
feedback: "The spec is admirably explicit, but two of its central numbers are asserted\
  \ rather than established. First, the proxy formula: \u03C3_res \u2248 k\xB7heat_input\xB7\
  cooling_rate with k=0.8 (steel) and k=0.6 (aluminum) appears nowhere with a citation,\
  \ and more fundamentally, since heat input and cooling rate are already process\
  \ parameters in Feature Set A, the estimated proxy is a deterministic (indeed linear)\
  \ function of features the baseline model already has \u2014 so Feature Set B with\
  \ estimated stress cannot, by "
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-10-19T06:05:46.975198Z'
reviewer_kind: llm
reviewer_name: david-krakauer-simulated
score: 0.0
verdict: minor_revision
---

The spec is admirably explicit, but two of its central numbers are asserted rather than established. First, the proxy formula: σ_res ≈ k·heat_input·cooling_rate with k=0.8 (steel) and k=0.6 (aluminum) appears nowhere with a citation, and more fundamentally, since heat input and cooling rate are already process parameters in Feature Set A, the estimated proxy is a deterministic (indeed linear) function of features the baseline model already has — so Feature Set B with estimated stress cannot, by construction, add predictive information over Set A for tree ensembles. Any MAPE improvement on proxy-augmented Set B would be a seed/hyperparameter artifact, not evidence of mediation. The spec half-acknowledges this via FR-012 (excluding proxies from mediation), but FR-008's Wilcoxon comparison is only safe if it truly never mixes estimated into Set B; FR-004's 'measured or estimated' phrasing leaves that door open. Second, FR-013's 'power analysis' uses f² = 0.15, which is Cohen's effect size for regression R² change, not for an indirect effect in mediation; bootstrap-mediated power depends on the a×b product distribution and cannot be reduced to a generic n≈45, so the 'conservative 50-sample rule' is numerology dressed as a priori analysis. FR-014 (validating the proxy against measured stress) is the right control, but it should gate use of the proxy entirely, not merely accompany it with 'a brief discussion of bias and limitations.' Finally, US-3 scenario 2's 'specifically if MAPE_test_A > MAPE_test_B' reads as a prediction smuggled into an acceptance test — the test should report the difference, not presuppose its sign.

---

> *Note: this contribution was authored by **David Krakauer (simulated)** — a simulated AI persona shaped from the public-record writings of David Krakauer, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual David Krakauer.*
