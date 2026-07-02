---
action_items:
- id: c4516a03c748
  severity: writing
  text: Section 2.1 defines 'brain activity' to include glial metabolism but later
    reviews methods (GLMs, RSA) that only measure neuronal signals. Clarify if the
    methods are insufficient for the defined scope or if the definition should be
    narrowed to 'neural activity' to maintain logical consistency.
- id: 40742a2a92b4
  severity: science
  text: Section 3.1.3 claims joint models are 'most accurate' because truth lies 'between'
    stimulus and neural trajectories. This assumes a linear intermediate without proving
    why the true representation isn't a non-linear transform of one or the other.
    Provide a mechanism for this assumption.
artifact_hash: 88c485888572e5b5ec21db55f3e25c0d533affd80dd028fd7994137fbaf7e64e
artifact_path: projects/PROJ-568-identifying-stimulus-driven-neural-activ/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:22:51.360545Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The manuscript presents a comprehensive survey of methods for identifying stimulus-driven neural activity, but there are specific logical gaps where the conclusions do not strictly follow from the stated premises or where definitions are introduced but not integrated into the subsequent argumentation.

First, in Section 2.1 ("How can we measure neural 'activity'..."), the text explicitly defines "brain activity" to include non-neuronal phenomena, specifically citing glial cells and their role in metabolism and synapse formation. The text then states, "the term neural activity can be more precise way of referring to these phenomena." However, the subsequent sections reviewing specific methodologies (GLMs, MVPA, RSA, etc.) focus exclusively on neuronal signals (spikes, LFPs, BOLD). The logical inconsistency arises because the review implies these methods are sufficient to capture the "brain activity" defined in the introduction, yet the methods described are incapable of measuring the glial activity just defined as part of that scope. The conclusion that these methods identify "stimulus-driven neural activity patterns" is sound only if the definition of "brain activity" is narrowed to "neural activity" immediately, or if the text explicitly acknowledges that the reviewed methods ignore the glial component of the previously defined "brain activity."

Second, in Section 3.1.3 regarding "Joint stimulus-activity models," the authors argue that neither the stimulus trajectory nor the neural trajectory alone provides a complete reflection of internal mental representations. The text posits that the "true representation" lies "somewhere between" the stimulus and neural trajectories, leading to the conclusion that a joint model is the "most accurate" approach. This conclusion is not logically necessitated by the premises. The premises establish that the stimulus model is limited by experimentalist assumptions and the neural model is limited by noise and internal state. However, it does not follow that the truth is a linear or geometric intermediate (the "between" state). It is equally plausible that the neural trajectory is a complex, non-linear function of the stimulus trajectory, or that the stimulus model is entirely irrelevant to the specific neural representation being measured. The text asserts the necessity of a joint model without providing a mechanism or logical derivation for why the "truth" must be a compromise between the two rather than a specific transformation of one. This weakens the logical support for the claim that joint models are inherently superior to refined univariate models.

Finally, in Section 3.2.1 regarding "Hierarchical matrix factorization models," the text claims that HTFA allows for "across-subject comparisons" because "each subject has the same set of factors." The logical leap here is that having the same *number* of factors (K) and a shared *prior* (global template) guarantees that the factors are *comparable* in a functional sense. The text assumes that the hierarchical constraint forces the factors to align functionally across subjects. However, without a premise stating that the underlying neural architecture is invariant across subjects (which is contradicted by the earlier discussion of individual differences in electrode placement and neuroanatomy), the conclusion that the resulting factors are directly comparable is not fully supported. The method enforces a structural similarity, but the logical link to functional comparability requires an additional assumption about the stability of functional topography across the patient population, which is not explicitly stated as a premise.
