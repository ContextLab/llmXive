---
action_items:
- id: 47fe3631fda5
  severity: science
  text: Clarify the teacher source for L_DMD_BS in the Effect Stream (Sec 4.4). Is
    it the base model (like General Stream) or the specific effect teacher? The current
    text implies it acts as a regularizer but lacks logical precision on the target
    distribution.
- id: e19d877e031b
  severity: science
  text: The claim that AOP creates 'orthogonal subspaces' enabling zero-shot composition
    (Sec 5.2) lacks supporting evidence. Provide empirical proof (e.g., embedding
    similarity) or remove the causal claim linking orthogonality to the emergent capability.
- id: b95cd01abf08
  severity: writing
  text: The Introduction claims routing latency is 'fundamentally resolved,' yet Sec
    5.1 states routing reverts for 100+ LoRAs. Reconcile this contradiction by clarifying
    the scaling threshold where routing is re-enabled.
artifact_hash: 2a1b4c65ebf4844ee4cfea5a1931c70997d4322d1755391c095bba4101b76763
artifact_path: projects/PROJ-643-collectionlora-collecting-50-effects-in/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T19:50:25.866209Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The logical consistency of the paper is generally strong in its problem formulation and the high-level motivation for the proposed framework. The transition from identifying the "Dilemma of Multi-Module Composition" (Section 4.1) to the "Proposed Paradigm" is well-reasoned. However, there are specific gaps in the logical derivation of certain claims and the precise definition of the optimization objectives that require clarification.

First, in Section 4.4 (Coarse-to-Fine Distillation Objective), the formulation of the total loss $\mathcal{L}_{\text{C2F-DO}}$ includes $\mathcal{L}_{\text{DMD\_BS}}$ (Backward Simulation). The text describes this term as a "persistent regularizer" within the Effect Stream. However, Section 4.2 defines the General Stream as utilizing $\mathcal{L}_{\text{DMD\_BS}}$ with the *frozen base model* as the teacher. The logical connection is ambiguous: does the $\mathcal{L}_{\text{DMD\_BS}}$ term in the Effect Stream also use the base model (acting as a generalization anchor) or the specific effect teacher? If it uses the effect teacher, it effectively becomes a standard DMD loss, which the authors claim causes collapse in the early stages. If it uses the base model, the logic of why it is included in the *Effect* stream (which is supposed to learn the effect) needs explicit justification to avoid circular reasoning regarding the "distribution gap."

Second, the claim of "zero-shot effect composition" in Section 5.2 relies heavily on the Asymmetric Orthogonal Prompting (AOP) strategy. The authors assert that AOP "encodes each effect into an orthogonal subspace of the prompt manifold," enabling compositional activation. While this is a plausible hypothesis, the paper lacks the logical or empirical evidence to support the premise of orthogonality. There is no analysis of the prompt embeddings (e.g., cosine similarity between trigger words) or ablation showing that non-orthogonal triggers fail to compose. The conclusion that the emergent capability is *caused* by the orthogonality of the prompts is an assumption not fully supported by the provided evidence, which only shows the *result* of the composition.

Finally, there is a minor logical tension regarding the deployment claims. The Introduction states the method "fundamentally resolves" routing latency. However, Section 5.1 admits that for 100-150 LoRAs, the method "reverts to VLM routing." While the storage overhead is still reduced, the re-introduction of routing logic at scale suggests the solution is not a complete elimination of the routing problem but a mitigation up to a certain threshold. The text should be adjusted to reflect this nuance to maintain logical consistency between the abstract claims and the detailed experimental analysis.
