# Revision Specification: Paper Science Revision — PROJ-571-co-evolving-policy-distillation round 1

**Generated**: 2026-06-23T04:26:12.146051+00:00
**Kind**: paper_science
**Project**: PROJ-571-co-evolving-policy-distillation
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[5f517da466b9] (severity: writing)** Citations reference multiple 2025-2026 dated papers (e.g., mimo2025flash-mopd, deepseekai2026deepseekv4, yang2026selfdistilledrlvr) that cannot be externally verified at review time. Verify these are actual preprints with accessible URLs or adjust citation dates.
- **[3679cf462eca] (severity: science)** The claim of 'significant' outperformance over baselines (Abstract, Introduction) lacks statistical significance testing (e.g., p-values, confidence intervals). Add statistical validation to support this claim.
- **[fb561ff39097] (severity: writing)** Some citations are blog posts/preprints (e.g., lu2025onpolicy-opd is a Thinking Machines Lab blog post) cited as if peer-reviewed. Clarify source type in citations or find peer-reviewed alternatives.
- **[05044dedd3c7] (severity: science)** Provide a link to the public code repository (GitHub/GitLab) containing the CoPD implementation to enable reproducibility verification.
- **[6466759b3244] (severity: science)** Include a requirements.txt or environment.yml file to document exact dependency versions for the EasyVideoR1, verl, and EasyR1 frameworks.
- **[26a3afc07384] (severity: writing)** Fix the typo 'specifc' to 'specific' in the Implementation Details section (eval.tex).
- **[40765687bcfd] (severity: writing)** Dataset licenses not documented for Polaris-Dataset-53K, MMFineReason-123K, or video training data. Critical for reproducibility and legal compliance.
- **[a28579fe19b1] (severity: writing)** No version numbers provided for any training datasets. Dataset versions can drift over time affecting reproducibility.
- **[a50b58257d01] (severity: writing)** External dataset links (e.g., Polaris blog, Notion) may experience link rot. Recommend archiving or DOI assignment.
- **[2e347e0b8477] (severity: writing)** Figure 3 (method overview) caption is too generic ('An overview of our method'). It should explicitly describe the RLVR and mutual OPD phases to be self-contained.
- **[6b76d5561671] (severity: writing)** Inconsistent figure sizing commands (e.g., 'width=0.99	extwidth' vs 'scale=0.34'). Standardize to 'width=	extwidth' for print consistency.
- **[cb9d5a2c0541] (severity: writing)** Ensure axis labels in Figure 2 (pilot) and Figure 4 (analysis) include explicit units (e.g., 'Score (%)', 'Steps') for clarity at print scale.
- **[08d616c7c735] (severity: writing)** Define 'GRPO' (Group Relative Policy Optimization) at first use in the main text (Section 3.1) rather than deferring to the Appendix. Currently, 'GRPO' appears in Eq. 1 and Section 3.1 before its expansion is available to the reader.
- **[a8c1f586141a] (severity: writing)** Replace 'rollouts' with 'generated sequences' or 'responses' in Section 3.1 and 3.2 to reduce RL-specific jargon. While standard in reinforcement learning, 'rollouts' may exclude non-specialist readers unfamiliar with the term.
- **[70b4d5cc7347] (severity: writing)** Clarify 'hub-and-spoke topology' in Section 3.3. While a standard networking term, briefly explain its application to model branches (e.g., 'a central branch coordinating with peripheral branches') to aid readers from other ML subfields.
- **[704b2d9cce8e] (severity: writing)** Abstract claims 'significantly outperforming' without statistical significance testing. Replace 'significantly' with 'modestly' or add p-values/confidence intervals to benchmark comparisons (e.g., Tables 1-2).
- **[b37d196b2d53] (severity: writing)** Limitations section is commented out in paper.tex (% \input{limitations}). Strong claims about breaking 'conventional ceilings' require honest discussion of boundary conditions and failure modes.
- **[eab1c1248246] (severity: science)** Table 2 shows Mixed RLVR (59.62) outperforms CoPD (59.21) on Video Avg, contradicting the claim that CoPD 'improves over MOPD across major capability groups' (Section 5.2). Generalization claims need qualification.
- **[af42e6632ea0] (severity: science)** Pilot study (Figure 3) reports r=0.89, R²=0.79 from a single experiment without error bars or repeated trials. Correlation-to-causation claims about behavioral distance need stronger statistical support.
- **[5eab978c65ac] (severity: writing)** Add a dedicated ethics/limitations section addressing dual-use potential of the trained models, including discussion of potential misuse scenarios (e.g., generating harmful reasoning outputs, misinformation) and proposed safeguards.
- **[a7ac3c679f5a] (severity: writing)** Provide transparency on data provenance and licensing for all training datasets (Polaris-Dataset-53K, MMFineReason-123K, OneThinker, VideoChat-R1, Video-R1). Include discussion of consent, privacy considerations, and whether any personally identifiable information may be present.
- **[9ea56357c936] (severity: writing)** Include a model release policy statement addressing whether/when the trained models will be made publicly available and what access controls or usage restrictions might apply given the enhanced reasoning capabilities demonstrated.
- **[3776f795c245] (severity: science)** The empirical evidence relies on single-run benchmark scores without reported standard deviations or multiple seeds (e.g., Tables 1-3). Claims of 'significant outperformance' in the Abstract (line 24) lack statistical testing. Re-run experiments with multiple seeds and report error bars to validate robustness.
- **[34f65e61ab78] (severity: science)** Report standard deviations or confidence intervals for all benchmark scores in Tables 1-3. Single-point accuracy estimates without variance measures cannot support claims of 'consistent outperformance' across 16 benchmarks.
- **[82857b9fa671] (severity: science)** Address multiple comparisons problem: with 16 benchmark tests, report adjusted p-values or use appropriate correction (e.g., Bonferroni, FDR) when claiming statistical significance.
- **[710bdfeea5fb] (severity: science)** Include statistical significance tests (paired t-tests, Wilcoxon signed-rank) comparing CoPD against each baseline, with effect sizes (Cohen's d) reported alongside accuracy differences.
- **[d0f2a9c491da] (severity: science)** Pilot study (Fig. 2): Report confidence intervals on correlation coefficients (r=0.89, R²=0.79) and test whether the linear relationship is significantly different from zero.
- **[f607b7e66ee8] (severity: writing)** Fix broken sentence in Introduction (main-llmxive.tex, line ~100) where a comment '%' splits the text 'capability divergence % . Combined', leaving a dangling comma and fragmented syntax.
- **[3f6f5b9b0604] (severity: writing)** Replace non-standard \fakeparagraph commands in eval.tex with semantic LaTeX \paragraph or \subsubsection for consistent heading hierarchy and TOC generation.
- **[f8ad876b7f0c] (severity: writing)** Remove commented-out code fragments (e.g., intro.tex lines 80-85, method.tex line 13) before final compilation to ensure clean LaTeX hygiene.
- **[3319f1987485] (severity: writing)** The introduction (intro.tex) effectively sets up the problem with a clear progression from RLVR limitations → OPD pipeline → proposed CoPD solution
- **[256e37e73c06] (severity: writing)** The motivation section (motivation-new.tex) uses a unified utility framework that makes the analysis coherent Weaknesses:
- **[bb5d8b75f999] (severity: writing)** Section 3.2 (method.tex, lines 45-50): *"where $\beta_k$ balancing the relative contribution of cross-branch distillation"* — This is grammatically incorrect. Should read *"where $\beta_k$ balances the relative contribution..."*
- **[a478f46c8796] (severity: writing)** Section 4.1 (eval.tex, lines 85-90): *"Specific experts and performs one additional stage of OPD"* — Missing article; should be *"on two independently trained specific experts"*
- **[9e96bc7603df] (severity: writing)** Inconsistent use of hyphenation: *"on-policy"* vs *"on policy"* appears throughout (e.g., abstract vs. Section 3) ### Paragraph Cohesion
- **[af918a344123] (severity: writing)** Section 2.3 (motivation-new.tex, lines 180-210): The "Implications for method design" paragraph is dense and could benefit from breaking into 2-3 shorter paragraphs for better digestibility
- **[fdee5065baa8] (severity: writing)** $\pi_\theta$ vs $\pi_{\theta_k}$ usage is inconsistent between Sections 2 and 3
- **[8d20bb5d9aad] (severity: writing)** Dataset notation varies: $D_1, D_2$ (Section 2.1) vs $\mathcal{D}_k$ (Section 3) — should be standardized throughout ### Recommendations
- **[7a92c0ed0c41] (severity: writing)** Split long sentences (especially in Introduction and Motivation sections) to improve readability
- **[c7903195f6ce] (severity: writing)** Fix grammatical errors noted above, particularly the $\beta_k$ balancing issue
- **[38a8d340adfb] (severity: writing)** Standardize notation for models and datasets across all sections
- **[f76169b0baf9] (severity: writing)** Add transition sentences between major subsections in the motivation section
- **[8273c771be7a] (severity: writing)** Review hyphenation consistency for compound terms like "on-policy," "cross-branch," "multi-teacher" The writing quality is fundamentally sound and the paper is readable, but these revisions would elevate the clarity and professionalism of the presentation.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 43 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
