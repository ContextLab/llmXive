---
action_items:
- id: 69de55c9bd14
  severity: writing
  text: The paper presents an extensive benchmark of 24 optimizers across multiple
    scales and architectures, but the evidentiary strength of the central claims is
    compromised by a lack of variance reporting and potential confounds in hyperparameter
    tuning. First, the headline results in Section 4.2 (Tables 1, 2, and 3) are presented
    as definitive rankings based on single training runs. For instance, the claim
    that APOLLO achieves a PPL of 13.53 at 1B parameters, significantly outperforming
    AdamW (14.48)
artifact_hash: dbc48f30e617ac30caed20a396534de7c2a315d3d80c0dacd34ca49ae13f2258
artifact_path: projects/PROJ-1007-omniopt-taxonomy-geometry-and-benchmarki/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-08T03:12:49.563293Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents an extensive benchmark of 24 optimizers across multiple scales and architectures, but the evidentiary strength of the central claims is compromised by a lack of variance reporting and potential confounds in hyperparameter tuning.

First, the headline results in Section 4.2 (Tables 1, 2, and 3) are presented as definitive rankings based on single training runs. For instance, the claim that APOLLO achieves a PPL of 13.53 at 1B parameters, significantly outperforming AdamW (14.48), is reported without any measure of stability (standard deviation, standard error, or confidence intervals). In large-scale LLM training, performance can vary by 0.5–1.0 PPL points across different random seeds due to initialization and stochasticity. Without reporting results across at least 3–5 seeds, it is impossible to distinguish a genuine algorithmic improvement from a lucky seed. The current design cannot rule out that the reported "best" optimizers are simply the result of favorable random initialization.

Second, the dramatic failure mode attributed to APOLLO in long-context training (Section 4.2, "Scenario Sensitivity") appears confounded by hyperparameter settings. The text claims APOLLO collapses (PPL 35.40) while AdamW remains stable, but the hyperparameter table (Appendix) reveals that APOLLO was trained with a learning rate of 0.01 at 1B scale, whereas AdamW used 0.001. This tenfold difference in learning rate is a massive confound; the "collapse" could easily be a result of the optimizer being pushed into an unstable regime by an aggressive learning rate rather than an intrinsic inability to handle long contexts. To support the claim that APOLLO is "rank-bounded" or "fails" in long contexts, the authors must demonstrate this failure under a matched or carefully tuned learning rate schedule comparable to the baseline.

Finally, the mechanistic ablation of Muon (Section 4.2) attributes performance gains primarily to the Newton-Schulz (NS) orthogonalization step. However, the ablation compares the full Muon method against a baseline that likely differs in both the orthogonalization operator and the momentum state evolution (S3). The Muon paper specifically modifies how momentum is accumulated in the matrix space. Without a control run that keeps the Muon-specific momentum state evolution but removes the NS orthogonalization (replacing it with identity), the design cannot isolate the contribution of the geometric operator from the state evolution changes. The reported gains might be driven by the momentum structure rather than the orthogonalization itself.

To strengthen the evidence, the authors should: (1) report mean and standard deviation over multiple seeds for all key benchmark results; (2) re-run the long-context APOLLO experiments with a learning rate schedule matched to AdamW to rule out tuning artifacts; and (3) refine the Muon ablation to isolate the NS operator from the momentum state evolution.
