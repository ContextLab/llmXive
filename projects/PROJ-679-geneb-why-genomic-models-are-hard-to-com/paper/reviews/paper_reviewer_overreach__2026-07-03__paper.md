---
action_items:
- id: f4d2b6507a6b
  severity: writing
  text: The claim that 'Transformer-based models generally outperform the state-space
    alternative' (Conclusion) overgeneralizes from a limited set of controlled pairs.
    While the paper notes exceptions (e.g., Chromatin Accessibility), the phrasing
    implies a universal architectural superiority not fully supported by the data,
    which shows SSMs can be competitive or superior in specific domains. Qualify this
    claim to reflect the domain-specific nature of the findings.
- id: dc43d549000a
  severity: writing
  text: 'The statement that ''domain mismatch cannot be overcome by scale'' (Section:
    Transfer Learning Analysis) is an absolute claim that risks overreach. The data
    shows a catastrophic failure for one specific prokaryotic model (Evo-1-131k) on
    eukaryotic tasks, but this does not prove that *no* amount of scale could ever
    bridge such a gap. Rephrase to reflect that ''in the evaluated regime, scale did
    not compensate for domain mismatch'' or similar.'
- id: 9e5acd157ac6
  severity: writing
  text: The conclusion that 'Microbial-only corpora transfer poorly to eukaryotic
    tasks' (Conclusion) is based on a single controlled pair (DNABERT-S vs. NT-v2)
    and the performance of Evo-1-131k. While the trend is clear, presenting this as
    a definitive principle without acknowledging the limited sample size of microbial-only
    models in the benchmark constitutes a slight overreach. Add a qualifier regarding
    the sample size.
artifact_hash: 043e93d2fab619e0251c0029f296fc31d53c712bc78a466a1a30d67af8b711e1
artifact_path: projects/PROJ-679-geneb-why-genomic-models-are-hard-to-com/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T13:08:37.380942Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes a compelling case for the heterogeneity of genomic model performance, but several conclusions overreach the specific evidence provided by the benchmark's scope and sample size.

First, the conclusion states that "Transformer-based models generally outperform the state-space alternative." While the data supports this for the majority of categories and the specific controlled pairs analyzed (e.g., Omni-DNA vs. eccDNAMamba), the paper explicitly identifies a domain where SSMs are competitive or superior (Chromatin Accessibility, where eccDNAMamba outperforms GenomeOcean-500M). The use of "generally" without immediately qualifying the specific conditions under which SSMs succeed risks misleading readers into a binary architectural hierarchy that the data does not fully support. The claim should be tempered to emphasize that architectural superiority is highly task-dependent.

Second, the assertion that "domain mismatch cannot be overcome by scale" (Section: Transfer Learning Analysis) is an absolute negative claim. The evidence provided is the failure of a single 7B prokaryotic model (Evo-1-131k) on eukaryotic tasks. While this is a striking result, extrapolating from one data point to a universal law that scale *cannot* overcome domain mismatch is an overreach. It is possible that a larger prokaryotic model or a different training objective could yield different results. The text should be revised to state that "in the evaluated regime, scale did not compensate for domain mismatch" or "the observed data suggests scale alone is insufficient," rather than stating it as an impossibility.

Third, the conclusion that "Microbial-only corpora transfer poorly to eukaryotic tasks" relies heavily on the performance of DNABERT-S (microbial) compared to multi-species models and the prokaryotic Evo-1-131k. Given that the benchmark includes only one or two models with strictly microbial-only pretraining, presenting this as a definitive, generalizable principle without explicitly noting the limited sample size of such models in the study is a minor overreach. The authors should qualify this finding to reflect the specific constraints of their model coverage.

Finally, the claim that "The model that wins under full supervision reranks under 10-shot evaluation in 8 of 13 categories" (Conclusion) is a strong statistical claim. While the data likely supports this, the phrasing implies a systematic instability that might be better described as "significant rank instability" or "frequent reranking" to avoid implying a deterministic rule for 8/13 categories without a deeper statistical test of the stability of these specific rank changes.

These issues are primarily matters of phrasing and the strength of the logical leap from specific data points to general principles. The core science is sound, but the conclusions should be more precisely bounded by the specific limitations of the evaluated model set.
