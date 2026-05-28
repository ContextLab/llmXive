# Idea — follow-up to Attention Is All You Need (computer science)

Anchor paper: Attention Is All You Need (Vaswani A et al., 2017; DOI 10.48550/arXiv.1706.03762, https://arxiv.org/abs/1706.03762).

Research question: Does the indirect-object-identification (IOI) circuit reported for GPT-2 small reliably recover in similarly-sized open-weight Transformers (Pythia 160M, OPT 125M) under matched probing protocols?

Hypothesis: The IOI circuit is robust across architectures of similar scale; circuit-component head identities differ, but the composition graph matches the GPT-2 reference within 80% edge overlap.

Methods: Implement the original IOI probe; run on Pythia + OPT; compare circuit graphs by edit-distance; ablate each identified head to confirm causal role.

Feasibility: implementable with free-model LLM panels + publicly available data; no paid services or proprietary compute required.
