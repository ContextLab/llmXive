# Automated-review action items — Gamma-World: Generative Multi-Agent World Modeling Beyond Two Players

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The claim that Solaris uses 'dense joint attention' with quadratic cost (Sec 1, lines 38-40) is supported by the citation, but the paper does not explicitly state Solaris's complexity is O(P^2). Verify if Solaris's paper explicitly claims this or if the authors are inferring it from the architecture description.
- **[science]** The claim that the model generalizes from two to four players 'without additional training' (Abstract, line 24; Sec 1, line 68) relies on the simplex pool mechanism. Ensure the experimental setup (Sec 4.1) explicitly confirms that the 4-player evaluation used a checkpoint trained *only* on 2-agent data, with no fine-tuning or curriculum learning involving 4 agents.
- **[writing]** The claim that Sparse Hub Attention reduces cost to 'linear in the number of agents' (Abstract, line 18; Sec 3.2, line 138) is mathematically derived in the text. However, the empirical validation in Figure 3 (Sec 4.1) only shows results for 2, 4, and 8 agents. Ensure the text clarifies that the linearity is observed empirically within this range and not extrapolated beyond.
- **[writing]** The claim that the model achieves '24 FPS' (Abstract, line 22; Sec 3.3, line 178) is a specific performance metric. Verify that the experimental setup (Sec 4.1 or Appendix) specifies the hardware used for this measurement (e.g., specific GPU model) and the context (e.g., resolution, sequence length) to ensure the claim is reproducible and not misleading.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption contains a grammatical error and missing subject: 'We propose , a novel generative...' (the model name 'Gamma-World' is omitted).
- **[writing]** Figure 1: The URL provided in the caption is malformed and missing a slash: 'gamma-worldproject' should likely be 'gamma-world/project'.
- **[science]** Figure 2: The 'Self-attention FLOPS (analytical)' plot shows the blue line (Sparse Hub Attention) starting at 245.3G for 2 players, which is lower than the red line (Dense Attention) at 477.8G. However, the caption claims Sparse Hub Attention achieves lower FLOPs 'as the number of agents increases,' implying a scaling advantage. The plot shows the gap widening, but the absolute values for 2 agents suggest Sparse Hub is already more efficient, which might be a baseline issue or a specific archite
- **[writing]** Figure 2: The y-axis label in the third subplot is 'FLOPS', which denotes a rate (operations per second), but the values (e.g., 7.6T) represent total computational cost (FLOPs). This is a unit mismatch that could mislead readers about the metric being plotted.
- **[writing]** Figure 4: The caption states the first frame shows the 'initial state for one agent', but the image displays 'Initial State' labels for all four agents (Agent 1-4) simultaneously.
- **[writing]** Figure 4: The caption claims 'synchronized rollouts', but the visual content shows four distinct, independent first-person perspectives rather than a synchronized view of the agents interacting.
- **[science]** Figure 5: The caption claims to show 'real-world robotic coordination,' but the images depict a static living room scene with a cardboard box and a green box on a sofa. There are no visible robots, robotic arms, or agents performing actions, making the figure fail to support the caption's claim.
- **[writing]** Figure 5: The figure lacks a legend or labels to distinguish between 'Agent 1' and 'Agent 2' (or other agents) in the rows, unlike the clear labeling seen in Figure 3. Without this, the viewer cannot identify which agent is acting in the sequence.
- **[writing]** Figure 6: The caption contains empty parentheses 'using Simplex Rotary Agent Encoding (),' and 'through Sparse Hub Attention ()' where section numbers or citations are missing.
- **[writing]** Figure 6: The caption begins with 'takes synchronized observations...' but omits the model name (Gamma-World) at the start of the sentence.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'DiT' (Diffusion Transformer) at first use in Section 3.1. The acronym is used repeatedly without expansion, excluding readers unfamiliar with the specific transformer variant nomenclature.
- **[writing]** Define 'KV caching' (Key-Value caching) upon first mention in the Abstract and Section 3.3. While common in LLM circles, this term is jargon that should be briefly explained for a general computer vision or robotics audience.
- **[writing]** Replace 'rollout' with 'simulation run' or 'sequence generation' in the Abstract and Section 3.3. 'Rollout' is domain-specific jargon (often from reinforcement learning) that may be opaque to readers from other subfields.
- **[writing]** Define 'FVD' (Fréchet Video Distance) and 'FID' (Fréchet Inception Distance) at their first appearance in Section 4.1. These acronyms are standard but should be spelled out for non-specialist readers.
- **[writing]** Replace 'block-causal' with 'block-wise causal' or explain the specific masking mechanism in Section 3.1. The term is a compound jargon that assumes prior knowledge of specific attention masking strategies.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** The claim that Sparse Hub Attention reduces cost to 'linear in agents' (Sec 3.2) conflates total cost with cross-agent cost. The derived O(P nL^2) term is quadratic in sequence length. Clarify that linearity applies only to the cross-agent interaction term, not total inference cost.
- **[science]** The 'zero-shot generalization' to 4 players (Sec 4.2) relies on a fixed training pool of V=4 (App B). This is inference-time selection from learned identities, not true extrapolation to unseen counts (e.g., P=5). Clarify that scaling is bounded by the pre-defined pool size V.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The claim of generalizing 'without additional training' (Abstract) is overreaching. Appendix details show a simplex pool of size 4 was used during training. The model was exposed to 4-agent geometry, just not simultaneously active. Refine to 'zero-shot generalization to unseen counts within the trained pool'.
- **[science]** The claim that Sparse Hub Attention reduces cost to linear in P (Abstract, Sec 3.2) assumes fixed K. Table 4 shows quality improves as K increases. If K must scale with P for large populations, linearity fails. Clarify if K is fixed or adaptive in the scaling analysis.
- **[writing]** The '24 FPS' claim (Abstract) lacks hardware context. Appendix notes 32 GB200s were used. This overstates general deployability. Qualify as 'on high-end hardware' or provide latency breakdowns per agent count to justify the real-time label broadly.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The manuscript presents a generative multi-agent world model with significant potential for interactive simulation and embodied AI. From a safety and ethics perspective, the work is generally sound but requires specific clarifications regarding data provenance and dual-use implications before final acceptance. Data Provenance and Consent: The paper states in the abstract and Section 5 (Experiments) that it utilizes the "RealOmin-Open Dataset" and "generated Minecraft trajectories." While the lic

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim of zero-shot generalization from 2 to 4 agents (Sec 4.2, Fig 4) lacks quantitative metrics. Provide FVD/FID scores for the 4-agent setting to substantiate the visual evidence and rule out overfitting to the 2-agent training distribution.
- **[science]** The efficiency comparison in Fig 3 and Sec 4.2 reports latency and FLOPs but omits the actual generation quality (FVD/FID) for the 4 and 8 agent configurations. Without these metrics, the trade-off between the claimed linear scaling and potential quality degradation remains unverified.
- **[science]** The ablation study in Table 2 (Hub Token count) shows diminishing returns for K > 8, yet the main model uses K=8. The text does not explicitly justify why K=8 was chosen over K=32 or K=128 given the marginal quality gains, nor does it report the inference latency impact of increasing K.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Table 1 and Table 2 report point estimates for FVD, FID, LPIPS, PSNR, and SSIM without any measure of statistical uncertainty (e.g., standard deviation, standard error, or confidence intervals). Given that video generation metrics often exhibit high variance across seeds, the authors must report results averaged over multiple random seeds with error bars to substantiate the claimed improvements.
- **[science]** The efficiency claims in Figure 3 and Section 5.1 rely on latency and FLOPs measurements. The text states latency is 'averaged over 3 full rollouts' but does not specify if this accounts for system-level variance or if multiple independent runs were performed. Statistical significance testing (e.g., t-tests) or reporting variance across multiple independent hardware runs is required to confirm the robustness of the linear scaling claim.
- **[science]** The ablation study in Table 2 compares 'Simplex Encoding' vs 'View Embedding' and 'Sparse Hub' vs 'Full' attention. The differences in FVD (e.g., 228.5 vs 223.4) are small. Without reported standard deviations or statistical significance tests, it is unclear if these improvements are statistically distinguishable from noise or if they represent genuine architectural gains.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.2, the sentence 'This hub-mediated topology preserves a shared communication pathway...' is redundant as the preceding sentence already states hub tokens provide this pathway. Merge or delete to improve flow.
- **[writing]** In Section 3.3, the phrase 'train--test mismatch' uses an en-dash. Ensure consistency with the rest of the document, as standard English typically uses a hyphen for compound adjectives like 'train-test mismatch'.
- **[writing]** In the Abstract, a sentence starting 'Finally, we use a bidirectional multi-agent teacher...' is commented out in the LaTeX source. Uncomment it if intended, or remove it entirely to avoid confusion.
