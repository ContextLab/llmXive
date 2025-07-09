# llmXive Prompts Directory

This directory contains all prompt templates used by the llmXive research pipeline. Each prompt is stored as a separate Markdown file with variable placeholders and documentation.

## 🏗️ Prompt System Architecture

The prompt system is managed by the `PromptLoader` class in `scripts/llmxive-cli.py`, which:
- Loads templates from `.md` files in this directory
- Performs variable substitution using `{variable_name}` syntax
- Caches loaded prompts for performance
- Falls back to hardcoded prompts if files are missing

## 📋 Pipeline Stages and Prompts

### 1. **Idea Generation Stage**
- **File**: `idea_generation.md`
- **Used in**: `PipelineOrchestrator.brainstorm_idea()` (line ~355)
- **Purpose**: Generate novel research ideas in specified fields
- **Variables**: `{field}` - Research field (biology, chemistry, etc.)
- **Output**: Research idea with title, description, and keywords

### 2. **Technical Design Stage**
- **File**: `technical_design.md`  
- **Used in**: `PipelineOrchestrator.generate_technical_design()` (line ~444)
- **Purpose**: Create comprehensive technical design documents
- **Variables**: `{title}`, `{description}` - Project title and description
- **Output**: Detailed technical design with methodology, timeline, resources

### 3. **Implementation Planning Stage**
- **File**: `implementation_plan.md`
- **Used in**: `PipelineOrchestrator.generate_implementation_plan()` (line ~467)
- **Purpose**: Generate detailed implementation plans
- **Variables**: `{title}`, `{design_doc}` - Project title and technical design
- **Output**: Structured implementation plan with tasks, milestones, timelines

### 4. **Code Generation Stage**
- **File**: `code_generation.md`
- **Used in**: `PipelineOrchestrator.implement_code_and_data()` (line ~490)
- **Purpose**: Generate code structure and data collection procedures
- **Variables**: `{title}`, `{impl_plan}` - Project title and implementation plan
- **Output**: Python code structure, data collection procedures, testing workflows

### 5. **Data Analysis Stage**
- **File**: `data_analysis.md`
- **Used in**: `PipelineOrchestrator.run_analyses()` (line ~534)
- **Purpose**: Generate analysis results and interpretations
- **Variables**: `{code_content}`, `{data_summary}` - Generated code and data info
- **Output**: Statistical analysis results, key findings, visualizations

### 6. **Paper Writing Stage**
- **File**: `paper_writing.md`
- **Used in**: `PipelineOrchestrator.write_paper()` (line ~557)
- **Purpose**: Generate complete research papers in LaTeX format
- **Variables**: `{title}`, `{design_doc}`, `{impl_plan}`, `{code_content}`, `{analysis_results}`
- **Output**: Complete LaTeX research paper with proper structure

### 7. **LaTeX Fixing Stage**
- **File**: `latex_fixing.md`
- **Used in**: `PipelineOrchestrator.fix_latex_document()` (line ~703)
- **Purpose**: Fix malformed LaTeX documents
- **Variables**: `{latex_content}` - The broken LaTeX content
- **Output**: Corrected LaTeX document ready for compilation

## 🔍 Review System Prompts

### 8. **Generic Review**
- **File**: `review_generic.md`
- **Used in**: `ReviewManager.conduct_review()` (line ~278)
- **Purpose**: Conduct reviews for any type of content
- **Variables**: `{review_type}`, `{content}` - Type of review and content
- **Output**: Score (0.0-1.0), detailed feedback, recommendations

### 9. **Content Revision**
- **File**: `content_revision.md`
- **Used in**: `PipelineOrchestrator.iterative_review_process()` (line ~389)
- **Purpose**: Revise content based on review feedback
- **Variables**: `{review_type}`, `{score}`, `{current_content}`, `{feedback}`
- **Output**: Revised content addressing review concerns

## 📚 Legacy Review Prompts

These prompts were created earlier but are currently unused in the main pipeline:

### 10. **Design Review**
- **File**: `review_design.md`
- **Purpose**: Review technical design documents
- **Status**: Available but not actively used

### 11. **Implementation Review**
- **File**: `review_implementation.md`
- **Purpose**: Review implementation plans
- **Status**: Available but not actively used

### 12. **Paper Review**
- **File**: `review_paper.md`
- **Purpose**: Review research papers
- **Status**: Available but not actively used

## 🔧 Modifying Prompts

To modify a prompt:

1. **Edit the `.md` file** in this directory
2. **Maintain variable placeholders** using `{variable_name}` syntax
3. **Test the changes** by running the pipeline
4. **No code changes needed** - prompts are loaded dynamically

## 🚀 Adding New Prompts

To add a new prompt:

1. **Create a new `.md` file** in this directory
2. **Document variables** in the Variables section
3. **Update the code** to call `prompt_loader.load_prompt('new_prompt_name', **kwargs)`
4. **Add fallback** in `PromptLoader._get_fallback_prompt()` method
5. **Update this README** with the new prompt information

## 📖 Template Format

Each prompt file follows this structure:

```markdown
# Prompt Name

[Main prompt content with {variable} placeholders]

## Instructions
- Additional instructions
- Formatting requirements

## Variables
- {variable1}: Description of variable
- {variable2}: Description of variable

## Response Format Required
Expected output format
```

## 🔍 Debugging

To debug prompt issues:

1. **Check the cache**: PromptLoader caches prompts - restart if modified
2. **Verify variables**: Ensure all `{variables}` are provided in the code
3. **Check fallbacks**: If file is missing, fallback prompts are used
4. **Test manually**: Load prompts directly with `prompt_loader.load_prompt()`

## 📈 Performance Notes

- Prompts are cached after first load for performance
- File reads only happen once per prompt per session
- Variable substitution is performed on each call
- Fallback prompts are used if files are missing or corrupted

---

*This README is automatically maintained and should be updated whenever new prompts are added or the pipeline structure changes.*