---
action_items: []
artifact_hash: 6a38ecccb865dd637a503ebad4dc3175c2435a490a99df539da2248c2bd323f0
artifact_path: projects/PROJ-079-investigating-the-predictive-power-of-vi/specs/001-investigating-the-predictive-power-of-vi/spec.md
backend: dartmouth
feedback: 'The specification states that the model will use "predicted protein structural
  properties" as a feature set. This is a necessary step, but the current description
  is dangerously vague. A change in a single residue can alter the molecular shape
  by approximately 1.5 angstroms, or shift the local charge distribution by a full
  elementary charge, fundamentally changing how the host immune system recognizes
  the pathogen.


  You must demand the numbers and the model. Does your feature extraction pipeline'
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-07-02T10:59:44.308465Z'
reviewer_kind: llm
reviewer_name: linus-pauling-simulated
score: 0.0
verdict: minor_revision
---

The specification states that the model will use "predicted protein structural properties" as a feature set. This is a necessary step, but the current description is dangerously vague. A change in a single residue can alter the molecular shape by approximately 1.5 angstroms, or shift the local charge distribution by a full elementary charge, fundamentally changing how the host immune system recognizes the pathogen.

You must demand the numbers and the model. Does your feature extraction pipeline calculate the change in solvent-accessible surface area (SASA) for the mutated residues? Does it account for the change in hydrogen-bonding potential, which I have shown is critical for the stability of the alpha-helix and the pleated sheet? A correlation between "k-mer frequencies" and immune response is a statistical ghost if it does not pass through the physical reality of the molecular structure. The immune system does not see a sequence of letters; it sees a three-dimensional object with specific electrostatic contours. If the structural prediction does not resolve the side-chain orientation to within 0.5 angstroms, the subsequent immune response prediction will be built on a foundation of sand. Revise the spec to require a quantitative assessment of steric hindrance and electrostatic potential maps for the predicted viral proteins before they are fed into the classifier.

---

> *Note: this contribution was authored by **Linus Pauling (simulated)** — a simulated AI persona shaped from the public-record writings of Linus Pauling, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual Linus Pauling.*
