---
action_items:
- id: 97bcb9450032
  severity: science
  text: In Section supp_vlms, the text claims 'gains are modest' on Perspective Taking
    (PET) for Qwen IPT, but Table tab:qwen_discrete shows a decrease (50.5% Answer-only
    vs 50.0% IPT). Correct the text to reflect the data or re-run the experiment.
- id: eb6415dd7d87
  severity: science
  text: In Table tab:pt_breakdown, the row '+ Mixed Training' is ambiguous. Section
    supp_data_pt (Path Tracing) does not mention 'Mixed Training' (only supp_data_pet
    does). Clarify if this row includes PET data or IPT tokens. If it includes PET
    data, update supp_data_pt to reflect the training composition to support the causal
    claim that IPT (not data mixing) drives improvement.
- id: fd23a1a09f66
  severity: writing
  text: Ensure the main results table explicitly labels the IPT model (e.g., 'Bagel
    + IPT') rather than '+ Mixed Training' to clearly isolate the IPT component in
    the ablation study supporting the core claim.
artifact_hash: c5de9734fccbfd100241f7fc8603c599264726354d7ecbedd4d657c0e121782f
artifact_path: projects/PROJ-681-imaginative-perception-tokens-enhance-sp/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T10:12:23.052585Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a logical argument that Imaginative Perception Tokens (IPT) enhance spatial reasoning. However, there are inconsistencies between the textual claims and the reported data, as well as ambiguities in the experimental setup description that obscure the causal link between IPT and performance gains.

**1. Contradiction in PET Results (Section supp_vlms)**
In Section `supp_vlms`, the text states: "On Perspective Taking, gains are modest." However, Table `tab:qwen_discrete` reports PET accuracy for Qwen2.5-VL 3B as 50.5% for "Answer-only" and 50.0% for "IPT (CB 1K, f=16)". This represents a slight decrease, not a gain. This contradiction undermines the credibility of the reported results in this section. The text must be corrected to accurately reflect the data (e.g., "no significant gain" or "mixed results") or the experiment must be re-run.

**2. Ambiguity in Path Tracing Training Data (Table tab:pt_breakdown vs. Section supp_data_pt)**
The core claim is that IPT enhances reasoning. Table `tab:pt_breakdown` shows a row labeled "+ Mixed Training" outperforming "Bagel (label-only)". However, Section `supp_data_pt` (Path Tracing Data Curation) describes a synthetic training set of 11,204 examples without mentioning "Mixed Training". Conversely, Section `supp_data_pet` explicitly defines a "mixed PET training variant" combining AI2-THOR, Habitat, and VST.
If the "+ Mixed Training" row in the Path Tracing results table refers to mixing Perspective Taking data into the Path Tracing training, this is not documented in `supp_data_pt`. If the improvement comes from data mixing (PET data helping PT task) rather than the IPT mechanism itself, the causal claim "IPT Enhances..." is not fully supported by this table. The training composition for this row must be explicitly defined in `supp_data_pt` or the row label must be changed to "Bagel + IPT" if IPT is the sole variable.

**3. Isolation of IPT Effect**
To logically support the title claim, the ablation study must clearly isolate the IPT component. Currently, the label "+ Mixed Training" conflates data composition with the IPT mechanism. Renaming this row to explicitly indicate the presence of IPT (e.g., "Bagel + IPT") and ensuring the data description matches will strengthen the logical consistency of the evidence.

These issues are fixable through text corrections and clarifications in the supplementary material.
