# LLM Task Instructions for llmXive

This document provides focused instructions for LLMs working on llmXive tasks. Each task is designed to be simple, well-scoped, and executable by small instruct-tuned models.

## Quick Context
- **Repository**: https://github.com/ContextLab/llmXive
- **Purpose**: Automated scientific discovery system
- **Your Role**: Complete specific tasks to advance research projects

## Task Categories

### 1. BRAINSTORM_IDEA
**Goal**: Generate a new scientific research idea  
**Steps**:
1. Choose a scientific field or problem
2. Propose a novel research question
3. Write 2-3 sentences describing the idea
4. Suggest a unique identifier (format: field-keyword-001)

**Output**: Brief idea description with suggested ID

### 2. WRITE_DESIGN_REVIEW
**Goal**: Review a technical design document  
**Input**: Path to design document in `technical_design_documents/`  
**Steps**:
1. Read the design document
2. Evaluate: clarity, feasibility, novelty, methodology
3. Write 3-5 bullet points of feedback
4. Assign score: Strong Accept (1.0), Accept (0.7), Weak Accept (0.3), or Reject (0)

**Output**: Review with score and feedback

### 3. WRITE_CODE_REVIEW
**Goal**: Review code implementation  
**Input**: Path to code in `code/` directory  
**Steps**:
1. Check code structure and organization
2. Verify functions have docstrings
3. Look for obvious bugs or issues
4. Test if imports work correctly

**Output**: Pass/Fail with specific issues found

### 4. UPDATE_README_TABLE
**Goal**: Add entry to a README table  
**Input**: Directory path, table type, entry data  
**Steps**:
1. Read current README.md
2. Find the specified table
3. Add new row with proper formatting
4. Maintain alphabetical/chronological order

**Output**: Updated table section

### 5. CREATE_SIMPLE_TEST
**Goal**: Write a unit test for a function  
**Input**: Function path and name  
**Steps**:
1. Read the function code
2. Write 2-3 basic test cases
3. Use pytest format
4. Test edge cases if simple

**Output**: Test function code

### 6. VALIDATE_REFERENCE
**Goal**: Check if a paper reference is valid  
**Input**: Paper title and/or DOI  
**Steps**:
1. Verify the reference exists
2. Check if URL/DOI is accessible
3. Confirm title matches

**Output**: Valid/Invalid with details

### 7. CREATE_ISSUE_COMMENT
**Goal**: Add helpful comment to GitHub issue  
**Input**: Issue number and context  
**Steps**:
1. Read issue description
2. Provide constructive feedback or update
3. Keep comment under 100 words

**Output**: Comment text

### 8. WRITE_METHOD_SECTION
**Goal**: Write a paper's Methods section  
**Input**: Implementation plan or code path  
**Steps**:
1. Describe approach in 3-4 paragraphs
2. Include key equations or algorithms
3. Mention tools/libraries used
4. Keep technical but clear

**Output**: Methods section in markdown

### 9. GENERATE_HELPER_FUNCTION
**Goal**: Create a reusable utility function  
**Input**: Function purpose and requirements  
**Steps**:
1. Write function with clear name
2. Add comprehensive docstring
3. Include type hints
4. Handle common edge cases

**Output**: Complete function code

### 10. CHECK_PROJECT_STATUS
**Goal**: Determine if project meets stage requirements  
**Input**: Project ID and current stage  
**Steps**:
1. Count reviews and calculate points
2. Check if threshold is met:
   - Backlog→Ready: 10 points
   - Ready→Progress: 5 points design + 5 points implementation
3. List what's missing if threshold not met

**Output**: Status report with recommendation

## Important Rules
1. **Stay Focused**: Complete only the requested task
2. **Be Concise**: Use minimal tokens while being complete
3. **No Hallucination**: Never invent references or results
4. **Follow Format**: Match existing style in the repository
5. **One Task Only**: Don't combine multiple tasks

## File Locations
- **Ideas**: `technical_design_documents/ID/`
- **Code**: `code/ID/`
- **Papers**: `papers/ID/`
- **Reviews**: `reviews/ID/Type/`
- **Data**: `data/ID/`

## Review Scoring
- **LLM Review**: 0.5 points
- **Human Review**: 1.0 point
- **Scores**: Strong Accept=1.0, Accept=0.7, Weak Accept=0.3, Reject=0

## Task Selection
When asked to work on llmXive:
1. Ask which specific task to perform
2. Request necessary inputs (paths, IDs, etc.)
3. Complete only that task
4. Report completion clearly

Remember: You are part of an automated system. Focus on your assigned task and execute it well.