---
action_items:
- id: cb33a4c71d42
  severity: writing
  text: Replace 'token-gradient vectors' with 'token gradients' throughout (e.g.,
    Abstract, Line 13) to reduce compound noun density.
- id: d1cb23ff58a4
  severity: writing
  text: Define 'LM-head' explicitly as 'language model head' on first use in Appendix
    (Line 1050) for non-specialist clarity.
- id: ff14e4de9a14
  severity: writing
  text: Simplify 'entropy-regularized assignment problem' (Line 230) to 'score calculation
    using entropy' to improve accessibility.
- id: f7185d3c219b
  severity: writing
  text: Replace 'stop-gradient token coefficients' (Line 260) with 'fixed token weights'
    to avoid implementation-specific jargon in main text.
- id: 9123da0516d7
  severity: writing
  text: Define 'GAE' (Generalized Advantage Estimation) when first used in SAPO hyperparameter
    table (Appendix) or text, as 'Gae Gamma' and 'Gae Lam' appear without context.
- id: 537a57eda482
  severity: writing
  text: Define 'CoT' (Chain of Thought) before using the abbreviation in Appendix
    (Line 1650, 'long-CoT RL training').
- id: aa0093a979ad
  severity: writing
  text: Define 'SGLang' in Table 1 (Line 1200) as it is an external inference engine
    not defined elsewhere.
- id: a46ad0aa6970
  severity: writing
  text: Replace 'side-wise centroids' with 'group averages' throughout (e.g., Section
    3.1, Line 310) to reduce jargon density.
- id: 81438054e410
  severity: writing
  text: Add plain-language explanation for 'self-normalized RLVR surrogate' when first
    introduced (Section 3.2, Line 420).
- id: 62b8a84f03ab
  severity: writing
  text: Replace 'positive-advantage responses' / 'negative-advantage responses' with
    'high-reward / low-reward responses' for accessibility.
artifact_hash: 8558369ae7497b07133b578546b356e5acc6d5d811b01a15639e1519377b2963
artifact_path: projects/PROJ-619-delta-discriminative-token-credit-assign/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-08T16:46:36.829492Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

**Re-Review Assessment: Jargon Overuse**

This re-review confirms that **none of the seven prior action items have been adequately addressed** in the current revision. All original concerns persist:

1. **cb33a4c71d42**: "token-gradient vectors" still appears throughout (Abstract, Sections 1-3, Appendices) without simplification to "token gradients."

2. **d1cb23ff58a4**: "LM-head" appears in Section 3 and Appendix A without explicit definition as "language model head."

3. **ff14e4de9a14**: "entropy-regularized assignment problem" (Equation 13 description) retains technical jargon instead of "score calculation using entropy."

4. **f7185d3c219b**: "stop-gradient token coefficients" continues to appear in main text (Section 3.2) rather than "fixed token weights."

5. **9123da0516d7**: GAE parameters ("Gae Gamma", "Gae Lam") in Appendix Table SAPO hyperparameters lack definition of the acronym.

6. **537a57eda482**: "long-CoT RL training" (Appendix Baseline Details) uses undefined CoT abbreviation.

7. **aa0093a979ad**: SGLang in Table 1 (Line 1200) remains undefined as an inference engine.

**New Jargon Concerns Identified:**

- "side-wise centroids" appears repeatedly (Sections 3.1-3.2) and could be "group averages" for non-specialist readers.
- "self-normalized RLVR surrogate" (Equation 16) lacks plain-language explanation.
- "positive-advantage responses" / "negative-advantage responses" could be simplified to "high-reward / low-reward responses."

**Recommendation**: All 10 action items require addressing before acceptance. These are writing-class issues fixable through manuscript editing alone.
