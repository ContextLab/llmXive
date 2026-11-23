# Revision Specification: Paper Science Revision — PROJ-644-omniretrieval-unified-retrieval-across-h round 1

**Generated**: 2026-06-14T10:12:53.974037+00:00
**Kind**: paper_science
**Project**: PROJ-644-omniretrieval-unified-retrieval-across-h
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[d53f886aa702] (severity: science)** Verify all bibliography entries have valid publication dates and accessible URLs; remove or replace citations to 2025-2026 dated papers that cannot be confirmed (e.g., GPT-5 arXiv:2601.03267, Text2Cypher 2025)
- **[a375627258b1] (severity: science)** Replace references to non-existent model versions (GPT-5.4, Gemini-3.1, Sonnet-4.6, Qwen-3.5, Gemma-4) with publicly verifiable models; re-run all experiments and report results
- **[4665745e5756] (severity: science)** Provide complete implementation artifacts (code, data splits, model checkpoints) to enable independent reproduction of all reported metrics in Table 1
- **[bd2ad8f04335] (severity: writing)** Add verification_status field to all bibliography entries and ensure every citation is either verified or marked as unverified with explanation
- **[bf875b85f2e9] (severity: science)** Multiple critical citations referenced in text have no corresponding bibliography entries: GPT-54 (GPT-5.4/GPT-5.4-mini), Gemini31Pro (Gemini-3.1 Pro), Sonnet46 (Sonnet-4.6), Qwen3.5, Gemma4, GEval (LLM-as-a-Judge), HyDE (search rewriting), SBERT (all-MiniLM-L6-v2), ToG (entity-linking), vLLM. These undermine verifiability of claims throughout Sections 2, 5, and 6.
- **[260be91f1bb6] (severity: writing)** BEIR benchmark description in Section 5.1 is incomplete: BEIR contains 18 datasets total, not 7. The paper lists 7 specific datasets used but should clarify this is a subset selection, not the full benchmark. Current phrasing could mislead readers about benchmark coverage.
- **[fb70fe1554a3] (severity: science)** Specific numerical claims in Section 6 require verification against figures/tables: (1) 'multi-candidate 1-of-k accuracy drops from 67.5% at k=3 to 62.8% at k=10' (Figure 2); (2) 'off-diagonal mean of 28.2% against 15.2 to 22.1% for structured paradigms' (Figure 4). Exact numbers should be cross-checked with source data.
- **[5ce5f217179c] (severity: writing)** BIRD benchmark database count (80 databases) and Spider count (206 databases) should be verified against official benchmark releases. The total of 286 knowledge bases is stated as fact but needs explicit confirmation from source documentation.
- **[eb0be03fdde2] (severity: science)** Code artifacts (implementation scripts, configs, dependencies) are not included in the review input, preventing verification of reproducibility, modularity, and test coverage.
- **[5c11321cbc97] (severity: writing)** Dataset versions not specified for reproducibility. Section 5.1 lists 13 datasets (Spider, BIRD, BEIR, etc.) but does not state version numbers or commit hashes. Add version identifiers for each dataset to enable exact replication.
- **[3120e6e819bd] (severity: writing)** External endpoint URLs lack versioning. Section 5.1 references Wikidata SPARQL endpoint (query.wikidata.org/sparql) and Neo4j demo endpoint without version tags. These are mutable; archive snapshots or versioned endpoints should be cited.
- **[686261e979cb] (severity: writing)** Dataset licenses not itemized. Appendix A Section "Use of Existing Artifacts" states "use each under its respective license" but does not enumerate licenses per dataset. Add a table mapping each of the 13 datasets to its specific license for compliance verification.
- **[771fd70675a0] (severity: science)** Missing-data handling not discussed. The benchmark spans 309 knowledge bases with heterogeneous schemas, but no protocol for missing values, incomplete triples, or empty query results is described. Clarify how such cases are treated in metrics.
- **[8884ed8a69f4] (severity: writing)** In figures/cross_backbone_selector.tex, the figure* environment contains three distinct elements (two figures and a table) with separate \\captionof commands. This fragments the figure's semantic identity and confuses PDF accessibility tools. Consolidate into a single figure with subcaptions or split into separate figure environments.
- **[66c66b05a8bf] (severity: writing)** In figures/cross_backbone_selector.tex, the table uses \\resizebox{\\linewidth}{!}{...} to fit a 0.315\\linewidth minipage. This risks distorting aspect ratios and rendering text illegibly small at print scale. Use font size adjustments (e.g., \\small) or \\tabularx instead.
- **[96afa7b3d28c] (severity: writing)** In figures/qwen_scaling.tex, the right minipage width is set to 0.28\\linewidth. This leaves insufficient space for the embedded plot (qwen_diversity_fig.pdf) to display axis labels and legends legibly. Increase width to at least 0.35\\linewidth or reduce the left plot's width.
- **[8c0fb38c8c7b] (severity: writing)** In figures/prompts/*.tex, the promptbox uses \\footnotesize for code content. In a two-column print layout, this may be too small for readers to parse the prompt structure. Consider \\scriptsize for the box frame but \\normalsize for the verbatim content, or ensure the box height does not exceed 3-4 lines.
- **[53f54f5a6ad0] (severity: writing)** Define the acronym 'KB' (Knowledge Base) at first use in the main text, as it appears in Figure 4 and Section 6 without explicit definition.
- **[4c9ac347123c] (severity: writing)** Spell out 'NDCG@10' as 'Normalized Discounted Cumulative Gain at 10' upon first mention in Section 5.3 to aid non-specialist readers.
- **[72ec625545c0] (severity: writing)** Replace dense phrases like 'structural affordances' (Abstract, Introduction) with plainer alternatives like 'structural features' or 'unique capabilities'.
- **[6e9fca54decf] (severity: writing)** Clarify 'LLM-as-a-Judge' and 'vLLM' acronyms in Section 5.3, ensuring 'LLM' is explicitly linked to 'Large Language Model' in that context.
- **[3844287e820f] (severity: science)** The claim that unified-representation methods have a 'fundamental limit' is based on a constrained baseline that is not comparable to full-scale unified methods. The paper acknowledges this setup is 'non-comparable' (Table 2) yet draws general conclusions. Either remove this claim or provide a fair comparison.
- **[77a36298681a] (severity: science)** The 'Retrieval Accuracy' metric macro-averages NDCG@10 (ranking quality, continuous) with Execution Match (binary correctness). These measure fundamentally different aspects of retrieval. The paper should clarify this distinction or use separate metrics for each paradigm.
- **[5d34e256a3fd] (severity: writing)** The claim that evidence selection 'recovers' semantically equivalent answers from alternative KBs relies on the LLM-as-a-Judge accepting alternative KBs as correct. This is a design choice for the judge metric, not a general retrieval property. Clarify this distinction to avoid conflating metric definition with task objective.
- **[237efcf6018e] (severity: writing)** Tone down the claim that source selection identifies correct KBs with 'high accuracy' (Introduction) to reflect the ~66% average performance reported in Table 1.
- **[28b627734478] (severity: writing)** Add a limitation regarding the context-window constraints of the source-selection step when scaling beyond 309 KBs, currently missing from Section 7.
- **[5a10634aff4d] (severity: writing)** Clarify that the benchmark is skewed toward Search (7/13 datasets) and discuss how this affects the 'Unified' performance claim.
- **[3b8fbb7558af] (severity: writing)** Temper the Abstract's claim of a 'general-purpose interface' to acknowledge the ~34% source selection failure rate and reliance on evidence-selection fallback.
- **[1c04da352a64] (severity: writing)** Add a dedicated discussion of privacy and PII handling, especially given that the benchmark includes unfiltered document corpora (see Appendix A, §A.1).
- **[e89af1b736eb] (severity: science)** Provide an evaluation of content-filtering or toxicity-mitigation mechanisms for the retrieved evidence across all backends (document, SQL, SPARQL, Cypher).
- **[cc63454648ed] (severity: writing)** Explicitly state the licensing terms of each of the 13 datasets and 309 knowledge bases, and describe how the system respects copyright and data-use restrictions.
- **[21b54ac18ec9] (severity: writing)** Discuss dual-use risks: the ability to issue native queries to heterogeneous backends could be abused to extract disallowed or harmful information, and outline mitigation strategies (e.g., rate-limiting, query sanitisation, access-control policies).
- **[5360f539f94b] (severity: science)** Re-run experiments with multiple random seeds to report standard deviation or confidence intervals for all main metrics in Table 1. Single-run results (Section 5.3) do not support statistical claims.
- **[2866fd9c238e] (severity: science)** Perform statistical significance testing (e.g., t-test or permutation test) on the reported gains over baselines to validate that improvements are not due to random variance.
- **[3453773c9c12] (severity: science)** Address potential evaluation bias in the LLM-as-a-Judge metric (Section 5.3). Using GPT-5.4-mini to judge GPT-5.4 outputs may introduce family bias; consider using an independent judge model.
- **[eaf992545185] (severity: science)** Report 95% confidence intervals for all metrics in Table 1 via bootstrapping over the test set, as single-run results lack variance estimates.
- **[1ff2bf25f24c] (severity: science)** Address multiple comparisons in ablation studies (Figures 3-5) where $k$ and backbone scales are swept; justify significance or apply correction.
- **[b8517e4608cb] (severity: writing)** Fix \appendix syntax: \appendix does not accept arguments in standard LaTeX; change \appendix{\input{...}} to \appendix followed by \input on a new line.
- **[ca2364361ed7] (severity: writing)** Add missing table packages: \rowcolor and \toprule require colortbl/xcolor[table] and booktabs, which are not explicitly loaded in paper.tex.
- **[b56ea5836f14] (severity: writing)** Reorder sections: sections/3_related_work.tex is included after experimental results; move to before method or setup for standard logical flow.
- **[9cc8c03eeba7] (severity: writing)** Standardize cross-references: cleveref is loaded but text uses Figure~\ref{}; switch to \cref{} for consistency with package configuration.
- **[b996fa3c61e1] (severity: writing)** Replace the colloquial phrase "In the meantime" in sections/3_related_work.tex with "Meanwhile" or "Concurrently" to maintain formal register.
- **[00013cd1ef7e] (severity: writing)** Change sentence-initial "Also" to "Furthermore" or "Additionally" in sections/6_experimental_result.tex for improved academic tone.
- **[9317eeec68d9] (severity: writing)** Clarify the ambiguous antecedent in sections/5_experimental_setup.tex regarding "itself a small slice" to ensure precision.
- **[f1b84376620c] (severity: writing)** Split dense sentences in sections/4_method.tex (Query Formulation paragraph) to improve readability without losing technical rigor.
- **[900a791146dc] (severity: writing)** Replace the phrasing "traces to" with "stems from" in sections/6_experimental_result.tex (Analysis on Source Candidate Size) for better academic register.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 46 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
