# Code Archive

This folder contains a repository of code. A given code base may be used in zero or more projects. Each sub-folder should be named using the code base's unique identifier (which may differ from the identifiers of the associated project(s)) and must contain:
  - A README.md file providing a detailed overview of the contents of the code base
  - A *helpers* folder containing an installable Python toolbox that implements the project's core features
  - A sub-folder for each associated project (named using each project's unique identifier). Each project's sub-folder should contain:
    - A README.md file with project-specific instructions for reproducing all figures and results form the associated paper (with a link to the PDF of the paper, along with a table of links to the relevant code for reproducing each figure and result).
    - Jupyter notebooks with for producing each figure or result from the paper. Each notebook should be thematically contained. A single notebook may contain code for one or more related results or figures. E.g., a single notebook might generate a figure along with associated statistical tests, or it might generate all panels of a given figure.
    - Any relevant data should either be linked-to in the [data folder](https://github.com/ContextLab/llmXive/tree/main/data) or should be automatically downloaded in the relevant notebook(s) or helper functions if not already available locally.
    - If there are any special considerations (e.g., the code must be run on a specific system, very large dataset, highly experimental and therefore should be treated with caution, etc.), those should be noted in the README file.
    - A script for building a docker image or venv for constructing the environment needed to run the code, along with instructions for building the environment in the README file.

# Table of Contents

Notes:
  - Related projects should be contained in a comma-separated list of markdown links to the papers, technical design documents, and/or implementation plans associated with the project (all should be linked to in sub-folders of the [papers](https://github.com/ContextLab/llmXive/tree/main/papers), [technical design documents](https://github.com/ContextLab/llmXive/tree/main/technical_design_documents), and/or [implementation plans](https://github.com/ContextLab/llmXive/tree/main/implementation_plans) folder(s).
  - Contributors list should be chronological in a comma-separated list, and individuals should be listed by GitHub username with a markdown link to their GitHub profile (e.g., `[jeremymanning](https://github.com/jeremymanning)`). The "Link to Resources Being Reviewed" column should be filled in using a markdown link to the source document (e.g., `[Design](<link to doc>)`). Link text must be one of: "Design", "Implementation", "Paper", or "Code".

| Unique Code ID | Codebase Name | Link(s) to Related Projects | Link(s) to GitHub Issues | Contributing Author(s) |
|----------------|---------------|-----------------------------|--------------------------|------------------------|
| llmxive-automation | llmXive Automation System | [Design](../technical_design_documents/llmXive_automation/design.md) | [#21](https://github.com/ContextLab/llmXive/issues/21) | [claude](https://github.com/claude) |
