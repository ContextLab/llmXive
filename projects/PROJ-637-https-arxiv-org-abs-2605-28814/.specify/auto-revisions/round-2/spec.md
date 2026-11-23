# Revision Specification: Paper Science Revision — PROJ-637-https-arxiv-org-abs-2605-28814 round 2

**Generated**: 2026-06-21T10:17:45.276210+00:00
**Kind**: paper_science
**Project**: PROJ-637-https-arxiv-org-abs-2605-28814
**Round**: 2

## Input

Address the following reviewer-raised action items:

- **[8275443f8291] (severity: writing)** Multiple citation keys used in the text (e.g., skydiscover, openevolve, gepa, musique, maxrl, selftaught, wu2025inference) are missing from the provided ref.bib. This prevents verification of claims regarding baseline data provenance (Section 4.2, Table 2) and related work (Section 1). Add these entries to ref.bib to support the factual claims.
- **[0a384a504686] (severity: writing)** Supplementary material must include a requirements.txt or Dockerfile to ensure reproducibility of the experimental environment (e.g., vLLM, FAISS versions).
- **[4f1447719bd9] (severity: writing)** Clarify the exact commit hash or version of the GitHub repository linked in the Abstract, as the public URL may change.
- **[7db0eb15395f] (severity: writing)** Appendix Section 5 (Prompts) is helpful, but ensure the Python snippets in verify_code (Appendix ef{app:prompts:backward}) are validated for syntax and dependencies.
- **[161ea9030647] (severity: writing)** In Appendix Section 5 (sections/appendix.tex), the verify_code prompt examples reference 'np.' (numpy) without specifying imports or environment context, risking runtime errors if evaluated as stated.
- **[e374e8c83430] (severity: writing)** Explicitly state the license terms for the Knights-and-Knaves and MuSiQue datasets used in training and validation.
- **[4acb3970c8bd] (severity: science)** Clarify data split integrity in Appendix A.2 to ensure the 'solvable split' for training does not leak validation information.
- **[78da07a452b4] (severity: writing)** Document API dependency risks for the Open Problem Solving benchmark (GPT-5) to address reproducibility constraints.
- **[5b17f4717f33] (severity: writing)** Add alt text for all figures to ensure accessibility compliance (missing in LaTeX source for fig:teaser, fig:forward, fig:kk, fig:kk_abl, fig:case).
- **[3bae699b4a49] (severity: writing)** Verify axis labels include units on all plots (fig:kk, fig:kk_abl, tab:cost_posttraining, tab:cost_inference); currently unverifiable from LaTeX source alone.
- **[22fa474fc243] (severity: writing)** Ensure color choices (green!60!black, red!70!black) are colorblind-safe; recommend adding patterns or shapes as secondary encodings.
- **[5c5af3d8697f] (severity: writing)** Define acronyms RLVR, SFT, EMA, and OOD at first use. RLVR appears in Intro without definition. SFT appears in Appendix without definition. EMA appears in Fig 2 caption without definition. OOD appears in Keywords but not text.
- **[ec52ba98becb] (severity: writing)** Replace or gloss heavy mathematical jargon in Theoretical Motivations (Appendix). Terms like 'filtration', 'martingale difference sequence', and 'Doob martingale' exclude non-specialist readers.
- **[1e86bb319754] (severity: writing)** Clarify biological metaphors in Method section. 'Translocation' and 'evolution operators' need plain English equivalents or clearer definitions for general AI audiences.
- **[e87e33d159e7] (severity: writing)** Clarify whether 'answer reweighting' is an integral component of BES or an external MaxRL technique. The Method section defines BES as a search algorithm agnostic to training, but the Ablation study treats reweighting as a BES component. Explicitly distinguish 'BES Search' from 'BES + Training Tricks' to ensure logical consistency between definition and experimental claims.
- **[5d64986d8ca8] (severity: science)** Temper theoretical claims in Abstract and Section 3 to reflect that assumptions (e.g., sub-goal independence) are not empirically validated on the models used.
- **[b95399fd677c] (severity: writing)** Revise cost analysis claims in Section 4.3; characterize the ~40% API cost increase more accurately rather than as 'modest'.
- **[45badd653540] (severity: writing)** Expand the broader impacts section (app/lim.tex) to specify concrete dual-use scenarios beyond generic 'tasks that could be misused' — e.g., could BES improve generation of harmful code, exploit strategies, or adversarial examples?
- **[927db125f2e2] (severity: writing)** Add discussion of safety evaluation protocols before releasing trained models on GitHub. Consider whether capability gating or usage restrictions should accompany the release.
- **[33732edd395a] (severity: writing)** Clarify the provenance and safety status of GPT-5 in the inference experiments (app/inference_setup). If this is a future/fictional model, note the implications for reproducibility and safety assessment.
- **[3202067920a9] (severity: science)** Table 2 relies on external baseline results from SkyDiscover (Section 4.2). To establish scientific control, re-run baselines in the same environment or provide variance estimates acknowledging environmental confounds.
- **[e00af43ecdfd] (severity: science)** Table 1 reports accuracy without standard deviations across seeds. Add error bars or report mean±std over multiple independent training runs to assess statistical significance.
- **[ddfeec160f3b] (severity: writing)** Inference benchmarks (Table 2) report only 3 runs. Justify this sample size or increase replication to ensure reported means are stable against stochastic search variance.
- **[a97df04d9085] (severity: science)** Add standard deviations and confidence intervals to Table 2 (Multi-Hop Reasoning) to quantify variance across seeds.
- **[344ccfa3e424] (severity: science)** Increase the number of random seeds for Open Problem Solving benchmarks from 3 to at least 5 for robust statistical inference.
- **[f1741f241ef4] (severity: science)** Perform statistical significance testing (e.g., t-tests) to validate claims of outperformance over baselines.
- **[573e45a395ae] (severity: writing)** Reorder main sections: 'Related Work' (sections/rw.tex) is currently included after 'Experiments' (line 102 in neurips_2026.tex). Standard NeurIPS convention places Related Work immediately after Introduction.
- **[b347b752a7dc] (severity: writing)** Remove duplicate package loading: 'xcolor' is loaded at line 82 and again at line 129 in neurips_2026.tex. Keep only one instance to avoid compilation warnings.
- **[4a212af98d8e] (severity: writing)** Resolve duplicate section titles: 'Theoretical Motivations' appears in both main body (theory.tex) and Appendix (appendix.tex, line 305). Rename the Appendix section to 'Additional Theory' for clarity in the Table of Contents.
- **[8b02ff5fc9e5] (severity: writing)** Replace esizebox on tables: Tables tab:multihop (exp.tex, line 135) and tab:ops (exp.tex, line 176) use esizebox which distorts typography. Use tabularx width settings instead.
- **[9a737a50303f] (severity: writing)** Fix theorem statement formatting: In appendix.tex (lines 428, 525), the period is inside the 	extbf{} command (e.g., 	extbf{.}). Move the period outside the bold scope for standard punctuation.
- **[8665acb3427b] (severity: writing)** In sections/rw.tex, the section header 'Self-Improvement for LLM and Agent' uses singular nouns where plural is standard for the field. Please change to 'LLMs and Agents'.
- **[5e6cb1b9b66f] (severity: writing)** In sections/method.tex, the phrase 'every several forward search steps' is awkward. Replace with 'every few forward search steps' for better flow.
- **[05dab288d242] (severity: writing)** In sections/intro.tex, ensure consistent pluralization of 'agentic systems' and 'models' throughout the text to avoid singular/plural mismatch.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 34 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
