---
artifact_hash: 88c485888572e5b5ec21db55f3e25c0d533affd80dd028fd7994137fbaf7e64e
artifact_path: projects/PROJ-568-identifying-stimulus-driven-neural-activ/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T14:44:06.389717Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

**Claim Accuracy Review**

This survey chapter makes many literature-anchored claims that generally appear well-supported, but several citations require verification for accuracy:

**Section 1.1 (Overview, lines 95-115):** The claim that identifying neural responses to stimuli "can be incredibly challenging" is attributed to Jonas & Kording 2017 (JonaKord17). This paper addresses whether neuroscientists can understand a microprocessor—not the general challenge of stimulus-response mapping. Consider replacing with a more directly relevant citation on neural decoding challenges.

**Section 1.2.2 (Invasive approaches, lines 325-335):** The statement that "Stimulus-driven responses in individual neurons or small circuits that unfold over sub-millisecond timescales can **only** be measured using invasive approaches like iEEG and ECoG" is overly strong. MEG can capture millisecond-scale dynamics non-invasively. The absolute "only" should be softened to "primarily" or similar language.

**Section 1.2 (Activity, lines 165-185):** The claim that "the adult human brain contains roughly 100 billion neurons" lacks a direct citation despite appearing as a standalone factual claim. The Herculano-Houzel 2009 (Herc09) citation appears later for the cortex mass/neuron proportion—consider consolidating or adding a direct citation for the 100B figure.

**Section 2.1.3 (Joint stimulus-activity models, lines 740-850):** The geometric descriptions of procrustean transformations and trajectory alignment cite Haxby et al 2011 (HaxbEtal11). This is appropriate for hyperalignment, but the description conflates hyperalignment with general Procrustes analysis—these are related but distinct. Clarify whether the paper is describing hyperalignment specifically or Procrustes more broadly.

**Figure captions (e.g., Fig. 3, Fig. 4):** Several figure captions reference "adapted from" citations without specifying which portions were adapted. For reproducibility and accuracy, indicate which figure elements derive from which sources.

**Recommendation:** Minor revision to address citation precision and soften overly strong claims about methodological exclusivity.
