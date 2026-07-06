# Research Limitations and Scope

## Level of Explanation
This study anchors its findings at the **systems/network level** of explanation.
We investigate the correlation between resting-state functional connectivity topology
and susceptibility to visual illusions. While compelling, these findings do not
establish a causal mechanism at the synaptic or molecular level (e.g., involving
CREB/BDNF pathways or synaptic plasticity).

Future research is required to bridge the gap between network topology and
cellular mechanisms. As noted in the literature, cognitive claims must eventually
be traced back to synaptic change to be considered mechanistic. This project
explicitly limits its scope to the associational level to maintain rigor within
the available data constraints.

## Stimulus "Texture"
The analysis utilizes visual illusion stimuli (Müller-Lyer and Ponzo) from the
OpenNeuro ds004285 dataset. The specific "texture" of these illusions refers to
the geometric parameters of the stimuli (e.g., line lengths, arrow angles,
background patterns).

Current analysis measures the *frequency and magnitude of the perceptual error*
induced by these stimuli. It does not analyze the topological shape of the
stimulus geometry itself.

**Future Direction**: Applying Topological Data Analysis (TDA) to the stimulus
geometry could provide insights into how the brain processes the topological
features of the visual field, potentially linking stimulus shape to network
response.

## Data Constraints
- Reliance on existing OpenNeuro data limits control over experimental conditions.
- Motion artifacts (FD > 0.5mm) are excluded, potentially reducing sample size. [UNRESOLVED-CLAIM: c_4736d450 — status=not_enough_info]
- Correlation does not imply causation; findings are strictly associational.