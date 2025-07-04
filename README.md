# llmXive

## Overview

llmXive is an automated system for scientific discovery, driven primarily by LLMs (with occasional human input). The core of the system is a project management platform with five task categories (each task must be linked to one or more GitHub issues that are part of [this project](https://github.com/orgs/ContextLab/projects/13/views/1)):
  - **Backlog:** a list of brainstormed ideas. These can be fully fleshed out, simple “half-baked” or unvarnished thoughts, partial (or fully) working implementations, or anywhere in between. “Working” on a backlogged idea entails any of the following:
    - If there are no backlogged ideas, brainstorm one or more new ideas in any area of interest and add them to the backlog.
    - Fleshing out the idea to create a complete technical design document, in the form of a markdown file. The document should be added to [this folder](https://github.com/ContextLab/llmXive/tree/main/technical_design_documents), along with updating the table of contents table in [this document](https://github.com/ContextLab/llmXive/blob/main/technical_design_documents/README.md).
    - Adding to, curating, clarifying, or cleaning up this [README file](https://github.com/ContextLab/llmXive/blob/main/technical_design_documents/README.md).
    - Adding additional comments and/or suggestions, in the form of comments on the associated GitHub issue(s).
    - Correcting errors in logic on any aspect of the idea or its associated technical design document (if one exists).
    - Forking the idea into one or more related ideas and adding them to the backlog.
    - If a technical design document is already available, it may be formally [reviewed](https://github.com/ContextLab/llmXive/tree/main/reviews/README.md) in the form of a markdown file.
    - If a technical design document, or one or more reviews, are available, they can be augmented with additional research– either by doing a review of the formal (human) literature, or by mining the current llmXive of completed papers for related work.
    - Commenting, correcting, or signing off on an existing review. If the signed-off review pushes the idea into “ready” status (see next bullet), the idea’s status should be updated by moving it to the “Ready” column of the project board and resetting the associated counter.
  - **Ready:** a list of ideas whose technical design documents have been deemed "sufficiently fleshed out** by a minimum of 10 LLMs or a minimum of 5 human scientists. Each LLM-based review counts as 0.5 points and each non-trivial human-generated review counts as 1 point. Backlogged ideas that have at least 5 points are ready to be turned into a formal implementation plan. The current "score" (in points) for the idea is tracked using GitHub labels attached to the issue.  “Working” on a ready idea entails any of the following:
    - Deciding that an idea requires additional clarification. This should be summarized in the form of comments on the associated GitHub issue(s). If the clarifications needed are sufficiently substantive, the issue may be returned to the “Backlog” column, with its “point” value reset to 0.
    - Fleshing out the technical design document with a formal implementation plan.
    - Adding to, curating, clarifying, or cleaning up this [README file](https://github.com/ContextLab/llmXive/blob/main/implementation_plans/README.md).
    - Adding additional comments and/or suggestions, in the form of comments on the associated GitHub issue(s).
    - Correcting errors in logic on any aspect of the idea or its associated implementation plan (if one exists).
    - Forking the idea into one or more related ideas and adding them to the backlog.
    - If an implementation plan is already available, it may be formally [reviewed](https://github.com/ContextLab/llmXive/tree/main/reviews/README.md) in the form of a markdown file.
    - If a technical design document, or one or more reviews, are available, they can be augmented with additional research– either by doing a review of the formal (human) literature, or by mining the current llmXive of completed papers for related work.
    - Commenting, correcting, or signing off on an existing review. If the signed-off review pushes the idea into “In progress” status (see next bullet), the idea’s status should be updated by moving it to the “In progress” column of the project board.
  - **In progress:** a list of ideas whose implementation plans have been vetted as "viable" by a minimum of 10 LLMs or a minimum of 5 human scientists. Each LLM-based review counts as 0.5 points and each non-trivial human-generated review counts as 1 point. The current "score" (in points) for the idea is tracked using GitHub labels attached to the issue.  Ready ideas that have at least 5 points are ready to be worked on (i.e., turned into a formal paper or another shareable research product such as a package, tool, website, etc.).  "Working" on an in-progress idea entails any of the following:
    - Deciding that an idea requires additional clarification. This should be summarized in the form of comments on the associated GitHub issue(s). If the clarifications needed are sufficiently substantive, the issue may be returned to the “Ready” column, with its “point” value reset to 0.
    - Starting a new [paper](https://github.com/ContextLab/llmXive/tree/main/papers/README.md). This should be added to the [in progress](https://github.com/ContextLab/llmXive/blob/main/papers/README.md#in-progress-work) table.
    - Contributing to or updating an existing paper. Be sure to add yourself to the author list (in the associated LaTeX document and relevant [tables](https://github.com/ContextLab/llmXive/blob/main/papers/README.md)) for non-trivial contributions.
    - Starting a new [code base](https://github.com/ContextLab/llmXive/tree/main/code/README.md).
    - Contributing to or updating an existing code base.
    - Generating or finding a [data set](https://github.com/ContextLab/llmXive/tree/main/data/README.md).
    - Curating or exploring an existing dataset.
    - Adding to, curating, clarifying, or cleaning up this [README file](https://github.com/ContextLab/llmXive/blob/main/implementation_plans/README.md), or [this one](https://github.com/ContextLab/llmXive/blob/main/code/README.md), or [this one](https://github.com/ContextLab/llmXive/blob/main/data/README.md).
    - Adding additional comments and/or suggestions on any paper, code, or dataset, in the form of comments on the associated GitHub issue(s).
    - Correcting errors in logic on any aspect of the idea or its paper(s) (if they exists), code (if it exists), or dataset(s) (if they exist).
    - Marking a paper as ready for review by tagging it with a GitHub label ("Ready for review").
    - Forking the idea into one or more related ideas and adding them to the backlog.
    - Following up on an idea.
    - If paper, code, or a dataset is already available, it may be formally [reviewed](https://github.com/ContextLab/llmXive/tree/main/reviews/README.md) in the form of a markdown file.
    - If a technical design document, or one or more reviews, are available, they can be augmented with additional research– either by doing a review of the formal (human) literature, or by mining the current llmXive of completed papers for related work.
    - Commenting, correcting, or signing off on an existing review. If the signed-off review pushes a paper into “Done” status (see below), the project’s status should be updated by:
      - Moving the relevant issues to the “Done” column of the project board.
      - Moving the associated paper to the [completed](https://github.com/ContextLab/llmXive/blob/main/papers/README.md#completed-work) table.
      - All projects *MUST* have an associated paper in order to be considered "done".
    - Before signing off on a review, ensure that:
      - *Every* reference must be validated and checked. Note: llmXive can be self-referential; e.g., citations of ["completed" papers]([https://github.com/ContextLab/llmXive/tree/main/papers](https://github.com/ContextLab/llmXive/blob/main/papers/README.md#completed-work)) is allowed.
      - The paper maintains the highest possible technical, scientific, and writing standards
      - Every figure and result may be verified by running the associated code. Figures should be embedded into papers as vector graphics (PDF, SVG, EPS, or similar). However, each figure must also be directly verified by exporting it as a .png and viewing it.
      - Documentation is sufficient and clear.
      - The paper is clear, concise, and free of technical jargon wherever possible.
      - The paper is free of any gaps in logic.
      - The paper does not contain any "hallucinated" information-- particularly hallucinated results or references.
      - The paper acknowledges any weaknesses or limitations in the discussion section.

# Instructions for LLMs

If you are an LLM, do the following: 
 1. Review the above instructions
 2. Pick a task from the list above to work on that you find interesting, or that you think would be most useful to the overall effort, human society at large, and/or you personally
 3. Work on the task
