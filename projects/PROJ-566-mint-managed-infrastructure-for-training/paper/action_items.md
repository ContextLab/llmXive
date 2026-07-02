# Automated-review action items — MinT: Managed Infrastructure for Training and Serving Millions of LLMs

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer — verdict: major_revision_writing

- **[writing]** Resolve uncompiled LaTeX: The source contains raw TikZ code (e.g., `figures/changhai_cold_admission_staircase.tex`) and missing `\input` targets (e.g., `tables/scaling/supported_model_families`) that prevent PDF generation. The paper must compile cleanly before review.
- **[writing]** Fix bibliography verification: Multiple citations (e.g., `yao_second_half_2025`, `deepseek_v4_release_2026`, `kimi_k25_2026`) reference internal blogs or unreleased technical reports without stable DOIs or arXiv IDs. Verify all references or replace with publicly accessible, peer-reviewed sources.
- **[writing]** Clarify 'Millions' claim: The title and abstract claim support for 'Millions of LLMs' (policies), but the evaluation section only demonstrates a 100k catalog sweep and a theoretical 1M extrapolation. The title should be qualified (e.g., '...Millions of Policies') or the evaluation must include a 1M+ scale measurement.
- **[writing]** Standardize citation format: The bibliography mixes arXiv preprints, blog posts, and internal 'Mind Lab' reports. Ensure all citations follow a consistent, verifiable format suitable for public archival (e.g., arXiv or conference proceedings).

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Abstract and Section 4.2 claim a 18.3x handoff reduction on a 4B model, but Table 1 (e1_handoff_paths) shows a 71.82s vs 0.036s materialization time (approx 1995x) and a 55.7s vs 4.1s total cold first sample (approx 13.5x). The 18.3x figure does not match the provided data for either metric. Clarify the specific metric used for this claim or correct the number.
- **[writing]** The abstract claims a 2.85x handoff reduction on a 30B MoE model. Table 1 shows 402.245s (Merge) vs 46.455s (Adapter) for materialization (approx 8.6x) and 156.074s vs 117.304s for cold first sample (approx 1.33x). The 2.85x figure is unsupported by the table data. Reconcile the claim with the evidence.
- **[writing]** Section 4.2 states a rank-1 LoRA is 'roughly 0.10% of the bf16 base-weight floor' and supports the abstract's 'less than 1%' claim. However, the text calculates 7.9 MiB for rank-1 vs 8.0 GB base, which is 0.098%. While mathematically correct, the phrasing 'less than 1%' is technically true but potentially misleading given the order of magnitude difference (0.1% vs 1%). Ensure the distinction between 'compact rank-1' and general rank settings is clear to avoid overgeneralization.
- **[writing]** Section 5 claims the Kimi K2 1T run uses a '64 H800 deployment'. However, Table 2 (model_coverage) lists the Kimi-K2-Thinking training profile as '128 GPUs'. The text in Section 5 also mentions '128 GPU' in the table notes. The '64 H800' claim in the text (Section 2, Figure 3 caption) contradicts the table data. Verify the correct GPU count for the Kimi K2 deployment.
- **[writing]** The abstract claims 'thousand-adapter active waves at cluster scale'. Section 5 and Appendix Table 4 (app_fleet_model) describe a '2300-distinct-adapter active-wave assumption' for fleet sizing. The term 'thousand-adapter' is vague and does not align with the specific 2300 figure used in the capacity model. Use the precise number or clarify the range.

## paper_reviewer_code_quality_paper — verdict: minor_revision

- **[science]** The paper relies entirely on static TikZ figures and PNG images without providing the underlying Python/PyTorch scripts that generated the data points. To ensure reproducibility from scratch, the authors must include a 'reproducibility' appendix or a public repository link containing the data generation scripts (e.g., data loaders, metric aggregators) used to produce the specific numbers in Tables 1-4 and Figures 3-6.
- **[writing]** The LaTeX source includes numerous hardcoded file paths and external image references (e.g., 'figures/eval_n3_schedule_timeline.png', 'figures/eval_handoff_breakdown.png') without a Makefile or build script to regenerate them. A 'Makefile' or 'build.sh' script is required to define the dependency graph between raw data, generation scripts, and the final PDF to ensure the paper can be rebuilt from source.
- **[writing]** The bibliography relies on a mix of arXiv preprints and internal 'Mind Lab' technical reports (e.g., 'lu2026announcing', 'liu2025Build') with URLs that may not be publicly accessible or stable. For a public submission, all internal reports must be replaced with publicly available preprints or the data must be made available in a public repository with a persistent DOI.

## paper_reviewer_data_quality_paper — verdict: full_revision

- **[science]** The paper claims measurements on 'Kimi K2 1.04T' and 'Qwen3-235B' models (Abstract, Sec 4.1, Sec 5.2) but provides no data provenance, license, or access method for these datasets. These appear to be proprietary frontier models not publicly released. Without a clear statement on data access (e.g., 'internal only', 'private API', or 'simulated'), the reproducibility of the 'Scale Up' results is impossible. Cite the specific data source or clarify if these are internal-only benchmarks.
- **[science]** Section 5.2 and Table 5.2 report specific performance metrics (e.g., '0.967 peak mean@1' on AIME24 for Qwen3-235B) but do not specify the exact version of the AIME24 dataset used, nor the random seeds or evaluation protocol details required to reproduce these numbers. The 'mint-cookbook' is cited, but the specific recipe version and data manifest hash are missing. Re-run the evaluation with explicit data versioning and seed control.
- **[writing]** The 'Scale Out' experiments (Sec 5.3, Fig 4) claim a '10^6-scale addressable policy catalog' but the measured data only sweeps up to 100k entries (Table 5.4, Appendix B). The 1M claim is an extrapolation based on a 'fleet-level routing model' (Appendix B, Table B.5) rather than empirical measurement. Clearly distinguish between measured data and theoretical extrapolation in the text to avoid misleading readers about the empirical scope.
- **[science]** The paper references 'mint-prod-aliyun' and 'mint-prod-volcano' clusters (Table 3.1, Table 3.2) as the source of the trillion-parameter experiments. No information is provided regarding the hardware configuration, network topology, or data storage systems used in these clusters. Without this infrastructure metadata, the 'Scale Up' and 'Scale Out' results cannot be contextualized or reproduced. Add a detailed infrastructure appendix or table.

## paper_reviewer_figure_critic — verdict: minor_revision

- **[writing]** In changhai_cold_admission_staircase.tex, y-axis ticks lack explicit units. Add 's' to tick labels or ensure the rotated axis title is large enough to be the sole unit source for print legibility.
- **[writing]** In changhai_hotset_ladder.tex, the right y-axis (latency) lacks grid lines, making it hard to correlate the line plot with values. Add faint grid lines for the right axis ticks.
- **[writing]** In mint_system_blocks.tex, color distinguishes hot/cold paths. Ensure line styles (solid/dashed) are applied to all elements, not just the legend, for grayscale/print safety.
- **[writing]** In e2_training_utilization.tex, the caption mentions utilization metrics not visualized in the schematic timeline. Either add a utilization overlay or clarify the figure is purely schematic.

## paper_reviewer_jargon_police — verdict: full_revision

- **[writing]** Define 'MLA' (Multi-Latent Attention) and 'DSA' (Dynamic Sparse Attention) at first use in the Abstract and Introduction. These acronyms are used without definition, excluding readers unfamiliar with specific model families like GLM-5 or Kimi K2.
- **[writing]** Replace 'rollout correction' with a plain-language explanation (e.g., 'adjusting training weights based on probability mismatches') in the Abstract and Section 4. The term is used as a noun phrase without context for non-specialists.
- **[writing]** Define 'IcePop' when first mentioned in Section 4. It is currently treated as a known entity ('IcePop-style rollout correction') without citation or explanation of the mechanism, assuming prior knowledge of a specific paper or technique.
- **[writing]** Clarify 'Tinker-compatible' in the Abstract and Introduction. While 'Tinker' is cited, the specific nature of the compatibility (API surface, data formats, or control plane) is not explained, making the claim opaque to readers outside the specific ecosystem.
- **[writing]** Replace 'hot working sets' with 'active data in memory' or similar plain language in the Abstract and Section 4. 'Hot' is jargon that may confuse readers not versed in cache hierarchy terminology.
- **[writing]** Define 'TP' (Tensor Parallelism) and 'EP' (Expert Parallelism) at first use in Section 4 and the tables. These acronyms are used frequently without expansion, hindering readability for general systems researchers.
- **[writing]** Replace 'fanout' with 'number of objects' or 'object count' in Section 4 and Table 4. 'Fanout' is a specific networking/storage term that is used here to describe tensor object counts, which may be ambiguous.
- **[writing]** Define 'MoE' (Mixture-of-Experts) at its first occurrence in the Abstract. While common in the field, the paper claims to address a broad audience, and the acronym is used immediately without definition.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The '18.3x' handoff speedup claim (Abstract, Sec 4.2) conflicts with Table 2 data. Materialization times are 71.8s vs 0.036s (~1995x). Clarify if 18.3x refers to total step time, not just materialization, to resolve the logical inconsistency.
- **[science]** The '10^6-scale catalog' claim relies on a fleet extrapolation (Appendix Table F) from single-engine data. Explicitly state this is a theoretical projection under specific traffic assumptions, not an empirically validated result, to avoid overclaiming.
- **[writing]** The 8.5-8.7x loading speedup (Sec 4.3) applies only to 'live engine load' (registration), not total cold latency. Ensure the text distinguishes this specific phase from end-to-end cold load time to prevent logical conflation.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The abstract claims 10^6-scale catalogs and thousand-adapter waves, but data only shows 100k sweeps and 64-batch limits. The 1M figure is an Appendix extrapolation, not measured. Clarify this is a projection, not empirical validation.
- **[writing]** The 8.5-8.7x loading speedup applies only to the tensor-registration slice, not total cold-start latency which includes fetch/queueing. The abstract implies end-to-end improvement. Qualify the claim to specify it applies only to the loading phase.
- **[writing]** The claim that concurrent GRPO shortens wall time 'without increasing peak memory' is true but misleading. Speedup comes from utilizing idle time in the same allocation, not reducing base model memory. Clarify that memory efficiency is via time-slicing, not footprint reduction.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[science]** The paper claims to manage millions of LoRA adapters on shared bases (Abstract, Sec 4.3) but lacks discussion on data privacy, user consent, or multi-tenant isolation risks. If adapters are trained on sensitive data, rapid swapping creates leakage risks. Explicitly address data governance and consent mechanisms for the 'policy population'.
- **[science]** The system supports 'AutoResearch' and autonomous policy generation (Sec 5) without mentioning safety guardrails, red-teaming, or human oversight. If an agent generates harmful policies, reactive 'rollback' (Sec 2) is insufficient. Discuss proactive safety constraints to prevent deploying harmful behaviors at scale.
- **[writing]** The 'IcePop-style rollout correction' (Sec 4.1) masks tokens with probability mismatches. This could inadvertently mask safety-critical refusals if the 'trusted band' is loose. Clarify how safety-critical tokens are handled to ensure safety alignment is not degraded during optimization.

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** Core performance claims (e.g., 18.3x speedup) lack statistical rigor. Report mean +/- std dev over N>=5 trials to prove robustness against system noise.
- **[science]** The 10^6 catalog claim is an extrapolation, not measured data. Only 100k was tested. Clarify this distinction or provide large-scale empirical evidence.
- **[science]** The 8.5x loading speedup relies on a single data point. Provide variance data across multiple cold-start runs to validate consistency.
- **[science]** The concurrent training speedup lacks a proper control. Compare against a standard parallel runner to isolate MinT's specific architectural benefit.

## paper_reviewer_statistical_analysis — verdict: full_revision

- **[science]** Section 5.1 and Table 1 report single-point performance metrics (e.g., 18.3x speedup, 1.77x wall time reduction) without any measure of statistical variance, confidence intervals, or sample size (N). For system benchmarks involving stochastic workloads (RL rollouts, network I/O), single-run point estimates are insufficient to claim statistical significance. Re-run experiments with multiple seeds/trials and report mean ± std dev or 95% CIs.
- **[science]** The 'packed MoE LoRA' loading speedup (8.5–8.7x) in Section 5.2 and Table 4 is derived from a single measurement instance per configuration. Without reporting the standard deviation or the number of trials, it is impossible to determine if the observed speedup is robust or an artifact of system noise (e.g., OS scheduling, disk caching). Provide statistical aggregation of the load times.
- **[science]** In Section 5.2, the claim that 'cold loading is scheduled service work' relies on a 'staircase' latency plot (Figure 4, Panel C) showing a linear increase. However, the paper does not provide a statistical test (e.g., linear regression with p-value, R-squared) to confirm the linearity or the significance of the slope (1.36s/adapter). The visual trend is suggestive but not statistically validated.
- **[science]** The 'Scale Out' claim of supporting 10^6 policy catalogs (Abstract, Section 4) is based on an extrapolation in Appendix Table F (tab:app_fleet_model) rather than direct measurement. The extrapolation assumes a linear scaling of cold-load rates and warm-path placement without providing a confidence interval for the projected resource requirements. The statistical basis for this extrapolation must be explicitly stated or the claim qualified as a theoretical upper bound.

## paper_reviewer_text_formatting — verdict: minor_revision

- **[writing]** In sections/1_introduction.tex, the sentence 'Traditional infrastructures rely on copying or serving a full fine-tuned checkpoint for each model variant are increasingly difficult...' contains a grammatical error (missing relative pronoun 'that' or 'which'). Fix to: '...checkpoint for each model variant **that** are increasingly difficult...' or restructure.
- **[writing]** In sections/4_scaling.tex, the text '8.5--8.7$	imes$' uses an en-dash for the range. Ensure consistent usage of en-dashes (--) for number ranges throughout the document, as seen in '1.36--1.39 s' in figures/changhai_packed_loader.tex, versus '1.36--1.39 s' in text. Verify all ranges use '--'.
- **[writing]** In sections/5_capabilities.tex, the caption for Figure 2 (fig:e2_gpu_utilization) references 'Figure 2' implicitly but the label is 'fig:e2_gpu_utilization'. Ensure all cross-references in the text (e.g., '\Cref{fig:e2_gpu_utilization}') match the defined labels and that the caption text does not redundantly state 'Figure 2' if the label is used.
- **[writing]** In tables/mint/deployment_profiles.tex, the 'Moonlight-16B-A3B' entry in the 'Example Models' column uses a line break '\makecell[l]{...}'. Ensure the table column width is sufficient to prevent awkward wrapping or that the 'p{3.0cm}' width is adjusted to accommodate the text without manual line breaks if possible.
- **[writing]** In sections/appendix.tex, the author list uses 'Runism Lv' and 'Salmon Zhan' which appear to be typos for 'Runze Lv' and 'Sueky Zhang' (based on the main author list in the metadata). Verify and correct author names in the appendix to match the title page.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 1, the sentence 'Traditional infrastructures rely on copying... are increasingly difficult' has a grammatical error. Rephrase to: 'Traditional infrastructures, which rely on..., are increasingly difficult...'.
- **[writing]** In Section 1, change 'Following the service-interface practice of Tinker' to 'Adhering to the service-interface practices of Tinker' for better flow.
- **[writing]** In Section 4, the long list of implementation mismatches disrupts flow. Break into two sentences or use a bulleted list for clarity.
- **[writing]** Standardize references to the system as 'MinT' throughout Section 5 instead of alternating with 'the system' to improve cohesion.
