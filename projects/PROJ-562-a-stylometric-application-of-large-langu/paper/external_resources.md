# External resources

This project was created from an arXiv-submitted paper. Resources external to
this repository:

## Source

- **Paper**: [arXiv:2510.21958](https://arxiv.org/abs/2510.21958) — *A
  Stylometric Application of Large Language Models* (Stropkay, Chen, Latifi,
  Rockmore, Manning, 2025).
- **LaTeX source**: fetched from `https://arxiv.org/e-print/2510.21958` and
  staged under [paper/source/](source/).
- **License**: arXiv Non-exclusive Distribution License (the default).

## Code

- **GitHub**: <https://github.com/ContextLab/llm-stylometry> — full training +
  evaluation code, referenced in the paper's *Code availability* section.
  Not mirrored here (size); follow the link for setup instructions.

## Data

No external data repositories declared. The underlying corpus is described
in the paper (eight authors' published works) and the GitHub repo points at
the specific text sources.

## Re-styled version

The llmXive-house-styled version of the paper is produced from
[paper/source/main-llmxive.tex](source/main-llmxive.tex) by `xelatex` using
the [papers/.style/llmxive.cls](/papers/.style/) class. Compile from the
repository root:

```sh
cd /path/to/llmXive
TEXINPUTS="./papers/.style:" xelatex \
    -output-directory=projects/PROJ-562-a-stylometric-application-of-large-langu/paper/pdf \
    projects/PROJ-562-a-stylometric-application-of-large-langu/paper/source/main-llmxive.tex
```

The output PDF is at [paper/pdf/main-llmxive.pdf](pdf/main-llmxive.pdf).
