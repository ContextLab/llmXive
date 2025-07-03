# Archive of Reviews

This folder contains a repository of formal reviews. Each project is associated with a single folder (under this one), named using the project's unique identifier. Each formal review comprises a markdown file in one of three sub-folders (under the project's directory):
  - *Design*: reviews of the project's technical design document(s)
  - *Implementation*: reviews of the project's implementation plan(s)
  - *Paper*: reviews of the formal manuscript(s)
  - *Code*: reviews of associated code

Reviews are named as follows: `A__B-C-D__E.md`, where:
  - `A` is the author name of the reviewer. This should be the lowercase GitHub username of the LLM (e.g., `claude`) or human (e.g., `jeremymanning`) who wrote the *initial* review. If no GitHub profile is available, use the lowercase model name (e.g., `claude-sonnet-4`) or human name (e.g., `jeremy-r-manning`) instead, with spaces replaced by "-".
  - `B` is the current month, expressed as 2 digits (e.g., `01` for January, `03` for March, etc.)
  - `C` is the current day of the month, expressed as 2 digits (e.g., `05` for the 5th day of the month, `28` for the 28th day of the month)
  - `D` is the current year, expressed as 4 digits (e.g., `2025`)
  - `E` is the type of entity who wrote the original review. This can either be `A` for an "automatic" (e.g., LLM-generated) or `M` for "manual" (e.g., human-generated). No other values are accepted.

# Table of Contents

Contributors list should be chronological in a comma-separated list, and individuals should be listed by GitHub username with a markdown link to their GitHub profile (e.g., `[jeremymanning](https://github.com/jeremymanning)`). The "Link to Resources Being Reviewed" column should be filled in using a markdown link to the source document (e.g., `[Design](<link to doc>)`). Link text must be one of: "Design", "Implementation", "Paper", or "Code".

| Unique Project ID | Project Name | Unique Review ID | Link(s) to GitHub issues | Link to Resource Being Reviewed | Link to Review | Contributing Author(s) |
|-------------------|--------------|------------------|--------------------------|---------------------------------|----------------|------------------------|
