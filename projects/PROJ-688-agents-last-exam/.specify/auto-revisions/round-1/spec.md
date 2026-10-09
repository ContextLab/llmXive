# Revision Specification: Paper Science Revision — PROJ-688-agents-last-exam round 1

**Generated**: 2026-06-11T19:00:15.736571+00:00
**Kind**: paper_science
**Project**: PROJ-688-agents-last-exam
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[2c5f5b8d9a7a] (severity: writing)** Verify that every bibliography entry has verification_status: verified; add any missing citations and ensure all in‑text citations resolve to these entries.
- **[7494c40be1e0] (severity: writing)** Add explicit statements linking each major claim in the abstract, introduction, and conclusion to the corresponding figures or tables (e.g., Fig. 2, Table 1) that provide the supporting evidence.
- **[5b57a1b54a10] (severity: writing)** Provide a concise reproducibility checklist in the Methods/Experiment sections, specifying software versions, VM configurations, and random seed handling to ensure results can be replicated.
- **[1897a2189457] (severity: writing)** Replace any placeholder macros (e.g., \taskcount, \totalvariants) in the final PDF with their concrete values to avoid ambiguity for readers.
- **[a6075591647c] (severity: writing)** Abstract claims average full pass rate is 2.6% for hardest tier but Table tab:main-results Last-Exam column shows pass rates from 0.0% to 8.6% across configurations. Verify this aggregate value is explicitly calculated and documented.
- **[3b183e383be0] (severity: writing)** Paper claims 13 of taskcount subdomains entirely uncovered but Table tab:related-comparison does not display coverage counts per benchmark. Include actual numbers to support this claim.
- **[f2da61766859] (severity: writing)** The first benchmark to cover all taskcount SOC/O*NET industries claim is strong. The related work table shows breadth as ratios without explicit verification that ALE uniquely covers all 55 subdomains. Add clarifying text or footnote.
- **[8b2948fa2ebe] (severity: writing)** ALE-CLI comparison states 25.2% overall pass rate for Codex plus GPT-5.5 but Table tab:main-results lower panel shows 26.4% for this configuration. This numerical discrepancy must be resolved.
- **[2d6a196dd14c] (severity: writing)** Bibliography file references.bib is not included in the submission. All citation keys cannot be verified. Include the bibliography file or confirm citations are externally accessible.
- **[284b993efdc3] (severity: writing)** Code quality review cannot be performed: no actual code repository, task specifications (main.py), evaluation scripts, or test files were provided. Only paper LaTeX source and figures are available. For code-quality review, submit the benchmark implementation repository or at minimum representative task specification files and scoring code.
- **[0e35453b79be] (severity: writing)** Explicitly state the data license (e.g., CC-BY, OpenRAIL) for the benchmark dataset in the main text or appendix. Currently, only repository links are provided (main.tex lines 55-58), leaving legal terms ambiguous for downstream reuse.
- **[e9f5c9642313] (severity: writing)** Document the task metadata schema (e.g., JSON/YAML structure) in an appendix. The paper describes Python functions (app:task-spec-protocol lines 1350-1400) but lacks a concrete schema definition for the 1.5K task instances.
- **[490821af1d89] (severity: writing)** Clarify the dataset versioning policy in the main text. While 'ALE-V1, 2026/06' appears in an appendix (app:executed-industry-task-inventory.tex line 1230), the rolling evaluation strategy requires explicit version tags for reproducibility.
- **[8a49f157f589] (severity: writing)** Figure 2 (panel_c_subdomain.pdf) plots 55 subdomains on a single axis. At print scale, y-axis labels will overlap or become illegible. Aggregate categories or use an interactive supplement.
- **[26afbcc92a56] (severity: writing)** Appendix heatmaps (Figs A4-A6) use 1.25\textwidth for ~150 rows. Cell text will be unreadable. Reduce instance count or provide high-res vector versions for inspection.
- **[dff08ffdb44f] (severity: writing)** The custom scoring palette (sc0-s5) uses a red-green gradient. This is not colorblind-safe. Switch to viridis/cividis for quantitative heatmaps to ensure accessibility.
- **[6a9eb68bea70] (severity: writing)** All includegraphics commands lack alt text attributes. Add descriptive alt text or ensure captions are sufficiently detailed for screen readers.
- **[d9d4f5a33ca9] (severity: writing)** Define 'LLM' (Large Language Model) at first use in Abstract.
- **[14d1ebe01acf] (severity: writing)** Spell out 'SOC' (Standard Occupational Classification) and 'O*NET' (Occupational Information Network) in Abstract.
- **[88fe7e6ca8fb] (severity: writing)** Define 'harness' and 'backbone' with plain English equivalents (e.g., 'orchestration system', 'foundation model') in Abstract/Intro.
- **[acb36a08dce0] (severity: writing)** Define common acronyms (CLI, GUI, VM, API, JSON, TSV) at first occurrence in Introduction or Appendix.
- **[2828ef28dd24] (severity: writing)** Define domain-specific acronyms (CAD, CAM, PLC, SCADA, SPC, URDF, MSA, VST, DAW, MIDI) in relevant Appendix sections.
- **[cc6dff66529b] (severity: writing)** Replace 'GDP relevant' with 'economically significant' for broader accessibility.
- **[b07100c643b3] (severity: writing)** Define 'MCP' (Model Context Protocol?) in Appendix A.1 where 'CUA MCP bridge' is mentioned.
- **[95f3fc40eb30] (severity: writing)** Clarify 'vCPUs', 'RAM', and 'GPU' definitions in Appendix A.4.
- **[dbba6cf2ca87] (severity: science)** Correct Section 4.1 claim that 'most agents achieve a 0% pass rate' on Last-Exam tier; Table 1 shows only 5/12 mainstream configs are 0%.
- **[7d2667917cf3] (severity: science)** Resolve numerical discrepancy between Section 4.1 (25.2% ALE-CLI pass rate) and Table 1 ALE-CLI panel (26.4% for Codex/GPT-5.5).
- **[e7d1a4da9070] (severity: writing)** Clarify Abstract's '2.6% average full pass rate' to explicitly specify it refers to the Last-Exam tier, not overall benchmark average.
- **[448491b6237f] (severity: writing)** Abstract and Introduction claim ALE is an 'instrument for closing the gap... GDP relevant impact'. This conflates benchmark task completion with actual economic value. The paper measures capability, not GDP impact. Suggest reframing to 'measuring potential for economic transformation' to avoid overclaiming causal economic linkage.
- **[910555e72374] (severity: science)** Appendix A.6 claims the public subset 'confirms' representativeness based on a single model (Claude Code + Opus 4.7) correlation. A single configuration is insufficient to confirm general representativeness across diverse agent architectures. Qualify this claim (e.g., 'suggests' or 'under tested configurations').
- **[d022e6a0b9a2] (severity: writing)** Table 1 and Introduction state ALE covers 'all 55 SOC/O*NET industries'. While taxonomy-mapped, the public release contains only 150 tasks. Clarify if 'coverage' refers to taxonomy inclusion or statistically significant evaluation coverage per industry to prevent overstatement of evaluation breadth.
- **[f0ec83455d79] (severity: science)** Include an explicit ethics statement regarding IRB approval or exemption for the 250+ industry experts who contributed tasks. Section 'dataset-details.tex' describes human data collection but lacks consent/IRB documentation.
- **[142a80dcfac1] (severity: writing)** Add a dual-use risk discussion for sensitive task domains (e.g., 'radiology/microdicom' and 'cybersecurity/snake_crackme'). Explain mitigation strategies for potential misuse of medical or offensive security capabilities.
- **[ac5b4de918ed] (severity: writing)** Formalize Conflict of Interest disclosures. 'acknowledgements.tex' lists industry funding (Snorkel AI, Unipat AI) and many industry affiliations, but no explicit COI statement is present.
- **[840012d78111] (severity: science)** Add confidence intervals or standard errors to Table 1 (main results) to quantify uncertainty, as most configurations currently report single-run averages despite agent stochasticity.
- **[9a053e6b5010] (severity: science)** Clarify whether the 'Last-Exam' tier stratification was defined a priori or derived from pilot results to avoid circularity in difficulty claims.
- **[e08a55cf6855] (severity: science)** Validate the public subset's representativeness across multiple model classes, not just Claude Code + Opus 4.7 (Fig. 7), to ensure generalizability.
- **[26a9f526d947] (severity: science)** Report 95% confidence intervals for all mean pass rates and scores in Table 1, not just the subset with repeated runs.
- **[53520924336b] (severity: science)** Apply multiple-comparison correction (e.g., Bonferroni) when ranking harness-model configurations to control Type I error.
- **[2ec9f535acfc] (severity: science)** Validate public subset representativeness using multiple agent configurations, not just a single correlation coefficient.
- **[211c49458c66] (severity: writing)** Replace \resizebox in tables/main_results.tex with \small/\footnotesize and manual column widths to prevent font distortion.
- **[54e35fae747f] (severity: writing)** Remove aggressive \vspace{-5.2em} in main.tex (line 148) in favor of standard spacing commands to improve layout robustness.
- **[3f344deae294] (severity: writing)** Clean up empty \input{author} block in main.tex (line 145) and standardize \par usage in appendix/authors.tex for consistency.
- **[1988e82e6589] (severity: writing)** Verify \faIcon rendering within \resizebox table cells in tables/main_results.tex to ensure correct scaling and alignment.
- **[5c1965f2cf50] (severity: writing)** In Section 4 (Evaluation Pipeline), correct the phrasing 'The rare appearance single ``task'' refers to...' to clarify that the term 'task' alone refers to the instance level.
- **[5e5f83317800] (severity: writing)** In Appendix D (Task Specification Protocol), fix the sentence fragment 'Operating through a mph{session API}...' by integrating it with the preceding sentence or adding a subject.
- **[a0a49654f8a9] (severity: writing)** Replace informal '1K+' notation in the Abstract and Section 3 with formal 'over 1,000' or '1,000+' to match academic style.
- **[392394377237] (severity: writing)** In Appendix E (Timeout Analysis), hyphenate 'five hour' to 'five-hour' when used as a compound modifier before 'wall clock cap'.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 48 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
