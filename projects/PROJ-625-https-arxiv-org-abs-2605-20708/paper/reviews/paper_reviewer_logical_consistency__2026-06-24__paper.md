---
action_items:
- id: b292a44b4295
  severity: science
  text: Provide a direct causal analysis linking the reduction of each diagnosed symptom
    (forward magnitude inflation, backward gradient decay, block-wise redundancy)
    to the observed performance gains (FID/IS). For example, include ablations where
    only one symptom is mitigated to isolate its impact.
- id: aa9c051ccfd4
  severity: writing
  text: "Clarify the apparent contradiction between the claim that standard residuals\
    \ cannot adaptively weight earlier layers and the counterfactual gate experiment\
    \ (Fig.\u202F5) which shows timestep\u2011dependent source importance even without\
    \ an explicit router."
- id: 45711407249a
  severity: writing
  text: "Re\u2011evaluate the claim that the dynamic query variant is superior to\
    \ the static variant with explicit timestep injection; the current ablation (Table\u202F\
    4) shows comparable or better performance for the static\u2011with\u2011t\u2011\
    injection model."
- id: 2fefb69eadcb
  severity: science
  text: "Report quantitative measurements of how DAR affects the forward hidden\u2011\
    state magnitude and gradient magnitude across depth, to substantiate the argument\
    \ that DAR alleviates PreNorm dilution."
- id: 427300163bee
  severity: writing
  text: "In the chunk\u2011size analysis, explicitly state the assumed values of the\
    \ hyper\u2011parameter \u03B1 used in Eq.\u202F(9) and verify that the predicted\
    \ S* aligns with the empirical optimum for the exact \u03B1 chosen."
artifact_hash: 7a4bc7e64a39662319f7490ada4c2be57d6c20dd18ca5f1225c2e0b697bf14b3
artifact_path: projects/PROJ-625-https-arxiv-org-abs-2605-20708/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-24T18:00:13.312266Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The manuscript presents a systematic empirical diagnosis of three “symptoms” of the standard residual stream in Diffusion Transformers (DiTs) and proposes Diffusion‑Adaptive Routing (DAR) as a remedy. Overall the logical flow is coherent, but several conclusions are not fully justified by the presented evidence.

1. **Causal link between diagnosed symptoms and performance**  
   The authors argue that forward magnitude inflation, backward gradient decay, and block‑wise redundancy are detrimental and that DAR’s improvements stem from mitigating these issues. However, the paper only shows that DAR reduces the symptoms (Fig. 2) *and* improves FID/IS (Table 1). There is no ablation that isolates each symptom’s contribution to the final quality. Without such a controlled experiment, the claim that the performance gains are caused by symptom reduction remains an inference rather than a demonstrated causal relationship.

2. **Residual “inability” vs. implicit weighting**  
   Section 3 states that standard residuals “cannot explicitly decide which earlier representations should be retrieved or suppressed.” Yet the counterfactual gate experiment (Fig. 5) demonstrates that, even without an explicit router, the network exhibits timestep‑dependent source preferences. This suggests that the residual pathway does have an implicit, gradient‑driven weighting mechanism. The manuscript should reconcile this apparent contradiction, perhaps by clarifying that the implicit weighting is not learnable in the forward pass and therefore less flexible than the explicit attention‑based routing.

3. **Dynamic vs. static query with explicit timestep injection**  
   The paper emphasizes that the dynamic query (query = W_q v_{l‑1}) is crucial because it injects timestep information implicitly. Yet Table 4 shows that a static query augmented with the existing timestep embedding (static + t‑injection) achieves comparable or even better FID at later training stages. The narrative that the dynamic variant is categorically superior is therefore overstated; the authors should either provide additional evidence (e.g., training speed, stability) or temper the claim.

4. **Evidence that DAR alleviates PreNorm dilution**  
   The diagnosis of PreNorm dilution is based on the monotonic increase of RMS(z_k) (Fig. 2). While DAR replaces the additive residual with a softmax‑weighted sum, the manuscript does not present explicit plots of RMS(z_k) or gradient magnitude after DAR is applied. Demonstrating that DAR indeed curtails magnitude inflation and restores more uniform gradient flow would strengthen the argument that the architectural change directly addresses the identified pathology.

5. **Chunk‑size theoretical justification**  
   Proposition 1 provides a U‑shaped cost model with a closed‑form optimum S*. The empirical sweep (Table 5) shows S = 4 as optimal, matching the predicted range for reasonable α. However, the paper does not disclose the exact α used in Eq. (9) nor show the computed S* for that α. Including these details would make the theoretical‑empirical alignment transparent.

6. **Orthogonality to REPA**  
   The claim that DAR is orthogonal to REPA is supported by Table 3, where the combination yields better FID than REPA alone. This logical inference is sound, though a brief discussion of why the two methods do not interfere (e.g., different loss components vs. architectural changes) would improve clarity.

In summary, the manuscript’s logical structure is solid, but several key conclusions are presented without sufficient empirical justification. Addressing the points above will tighten the logical chain from diagnosis to proposed solution and its measured benefits.
