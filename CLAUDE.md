# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

llmXive is an automated system for scientific discovery driven by LLMs with occasional human input. It's structured as a project management platform with five main task categories, each linked to GitHub issues:

1. **Backlog**: Brainstormed ideas requiring development
2. **Ready**: Ideas with technical design documents reviewed by ≥10 LLMs or ≥5 human scientists
3. **In Progress**: Ideas with vetted implementation plans ready for execution
4. **Reviews**: Formal reviews of designs, implementations, papers, and code
5. **Done**: Completed projects with associated papers

## Repository Architecture

The repository is organized into six main directories:

- **`papers/`**: LaTeX documents, PDFs, and figures for research papers
- **`code/`**: Reusable code bases with Python toolboxes and project-specific implementations
- **`data/`**: Datasets organized by unique identifiers
- **`technical_design_documents/`**: Design documents for project ideas
- **`implementation_plans/`**: Detailed implementation plans for ready projects
- **`reviews/`**: Formal reviews organized by project and review type (Design/Implementation/Paper/Code)

Each directory contains a README.md with specific tables tracking projects, contributors, and status.

## Key Workflows

### Project Status Management
- Projects move through: Backlog → Ready → In Progress → Done
- Each stage requires specific point thresholds (LLM reviews = 0.5 points, human reviews = 1 point)
- Status is tracked via GitHub issue labels and project board columns

### Documentation Standards
- All papers must include: Abstract, Introduction, Methods, Results, Discussion, Bibliography
- All references must be validated by downloading and reviewing PDFs
- Contributors are listed chronologically by GitHub username with profile links
- Each project requires a unique identifier used consistently across all directories

### Code Organization
- Each code base has a `helpers/` folder with installable Python toolbox
- Project-specific folders contain Jupyter notebooks for reproducing figures/results
- Each project folder includes README with reproduction instructions
- Docker/venv build scripts required for environment setup

### Review Process
- Review files named as: `author__MM-DD-YYYY__type.md` (type: A=automatic, M=manual)
- Reviews organized in subdirectories: Design/Implementation/Paper/Code
- Minimum review thresholds must be met before status advancement

## Common Development Tasks

Since this is primarily a research documentation repository without traditional build tools, common tasks include:

- **Adding new projects**: Follow the unique ID convention and update relevant README tables
- **Moving projects between stages**: Update GitHub labels and project board columns
- **Creating reviews**: Use the standardized naming convention and directory structure
- **Validating references**: Download and verify all cited papers exist
- **Organizing contributions**: Maintain chronological contributor lists with GitHub links

## Working with the Repository

- Always use absolute paths when referencing files across directories
- Maintain the table structures in README files when adding new entries
- Verify all external links and references before committing
- Follow the point-based review system for project advancement
- Use GitHub issues for all project tracking and communication