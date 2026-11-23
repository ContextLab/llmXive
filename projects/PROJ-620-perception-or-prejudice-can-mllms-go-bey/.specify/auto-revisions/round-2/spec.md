# Revision Specification: Paper Science Revision — PROJ-620-perception-or-prejudice-can-mllms-go-bey round 2

**Generated**: 2026-06-26T01:11:54.006188+00:00
**Kind**: paper_science
**Project**: PROJ-620-perception-or-prejudice-can-mllms-go-bey
**Round**: 2

## Input

Address the following reviewer-raised action items:

- **[17b7aecc1a0b] (severity: science)** Code artifacts (evaluation scripts, annotation pipeline, config files) are not included in the review input, preventing assessment of reproducibility, modularity, and test coverage.
- **[c619818dd2f5] (severity: writing)** Explicitly state the SPDX license identifier for the MM-OCEAN annotations (e.g., CC-BY-NC 4.0) rather than 'research-only' (Appendix D).
- **[08d3f811dd8f] (severity: writing)** Replace the anonymized Hugging Face URL with a permanent DOI or stable repository link for publication (Title page).
- **[1fb3faaae287] (severity: writing)** Verify and resolve all [PLEASE-VERIFY] and [TBD] flags in references.bib to ensure citation integrity.
- **[d603ca5cbd8e] (severity: writing)** Report the exact number of videos dropped due to the <3 MCQs filter in Stage 5 for full data transparency (Section 4.3).
- **[9f7b1c51deef] (severity: writing)** Add accessibility alt-text attributes to all figure environments to comply with modern conference standards for screen readers.
- **[9593c6b6aa3f] (severity: writing)** Review color palette in Figure 5 (radarv3.pdf) and Figure 6 (prg_archetypesv2.pdf) for colorblind accessibility; Red/Green distinctions (openc/humanc) may be indistinguishable to deuteranopes.
- **[022581bde093] (severity: writing)** Resolve redundancy between Figure 1 (pipelinev4.png) and Figure 3 (agentv5b.png). Both depict the annotation pipeline; consolidate to save space or differentiate content clearly.
- **[95dbc52fe5dc] (severity: writing)** Define 'CV' (Coefficient of Variation) at first use in Section 5.3 (Line 269) to aid non-statisticians.
- **[050fbc0c79fe] (severity: writing)** Replace informal shorthand 'bbox' with 'bounding box' in Section 3.1 (Line 333) and Appendix.
- **[965007845b2b] (severity: writing)** Define 'pp' (percentage points) when first used in Section 5.2 (Line 477).
- **[37ad26ebf9e2] (severity: writing)** Expand 'ASR' to 'automatic speech recognition (ASR)' upon first mention in Section 3.3 (Line 463).
- **[982a6081bc12] (severity: science)** The Prejudice Rate (PR) is defined as Pr[r3=0 | r1=1] where r3 comes from T3 MCQs. This does not directly measure whether a specific T1 rating was grounded in the model's actual evidence—it measures separate MCQ performance. The claim '51% of correct ratings are ungrounded' requires clarification or a revised metric that links T1 and T3 on the same sample.
- **[405327bf8043] (severity: writing)** The 'Reasoning-capable MLLMs dominate' finding (Appendix Table) is explicitly marked as observational and confounded (different sizes, families, generations). Yet the abstract and conclusion present this as a finding without qualification. Either reframe as correlational pattern or remove causal language.
- **[3013d8917269] (severity: science)** The T3 vs T1/T2 closed-vs-open gap comparison (Δ_T3 = -26.6pp vs Δ_T1 = -5.6pp) uses different scales (6-option MCQ vs 5-level ordinal). Report normalized gaps (e.g., relative to chance) to make the comparison logically valid.
- **[e112cc84234f] (severity: science)** The AI-as-Judge for T2 shows +1.0 point self-preference for GPT-family models (Table A.12), yet GPT-4o-mini is the primary judge. This circularity should be acknowledged in the main text with sensitivity analysis showing whether it affects the HR ranking.
- **[574dbc83404c] (severity: science)** Temper the claim '51% of correct ratings are not grounded' in Abstract/Intro to acknowledge MCQ limitations (Appendix E).
- **[4df4c142ef16] (severity: writing)** Align 'Reasoning-capable models dominate' claim in Abstract/Intro with 'observational/confounded' language in Appendix H.
- **[52de3d5e996d] (severity: writing)** Clarify EU AI Act claim regarding 'per-prediction explainability' to avoid over-interpreting the regulation (Intro).
- **[cef8ce5ea2d2] (severity: writing)** Explicitly state IRB/ethics committee approval status for the 24 human annotators involved in Stage 1 and Stage 5 of the pipeline (Appendix \ref{app:human}).
- **[bb7d57584347] (severity: writing)** Clarify the consent scope of the source ChaLearn V2 data regarding personality inference and ensure the new annotation layer does not exceed original consent terms.
- **[0697d5f6500d] (severity: writing)** Strengthen the limitation statement in Appendix \ref{app:ethics} to explicitly prohibit using the benchmark for high-stakes decision-making (e.g., hiring) without regulatory approval.
- **[2b3faa972803] (severity: science)** Add statistical significance tests (e.g. bootstrap confidence intervals) for the central 'Prejudice Gap' (51% PR) and the Closed-Open T3 gap (-26.6%) to quantify uncertainty.
- **[2f6f71faf752] (severity: science)** Report confidence intervals for the PR/HR metrics across the 27 models to assess the stability of the failure-mode rates beyond point estimates.
- **[eecdd483931e] (severity: science)** Report 95% confidence intervals (e.g., via bootstrapping) for all primary metrics (T1 Acc, T3 Acc, HR) in Table 1 to quantify estimation uncertainty.
- **[dc39e97bf514] (severity: science)** Perform statistical significance testing (e.g., paired t-test or McNemar's) for top-model comparisons rather than relying solely on point-estimate rankings.
- **[549731ad4227] (severity: science)** Address multiple-comparisons correction when claiming specific performance gaps (e.g., the -26.6% open-vs-closed T3 gap) are statistically significant.
- **[0e71572a152d] (severity: writing)** Replace the custom author block (centerline + tabular) with the standard LaTeX uthor macro to avoid potential alignment issues and to comply with the conference template's author formatting guidelines.
- **[6817b4bc904e] (severity: writing)** Remove or reduce the numerous negative space commands (e.g., \vspace{-0.6cm}, \vspace{-0.2cm}) placed before sections and inside figures; they can cause overlapping text and inconsistent vertical spacing across pages.
- **[4bd387f5315e] (severity: writing)** Ensure that figure captions are placed immediately after the \includegraphics line and before any manual vertical spacing adjustments; the current \vspace{-0.6cm} after \caption may truncate the caption or cause it to collide with surrounding text.
- **[f93c6e078043] (severity: writing)** Standardize list formatting: the itemize environments use custom leftmargin and itemsep settings; verify that these do not exceed the template's margin limits and that bullet alignment is consistent throughout the manuscript.
- **[67937c547343] (severity: writing)** Check table scaling commands (e.g., \scalebox{0.85}{...}) for readability; excessive scaling can make column headers too small and may violate the minimum font size requirement of the venue.
- **[22bbc2a0093d] (severity: writing)** Confirm that all citation commands follow the numeric style set by \setcitestyle; some in‑text citations appear without surrounding parentheses (e.g., "AI‑powered interview screening~\cite{naim2016automated}") which may be inconsistent with the bibliography style.
- **[1db95116e9ea] (severity: writing)** Review the use of \begin{center} environments after \maketitle; they introduce additional vertical space that may conflict with the template's title block layout.
- **[e5f59698aa3b] (severity: writing)** Section 4.4 states 'We define five quantities' but lists 'two population-level signals and four sample-level rates' (total 6). Correct the count or the list.
- **[0aeac965c67e] (severity: writing)** Section 5.3 contains a comma splice: 'Informative exceptions exist, Gemma-4-31B-it ranks...'. Use a semicolon or period. Also clarify the '13.5th' rank, as ranks are typically integers.
- **[5762fa6a0a72] (severity: writing)** Appendix (Open-Source Size Scaling) starts with a sentence fragment: 'Open-source MLLMs at three parameter scales (Table~ef{tab:scaling}).'. Complete the sentence.
- **[5082664d8109] (severity: writing)** Appendix (Worked Example) uses '+' informally: 'GPT-4o's matching T1 + plausible T2 reasoning'. Replace with 'and'.
- **[36cb42b668e2] (severity: writing)** Introduction (Section 5.2) has a missing relative pronoun: 'even at the closed-source frontier, $\sim\!15\%$ of correct ratings remain ungrounded.' Add 'where' before the percentage.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 39 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
