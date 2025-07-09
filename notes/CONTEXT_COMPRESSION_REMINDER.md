# CONTEXT COMPRESSION REMINDER

**If you see this note, context has been compressed.**

## 🚨 CURRENT STATUS (2025-07-09)

### ✅ COMPLETED:
- Repository reorganization with projects/ structure
- Database updates and migration scripts
- CLI pipeline fixes for incremental file saving
- **FULL E2E TEST SUCCESSFUL** - Generated 2 complete papers
- Critical requirement fulfilled: actual paper generation working

### ⚠️ CRITICAL ISSUES DISCOVERED:
1. **PDF compilation fails** - CLI generates Markdown instead of LaTeX
2. **Poor prompts** - Hardcoded, produce low quality outputs  
3. **Incomplete migration** - Old projects still in root directories
4. **Inconsistent naming** - Mix of PROJ-XXX, dates, descriptive names

### 📋 URGENT TASKS:
**See detailed plan in**: `/Users/jmanning/llmXive/notes/CRITICAL_FIXES_PLAN_2025-07-09.md`

**PRIORITY ORDER:**
1. Fix PDF compilation (LaTeX format + auto-fix)
2. Create prompts/ directory system
3. Complete project migration  
4. Standardize project naming (PROJ-###-name)

### 🎯 IMMEDIATE NEXT STEPS:
1. Fix `write_paper()` method to generate proper LaTeX
2. Add LaTeX validation/auto-fix using LLM
3. Create `prompts/` directory structure
4. Extract all prompts from CLI script

### 📁 KEY FILES:
- `scripts/llmxive-cli.py` - Main CLI (needs prompt fixes)
- `web/database/projects.json` - Project database
- `projects/` - New unified structure (partially complete)
- OLD: `papers/`, `technical_design_documents/`, etc. (needs migration)

**REMEMBER**: System generates papers but PDFs fail due to Markdown→LaTeX issue. Fix this first!