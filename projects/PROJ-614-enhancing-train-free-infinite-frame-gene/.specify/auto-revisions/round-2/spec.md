# Revision Specification: Paper Science Revision — PROJ-614-enhancing-train-free-infinite-frame-gene round 2

**Generated**: 2026-06-18T13:10:24.130682+00:00
**Kind**: paper_science
**Project**: PROJ-614-enhancing-train-free-infinite-frame-gene
**Round**: 2

## Input

Address the following reviewer-raised action items:

- **[8d6954317f13] (severity: writing)** Update the bibliography and data section to ensure every cited reference includes explicit verification status and provenance details as required by the acceptance criteria.
- **[576a988e1bfc] (severity: writing)** Clarify technical jargon and acronyms (e.g., TTA, DCE, TTS) in the first occurrence within the introduction and methods sections to improve accessibility.
- **[fd0dc5e12d4b] (severity: writing)** Enhance figure captions and ensure all visualizations (especially ablation studies) explicitly describe the baseline comparisons and metric definitions.
- **[aa3648abda19] (severity: writing)** Add confidence intervals or statistical significance tests to the main results tables in VBench and NarrLV to strengthen the scientific evidence claims.
- **[50808607dfb2] (severity: science)** Verify citation support: Line 1085 still cites `feng2024memvlt` (a vision-language tracking paper) to support the claim of enabling 'interactions among distant latents' in video generation. Ensure the source explicitly supports this specific mechanism in the generative context, or clarify that the method is adapted from tracking. Currently, the citation implies direct support for a generative mechanism which is unsupported.
- **[42e0d595a79b] (severity: writing)** Benchmark independence: The `feng2025narrlv` benchmark (Line 395, Table 2) is co-authored by the paper's authors. The Conflict of Interest section mentions using "standard public benchmarks (VBench and NarrLV)" but does not explicitly acknowledge the authors' involvement in creating the benchmark. Clarify this to ensure claims of 'state-of-the-art' performance are not perceived as biased.
- **[8c3f9a2b1d4e] (severity: writing)** Citation inconsistency: Section 3.3 cites `feng2024memvlt` for long-range frame guidance, while Appendix (Study on DCE) cites `feng2025atctrack` and `chen2025s2guidancestochasticselfguidance`. Clarify which source supports the proposed method to ensure factual consistency.
- **[ce594ee2f260] (severity: science)** No executable source code, dependency files (e.g., requirements.txt), or test suite included in the submission. Pseudocode in Appendix (Alg. 1-6) is not executable. Repository link or code artifacts must be provided to evaluate reproducibility, modularity, and implementation quality.
- **[7c02ab3093c4] (severity: writing)** The paper lacks explicit license information for VBench, NarrLV, and foundation models (VideoCrafter2, Wan2.1). Add a data availability statement specifying licenses for all external datasets and models used.
- **[b8b8f752539d] (severity: writing)** No version numbers are specified for VBench or NarrLV benchmarks. Include version identifiers or commit hashes to ensure reproducibility of evaluation results.
- **[1645e314732f] (severity: writing)** The project page URL (https://xiaokunfeng.github.io/miga_homepage/) in the abstract has no archival guarantee. Consider adding an arXiv snapshot or DOI for permanent access.
- **[68319942ac43] (severity: writing)** Evaluation data (VBench/NarrLV prompts, data splits) are not described with sufficient detail. Add a data card appendix specifying prompt counts, split sizes, and any preprocessing applied.
- **[e610e649a446] (severity: writing)** Revise Figure 1 caption (line ~130) to clarify that static images represent keyframes from videos, not the videos themselves.
- **[7eb1aa3ee923] (severity: writing)** Add accessibility alt-text descriptions for all figures using the accessibility package or descriptive captions to support screen readers.
- **[b4f8e5dd61c2] (severity: writing)** Ensure axis labels in ablation charts (Fig 5, Fig 6) are legible at print scale; verify font sizes are >= 8pt.
- **[6e7a18de3706] (severity: writing)** Define 'latents' with plain language (e.g., 'compressed representations') upon first use in Section 3.1 to aid non-specialist readers.
- **[b7c454ad9bb6] (severity: writing)** Provide a concise, intuitive explanation for 'noise span' in the Introduction or Section 3.2, as it is central to the method but currently defined only mathematically.
- **[9aface39a642] (severity: writing)** Ensure all acronyms in tables (S.C., B.C., M.S., T.F., O.S.) are explicitly defined in the table caption or immediately preceding text, not just in the main body.
- **[131b4a42dfc2] (severity: writing)** Simplify or define Appendix jargon such as 'MMDiT', 'KV Flush', and 'RoPE Cut' for readers who may only skim the main text.
- **[886c11510e7d] (severity: writing)** Define 'UniPC' upon first use in Appendix (Section 'Implementation on Different Foundation Models') as it is a specific sampler acronym not universally known.
- **[86b1a4b820d8] (severity: writing)** Expand 'DDPM' and 'DDIM' acronyms in Section 3.1 (e.g., 'Denoising Diffusion Probabilistic Models') for readers unfamiliar with diffusion nomenclature.
- **[0c98b1276abe] (severity: writing)** Revise Section 3.2 to align memory claims with Appendix analysis; explicitly state that Stage 2 requires O(N) storage, contradicting the 'constant memory' assertion.
- **[787583ad30f1] (severity: writing)** Clarify the definition of 'infinite-frame' in the Abstract/Intro to distinguish between streaming inference and the chunked buffering mechanism required by Stage 2.
- **[678babc0020d] (severity: writing)** The term 'infinite-frame' is used throughout (e.g., Abstract, Introduction, Title). This is technically inaccurate as the method is constrained by memory and time. Replace with 'very long' or 'arbitrarily long' with explicit caveats about practical limits.
- **[9454360c6b78] (severity: science)** State-of-the-art claims on VBench/NarrLV (Abstract, Sec 4.2) lack statistical significance testing. Report p-values or confidence intervals for the reported 4.7% and 2.0% improvements to justify SOTA language.
- **[0cdbd3b5fce3] (severity: writing)** The 'train-free' claim is qualified by the self-reflection mechanism which involves extended sampling (Sec 3.3). Clarify that this is 'training-free but inference-time computationally intensive' rather than purely train-free.
- **[04e287d3fa3c] (severity: science)** Memory consumption table (Tab memory_analysis) shows 0.66% increase at 2000 frames, contradicting the 'constant memory' claim in Introduction. Either revise the claim or provide stronger theoretical justification for asymptotic behavior.
- **[70c3ce5fd96f] (severity: writing)** Novelty claims for 'dual consistency enhancement' (Abstract, Introduction) cite ScalingNoise [yang2025scalingnoise] but don't sufficiently differentiate the self-similarity metric approach. Add a clear comparison paragraph highlighting the key methodological distinction.
- **[f232d747b625] (severity: writing)** Revise the Impact Statement to explicitly discuss dual-use risks (e.g., deepfakes, misinformation) and mitigation strategies, rather than dismissing societal consequences.
- **[c9e1d8a01556] (severity: writing)** Add a statement in the Appendix confirming that the user study received IRB approval or followed ethical guidelines regarding informed consent for annotators.
- **[daec83d23c43] (severity: science)** Add statistical significance testing (e.g., t-tests, confidence intervals) to all quantitative comparisons in Tables 1-3. Currently no p-values or error bars are reported for the claimed 4.7% S.C. improvement over FIFO-Diffusion.
- **[91c5627b535d] (severity: science)** Report the exact number of evaluation prompts used for main VBench/NarrLV experiments (only 50% subset mentioned for ablations in App.~\ref{app:ab_exp_imp}). This affects reproducibility and claim robustness.
- **[bb45b0ed7176] (severity: science)** Address multiple comparison concerns in ablation studies. Tab.~\ref{tab:ab_zig_length} tests 6 $L_{\mathrm{zig}}$ values and Tab.~\ref{app:tab_2} tests 8 $\delta_{\mathrm{adju}}$ values without correction for multiple testing.
- **[6e1332814088] (severity: science)** Provide power analysis or sample size justification for the user study (48 prompts, 8 annotators). Report confidence intervals for the percentage differences in Table~\ref{tab:user_study}.
- **[cecdfb352b8b] (severity: science)** Report standard deviations or 95% confidence intervals for all benchmark scores (VBench, NarrLV) in Tables 1 and 2 to assess result stability.
- **[9d454181aee5] (severity: science)** Include statistical significance tests (e.g., paired t-tests) comparing MIGA against baselines to validate claims of state-of-the-art performance.
- **[50afb12a21bd] (severity: science)** Provide p-values or binomial test results for the user study in Appendix Table 2 to support the claim of consistent outperformance.
- **[373410389d91] (severity: writing)** Remove commented-out code blocks (e.g., duplicate figure environment at lines 112-125, commented \vspace commands) before final submission.
- **[6e6bcd2e31f9] (severity: writing)** Standardize citation commands to use \citep consistently throughout (currently mixed \cite and \citep).
- **[a137a2c21ccb] (severity: writing)** Remove todonotes package usage for final submission; all TODO comments should be resolved or deleted.
- **[740aaa74273e] (severity: writing)** Consider renaming section "Related Works" to "Related Work" for grammatical consistency with academic conventions.
- **[ba07b387eb13] (severity: writing)** Standardize capitalization for model names – the manuscript uses both “Wan” (e.g., in the Introduction, line ≈ 115) and “Wan2.1” (e.g., in the Abstract and Experiments, lines ≈ 210 and ≈ 340). Use “Wan2.1” consistently throughout.
- **[87d6c45d980b] (severity: writing)** Remove all commented‑out LaTeX code (author list comments lines ≈ 65‑85, unused package lines ≈ 1‑45, and commented figure blocks lines ≈ 100‑110, 380‑390, 450‑470) to produce a clean source file.
- **[f981e3ba5e65] (severity: writing)** Tighten sentence structures in the Abstract and Introduction (lines ≈ 105‑250) to reduce redundancy of the phrases “training‑inference gap” and “consistency”, which appear repeatedly with similar wording.
- **[e9aed550b3e7] (severity: writing)** Reduce redundancy of the term “training‑inference gap” across the manuscript; after defining it once, refer to it with a single shorthand to improve readability.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 45 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
