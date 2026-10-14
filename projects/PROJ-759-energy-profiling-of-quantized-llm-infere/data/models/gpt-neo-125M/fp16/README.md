---
language:
- en
tags:
- text generation
- pytorch
- causal-lm
license: mit
datasets:
- EleutherAI/pile
---

# GPT-Neo 125M

## Model Description

GPT-Neo 125M is a transformer model designed using EleutherAI's replication of the GPT-3 architecture. GPT-Neo refers to the class of models, while 125M represents the number of parameters of this particular pre-trained model.

## Training data

GPT-Neo 125M was trained on the Pile, a large scale curated dataset created by EleutherAI for the purpose of training this model.

## Training procedure

This model was trained on the Pile for 300 billion tokens over 572,300 steps. It was trained as a masked autoregressive language model, using cross-entropy loss.

## Intended Use and Limitations

This way, the model learns an inner representation of the English language that can then be used to extract features useful for downstream tasks. The model is best at what it was pretrained for however, which is generating texts from a prompt.

### How to use

You can use this model directly with a pipeline for text generation. This example generates a different sequence each time it's run:

```py
>>> from transformers import pipeline
>>> generator = pipeline('text-generation', model='EleutherAI/gpt-neo-125M')
>>> generator("EleutherAI has", do_sample=True, min_length=20)

[{'generated_text': 'EleutherAI has made a commitment to create new software packages for each of its major clients and has'}]
```

### Limitations and Biases

GPT-Neo was trained as an autoregressive language model. This means that its core functionality is taking a string of text and predicting the next token. While language models are widely used for tasks other than this, there are a lot of unknowns with this work.

GPT-Neo was trained on the Pile, a dataset known to contain profanity, lewd, and otherwise abrasive language. Depending on your usecase GPT-Neo may produce socially unacceptable text. See Sections 5 and 6 of the Pile paper for a more detailed analysis of the biases in the Pile.

As with all language models, it is hard to predict in advance how GPT-Neo will respond to particular prompts and offensive content may occur without warning. We recommend having a human curate or filter the outputs before releasing them, both to censor undesirable content and to improve the quality of the results. 

## Eval results

TBD

### Down-Stream Applications

TBD

### BibTeX entry and citation info

To cite this model, use
```bibtex

@software{gpt-neo,

  author       = {Black, Sid and
                  Leo, Gao and
                  Wang, Phil and
                  Leahy, Connor and
                  Biderman, Stella},
  title        = {{GPT-Neo: Large Scale Autoregressive Language 
                   Modeling with Mesh-Tensorflow}},
  month        = mar,
  year         = 2021,
  note         = {{If you use this software, please cite it using 
                   these metadata.}},
  publisher    = {Zenodo},
  version      = {1.0},
  doi          = {10.5281/zenodo.5297715},
  url          = {https://doi.org/10.5281/zenodo.5297715}
}

@article{gao2020pile,
  title={The Pile: An 800GB Dataset of Diverse Text for Language Modeling},
  author={Gao, Leo and Biderman, Stella and Black, Sid and Golding, Laurence and Hoppe, Travis and Foster, Charles and Phang, Jason and He, Horace and Thite, Anish and Nabeshima, Noa and others},
  journal={arXiv preprint arXiv:2101.00027},
  year={2020}
}

```
# [Open LLM Leaderboard Evaluation Results](https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard)
Detailed results can be found [here](https://huggingface.co/datasets/open-llm-leaderboard/details_EleutherAI__gpt-neo-125m)

| Metric                | Value                     |
|-----------------------|---------------------------|
| Avg.                  | 25.79   |
| ARC (25-shot)         | 22.95          |
| HellaSwag (10-shot)   | 30.26    |
| MMLU (5-shot)         | 25.97         |
| TruthfulQA (0-shot)   | 45.58   |
| Winogrande (5-shot)   | 51.78   |
| GSM8K (5-shot)        | 0.3        |
| DROP (3-shot)         | 3.69         |
