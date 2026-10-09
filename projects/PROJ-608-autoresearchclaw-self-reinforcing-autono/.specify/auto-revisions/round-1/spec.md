# Revision Specification: Paper Science Revision — PROJ-608-autoresearchclaw-self-reinforcing-autono round 1

**Generated**: 2026-06-19T06:18:46.939908+00:00
**Kind**: paper_science
**Project**: PROJ-608-autoresearchclaw-self-reinforcing-autono
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[426e2d0b2b7f] (severity: science)** Ingest the full code repository (AutoResearchClaw) including source code, Dockerfiles, and CI configurations to enable modularity and dependency hygiene review.
- **[c4553af7e48b] (severity: science)** Provide the test suite (unit/integration tests) referenced in the paper (e.g., prompt parity test suite) to verify reproducibility claims.
- **[53029e96a935] (severity: science)** Include requirements.txt or environment.yml files to validate dependency hygiene and sandbox security model implementation.
- **[1cd6207a882c] (severity: writing)** Clarify the arXiv submission metadata; ID 2605.20025 implies a May 2026 date which conflicts with current review context.
- **[0d69b29b4171] (severity: writing)** Explicitly state the license for ARC-Bench artifacts (topics.yaml, rubrics/) to ensure reproducibility.
- **[df579a047402] (severity: writing)** Add schema versioning to the stage contract definitions in Appendix app:stages to prevent API drift.
- **[2c42246ad6ba] (severity: writing)** Provide DOIs or stable snapshots for cited arXiv preprints to mitigate link rot risks.
- **[b9c14615492d] (severity: writing)** Replace the raster PNG files (figures/main_figure.png, figures/casestudy.png, figures/AutoResearchClaw_transparent.png) with vector‑based PDFs or high‑resolution EPS to ensure crisp rendering at print scale.
- **[929b0bd0d99e] (severity: writing)** Add concise alt‑text descriptions for each figure (e.g., via the \caption* or \includegraphics[alt=...] options) to improve accessibility for screen‑reader users.
- **[ea366acc47ed] (severity: writing)** Review the colour palette used in the pipeline overview and case‑study figures to avoid red‑green or other colour‑blind problematic combinations; provide a colour‑blind safe version or a greyscale fallback.
- **[f6f1213c5155] (severity: writing)** Define 'HITL' (Human-in-the-Loop) before its first use in the Abstract; currently it is only defined in Section 1.
- **[ed9e6b08b730] (severity: writing)** Expand 'LLM' to 'Large Language Model' in the first sentence of the Introduction for broader accessibility.
- **[b249c659335f] (severity: writing)** Replace internal system jargon like 'Beast Mode' (Appendix A, Table 1 footnote) with descriptive functional terms.
- **[29ca1ff7c258] (severity: writing)** Define domain-specific acronyms (e.g., ECE, SHD, AIPW, BSM, UV) at first use in Appendix A for non-specialist readers.
- **[e99a5b4c3746] (severity: science)** Correct the overall cross‑domain score reported in Table 5. The weighted average of the Biology (0.912), Statistics (0.898) and HEP‑ph (0.489) domains (using the actual number of tasks per domain) does not equal the claimed overall 0.867. Re‑compute the overall mean (or clarify the weighting scheme) so that the reported figure is mathematically consistent with the per‑domain values.
- **[74164c39e00b] (severity: writing)** Add an explicit statement clarifying how the overall score in Table 5 is calculated (e.g., task‑weighted vs. simple arithmetic mean). This will prevent readers from perceiving a discrepancy between the component scores and the aggregate.
- **[7b0982fc235c] (severity: science)** Verify that any other aggregate metrics (e.g., overall improvement percentages) are derived using the same formula throughout the manuscript to avoid hidden inconsistencies.
- **[23a0d74eca4a] (severity: writing)** Temper the title claim 'Self-Reinforcing' given Appendix~\ref{app:agent_count} shows evolution yields only moderate reliability gains (-0.48 quality) compared to debate/self-healing.
- **[595b66d745f3] (severity: science)** Clarify whether cross-domain success (Table~\ref{tab:scidomain}) stems from research capability or software stack installation (Sec~\ref{sec:scidomain} admits baselines fail on stack installation).
- **[aa1724d4e08c] (severity: science)** Acknowledge LLM judge style bias (Appendix~\ref{app:judge-issues}) more prominently in the main text when citing the 54.7% performance gain.
- **[e1b06a09a8e1] (severity: science)** Explicitly detail dual-use mitigation strategies for sensitive scientific domains (e.g., systems biology) beyond code sandboxing, as the system can automate protocol design.
- **[a589fc1976f0] (severity: writing)** Clarify the IRB status of the 'scripted interventions' in the HITL ablation to confirm they do not constitute human-subject research requiring approval.
- **[7e8a734864f8] (severity: writing)** Strengthen the mitigation for 'submission flooding' risks by proposing technical enforcement (e.g., metadata tags) rather than relying solely on voluntary disclosure.
- **[246a4df3f48e] (severity: science)** Report confidence intervals or statistical significance (e.g., paired t-test) for the 25-topic benchmark results in Table tab:arcbench-aggregate to validate the 54.7% improvement claim.
- **[4d5c51887520] (severity: science)** Clarify that the HITL ablation uses scripted interventions, not live researchers, and adjust claims about 'Human-AI Collaboration' to reflect this limitation in the main text.
- **[bef8c0d842c0] (severity: science)** Address the 'Style bias' limitation noted in Appendix Judge and Rubric Issues (lines ~230-240) regarding the LLM judge's potential preference for the system's output style over scientific substance.
- **[91f79e19ef31] (severity: science)** Report confidence intervals for all mean scores in Tables 3-6. The 54.7% improvement claim lacks uncertainty quantification.
- **[ba2d2e57638e] (severity: science)** Apply multiple-comparisons correction (e.g., Bonferroni or FDR) for the 25×4 framework comparisons and 7-mode HITL ablation.
- **[3dbc579e5cd7] (severity: science)** Provide inter-rater reliability metrics (Cohen's kappa or ICC) for the dual-agent judge system, not just disagreement thresholds.
- **[36e7a17e4f89] (severity: science)** The best-of-3 rerun protocol inflates performance estimates. Report single-run baselines and adjust p-values for selection bias.
- **[d5953ff738ac] (severity: science)** The p=0.003 for debate contribution lacks test statistic, degrees of freedom, or effect size. Specify the statistical test used.
- **[0e75d038a870] (severity: writing)** Standardize float placement specifiers (replace [h] with [htbp]) to ensure consistent figure/table positioning across compilation runs.
- **[6a0d3348eb19] (severity: writing)** Review manual \vspace adjustments (e.g., -0.3em around sections); consider relying on class defaults to improve layout robustness.
- **[a8500f55805d] (severity: writing)** Unify table environments for full-width tables (prefer tabularx over tabular* to avoid overfull hbox warnings).
- **[8acd3bd807b5] (severity: writing)** Verify \beginappendix and \affiliation commands against fairmeta class documentation to ensure no custom hacks are required.
- **[c48225770dcc] (severity: writing)** Fix typo 'generatio' to 'generation' in sections/experiment.tex (Section 3.3).
- **[4c4167dd09fc] (severity: writing)** Standardize spelling of 'organized' vs 'organised' across the document.
- **[472f98dc20cd] (severity: writing)** Improve phrasing in sections/appendix.tex (e.g., 'manifested in' to 'shown in', '4/5 step-by-step pass' to '4/5 step-by-step runs passed').


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 38 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
