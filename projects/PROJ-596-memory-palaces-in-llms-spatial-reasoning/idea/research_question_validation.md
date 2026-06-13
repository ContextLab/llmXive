## Research-question validation

### Phenomenon-vs-method check

**Verdict**: fail

No explicit research question is stated in the document—only a title and concept. The title suggests a phenomenon question (whether spatial reasoning mechanisms can improve episodic recall in LLMs), but without a clear research question, it's impossible to verify independence from implementation details. The fleshed-out idea should have a dedicated `## Research question` section with a precise, answerable question.

### Circularity check

**Verdict**: concern

Based on the title alone, the implied predictor would be "spatial embedding structure" and the predicted variable would be "episodic recall performance." These could be independent (spatial organization vs. task accuracy), but the document doesn't specify how either is measured. There's a risk that if spatial embeddings are constructed from the same episodic data used to evaluate recall, circularity could emerge. The flesh_out stage needs to explicitly separate data sources for predictor and outcome.

### Triviality check

**Verdict**: pass

Either outcome would be informative: confirming that spatial reasoning improves episodic recall would support bio-inspired memory architectures for LLMs; finding no benefit would suggest LLMs don't leverage such mechanisms or that the implementation is flawed. However, this assessment is tentative given the lack of a concrete research question.

### Question-narrowing check

**Verdict**: fail

The title names a domain concept (spatial reasoning for episodic recall) but does not articulate a testable relationship. A proper domain question would be phrased as "How does X affect Y under Z conditions?" rather than a project title. The current framing risks implementation narrowing if the flesh_out stage defaults to "can we build a memory-palace module" rather than "what mechanism enables episodic recall."

### Overall verdict

**Verdict**: validator_rejected

The document lacks an explicit, testable research question in the required format. The concept is novel and potentially valuable, but it cannot be validated without a clear question specifying the phenomenon, predictor, outcome, and scope. The project should return to `brainstormed` to develop a concrete research question before re-entering flesh_out.

[REVISED]
How does explicit spatial organization of episodic memories in transformer architectures affect recall accuracy on sequential memory benchmarks compared to non-spatial embedding strategies?
[/REVISED]

This reframing names the domain relationship (spatial organization → recall accuracy), specifies the comparison (vs. non-spatial strategies), and identifies the evaluation context (sequential memory benchmarks), making it testable and independent of specific implementation constraints.
