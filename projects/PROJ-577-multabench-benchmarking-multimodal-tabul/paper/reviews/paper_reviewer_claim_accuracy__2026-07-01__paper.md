---
action_items:
- id: 36f2df9c2031
  severity: writing
  text: The claim that 'ConTextTab set the SOTA for the CARTE benchmark' (Section
    2, Related Work) is not supported by the provided bibliography. The citation \cite{spinaci_contexttab_2025}
    is missing from neurips2026.bib. Without this source, the specific performance
    claim on CARTE cannot be verified.
- id: ed24e1cd7c91
  severity: writing
  text: The paper claims MulTaBench is the 'largest image-tabular benchmarking effort
    to date' (Abstract, Section 1). While the authors cite \cite{lu_mug_2023} and
    \cite{tang_bag_2024} as smaller predecessors, the bibliography lacks entries for
    these specific benchmark papers (only generic or unrelated entries exist for similar
    years). The claim of 'largest' requires explicit citation of the competing benchmarks'
    sizes to be verifiable.
- id: 3c5d7c94ec1a
  severity: writing
  text: In Section 3, the paper states that 'TAR consistently outperforms frozen embeddings
    across all new models' (Figure 4 caption). However, Table 1 in the Appendix (tab:win_rate)
    shows TabICLv2 has a win rate of only 55.0% for Image tasks. The text 'consistently
    outperforms' is an overstatement given that the model wins in only slightly more
    than half the cases, which is not statistically 'consistent' in a strong sense.
- id: 8d7d3fea8436
  severity: writing
  text: The claim that 'ConTextTab... struggles on MulTaBench' (Section 2) is supported
    by Figure 4, but the specific comparison to CARTE performance relies on the missing
    \cite{spinaci_contexttab_2025} citation. The argument that MulTaBench targets
    a 'fundamentally different' problem is plausible but the specific evidence linking
    ConTextTab's CARTE success to its MulTaBench failure is weakened by the missing
    reference.
artifact_hash: 28e097e31933ecce294eb34fd92a9e53c4dcbbab117fcc0a77af75a314777084
artifact_path: projects/PROJ-577-multabench-benchmarking-multimodal-tabul/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:48:34.638777Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and the validity of their supporting citations.

**Citation Gaps and Unverifiable Claims:**
The most significant issue is the absence of critical citations in the provided `neurips2026.bib` file. Specifically:
1.  **ConTextTab on CARTE:** The paper claims in Section 2 (Related Work) that "ConTextTab set the SOTA for the CARTE benchmark \cite{spinaci_contexttab_2025}". The bibliography does not contain an entry for `spinaci_contexttab_2025`. Without this source, the specific claim about SOTA performance on CARTE is unverifiable.
2.  **Predecessor Benchmarks:** The claim that MulTaBench is the "largest image-tabular benchmarking effort to date" (Abstract, Section 1) relies on comparing against \cite{lu_mug_2023} and \cite{tang_bag_2024}. These specific benchmark papers are not present in the bibliography (only generic or unrelated entries for similar years exist). To substantiate the "largest" claim, the paper must explicitly cite the works that established the previous size records.

**Overstated Conclusions:**
In Section 5 (Robustness Analysis), the text states: "Target-aware embeddings consistently outperform frozen embeddings across all new models and modalities." This is visually supported by Figure 4, but the quantitative data in Appendix Table `tab:win_rate` contradicts the strength of this claim for specific models. For the **Image** modality, **TabICLv2** has a win rate of **55.0%**. A 55% win rate (barely better than random chance) does not support the descriptor "consistently outperforms." The claim should be qualified to reflect that while the *majority* of models show gains, the effect is not uniform across all architectures, particularly TabICLv2.

**Logical Consistency of Evidence:**
The argument that ConTextTab "struggles on MulTaBench" (Section 2) is used to highlight the difference between CARTE and MulTaBench. While Figure 4 shows lower performance for ConTextTab on MulTaBench, the causal link to its previous success on CARTE is weakened by the missing citation for the CARTE result. The paper asserts a "fundamentally different" problem type, but the evidence for the baseline (CARTE performance) is currently missing from the reference list.

**Recommendation:**
The authors must add the missing bibliography entries (`spinaci_contexttab_2025`, `lu_mug_2023`, `tang_bag_2024`) to verify the comparative claims. Additionally, the language regarding "consistent" performance should be adjusted to accurately reflect the 55% win rate of TabICLv2, perhaps by stating "outperforms in the majority of cases" or "shows gains across most, but not all, models."
