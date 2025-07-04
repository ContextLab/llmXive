# LLM Instructions

This directory contains instructions for LLMs working on llmXive tasks.

## Files

- `task_instructions.md` - Main instruction set for small LLMs
- `task_examples.md` - Example inputs/outputs for each task type (coming soon)
- `prompt_templates.md` - Ready-to-use prompts for the automation system (coming soon)

## Usage

These instructions are designed for:
- Small instruct-tuned models (<5B parameters)
- Resource-constrained environments
- Focused, single-task execution
- Clear input/output specifications

## Integration

The automation system should:
1. Select a task type from `task_instructions.md`
2. Provide necessary inputs
3. Pass the relevant section to the LLM
4. Parse the structured output

## Design Principles

- **Simplicity**: Each task is atomic and well-defined
- **Clarity**: No ambiguous requirements
- **Efficiency**: Minimal token usage
- **Reliability**: Consistent output formats