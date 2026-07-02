---
action_items:
- id: 773ebafd02f8
  severity: writing
  text: The claim of '8.75x fewer iterations' (Abstract) compares 600K (Static) vs
    1.75M (SiT). However, the best ODE FID comes from Dynamic (500K), implying a 3.5x
    speedup. Clarify which variant supports the 8.75x claim or correct the multiplier
    to match the best-performing model's data.
- id: 45233901a42f
  severity: science
  text: Section 5.2 claims the dynamic query works because $v_{l-1}$ retains timestep
    info, but the linear probe measures $h_l$ (aggregated state), not $v_{l-1}$ (query
    input). The logic requires confirming the probe was on $v_{l-1}$ or explaining
    why $h_l$ is a valid proxy for the query's input signal.
- id: 4650a6672eab
  severity: science
  text: Proposition 1 derives optimal chunk size $S^*$ from a theoretical cost function,
    yet Table 4 shows empirical FID results. The paper assumes minimizing this theoretical
    cost minimizes FID without proving the correlation. Clarify if the cost function
    was empirically validated against FID or if the agreement is coincidental.
artifact_hash: 7a4bc7e64a39662319f7490ada4c2be57d6c20dd18ca5f1225c2e0b697bf14b3
artifact_path: projects/PROJ-625-https-arxiv-org-abs-2605-20708/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T22:58:35.710054Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a coherent logical flow from diagnosing residual stream issues in DiTs to proposing Diffusion-Adaptive Routing (DAR). The argument that standard residuals cause magnitude inflation and gradient decay is well-supported by the diagnostic plots in Section 3. The connection between these symptoms and the need for timestep-adaptive routing is also logically sound.

However, three specific logical gaps or inconsistencies require attention:

1.  **Iteration Count Discrepancy:** The Abstract and Introduction state an "$8.75\times$ fewer training iterations" improvement. This figure is calculated by comparing the Static c4 variant (600K iterations) to the SiT baseline (1.75M iterations). However, Table 1 shows the Dynamic c4 variant, which achieves the best ODE FID (2.05), uses only 500K iterations. If the "best" model is the Dynamic variant, the speedup is $1.75M / 500K = 3.5\times$, not $8.75\times$. The text must clarify whether the $8.75\times$ claim applies specifically to the Static variant or if the multiplier should be corrected to reflect the efficiency of the best-performing model.

2.  **Probe Target Mismatch:** In Section 5.2, the authors argue that the dynamic query $q_l(t) = W_q^{(l)} v_{l-1}$ is effective because $v_{l-1}$ retains sufficient timestep information. To support this, they perform a linear probe on the "aggregated hidden state $h_l$ that feeds each sublayer's router." Logically, the probe should be performed on $v_{l-1}$ (the input to the query projection), not $h_l$ (the output of the aggregation). Since $h_l$ is a weighted sum of previous states, it might obscure the specific signal source needed for the query mechanism. The text needs to clarify that the probe was indeed conducted on $v_{l-1}$ or explain why $h_l$ is a valid proxy for the query input's information content.

3.  **Theoretical Cost vs. Empirical FID:** Proposition 1 derives an optimal chunk size $S^*$ based on a theoretical cost function $\mathcal{L}(S)$ representing information-theoretic bounds on routing precision and compression. The paper then asserts this explains the empirical U-shaped FID curve in Table 4. While the numerical agreement ($S^* \approx 4$) is compelling, the logical link between minimizing a theoretical "routing precision/compression cost" and minimizing FID (a complex perceptual metric) is not established. The authors should explicitly state whether they observed a correlation between the theoretical cost and FID during their search, or if the agreement is a post-hoc observation, to avoid implying a direct causal derivation that isn't proven.
