# Revision Specification: Paper Science Revision — PROJ-599-mmskills-towards-multimodal-skills-for-g round 1

**Generated**: 2026-06-27T14:52:58.682621+00:00
**Kind**: paper_science
**Project**: PROJ-599-mmskills-towards-multimodal-skills-for-g
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[ff2b5a588bdc] (severity: writing)** Correct Abstract claim regarding text-only performance; Table 2 shows GLM-5V macOSWorld Overall is tied (51.75%) and Productivity is worse for MMSkills.
- **[fa9ff904aeb9] (severity: writing)** Align model version names in text with bibliography entries (e.g., GLM-5V vs GLM-4.5V, Kimi-K2.6 vs K2.5).
- **[3621ec20f51d] (severity: writing)** Nuance 'first to introduce' claim in Introduction given related work on multimodal skills (e.g., Mirage-1).
- **[fd8cf4eec48b] (severity: writing)** The code repository link is present in metadata but external access cannot be verified. Ensure the repository at https://github.com/DeepExperience/MMSkills contains the full implementation corresponding to Algorithm 1 (app:branch-loaded-algorithm) and is publicly accessible.
- **[fa0d19c3a183] (severity: science)** Appendix app:experiment-details lacks specific hyperparameters for the Generator pipeline (e.g., clustering parameters, embedding dimensions, meta-skill configurations). Add a table or section listing these to ensure reproducibility from scratch.
- **[f36768a9f831] (severity: science)** Dependency hygiene cannot be verified. Include a requirements.txt or environment.yml in the code repository and cite it in the Appendix (e.g., app:experiment-details).
- **[06c3225509c9] (severity: science)** Specify the license for the generated MMSkills dataset on HuggingFace to ensure legal reuse and downstream compliance.
- **[0449179f4ec8] (severity: science)** Cite specific version commits or release tags for benchmark datasets (e.g., OSWorld, OpenCUA) to enable exact replication.
- **[2670f3d420f2] (severity: writing)** Archive external project links (GitHub, Website) via a persistent service like Zenodo to mitigate link rot and preserve artifact availability.
- **[2a1e10fc3698] (severity: writing)** Add accessibility alt text for all figures (e.g., using the alttext package or figure captions) to ensure screen reader compatibility, as none are present in the LaTeX source.
- **[73cb5819390f] (severity: writing)** Verify font legibility within the generated PDF figures (especially Figs 3, 4, and Appendix Prompt Examples) at print scale, as the code relies on external PDFs without inline font size control.
- **[d941b8f8ec6f] (severity: writing)** Reduce height of Appendix interaction case figures (lines 1650-1680) from 0.88\textheight to avoid page overflow and improve readability in standard print layouts.
- **[db20ee041129] (severity: writing)** Define 'LLM' as 'Large Language Model' at first use in Introduction. Currently appears as 'LLM agents' without expansion.
- **[91016a68955d] (severity: writing)** Replace 'degenerate package' (Methods, Eq. 5 area) with 'simplified version' or 'special case' to reduce mathematical jargon for general readers.
- **[63cb811a1301] (severity: writing)** Clarify 'privileged state' (Appendix, Experiment Details) with 'complete state information' to avoid RL-specific jargon.
- **[28754144674b] (severity: writing)** Define 'VAB' explicitly when first introducing 'VAB-Minecraft' in Experiments. Currently only 'VisualAgentBench' is written but the acronym is not formally defined.
- **[5d547ec9a023] (severity: writing)** Simplify 'model-internal priors' (Abstract, Introduction, Conclusion) to 'built-in knowledge' or 'internal knowledge' for broader accessibility.
- **[02bcf06c45dc] (severity: writing)** Add explicit definition for 'branch loading' at first use in Introduction, as this coined term may be unfamiliar to non-specialist readers.
- **[8c922caa5804] (severity: writing)** Replace 'state-conditioned procedure' with 'procedure that depends on current state' or similar plain-language alternative on first occurrence.
- **[14f18930953b] (severity: science)** Correct the claim in Section 3.2 regarding GLM-5V performance on macOSWorld. Table 2 shows identical Overall scores (51.75%) for Text-only and MMSkills, contradicting the text stating MMSkills improve GLM-5V on this benchmark.
- **[02a497f70a76] (severity: writing)** Qualify the novelty claim in Contributions (Intro) regarding 'first to introduce multimodal skill package' given citations to Mirage-1 and XSkill.
- **[c2e6a6b7a2bb] (severity: science)** Add statistical significance tests (e.g., t-tests, confidence intervals) to Table 1 and 2 results to support claims of 'significant gains'.
- **[8996dcce7d2f] (severity: writing)** Clarify that 'avoiding over-anchoring' is an inference from ablation results rather than a directly measured phenomenon in Section 3.4.
- **[c87528c4a57e] (severity: writing)** Qualify the 'consistently improve' claim in Abstract/Intro given GLM-5V Mail performance drop (Table 1: 40.00 vs 53.33 No-skill).
- **[7a97dabefb83] (severity: writing)** Explicitly describe the data privacy filtering process applied to source trajectory screenshots to ensure no PII or sensitive credentials were included in the skill library.
- **[7df31a5131ff] (severity: writing)** Expand the Broader Impact section to include concrete dual-use mitigation strategies, such as sandboxing or permission layers, rather than high-level risk statements.
- **[9bdfec0d600d] (severity: science)** Add statistical significance testing (e.g., bootstrap confidence intervals or paired t-tests) for all main performance tables to confirm gains are not due to random variance.
- **[d3416e42cd2d] (severity: science)** Report multi-seed results (e.g., 3-5 seeds) with standard error bars to address the high variance observed in baseline performance (e.g., GLM-5V Text-only drop in Table 1).
- **[a7600e6c8c22] (severity: science)** Provide an explicit audit or similarity analysis confirming no task overlap between OpenCUA source trajectories and OSWorld/macOSWorld evaluation tasks to rule out data leakage.
- **[16d5477a6b62] (severity: science)** Report standard errors or 95% confidence intervals for all success rate metrics in Tables 1 and 2 to quantify uncertainty.
- **[d71a9a046a43] (severity: science)** Apply multiple-comparison correction (e.g., Bonferroni or FDR) across the 6 models and 4 benchmarks tested, or justify its omission.
- **[13ca6fe7ab8a] (severity: science)** Provide sample sizes (N) for each cell in result tables and include error bars in ablation figures (Figure 2).
- **[245b7c0a52d3] (severity: writing)** The redundant \newcommand{\mfield} in the body of main-llmxive.tex (line 350, Methods section) remains. Remove it to prevent compilation conflict with the preamble shim definition (line 100).
- **[d2f6abe9c61d] (severity: writing)** The commented-out TODO note %\review{换成 item 的分点形式} in paper/introduction.tex (line 215) is still present. Remove all review/commented TODO notes before final submission.
- **[131b80826d1d] (severity: writing)** The \renewcommand{\mmskillhl} color changes in paper/experiments.tex remain unscoped globally. Wrap in local groups {\renewcommand{...}} or use \definecolor locally to avoid unintended side effects on subsequent tables.
- **[06dbe4ba928b] (severity: writing)** Fix the typo in author affiliations in mmskills_arxiv.tex (line 204): 'TongUniversity' should be 'Tong University'.
- **[b0ac44e077cd] (severity: writing)** Standardize terminology for 'branch loading' across paper/experiments.tex and paper/methods.tex. 'Direct load' in experiments.tex section RQ2 is inconsistent with the 'branch loading' terminology used throughout the manuscript.
- **[33310da11118] (severity: writing)** Remove the leftover LaTeX comment %\review{换成 item的分点形式} in paper/introduction.tex (line 37) to ensure source cleanliness.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 38 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
