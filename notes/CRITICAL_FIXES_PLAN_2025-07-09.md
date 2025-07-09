# CRITICAL FIXES PLAN - llmXive Production Issues

**Date**: 2025-07-09  
**Status**: ⚠️ URGENT - Multiple production issues identified  
**Priority**: HIGH - Must fix before system is truly production ready

## 🚨 CRITICAL ISSUES IDENTIFIED

### 1. **PDF Compilation Failure** 
- **Problem**: CLI generates Markdown instead of LaTeX, causing compilation failure
- **Root Cause**: write_paper prompt produces `**bold**` instead of `\textbf{bold}`
- **Impact**: No actual PDFs generated, only .tex files that won't compile

### 2. **Poor Quality Prompts**
- **Problem**: Hardcoded prompts in CLI script produce low-quality outputs
- **Root Cause**: Prompts scattered throughout code, hard to modify/improve
- **Impact**: Subpar research quality, inconsistent outputs

### 3. **Inconsistent Project Organization**
- **Problem**: Old projects still in root folders (papers/, technical_design_documents/, etc.)
- **Root Cause**: Migration incomplete, mixed old/new structure
- **Impact**: Confusion, broken references, incomplete database

### 4. **Inconsistent Project Naming**
- **Problem**: Mix of naming schemes (PROJ-XXX, dates, descriptive names)
- **Root Cause**: No enforced naming convention
- **Impact**: Database inconsistency, hard to manage projects

## 📋 DETAILED IMPLEMENTATION PLAN

### **PHASE 1: PDF Compilation Fix**

#### 1.1 Install/Verify LaTeX
- Check if pdflatex available: `which pdflatex`
- If not available: Install TeX Live or MacTeX
- Verify compilation works with test document

#### 1.2 Fix LaTeX Generation
- **File**: `scripts/llmxive-cli.py`
- **Method**: `write_paper()` around line 542
- **Fix**: Modify prompt to explicitly request LaTeX format
- **Add**: LaTeX validation function to check document structure
- **Add**: Auto-fix function using available LLM if LaTeX malformed

#### 1.3 Improve compile_latex_paper Method
- **File**: `scripts/llmxive-cli.py`
- **Method**: `compile_latex_paper()` around line 678
- **Fix**: Add LaTeX validation before compilation
- **Add**: Auto-fix malformed LaTeX using LLM
- **Add**: Better error handling and retry logic

### **PHASE 2: Prompt System Refactor**

#### 2.1 Create Prompts Directory Structure
```
prompts/
├── idea_generation.md
├── technical_design.md
├── implementation_plan.md
├── code_generation.md
├── data_analysis.md
├── paper_writing.md
├── review_idea.md
├── review_technical_design.md
├── review_implementation_plan.md
├── review_paper.md
└── latex_fixing.md
```

#### 2.2 Extract All Prompts from CLI
- **File**: `scripts/llmxive-cli.py`
- **Extract from methods**:
  - `brainstorm_idea()` - line ~270
  - `generate_technical_design()` - line ~366
  - `generate_implementation_plan()` - line ~407
  - `implement_code_and_data()` - line ~449
  - `run_analyses()` - line ~506
  - `write_paper()` - line ~542
  - `review_document()` - line ~170

#### 2.3 Create Prompt Loading System
- **New function**: `load_prompt(prompt_name, **kwargs)`
- **Template system**: Support variable substitution
- **Error handling**: Fallback to hardcoded if file missing

### **PHASE 3: Complete Project Migration**

#### 3.1 Audit Existing Projects
- **Scan directories**: papers/, technical_design_documents/, implementation_plans/, reviews/, code/, data/
- **Identify projects**: Group related files by project
- **Check database**: Compare with web/database/projects.json
- **Create mapping**: Old location → New project structure

#### 3.2 Create Migration Script v2
- **File**: `scripts/migrate-remaining-projects.js`
- **Features**:
  - Scan all root directories for projects
  - Group related files by project name/topic
  - Create new project IDs following naming convention
  - Move files to proper project structure
  - Update database with new projects

#### 3.3 Project Identification Strategy
- **papers/X/** → `projects/PROJ-###-X/paper/`
- **technical_design_documents/X/** → `projects/PROJ-###-X/technical-design/`
- **implementation_plans/X/** → `projects/PROJ-###-X/implementation-plan/`
- **reviews/X/** → `projects/PROJ-###-X/reviews/`
- **code/X/** → `projects/PROJ-###-X/code/`
- **data/X/** → `projects/PROJ-###-X/data/`

### **PHASE 4: Project Naming Standardization**

#### 4.1 Define Naming Convention
- **Format**: `PROJ-###-descriptive-name`
- **Number**: 3-digit sequential (001, 002, 003...)
- **Name**: Lowercase, hyphens, descriptive
- **Examples**: 
  - `PROJ-001-gene-regulation`
  - `PROJ-002-battery-prediction`
  - `PROJ-003-neural-networks`

#### 4.2 Rename Existing Projects
- **Current inconsistent names**:
  - `PROJ-20250704-biology-20250704-001` → `PROJ-001-gene-regulation`
  - `pipeline-test-20250709-96e797a7` → `PROJ-002-theorem-generation`
  - `TEST-E2E-complete` → `PROJ-003-math-formulation`

#### 4.3 Update Database References
- **File**: `web/database/projects.json`
- **Update**: All project IDs to new naming convention
- **Update**: All location paths to match new names
- **Validate**: No broken references

#### 4.4 Enforce in CLI
- **File**: `scripts/llmxive-cli.py`
- **Method**: `brainstorm_idea()` or new `generate_project_id()`
- **Add**: Auto-generate compliant project IDs
- **Add**: Validation to reject non-compliant names

## 🔧 IMPLEMENTATION ORDER

### **Week 1: Critical Fixes**
1. **Day 1**: Fix PDF compilation (Phase 1)
2. **Day 2**: Create prompts directory and extract prompts (Phase 2.1-2.2)
3. **Day 3**: Implement prompt loading system (Phase 2.3)

### **Week 2: Project Organization**
1. **Day 4**: Audit existing projects (Phase 3.1)
2. **Day 5**: Create migration script v2 (Phase 3.2)
3. **Day 6**: Execute migration (Phase 3.3)

### **Week 3: Naming Standardization**
1. **Day 7**: Define and implement naming convention (Phase 4.1-4.2)
2. **Day 8**: Update database and CLI enforcement (Phase 4.3-4.4)
3. **Day 9**: Final validation and testing

## 📝 FILES TO MODIFY

### **Primary Files**
- `scripts/llmxive-cli.py` - Main CLI script
- `web/database/projects.json` - Project database
- `scripts/migrate-remaining-projects.js` - New migration script
- `scripts/update-database.js` - Database sync script

### **New Files to Create**
- `prompts/*.md` - All prompt templates
- `scripts/validate-project-names.js` - Naming validation
- `scripts/fix-latex.js` - LaTeX fixing utility

## 🎯 SUCCESS CRITERIA

### **PDF Compilation**
- [ ] All generated .tex files compile to PDF without errors
- [ ] Auto-fix malformed LaTeX using LLM
- [ ] Proper LaTeX structure with \documentclass, \begin{document}, etc.

### **Prompt System**
- [ ] All prompts in separate markdown files
- [ ] Easy to modify and improve prompts
- [ ] Template system for variable substitution

### **Project Organization**
- [ ] All projects in unified projects/ structure
- [ ] No orphaned files in root directories
- [ ] Database reflects all projects accurately

### **Naming Convention**
- [ ] All projects follow PROJ-###-name format
- [ ] CLI enforces naming convention
- [ ] Database updated with consistent names

## ⚠️ CRITICAL REMINDERS

1. **Before starting**: Backup entire repository
2. **Test thoroughly**: Each phase before moving to next
3. **Update documentation**: Keep notes of all changes
4. **Validate database**: After every migration step
5. **Test E2E**: Full pipeline after all fixes

---

*This plan must be executed to achieve true production readiness*  
*Created 2025-07-09 - Context may compress, refer back to this plan*