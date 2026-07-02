# Automated-review action items — MinT: Managed Infrastructure for Training and Serving Millions of LLMs

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The abstract and Section 4 claim a 18.3x handoff reduction on a 4B model. Table 1 (e1_handoff_paths) shows 71.82s (merge) vs 0.036s (adapter load), which is ~1995x. The 18.3x figure likely refers to the total step time (55.7s vs 4.1s). The text must clarify that the 18.3x applies to the end-to-end step, not just the handoff artifact transfer, to avoid misrepresenting the data.
- **[writing]** The abstract claims a 2.85x handoff reduction on a 30B MoE model. Table 1 shows 402.2s (merge) vs 46.5s (adapter load), a ratio of ~8.6x. The 2.85x figure corresponds to the total step time (156s vs 117s). The text incorrectly attributes the step-time speedup to the 'handoff step' specifically, conflating the artifact transfer with the full generation latency.
- **[writing]** Section 4 claims packed MoE LoRA tensors improve 'live engine loading' by 8.5–8.7x. Table 4 (e4_packed_loader) confirms this speedup for the 'live engine loading' slice (1.36s -> 0.16s). However, the text implies this is the total cold-load time. The paper explicitly states elsewhere that total cold latency includes routing and fetch (199s). The claim needs to strictly specify that the 8.5x speedup applies only to the tensor-loading slice, not the full cold-path latency.
- **[writing]** The abstract states the system supports '10^6-scale addressable policy catalogs' and 'measured single-engine sweeps through 100K entries'. Section 4 clarifies the 1M number is an extrapolation from Appendix Table F (fleet_model), while the 100K is the measured sweep. The abstract presents the 1M figure as a direct system capability without immediately qualifying it as a modeled extrapolation, which risks overstating the empirical evidence.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The 'Wall time saved' legend entry (light blue) is not represented in the timeline charts; the light blue background shading is undefined in the legend and caption, creating ambiguity between the metric and the visual element.
- **[writing]** Figure 1: The 'Idle samples, GPU util. <10%' chart title is truncated to 'Idle samples, GPU util. <10%', which is grammatically incomplete and likely a rendering error for 'Idle samples (GPU util. <10%)'.
- **[science]** Figure 2: The 'Adapter' bars are labeled with 'materialize / admit' in the legend, but the caption states they represent 'adapter loading'. The visual composition (mostly teal/rollout) contradicts the legend's blue label for the 'Adapter' condition, creating ambiguity about which component is being measured.
- **[writing]** Figure 2: The y-axis scales differ significantly between the Qwen3-4B (0-80s) and Qwen3-30B (0-600s) panels without explicit indication that they are not directly comparable in height, which could mislead readers about the relative magnitude of the speedup.
- **[science]** Figure 4: The caption claims 'aligned y axes' for the 30B/235B panels, but the visual y-axis ranges differ (0.55–1.00 vs 0.55–1.00 is consistent, but the tick marks and grid lines suggest different scaling or alignment issues; verify if 'aligned' refers to range or scale).
- **[writing]** Figure 4: The legend in the Kimi K2 panel ('run trace' and 'smoothed') is not explicitly defined in the caption, though it is visually clear; consider adding a brief note in the caption for completeness.
- **[science]** Figure 5: The caption defines a 'black diamond' as the full-manifest control, but this symbol is not visible in the plot area.
- **[science]** Figure 5: The legend labels the dashed line as 'Full eval result', but the caption describes these as 'violet points' (full LawBench evaluations), creating a conflict between the legend and the caption.
- **[writing]** Figure 5: The legend entry for 'Proxy running best' is missing the corresponding line sample (solid blue line) that is visible in the plot.

## paper_reviewer_jargon_police — verdict: full_revision

- **[writing]** Define 'DSA' (Dynamic Sparse Attention) and 'MLA' (Multi-Head Latent Attention) at first use. These acronyms appear in the Abstract and Section 4 without definition, excluding readers unfamiliar with specific model architectures like GLM-5 or Kimi K2.
- **[writing]** Replace 'materializing' with 'creating' or 'generating' in the Abstract and Section 2. 'Materializing' is unnecessary jargon in this context and obscures the simple action of writing a full checkpoint to disk.
- **[writing]** Define 'IcePop' in Section 4.1. The text references 'IcePop-style rollout correction' as a known method without explaining what IcePop is or what the correction entails, assuming prior knowledge of a specific paper or technique.
- **[writing]** Replace 'fanout' with 'number of objects' or 'count of small files' in Section 4.2 and Section 5.3. 'Fanout' is a database/networking term that is slightly misapplied here to describe the number of tensor objects in a file, potentially confusing non-specialists.
- **[writing]** Define 'R3' in Section 4.1. The text states 'R3 identifies router mismatch' without defining R3 as a specific method, paper, or internal tool, making the sentence opaque to general readers.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Clarify the scope of the '8.5–8.7x' speedup claim in the abstract. The data supports this only for the 'live engine-load slice' (post-fetch), not end-to-end cold load. Ensure the abstract explicitly limits this metric to avoid implying total latency reduction.
- **[science]** Resolve the numerical discrepancy in Section 4.2. The text claims an 18.3x handoff reduction, but Table 2 shows a ~1995x difference in 'Materialization or load' times (71.8s vs 0.036s). Explicitly define the denominator used for the 18.3x figure to align with the raw data.
- **[writing]** Distinguish between measured and theoretical limits for the 10^6 catalog claim. The paper only measures up to 100k entries; the 1M figure is an extrapolation. Explicitly state this is a theoretical bound derived from the fleet model, not an empirical result.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The 1M catalog claim is an extrapolation from Appendix Table F, not a measured result. Clarify that 100k is the measured limit and 1M is a capacity model projection to avoid over-claiming empirical validation.
- **[writing]** The 8.5-8.7x speedup applies only to the 'live engine-load slice' (Table 5), not total cold latency (~190s). Restrict the claim to the specific registration phase to prevent over-generalization of end-to-end performance.
- **[writing]** The DSA support is described as a solution but admits lacking full replay (Section 4). Rephrase to state MinT offers a partial mitigation (IcePop masking) rather than a complete resolution of the DSA mismatch problem.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper claims to manage 'millions of LLMs' and 'million-scale LoRA policy catalogs' (Abstract, Sec 4.3). While framed as infrastructure, this scale of multi-tenant policy management introduces significant risks of model leakage, prompt injection across tenants, and unintended behavior propagation. Explicitly detail the isolation guarantees, access control mechanisms, and audit logging strategies for this scale.
- **[writing]** The system supports 'AutoResearch' and 'agentic RL' (Sec 5.2, Sec 6) where agents autonomously modify policies. There is no discussion of safety guardrails, human-in-the-loop approval for policy promotion, or mechanisms to prevent the system from optimizing for harmful objectives (e.g., jailbreaking) during the RL loop. A safety section is required.
- **[writing]** The paper mentions 'tenant-specific variants' and 'personalization branches' (Sec 4.3) but does not address data privacy, consent, or the potential for training on sensitive user data without explicit user consent. Clarify the data governance framework and compliance with privacy regulations (e.g., GDPR, CCPA) for these multi-tenant scenarios.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Section 5.1 and Table 1 report specific speedup factors (1.77x, 1.45x) and latency reductions (18.3x) based on single-point measurements. The paper lacks statistical validation (e.g., standard deviations, confidence intervals, or p-values) across multiple runs to confirm these gains are robust against system noise or scheduling variance.
- **[writing]** The 'Scale Out' claim of 10^6 addressable policies (Abstract, Sec 4.3) relies on an extrapolation in Appendix Table 6 (fleet_model) rather than direct measurement. The paper should explicitly clarify that the 10^6 figure is a theoretical capacity model derived from single-engine limits, not an empirically observed system state.
- **[science]** In Section 5.2, the MoE router replay (R3) results cite extremely low out-of-route ratios (0.0013%). The evidence does not specify the total token count or number of steps over which these ratios were aggregated, making it difficult to assess the statistical significance of the stability improvement.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Section 5.1 and Table 1 report single-point speedup metrics (e.g., 1.77x, 1.45x) and latency values without confidence intervals, standard deviations, or sample sizes (N). To support statistical rigor, report the number of independent runs, variance measures, and confidence intervals for all comparative metrics.
- **[science]** The cold-load staircase analysis (Section 5.2, Fig 4) presents a deterministic linear fit (1.36s/adapter) to observed data points. The paper lacks a statistical test (e.g., R-squared, p-value for slope) to validate the linearity assumption or quantify the residual error, which is critical for capacity planning claims.
- **[science]** In Section 5.2, the claim of '8.5–8.7x' speedup for packed loading is derived from three specific N values (4, 8, 16). The analysis does not address whether this range represents a stable asymptotic behavior or a small-sample fluctuation. A broader sweep or statistical bounds on this ratio are needed.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 1 (Introduction), the sentence 'Traditional infrastructures rely on copying or serving a full fine-tuned checkpoint for each model variant are increasingly difficult to scale...' contains a grammatical error where the verb 'are' lacks a proper subject. Rephrase to '...checkpoints, which are increasingly difficult to scale...' or similar.
- **[writing]** Section 1 contains a paragraph in Chinese (lines 135-158) that appears to be a draft or translation artifact. This must be removed or fully translated into English to maintain consistency with the rest of the manuscript.
- **[writing]** In Section 4 (Scaling), the phrase 'MinT time-slices LoRA training sessions' (Section 4.2) and similar technical descriptions are clear, but the transition between the 'Scale Up' and 'Scale Down' subsections feels abrupt. Consider adding a brief bridging sentence to improve flow between these distinct scaling axes.
- **[writing]** The abstract uses the phrase 'MinT scales this adapter-revision path along three axes' followed by bolded terms. Ensure the subsequent sections (4.1, 4.2, 4.3) explicitly mirror this structure with clear topic sentences to maintain cohesion between the abstract and the body.
