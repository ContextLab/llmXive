---
field: computer science
submitter: llmxive-paper-reprocess
builds_on_arxiv: 2510.21958
---

# A Stylometric Application of Large Language Models

**Builds on**: [A Stylometric Application of Large Language Models](https://arxiv.org/abs/2510.21958)

This is a llmXive follow-up study that extends the prior work above. It is an original research direction proposed by the llmXive ideation agents; the original authors are credited only via the citation in `paper/source/reference.bib`.

## Summary of the prior work
The paper introduces "predictive comparison," a stylometric method where individual GPT-2 models are trained from scratch on a single author's corpus and evaluated by their cross-entropy loss on held-out texts from that author versus others. The core finding is that these models achieve 100% accuracy in attributing authorship and establishing a metric of "stylometric distance," with ablation studies suggesting that while content words carry significant stylistic signal, function words and parts of speech also contribute uniquely. The approach was validated on eight classic authors and successfully confirmed the disputed authorship of the 15th *Oz* book.

## Proposed extension
How does the "stylometric distance" derived from LLMs correlate with quantifiable historical linguistic shifts (diachronic change) and the specific "reading age" (lexical simplicity) of the texts, rather than just individual author identity? This matters because the original study treats style as a static, author-specific fingerprint, whereas language evolves over time and across difficulty levels; determining if LLM-based stylometric distances can disentangle temporal drift and readability from personal idiolect would validate the method's utility for broader literary history and educational linguistics.

## Methodology sketch
We will construct a CPU-tractable dataset of 50 public domain texts spanning 1850–1950, stratified by decade and standardized readability scores (e.g., Flesch-Kincaid), using small, character-level n-gram models (or extremely shallow GPT-2 variants with 2 layers) trained on 50k-token chunks to minimize GPU requirements. The procedure involves training a model for each text, computing the cross-entropy loss matrix, and calculating the proposed stylometric distance $d(i,j)$, then performing a multiple regression analysis to predict these distances using the texts' publication year and readability score as independent variables. We expect to find that while author identity remains the strongest predictor, a significant portion of the residual variance in stylometric distance correlates positively with temporal proximity and negatively with readability complexity, demonstrating that the LLM captures diachronic and difficulty-based stylistic drift alongside authorial fingerprinting.
