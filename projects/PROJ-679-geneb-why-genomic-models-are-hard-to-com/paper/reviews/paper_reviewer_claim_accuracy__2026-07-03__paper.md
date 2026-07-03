---
action_items:
- id: 8ef3c62335e2
  severity: writing
  text: In 'Architecture Comparison', the claim that Omni-DNA-1B exceeds eccDNAMamba
    by +0.149 is from a specific controlled pair. Ensure text clarifies this is not
    a universal architecture advantage, as other pairs show negligible differences.
- id: 15de9b61bbd6
  severity: science
  text: In 'Transfer Learning Analysis', the text claims human-only pretraining has
    an advantage for Enhancers (+0.010), but Table tab:transfer_human_multi shows
    Delta = -0.001 (multi-species advantage). Correct the text to match the table
    data.
- id: ee7a6b3f36bd
  severity: writing
  text: In 'Practitioner Recommendations', the specific 10-shot score for MutBERT
    on Histone modifications (0.300) is not cross-referenced to a table or figure
    in the text. Add a citation to the specific data source for verification.
- id: c709861ebe79
  severity: writing
  text: The claim that species classification shows 'no significant scaling' (p=0.056)
    is technically correct at alpha=0.05 but overstates certainty. Rephrase as 'marginally
    non-significant' to accurately reflect the p-value proximity to the threshold.
artifact_hash: 043e93d2fab619e0251c0029f296fc31d53c712bc78a466a1a30d67af8b711e1
artifact_path: projects/PROJ-679-geneb-why-genomic-models-are-hard-to-com/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T13:08:00.271593Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper presents a comprehensive benchmark (GENEB) and makes several strong claims about the limitations of current genomic model comparisons. The core findings regarding the disconnect between model scale and performance, and the importance of pretraining data alignment, are generally well-supported by the provided statistical summaries and tables.

However, there are specific discrepancies between the textual claims and the data presented in the tables that require correction:

1.  **Contradictory Data in Transfer Learning:** In the "Transfer Learning Analysis" section, the text states that human-only pretraining shows an advantage for "Enhancers (+0.010)". However, Table `tab:transfer_human_multi` explicitly lists the $\Delta$ MCC for Enhancers as $-0.001$, indicating a slight advantage for multi-species pretraining (or parity), not human-only. This is a direct factual error in the prose that contradicts the provided data table. The text must be corrected to reflect the table's value.

2.  **Overstatement of Statistical Significance:** The text claims that "species classification" shows "no significant scaling" with a p-value of 0.056. While this is technically not significant at the standard $\alpha=0.05$ threshold, describing it as definitively "no significant scaling" ignores the marginal nature of the result. Given the p-value is very close to 0.05, a more precise phrasing such as "marginally non-significant" would be more accurate and scientifically rigorous.

3.  **Generalization of Controlled Pair Results:** The text frequently presents results from specific controlled pairs (e.g., Omni-DNA-1B vs. eccDNAMamba) as indicative of broader architectural trends. While the paper mentions these are controlled comparisons, the prose sometimes implies these are universal properties of the architectures (e.g., "Transformer models show substantial advantages"). It is crucial to ensure the reader understands these are specific findings from the 30 controlled pairs and not necessarily a universal law, especially given the variability seen in other pairs (e.g., GenomeOcean-500M vs. GENA-LM showing a negligible difference).

4.  **Traceability of Specific Scores:** In the "Practitioner Recommendations" section, specific numerical claims for 10-shot performance (e.g., MutBERT scoring 0.300 on Histone modifications) are stated without a direct citation to a table or figure in the text body. Since the figures are not visible in the text-only review, these claims are difficult to verify. The text should explicitly reference the specific table or figure where these 10-shot breakdowns are detailed.

Addressing these points will ensure the factual claims in the manuscript are perfectly aligned with the underlying data and statistical evidence.
