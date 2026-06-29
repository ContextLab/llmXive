---
action_items:
- id: 6e582c460272
  severity: writing
  text: Define all acronyms (MCC, SSM, BPE, k-mer, TF, lncRNA, MoE, T2T) at first
    use in Abstract or Introduction.
- id: 0b1dd7d161df
  severity: writing
  text: Replace technical shorthand (T-dec, T-enc, SN) with full terms in Appendix
    tables or define in caption.
- id: 1dfa52f6ae6b
  severity: writing
  text: Clarify 'shot' regimes (1-shot, 10-shot) as 'examples per class' for non-ML
    readers.
- id: d532821b6e19
  severity: writing
  text: Expand benchmark acronyms (GUE, GB, NT, iDHS) in Appendix Task Taxonomy.
artifact_hash: 043e93d2fab619e0251c0029f296fc31d53c712bc78a466a1a30d67af8b711e1
artifact_path: projects/PROJ-679-geneb-why-genomic-models-are-hard-to-com/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T02:55:26.288079Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript presents a comprehensive benchmark but relies heavily on domain-specific jargon that excludes non-specialist readers, particularly those from biology or general computer science backgrounds. While the field is technical, the paper frequently introduces acronyms and shorthand without definition, violating standard accessibility practices for broad-impact venues.

In the **Abstract**, "MCC" is used as the primary metric without expansion (Matthews Correlation Coefficient). Similarly, "13 functional categories" is vague; specifying "e.g., histone modifications, promoters" would aid clarity. The **Introduction** and **Related Work** sections introduce "SSM" (State Space Model), "BPE" (Byte Pair Encoding), and "$k$-mer" without definition. A reader unfamiliar with NLP or genomics preprocessing will not understand these terms. The **Methodology** section uses "linear probing" and "logistic regression (\texttt{max\_iter=1000})"; the code parameter is unnecessary jargon for a methods description and should be moved to an appendix or simplified to "standard logistic regression."

The **Appendix** contains significant jargon density. Table~\ref{tab:model_summary} uses "T-dec", "T-enc", and "SN" without a legend. "T2T" (Telomere-to-Telomere) and "MoE" (Mixture of Experts) appear in model names but are undefined. The **Task Taxonomy** (Appendix) lists benchmarks like "GUE", "GB", "NT", and "iDHS" without spelling out their full names or origins. Additionally, specific biological markers like "4mC", "5mC", and "6mA" are listed without context (DNA methylation types).

Finally, the term "shot" (1-shot, 10-shot) is standard in machine learning but may confuse biologists; clarifying this as "number of labeled examples per class" would improve accessibility. The **Figure Captions** (e.g., Fig.~\ref{fig:frontier}) use "Pareto frontier" without brief explanation.

To improve readability, the authors should add a glossary or ensure every acronym is defined at first mention. Shorthand in tables should be expanded or footnoted. This will ensure the benchmark's insights are accessible to the broader scientific community beyond genomic ML specialists.
