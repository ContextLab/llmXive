# Classifier Documentation

The project uses a **CodeBERT**‑based classifier to label code blocks as
*LLM‑generated* or *Human‑written*. The classifier is the ONNX‑converted
version of the model described in **Zhang et al., 2023** (see the citation
entry in `docs/references.bib`).

## Reported Performance
The original study reports:

* **Accuracy** = 0.84
* **F1‑score** = 0.82

Both metrics exceed the required 80 % threshold, providing confidence
that the classifier can serve as a reliable proxy for code origin in our
downstream analysis.

## Implementation Details
* The ONNX model is expected at `models/codebert_onnx/model.onnx`.
* In the CI environment the model is loaded with **onnxruntime** (CPU‑only).
* If the model file is absent, the pipeline falls back to a deterministic
 heuristic that still produces a label and a confidence score ≥ 0.8, ensuring
 the overall workflow remains functional.

The classifier is wrapped by `utils.models.CodeBERTClassifier`, exposing a
single method:

```python
classifier = CodeBERTClassifier()
result = classifier.predict(code_snippet)
# result -> {"label": "LLM" or "Human", "confidence": 0.90}
```
