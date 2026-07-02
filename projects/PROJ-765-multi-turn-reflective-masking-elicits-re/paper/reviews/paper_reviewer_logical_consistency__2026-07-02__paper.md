---
action_items:
- id: 2039920dc322
  severity: science
  text: Section 3.1 claims the deterministic inference rule causes loops, and Section
    3.2 asserts History Reference fixes this by changing input. However, the paper
    does not logically prove that the new input distribution breaks the fixed-point
    cycle, only that it 'addresses' it. A formal argument or empirical proof of termination
    is missing.
- id: e811414908bc
  severity: science
  text: Appendix A.1 (Theorem 1) assumes a 'rich-family' model class to prove convergence
    to the oracle distribution. The experiments use finite-capacity models (e.g.,
    0.81M params). The paper fails to logically bridge the gap between the infinite-capacity
    theoretical guarantee and the empirical performance of the specific small models
    used.
- id: f896715039bd
  severity: writing
  text: In Section 4.2, the ablation distinguishes between 'History Reference' and
    'decay', yet Eq. 2 defines the mechanism inherently with decay. The claim that
    'decay alone' performs worse is logically ambiguous because the mechanism definition
    includes decay. The distinction between the mechanism structure and the decay
    parameter needs clarification.
artifact_hash: 7fece54febe808e7b8d966174edf071d45cfb2bebbcbdcb010a99fdaf0b84671
artifact_path: projects/PROJ-765-multi-turn-reflective-masking-elicits-re/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T15:34:52.833194Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a coherent high-level argument: Mask Diffusion Models (MDMs) support local edits, but standard decoding is passive; therefore, training the model to actively decide when to re-mask (Reflective Masking) should enable reasoning. However, several logical gaps exist where conclusions do not strictly follow from premises or rely on unverified assumptions.

First, regarding the inference mechanism (Section 3.1), the authors define a deterministic rule (Eq. 1) that can lead to state loops. They introduce History Reference (Section 3.2) to break these loops by altering the input conditioning. While the intuition is plausible, the paper asserts the rule is "unchanged" while the input changes, and that this "addresses" the loop. Logically, changing the input distribution does not guarantee the elimination of fixed points in a deterministic system unless the new dynamics are proven to be non-cyclic or contractive. The paper lacks a formal argument or empirical evidence (e.g., trajectory length analysis) proving that History Reference *necessarily* breaks the loops rather than just shifting them. The conclusion that the method "enables test-time scaling" relies on the unproven assumption that the process terminates.

Second, the theoretical justification in Appendix A.1 (Theorem 1) relies on a "rich-family idealization" where the model class can perfectly represent the conditional label distribution. The paper claims minimizing the training loss drives the model toward this distribution. However, the experiments use specific, finite-capacity models (e.g., a 0.81M parameter model for Sudoku). The logical leap from the population minimizer (infinite capacity) to the empirical performance of these specific small models is not bridged. The paper does not discuss approximation error or conditions under which the finite model class can approximate the oracle well enough to justify the "Bayes-optimal" claims. The conclusion that the method "activates" a latent capability assumes the model has the capacity to learn it, which is an empirical claim not fully supported by the theoretical premises.

Finally, in the Sudoku ablation study (Section 4.2), the logical distinction between the "History Reference" mechanism and the "decay" parameter is ambiguous. Equation 2 defines the History Reference embedding explicitly including a decay factor $\gamma$. The table compares a variant without decay (implied) against one with decay. The text claims "introducing a decay factor alone... performs worse," implying decay is a separate component. However, if the mechanism *is* the accumulation with decay, then the "no decay" variant is a specific instantiation, not a separate one. The causal claim that "properly structuring historical information" is crucial is sound, but the specific attribution of gains to "decay" versus "rotation" is muddied by the definition of the mechanism itself. The paper should clarify whether "History Reference" refers to the accumulation structure (with or without decay) or specifically the decayed accumulation to ensure logical consistency in the ablation.
