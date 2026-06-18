---
action_items:
- id: 3cc4a76ddb0f
  severity: science
  text: "Clarify the underlying assumption that token vectors are well\u2011aligned\
    \ with the subspace spanned by expert weight matrices; provide empirical or theoretical\
    \ justification that maximizing the Rayleigh quotient of R\u1D62W\u1D62 indeed\
    \ leads to higher token\u2011expert affinity."
- id: 6d50f56dde3a
  severity: writing
  text: "Explicitly discuss how the retraction step (norm normalization) may affect\
    \ the load\u2011balancing loss, and separate its impact from genuine improvements\
    \ in routing balance to avoid conflating two effects."
- id: 5b70c609a9cc
  severity: writing
  text: "Re\u2011examine the claim that a single power\u2011iteration step per training\
    \ update is sufficient for convergence toward the principal singular direction;\
    \ either provide a convergence bound or qualify the claim as an empirical observation."
artifact_hash: 34fabb025335fc2fcf0855d53316dbb275a62eee03c0f1ad1b72c49ea11b1392
artifact_path: projects/PROJ-697-redesign-mixture-of-experts-routers-with/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T04:38:39.284843Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The manuscript presents a principled redesign of Mixture‑of‑Experts (MoE) routers by aligning each router row with the principal singular direction of its associated expert weight matrix via a “Power‑then‑Retract” (Manifold Power Iteration, MPI) update. The logical chain of the argument is largely coherent: the objective (Eq. 1) is a Rayleigh quotient whose maximizer is the dominant eigenvector of WᵢWᵢᵀ; a power‑iteration step (Eq. 2) indeed moves a vector toward this eigenvector; normalization (retraction) keeps the update stable; and the derived manifold gradient (Sec. 3.3) mirrors the MPI update up to a scalar factor.

However, a key logical leap is made when the paper asserts that aligning router rows with the principal singular direction automatically yields “more faithful token‑expert affinity.” This claim presupposes that token representations **x** lie in, or are strongly correlated with, the subspace spanned by the expert weight matrices. No formal justification or empirical evidence is offered for this assumption; the token‑router inner product could be dominated by aspects of x unrelated to the expert’s dominant direction, weakening the causal link between the alignment objective and improved routing quality. The paper would benefit from either (i) a theoretical argument that typical token embeddings (e.g., after the embedding layer or a projection) are expected to occupy the same subspace as the expert weights, or (ii) empirical diagnostics (e.g., cosine similarity distributions) demonstrating that the alignment indeed correlates with higher gating scores for appropriate experts.

Another subtle inconsistency concerns the reported improvement in load‑balancing loss (Fig. 5). The authors note that the reduction may be an artifact of the retraction step, yet they also present the lower MaxVio metric as evidence of improved balance. Without a controlled ablation that isolates the effect of retraction from the alignment mechanism, the claim that MPI “improves load balancing” remains logically ambiguous.

Finally, the statement that a single power‑iteration per training step “suffices” is presented as a theoretical guarantee, yet the derivation only shows that each step moves the router toward the dominant eigenvector; convergence speed depends on the spectral gap of WᵢWᵢᵀ. The empirical observation that more iterations hurt throughput is valid, but the paper should qualify the sufficiency claim or provide a bound on the expected alignment after one iteration.

In summary, the logical structure of the method and its derivations is sound, but the manuscript makes causal claims (better routing quality, load‑balancing improvement) that are not fully substantiated by the presented theory or experiments. Addressing these gaps will strengthen the logical consistency of the work.
