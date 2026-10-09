# Revision Specification: Paper Science Revision — PROJ-566-mint-managed-infrastructure-for-training round 2

**Generated**: 2026-06-17T04:35:10.654536+00:00
**Kind**: paper_science
**Project**: PROJ-566-mint-managed-infrastructure-for-training
**Round**: 2

## Input

Address the following reviewer-raised action items:

- **[55d12954a127] (severity: writing)** Align Abstract and Section 5.1 quantitative claims (e.g., 18.3x speedup) with detailed results tables to ensure exact numerical consistency and avoid overreach.
- **[812e1c67e12b] (severity: science)** Add rigorous statistical treatment (confidence intervals, variance metrics) to performance benchmarks to support reproducibility and confidence in reported gains.
- **[3a15a4bf51c5] (severity: writing)** Release code artifacts and data quality documentation (e.g., dataset sources, cleaning pipelines) in a supplementary repository or appendix to enable reproducibility review.
- **[f069e86c1671] (severity: writing)** Reduce domain-specific jargon in the Introduction and Related Work sections to improve accessibility for non-specialist readers without losing technical precision.
- **[c0e0302dd268] (severity: writing)** Abstract, Section 5.1, and Conclusion still claim adapter-only handoff reduces handoff time by 18.3× (4B) and 2.85× (30B). Table 1 shows materialization/load times of 0.036s vs 71.820s (4B, ~1995×) and 46.455s vs 402.245s (30B, ~8.65×). Cold first sample yields ~13.5× and ~1.33×. Neither metric supports the 18.3×/2.85× figures. This discrepancy remains unaddressed.
- **[54328fd1010b] (severity: writing)** Add a 'Code Availability' statement in the Conclusion or Appendix linking to the MinT infrastructure repository, and specify dependency versions (Ray, Megatron, vLLM) for reproducibility.
- **[9c49814b8ec0] (severity: writing)** Add explicit dataset version identifiers and download URLs for all training datasets (Fineval, FinGPT, AIME-24, LawBench) in Section 6.1 and Appendix A.
- **[f716eff99957] (severity: writing)** Include a data license statement for all external datasets and the MinT system itself (e.g., in Appendix or a dedicated data availability section).
- **[261456961701] (severity: writing)** Document the schema for policy records and adapter revisions (base version, LoRA rank, target modules, checkpoint locations) with a concrete example in Section 3.
- **[8b0a6d26555b] (severity: writing)** Add a data availability section describing how readers can access the MinT cookbook (mint_cookbook2026) and any released artifacts.
- **[15b9a01d6c83] (severity: writing)** Provide version pins for all cited external resources (tinker2025, skyrl_tx, mint_cookbook2026) to mitigate link rot risk.
- **[3b7ae3e338dd] (severity: writing)** Add alt text to all figures for accessibility compliance (LaTeX figures lack alt attribute)
- **[9574f6576656] (severity: science)** Replace tikz placeholder comments in fig:e4_cache_ladders and fig:e4_latency_catalog with actual rendered data visualizations; current code only contains data point comments without rendering
- **[779b999c6a42] (severity: writing)** Specify axis units and scales in all figure captions (e.g., p95 latency units in seconds for fig:e4_cache_ladders)
- **[9331ed0beda7] (severity: writing)** Standardize figure file formats (all .pdf or all .png) for consistent compilation; currently mixed between figures/*.png, figures/*.pdf, and tikz
- **[d531acb48b2e] (severity: science)** Add confidence intervals or error bars to performance comparison figures (e.g., fig:e1_handoff_breakdown, fig:e3_dense_curves) to support statistical claims
- **[bc370c2d41ee] (severity: science)** Resolve missing external figure files referenced in LaTeX (e.g., figures/changhai_hotset_ladder, figures/changhai_latency_cold_load_panels in fig:e4_cache_ladders) which are not present in the artifact bundle.
- **[1cf0cb7ae382] (severity: writing)** Remove .svg file format from figures directory (figures/eval_gpu_utilization.svg) to ensure consistent compilation across standard LaTeX engines.
- **[966b2a7f9599] (severity: writing)** Define all acronyms at first use (e.g., TP, SLO, HBM, FP8, KV, R3, DSA, MTP) in the Introduction or System Design sections rather than assuming reader familiarity.
- **[63ca1a87cda3] (severity: writing)** Move definitions of SFT, DPO, GRPO, PEFT, and MoE to the Introduction or Abstract glossary, as they appear in the Abstract and Section 3 before Section 5.1.
- **[951bb53234eb] (severity: writing)** Clarify system-specific terms like "adapter revision," "policy record," "service plane," and "compute plane" with brief parenthetical explanations for non-specialist readers.
- **[6f883b795751] (severity: writing)** Replace jargon-heavy phrases like "tensor-parallel serving actor" and "expert-parallel LoRA" with plain language or add a glossary entry for parallelism types.
- **[ad2bb682b189] (severity: writing)** Define "IcePop" upon first use in Section 5.1, as it introduces new specialized terminology not covered in prior action items.
- **[480d9c96280a] (severity: science)** Section 5.1 and Conclusion claim 18.3x speedup for 4B model handoff, but Table 1 data (71.820s vs 0.036s) implies ~1995x or ~13.5x depending on metric. Additionally, 30B claim (2.85x) is unsupported by Table 1 (missing rows) or e002 summary data (8.6x). Correct claims to match data or update data tables.
- **[e5b44bb7bd61] (severity: science)** Abstract and Section 5.1 claim '18.3×' (4B) and '2.85×' (30B) handoff speedups, but Table e001 (tab:e1_handoff_paths) shows ~13.5× (4B cold sample) and ~1.33× (30B cold sample) or ~1995× (4B materialization). The specific 18.3×/2.85× figures lack a clear derivation from the provided data, constituting an unsupported quantitative claim.
- **[c02041aef35f] (severity: writing)** Abstract states 'Scale Out to 10^6 addressable policies' as a measured capability. Section e001 clarifies this is a 'sizing sketch' in the Appendix, not a measured result. The Abstract must qualify this claim to distinguish between measured (100k) and modeled (1M) evidence.
- **[2b3093b01033] (severity: writing)** Add a 'Safety and Ethics' section (or paragraph) explicitly addressing safety constraints in the AutoResearch loop (Sec 5.4, Fig 6). The current text describes recipe promotion based solely on benchmark performance (LawBench), lacking discussion of safety alignment or misuse prevention during automated optimization.
- **[f830df50c28c] (severity: writing)** Clarify data privacy and consent protocols for training datasets. Section 5.2 cites FinGPT/FinEval without detailing PII removal, data sourcing consent, or privacy-preserving measures, which is critical for infrastructure handling 'Internet-scale Data'.
- **[b2bf0bc0f01a] (severity: writing)** Discuss dual-use risk mitigation for high-capability agent deployment. The Abstract and Conclusion emphasize 'Agentic LLM capabilities' and 'Millions of LLMs' serving; the manuscript should acknowledge potential misuse risks and describe any access controls or rate-limiting safeguards implemented.
- **[bf43e9dc218e] (severity: science)** Reconcile Abstract speedup claims (18.3x/2.85x) with Table tab:e1_handoff_paths data. The table shows ~1995x load time speedup for 4B (71.8s vs 0.036s) but ~3.3x sample speed (15.57 vs 4.70 tok/s). Define 'handoff step' precisely or correct the numbers.
- **[cf5b617c1142] (severity: science)** Report statistical variance for training benchmarks (AIME-24, LawBench, FinEval). Single-point accuracy (e.g., 0.967 mean@1 on 235B) without standard deviation or seed counts (n=?) limits reproducibility and confidence in RL gains.
- **[aaa0573e4bbf] (severity: science)** Clarify the baseline for the 8.5–8.7x live-load speedup. Is this compared to a naive tensor load, or a prior Multi-LoRA system (e.g., Punica, S-LoRA)? The current table (tab:e4_packed_loader) only shows packed vs. original format, not external baselines.
- **[78d43f413103] (severity: science)** Report mean and standard deviation for all benchmark tables (e.g., Table 1, Table 2) instead of single point estimates to quantify variability.
- **[ba7c1dcccbaf] (severity: science)** Specify the sample size (n) for all percentile claims (e.g., p95 latency in Table 4) to ensure statistical validity of tail metrics.
- **[d5e9aae38187] (severity: science)** Add error bands (e.g., std or confidence intervals) to learning curves in Figure 3 to demonstrate stability across training runs.
- **[85685734223e] (severity: writing)** Duplicate section labels detected: \section{Introduction} appears in both e000 (line 1) and e001 (end of chunk). Consolidate to a single definition to prevent LaTeX compilation errors.
- **[e712ee145b21] (severity: writing)** Duplicate figure labels: \label{fig:mint_overview} is defined in e000 (line 15) and e001 (end of chunk). Ensure unique labels across the entire document.
- **[c7786b9e659c] (severity: writing)** Inconsistent figure placement specifiers: Mix of [!htbp], [H], [tbp], [t], and [htbp] across e000, e001, e002, and e003. Standardize to [!htbp] or [htbp] unless [H] is strictly required.
- **[2c17c8e1aff3] (severity: writing)** Custom macro dependencies: \fittowidth, \apphead, and \appgroup are used throughout e000-e003 without preamble context. Verify these are defined or replace with standard \resizebox and \textbf.
- **[0455a07ffa7e] (severity: writing)** Table column type inconsistency: Use of custom M{width} (e000, e001) vs standard p{width} (e003) vs l (e002). Standardize column definitions for consistency.
- **[f9a2b3c4d5e6] (severity: writing)** Inconsistent figure inclusion: e000 uses \includegraphics while e002 uses \input{figures/...}. Standardize figure inclusion commands across all chunks.
- **[0ebba9469d29] (severity: writing)** Fix grammatical error in Introduction (e002): 'Traditional infrastructures rely on... are increasingly difficult' should be rephrased to fix subject-verb agreement/clause structure.
- **[63397f6a7db3] (severity: writing)** Resolve duplicate Introduction sections found in e000 and e002. Ensure only one Introduction section exists in the final manuscript.
- **[62e830e6e7f2] (severity: writing)** Tighten long, dense sentences in Section 1 (e.g., e000 paragraph 1) to improve readability and parseability for general readers.
- **[3ad6d80b1829] (severity: writing)** Verify LaTeX macro definitions for custom commands like \apphead, \appkey, and \appgroup to ensure compilation hygiene and consistency.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 45 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
