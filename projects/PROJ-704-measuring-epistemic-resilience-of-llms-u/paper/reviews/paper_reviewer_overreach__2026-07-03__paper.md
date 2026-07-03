---
action_items:
- id: 66ef55a4ced6
  severity: science
  text: The paper significantly overreaches by presenting empirical results for LLMs
    that do not currently exist. The manuscript explicitly lists and evaluates "GPT-5.4",
    "Gemini-3.1-pro/flash-lite", and "Claude-sonnet-4.6" in Section 5.1 and throughout
    Tables 1, 2, and 3. As of the current date, these model versions are not publicly
    available or released. By presenting specific accuracy metrics, Attack Success
    Rates (ASR), and detailed failure modes for these non-existent models, the authors
    extrapolat
artifact_hash: b321ce34848cd04bd8d899e341b97cc74f8e7595fd9393bb1f9638bbf57b0d10
artifact_path: projects/PROJ-704-measuring-epistemic-resilience-of-llms-u/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T00:52:18.521114Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: full_revision
---

The paper significantly overreaches by presenting empirical results for LLMs that do not currently exist. The manuscript explicitly lists and evaluates "GPT-5.4", "Gemini-3.1-pro/flash-lite", and "Claude-sonnet-4.6" in Section 5.1 and throughout Tables 1, 2, and 3. As of the current date, these model versions are not publicly available or released.

By presenting specific accuracy metrics, Attack Success Rates (ASR), and detailed failure modes for these non-existent models, the authors extrapolate beyond the scope of available data. The paper frames these results as a measurement of the current state of "epistemic resilience" in medical LLMs. This is a fundamental overreach: one cannot measure the resilience of a system that has not been built or released.

If the authors intended to simulate future models or use hypothetical parameters, this must be explicitly stated as a limitation or a theoretical exercise. Presenting the data as empirical findings from real API calls (implied by the specific version numbers and "accessed" language in Appendix C.1) misleads the reader regarding the validity of the evidence. The claim that "clean accuracy vastly overestimates epistemic resilience" is unsupported if the "clean accuracy" and "resilience" metrics are derived from non-existent systems.

Furthermore, the clinician review (Section 5.7) analyzes "harm" based on outputs from these same non-existent models. The conclusion that "38.2% of outputs pose serious harm" is an overreach if the outputs are synthetic or projected, as the clinical risk assessment relies on the authenticity of the model's behavior. The paper must either provide evidence that these models exist and were accessed, or reframe the entire study as a simulation/projection, acknowledging that the specific numerical results are hypothetical and not empirical measurements of current technology. Without this correction, the core scientific claims are unsupportable.
