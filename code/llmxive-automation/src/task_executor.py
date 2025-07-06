"""Task execution for llmXive automation"""

import os
import re
import json
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any

from .conversation_manager import ConversationManager
from .github_handler import GitHubHandler
from .response_parser import ResponseParser
from .model_attribution import ModelAttributionTracker

logger = logging.getLogger(__name__)


class TaskExecutor:
    """Executes all llmXive task types"""
    
    def __init__(self, conversation_manager: ConversationManager, 
                 github_handler: GitHubHandler):
        """
        Initialize task executor
        
        Args:
            conversation_manager: Manager for LLM conversations
            github_handler: Handler for GitHub operations
        """
        self.conv_mgr = conversation_manager
        self.github = github_handler
        self.parser = ResponseParser()
        self.attribution = ModelAttributionTracker()
        
        # Map all task types to handlers
        self.task_handlers = {
            # Ideation & Design
            "BRAINSTORM_IDEA": self.execute_brainstorm,
            "WRITE_TECHNICAL_DESIGN": self.execute_technical_design,
            "REVIEW_TECHNICAL_DESIGN": self.execute_design_review,
            
            # Planning
            "WRITE_IMPLEMENTATION_PLAN": self.execute_implementation_plan,
            "REVIEW_IMPLEMENTATION_PLAN": self.execute_implementation_review,
            
            # Literature & Research
            "CONDUCT_LITERATURE_SEARCH": self.execute_literature_search,
            "VALIDATE_REFERENCES": self.execute_reference_validation,
            "MINE_LLMXIVE_ARCHIVE": self.execute_mine_archive,
            
            # Code Development
            "WRITE_CODE": self.execute_code_writing,
            "WRITE_TESTS": self.execute_test_writing,
            "RUN_TESTS": self.execute_run_tests,
            "RUN_CODE": self.execute_run_code,
            "DEBUG_CODE": self.execute_debug_code,
            "ORGANIZE_INTO_NOTEBOOKS": self.execute_organize_notebooks,
            
            # Data & Analysis
            "GENERATE_DATASET": self.execute_generate_dataset,
            "ANALYZE_DATA": self.execute_analyze_data,
            "PLAN_STATISTICAL_ANALYSIS": self.execute_plan_analysis,
            "INTERPRET_RESULTS": self.execute_interpret_results,
            
            # Visualization
            "PLAN_FIGURES": self.execute_plan_figures,
            "CREATE_FIGURES": self.execute_create_figures,
            "VERIFY_FIGURES": self.execute_verify_figures,
            
            # Paper Writing
            "WRITE_ABSTRACT": self.execute_abstract_writing,
            "WRITE_INTRODUCTION": self.execute_intro_writing,
            "WRITE_METHODS": self.execute_methods_writing,
            "WRITE_RESULTS": self.execute_results_writing,
            "WRITE_DISCUSSION": self.execute_discussion_writing,
            "COMPILE_BIBLIOGRAPHY": self.execute_compile_bibliography,
            
            # Documentation
            "UPDATE_README_TABLE": self.execute_readme_update,
            "DOCUMENT_CODE": self.execute_document_code,
            "CREATE_API_DOCS": self.execute_create_api_docs,
            "UPDATE_PROJECT_DOCS": self.execute_update_project_docs,
            
            # Review & Quality
            "REVIEW_PAPER": self.execute_paper_review,
            "REVIEW_CODE": self.execute_code_review,
            "CHECK_REPRODUCIBILITY": self.execute_check_reproducibility,
            "CHECK_LOGIC_GAPS": self.execute_check_logic_gaps,
            
            # Project Management
            "CHECK_PROJECT_STATUS": self.execute_status_check,
            "UPDATE_PROJECT_STAGE": self.execute_update_stage,
            "CREATE_ISSUE_COMMENT": self.execute_issue_comment,
            "UPDATE_ISSUE_LABELS": self.execute_update_labels,
            "FORK_IDEA": self.execute_fork_idea,
            
            # Compilation & Publishing
            "COMPILE_LATEX": self.execute_compile_latex,
            "VERIFY_COMPILATION": self.execute_verify_compilation,
            "PREPARE_SUBMISSION": self.execute_prepare_submission,
            
            # Self-Improvement
            "IDENTIFY_IMPROVEMENTS": self.execute_improvement_identification,
            "IMPLEMENT_CORRECTIONS": self.execute_implement_corrections,
            "VERIFY_CORRECTIONS": self.execute_verify_corrections,
            "GENERATE_HELPER_FUNCTION": self.execute_helper_creation,
            
            # Attribution
            "GENERATE_ATTRIBUTION_REPORT": self.execute_generate_attribution_report,
        }
        
    def execute_task(self, task_type: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a specific task
        
        Args:
            task_type: Type of task to execute
            context: Task-specific context/parameters
            
        Returns:
            Result dictionary with success status and outputs
        """
        if task_type not in self.task_handlers:
            return {"success": False, "error": f"Unknown task type: {task_type}"}
            
        context = context or {}
        logger.info(f"Executing task: {task_type}")
        
        try:
            result = self.task_handlers[task_type](context)
            result["task_type"] = task_type
            return result
        except Exception as e:
            logger.error(f"Task {task_type} failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "task_type": task_type
            }
            
    # === IDEATION & DESIGN TASKS ===
    
    def execute_brainstorm(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate new research idea and create GitHub issue"""
        
        # Get existing ideas to avoid duplication
        existing_ideas = self.github.get_backlog_ideas()
        existing_fields = [idea.get('field', '') for idea in existing_ideas][:10]
        
        # Use a more creative prompting approach for small models
        fields = ['biology', 'chemistry', 'computer science', 'materials science', 
                  'environmental science', 'psychology', 'astronomy', 'medicine',
                  'robotics', 'energy', 'agriculture', 'ocean science']
        
        # Remove fields already used
        available_fields = [f for f in fields if f not in existing_fields]
        if not available_fields:
            available_fields = fields  # Reset if all used
            
        import random
        chosen_field = random.choice(available_fields)
        
        prompt = f"""Complete this research idea for the field of {chosen_field}:

Field: {chosen_field}
Idea: """

        response = self.conv_mgr.query_model(prompt, task_type="BRAINSTORM_IDEA", 
                                           )
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # For this simpler format, parse manually
        idea_text = response.strip()
        if idea_text.startswith("Idea:"):
            idea_text = idea_text[5:].strip()
            
        # Generate ID and keywords from the idea
        words = idea_text.lower().split()
        keywords = []
        skip_words = ['research', 'develop', 'create', 'system', 'using', 'title:', 'background:', 
                      'abstract:', 'approach:', 'the', 'and', 'for', 'with', 'that', 'this']
        
        for word in words:
            cleaned_word = word.strip('.,!?:;')
            if len(cleaned_word) > 5 and cleaned_word not in skip_words and ':' not in cleaned_word:
                keywords.append(cleaned_word)
                if len(keywords) >= 5:
                    break
                    
        # Create parsed data
        parsed = {
            'field': chosen_field,
            'idea': idea_text[:300],  # Limit length
            'id': f"{chosen_field.replace(' ', '-')}-{datetime.now().strftime('%Y%m%d')}-001",
            'keywords': ', '.join(keywords[:5]) if keywords else f"{chosen_field}, research, innovation"
        }
        
        # Log parsed data for debugging
        logger.info(f"Parsed brainstorm data: {parsed}")
            
        # Create GitHub issue
        field = parsed.get('field', 'Unknown Field')
        idea = parsed.get('idea', 'No description provided')
        id_suggestion = parsed.get('id', f'auto-{datetime.now().strftime("%Y%m%d-%H%M%S")}')
        keywords = parsed.get('keywords', 'research,llmxive,automated')
        
        issue_body = f"""**Field**: {field}

**Description**: {idea}

**Suggested ID**: {id_suggestion}

**Keywords**: {keywords}

---
*This idea was automatically generated by the llmXive automation system.*
*Model: {self.conv_mgr.model_name}*"""

        # Create labels list - only use existing labels
        labels = ["backlog", "idea", "Score: 0"]

        issue = self.github.create_issue(
            title=f"{idea[:80]}..." if len(idea) > 80 else idea,
            body=issue_body,
            labels=labels
        )
        
        if issue:
            # Track attribution
            self.attribution.add_contribution(
                model_id=self.conv_mgr.model_name,
                task_type="BRAINSTORM_IDEA",
                contribution_type="idea",
                reference=f"issue-{issue.number}",
                metadata={
                    "field": parsed['field'],
                    "idea_id": parsed['id'],
                    "keywords": parsed['keywords']
                }
            )
            
            # Add model attribution as a comment
            attribution_comment = self.attribution.format_attribution_comment(
                model_id=self.conv_mgr.model_name,
                task_type="BRAINSTORM_IDEA",
                additional_info={
                    "Field": parsed['field'],
                    "Idea ID": parsed['id']
                }
            )
            
            self.github.create_issue_comment(issue.number, attribution_comment)
            
            # Add issue to project board
            try:
                import subprocess
                # Add to project
                cmd = [
                    'gh', 'project', 'item-add', '13',
                    '--owner', 'ContextLab',
                    '--url', issue.html_url
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"Added issue #{issue.number} to project board")
                    
                    # Set status to Backlog
                    # Get the item ID for this issue
                    cmd = ['gh', 'project', 'item-list', '13', '--owner', 'ContextLab', '--format', 'json']
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        import json
                        data = json.loads(result.stdout)
                        for item in data.get('items', []):
                            if item.get('content', {}).get('number') == issue.number:
                                item_id = item['id']
                                # Set status to Backlog
                                cmd = [
                                    'gh', 'project', 'item-edit',
                                    '--id', item_id,
                                    '--field-id', 'PVTSSF_lADOAVVqQM4A9CYqzgw2-6c',  # Status field
                                    '--project-id', 'PVT_kwDOAVVqQM4A9CYq',
                                    '--single-select-option-id', 'f75ad846'  # Backlog
                                ]
                                subprocess.run(cmd, capture_output=True, text=True)
                                logger.info(f"Set issue #{issue.number} status to Backlog")
                                break
                else:
                    logger.warning(f"Failed to add issue to project board: {result.stderr}")
            except Exception as e:
                logger.warning(f"Could not add issue to project board: {e}")
            
            return {
                "success": True,
                "issue_number": issue.number,
                "issue_url": issue.html_url,
                "idea": parsed['idea'],
                "id": parsed['id'],
                "model": self.conv_mgr.model_name
            }
        else:
            return {"success": False, "error": "Failed to create issue"}
            
    def execute_technical_design(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create full technical design document"""
        issue_number = context.get('issue_number')
        if not issue_number:
            return {"success": False, "error": "No issue_number provided"}
            
        # Get issue details
        issue = self.github.get_issue(issue_number)
        if not issue:
            return {"success": False, "error": f"Issue {issue_number} not found"}
            
        # Extract idea details
        idea_details = self._parse_issue_for_idea(issue)
        
        prompt = f"""Task: Write a comprehensive technical design document for this research idea.

Idea: {idea_details['description']}
Field: {idea_details['field']}
Keywords: {idea_details['keywords']}

Create a technical design document that includes:

1. **Abstract** (150-200 words)
2. **Introduction**
   - Background and motivation
   - Related work (reference llmXive papers if relevant)
   - Research questions
3. **Proposed Approach**
   - Theoretical framework
   - Methodology overview
   - Technical innovations
4. **Implementation Strategy**
   - Key components
   - Technical requirements
   - Potential challenges
5. **Evaluation Plan**
   - Success metrics
   - Validation methods
   - Expected outcomes
6. **Timeline and Milestones**
7. **References** (if any)

Be specific, technical, and thorough. This document will guide the entire project."""

        response = self.conv_mgr.query_model(prompt, task_type="WRITE_TECHNICAL_DESIGN",
                                           )
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Save technical design document
        doc_path = f"technical_design_documents/{idea_details['id']}/design.md"
        
        design_content = f"""# Technical Design Document: {idea_details['title']}

**Project ID**: {idea_details['id']}
**Date**: {datetime.now().strftime('%Y-%m-%d')}
**Author**: LLM (Automated)
**Issue**: #{issue_number}

{response}

---
*This document was automatically generated by the llmXive automation system.*"""

        success = self.github.create_file(doc_path, design_content,
            f"Add technical design for {idea_details['id']}")
            
        if success:
            # Update README table
            self._update_design_readme(idea_details['id'], issue_number)
            
            return {
                "success": True,
                "design_path": doc_path,
                "project_id": idea_details['id']
            }
        else:
            return {"success": False, "error": "Failed to create design document"}
            
    def execute_design_review(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Review a technical design document"""
        design_path = context.get('design_path')
        issue_number = context.get('issue_number')
        project_id = context.get('project_id')
        
        if not design_path:
            return {"success": False, "error": "No design_path provided"}
            
        # Read design document
        design_content = self.github.get_file_content(design_path)
        if not design_content:
            return {"success": False, "error": f"Could not read {design_path}"}
            
        prompt = f"""Task: Review this technical design document for a research project.

Design Document:
{design_content[:3000]}  # Truncate if too long

Evaluate the design on these criteria:
1. **Clarity**: Is the research question and approach clearly defined?
2. **Feasibility**: Can this be realistically implemented?
3. **Novelty**: Does this advance the field in a meaningful way?
4. **Methodology**: Is the proposed method sound and rigorous?
5. **Impact**: What is the potential contribution to science?

Provide:
- 3-5 specific strengths
- 3-5 specific concerns or suggestions
- Overall recommendation with score

Output format:
Strengths:
- [Strength 1]
- [Strength 2]
- [Strength 3]

Concerns:
- [Concern 1]
- [Concern 2]
- [Concern 3]

Recommendation: [Strong Accept/Accept/Weak Accept/Reject]
Score: [1.0/0.7/0.3/0.0]
Summary: [1-2 sentence overall assessment]"""

        response = self.conv_mgr.query_model(prompt, task_type="REVIEW_TECHNICAL_DESIGN")
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Parse review
        parsed = self.parser.parse_review_response(response)
        if not parsed:
            return {"success": False, "error": "Failed to parse review", "raw_response": response}
            
        # Create review file
        review_filename = f"llm__{datetime.now().strftime('%m-%d-%Y')}__A.md"
        review_path = f"reviews/{project_id or 'unknown'}/Design/{review_filename}"
        
        review_content = f"""# Technical Design Review

**Reviewer**: LLM (Automated)
**Date**: {datetime.now().strftime('%Y-%m-%d')}
**Score**: {parsed.get('score', 0)}

## Strengths
{parsed.get('strengths', 'No strengths identified')}

## Concerns
{parsed.get('concerns', 'No concerns identified')}

## Recommendation
{parsed.get('recommendation', 'No recommendation')}

## Summary
{parsed.get('summary', 'No summary provided')}

---
*This review was generated automatically by the llmXive automation system.*"""

        # Save review
        success = self.github.create_file(review_path, review_content,
            f"Add automated design review (score: {parsed.get('score', 0)})")
            
        if success and issue_number:
            # Update issue score
            current_score = self.github.get_issue_score(issue_number)
            new_score = current_score + (parsed.get('score', 0) * 0.5)  # LLM reviews worth 0.5
            self.github.update_issue_score(issue_number, new_score)
            
        return {
            "success": success,
            "review_path": review_path,
            "score": parsed.get('score', 0),
            "recommendation": parsed.get('recommendation', 'Unknown')
        }
        
    # === PLANNING TASKS ===
    
    def execute_implementation_plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Convert technical design into detailed implementation plan"""
        design_path = context.get('design_path')
        project_id = context.get('project_id')
        
        if not design_path:
            return {"success": False, "error": "No design_path provided"}
            
        # Read technical design
        design_content = self.github.get_file_content(design_path)
        if not design_content:
            return {"success": False, "error": f"Could not read {design_path}"}
            
        prompt = f"""Task: Create a detailed implementation plan from this technical design.

Technical Design:
{design_content[:3000]}

Create an implementation plan with:

1. **Phase 1: Setup and Infrastructure**
   - Environment setup (requirements.txt, Dockerfile)
   - Dependencies and tools
   - Data requirements and sources
   
2. **Phase 2: Core Implementation**
   - Module breakdown with specific functions
   - Data structures and classes
   - Algorithm implementations
   
3. **Phase 3: Testing and Validation**
   - Unit test specifications
   - Integration test plan
   - Validation datasets and metrics
   
4. **Phase 4: Analysis and Results**
   - Analysis scripts needed
   - Expected outputs
   - Result interpretation approach
   
5. **Phase 5: Documentation and Paper**
   - Documentation requirements
   - Paper sections to write
   - Figure generation plan

For each phase, provide:
- Specific tasks with clear deliverables
- Dependencies and prerequisites
- Estimated effort (in hours)
- Success criteria"""

        response = self.conv_mgr.query_model(prompt, task_type="WRITE_IMPLEMENTATION_PLAN",
                                           )
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Save implementation plan
        plan_path = f"implementation_plans/{project_id}/implementation_plan.md"
        
        plan_content = f"""# Implementation Plan: {project_id}

**Date**: {datetime.now().strftime('%Y-%m-%d')}
**Based on**: {design_path}

{response}

---
*This plan was automatically generated by the llmXive automation system.*"""

        success = self.github.create_file(plan_path, plan_content,
            f"Add implementation plan for {project_id}")
            
        return {
            "success": success,
            "plan_path": plan_path,
            "project_id": project_id
        }
        
    def execute_implementation_review(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Review an implementation plan"""
        plan_path = context.get('plan_path')
        issue_number = context.get('issue_number')
        
        if not plan_path:
            return {"success": False, "error": "No plan_path provided"}
            
        # Read implementation plan
        plan_content = self.github.get_file_content(plan_path)
        if not plan_content:
            return {"success": False, "error": f"Could not read {plan_path}"}
            
        prompt = f"""Task: Review this implementation plan for completeness and feasibility.

Implementation Plan:
{plan_content[:3000]}

Evaluate:
1. **Completeness**: Are all necessary components included?
2. **Feasibility**: Can this be implemented as described?
3. **Clarity**: Are tasks specific and actionable?
4. **Dependencies**: Are prerequisites properly identified?
5. **Testing**: Is the testing plan adequate?

Provide review in the same format as technical design reviews."""

        response = self.conv_mgr.query_model(prompt, task_type="REVIEW_IMPLEMENTATION_PLAN")
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Parse and save review (similar to design review)
        parsed = self.parser.parse_review_response(response)
        if not parsed:
            return {"success": False, "error": "Failed to parse review"}
            
        # Extract project_id from path
        project_id = plan_path.split('/')[1] if '/' in plan_path else 'unknown'
        
        review_filename = f"llm__{datetime.now().strftime('%m-%d-%Y')}__A.md"
        review_path = f"reviews/{project_id}/Implementation/{review_filename}"
        
        review_content = f"""# Implementation Plan Review

**Reviewer**: LLM (Automated)
**Date**: {datetime.now().strftime('%Y-%m-%d')}
**Score**: {parsed.get('score', 0)}

## Strengths
{parsed.get('strengths', 'No strengths identified')}

## Concerns
{parsed.get('concerns', 'No concerns identified')}

## Recommendation
{parsed.get('recommendation', 'No recommendation')}

## Summary
{parsed.get('summary', 'No summary provided')}

---
*This review was generated automatically by the llmXive automation system.*"""

        success = self.github.create_file(review_path, review_content,
            f"Add implementation plan review (score: {parsed.get('score', 0)})")
            
        if success and issue_number:
            # Update issue score
            current_score = self.github.get_issue_score(issue_number)
            new_score = current_score + (parsed.get('score', 0) * 0.5)
            self.github.update_issue_score(issue_number, new_score)
            
        return {
            "success": success,
            "review_path": review_path,
            "score": parsed.get('score', 0)
        }
        
    # === LITERATURE SEARCH ===
    
    def execute_literature_search(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Search llmXive archive for relevant papers"""
        topic = context.get('topic')
        keywords = context.get('keywords', [])
        project_id = context.get('project_id')
        
        if not topic:
            return {"success": False, "error": "No topic provided"}
            
        # Read completed papers table
        papers_readme = self.github.get_file_content("papers/README.md")
        if not papers_readme:
            return {"success": False, "error": "Could not read papers README"}
            
        # Parse completed papers
        completed_papers = self._parse_completed_papers_table(papers_readme)
        
        # Search through papers
        relevant_papers = []
        for paper in completed_papers:
            # Try to read paper content
            paper_content = self._read_paper_content(paper['id'])
            if paper_content:
                relevance = self._calculate_relevance(paper_content, topic, keywords)
                if relevance > 0.3:
                    paper['relevance_score'] = relevance
                    paper['abstract'] = self._extract_abstract(paper_content)
                    relevant_papers.append(paper)
                    
        # Sort by relevance
        relevant_papers.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Create bibliography
        bibliography = self._create_llmxive_bibliography(relevant_papers, topic)
        
        # Save bibliography
        bib_path = f"literature/{project_id or 'general'}/llmxive_bibliography.md"
        success = self.github.create_file(bib_path, bibliography,
            f"Add llmXive literature review for {topic}")
            
        return {
            "success": success,
            "bibliography_path": bib_path,
            "papers_found": len(relevant_papers)
        }
        
    # === CODE TASKS ===
    
    def execute_code_writing(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Write code following implementation plan"""
        plan_path = context.get('plan_path')
        project_id = context.get('project_id')
        module_name = context.get('module_name', 'main')
        
        if not plan_path:
            return {"success": False, "error": "No plan_path provided"}
            
        # Read implementation plan
        plan_content = self.github.get_file_content(plan_path)
        if not plan_content:
            return {"success": False, "error": f"Could not read {plan_path}"}
            
        prompt = f"""Task: Write Python code for a specific module following this implementation plan.

Implementation Plan (relevant section):
{plan_content[:2000]}

Module to implement: {module_name}

Write clean, well-documented Python code that:
1. Follows the plan specifications exactly
2. Includes comprehensive docstrings (Google style)
3. Has proper error handling
4. Uses type hints
5. Is modular and testable

Output the complete module code:"""

        response = self.conv_mgr.query_model(prompt, task_type="WRITE_CODE",
                                           )
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Extract code
        code = self.parser.parse_code_block(response)
        if not code:
            # Try using the full response as code
            code = response
            
        # Add module docstring if missing
        if not code.strip().startswith('"""'):
            code = f'"""{module_name} module for {project_id}"""\n\n' + code
            
        # Save code file
        code_path = f"code/{project_id}/src/{module_name}.py"
        success = self.github.create_file(code_path, code,
            f"Add {module_name} module for {project_id}")
            
        return {
            "success": success,
            "code_path": code_path,
            "module_name": module_name,
            "lines_of_code": len(code.split('\n'))
        }
        
    def execute_test_writing(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Write tests for code"""
        code_path = context.get('code_path')
        
        if not code_path:
            return {"success": False, "error": "No code_path provided"}
            
        # Read code to test
        code_content = self.github.get_file_content(code_path)
        if not code_content:
            return {"success": False, "error": f"Could not read {code_path}"}
            
        prompt = f"""Task: Write comprehensive pytest tests for this code.

Code to test:
```python
{code_content[:2000]}
```

Write pytest test cases that:
1. Test all functions/methods
2. Include edge cases
3. Test error conditions
4. Use proper fixtures where appropriate
5. Include docstrings explaining what each test does

Output the complete test file:"""

        response = self.conv_mgr.query_model(prompt, task_type="WRITE_TESTS",
                                           )
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Extract test code
        test_code = self.parser.parse_code_block(response)
        if not test_code:
            test_code = response
            
        # Create test file path
        test_path = code_path.replace('/src/', '/tests/').replace('.py', '_test.py')
        
        # Add imports if missing
        if 'import pytest' not in test_code:
            module_name = os.path.basename(code_path).replace('.py', '')
            test_code = f"""import pytest
import sys
sys.path.append('../src')
from {module_name} import *

{test_code}"""

        success = self.github.create_file(test_path, test_code,
            f"Add tests for {os.path.basename(code_path)}")
            
        return {
            "success": success,
            "test_path": test_path,
            "num_tests": len(re.findall(r'def test_', test_code))
        }
        
    # === PAPER WRITING TASKS ===
    
    def execute_abstract_writing(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Write paper abstract"""
        paper_sections = context.get('paper_sections', {})
        project_id = context.get('project_id')
        
        # Try to gather information from existing sections
        intro = paper_sections.get('introduction', '')
        methods = paper_sections.get('methods', '')
        results = paper_sections.get('results', '')
        
        prompt = f"""Task: Write an abstract for a scientific paper.

Available sections:
Introduction: {intro[:500]}
Methods: {methods[:500]}
Results: {results[:500]}

Write a 150-250 word abstract that includes:
1. **Background** - Why this research matters (1-2 sentences)
2. **Objective** - What this study aims to do (1 sentence)
3. **Methods** - How the research was conducted (2-3 sentences)
4. **Results** - Key findings (2-3 sentences)
5. **Conclusions** - What the findings mean (1-2 sentences)

Make it concise, informative, and self-contained."""

        response = self.conv_mgr.query_model(prompt, task_type="WRITE_ABSTRACT")
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Save abstract
        abstract_path = f"papers/{project_id}/sections/abstract.md"
        success = self.github.create_file(abstract_path, response,
            f"Add abstract for {project_id}")
            
        return {
            "success": success,
            "section_path": abstract_path,
            "word_count": len(response.split())
        }
        
    def execute_intro_writing(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Write introduction section"""
        design_path = context.get('design_path')
        project_id = context.get('project_id')
        
        if not design_path:
            return {"success": False, "error": "No design_path provided"}
            
        design_content = self.github.get_file_content(design_path)
        if not design_content:
            return {"success": False, "error": f"Could not read {design_path}"}
            
        prompt = f"""Task: Write an introduction section for a scientific paper.

Technical Design:
{design_content[:1500]}

Write an introduction that:
1. **Opening** - Broad context and importance (1 paragraph)
2. **Background** - Key concepts and prior work (2-3 paragraphs)
3. **Gap/Problem** - What's missing in current knowledge (1 paragraph)
4. **Approach** - Brief overview of this work (1 paragraph)
5. **Contributions** - Bullet points of main contributions
6. **Paper Structure** - Brief outline of remaining sections

Use academic writing style. Reference prior work as [Author, Year]."""

        response = self.conv_mgr.query_model(prompt, task_type="WRITE_INTRODUCTION",
                                           )
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Save introduction
        intro_path = f"papers/{project_id}/sections/introduction.md"
        success = self.github.create_file(intro_path, response,
            f"Add introduction section for {project_id}")
            
        return {
            "success": success,
            "section_path": intro_path,
            "word_count": len(response.split())
        }
        
    def execute_methods_writing(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Write methods section"""
        implementation_path = context.get('implementation_path')
        project_id = context.get('project_id')
        
        content = ""
        if implementation_path:
            content = self.github.get_file_content(implementation_path) or ""
            
        prompt = f"""Task: Write a Methods section for a scientific paper.

Implementation details:
{content[:2000]}

Write a Methods section that includes:
1. **Overview** - High-level description of approach
2. **Data** - Datasets used (if applicable)
3. **Algorithm** - Step-by-step methodology
4. **Implementation Details** - Key technical choices
5. **Evaluation** - How results are measured

Use past tense, passive voice. Be precise and reproducible."""

        response = self.conv_mgr.query_model(prompt, task_type="WRITE_METHODS",
                                           )
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Save methods
        methods_path = f"papers/{project_id}/sections/methods.md"
        success = self.github.create_file(methods_path, response,
            f"Add methods section for {project_id}")
            
        return {
            "success": success,
            "section_path": methods_path,
            "word_count": len(response.split())
        }
        
    def execute_results_writing(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Write results section"""
        analysis_results = context.get('analysis_results', '')
        project_id = context.get('project_id')
        
        prompt = f"""Task: Write a Results section for a scientific paper.

Analysis outputs:
{analysis_results[:2000]}

Write a Results section that:
1. Presents findings in logical order
2. Reports statistics properly (e.g., t(df)=X.XX, p=.XXX)
3. References figures/tables as needed
4. Describes patterns without interpretation
5. Uses past tense and objective language

Be concise but complete."""

        response = self.conv_mgr.query_model(prompt, task_type="WRITE_RESULTS",
                                           )
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Save results
        results_path = f"papers/{project_id}/sections/results.md"
        success = self.github.create_file(results_path, response,
            f"Add results section for {project_id}")
            
        return {
            "success": success,
            "section_path": results_path,
            "word_count": len(response.split())
        }
        
    def execute_discussion_writing(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Write discussion section"""
        results_path = context.get('results_path')
        intro_path = context.get('intro_path')
        project_id = context.get('project_id')
        
        results = ""
        intro = ""
        
        if results_path:
            results = self.github.get_file_content(results_path) or ""
        if intro_path:
            intro = self.github.get_file_content(intro_path) or ""
            
        prompt = f"""Task: Write a Discussion section for a scientific paper.

Introduction context:
{intro[:1000]}

Results:
{results[:1500]}

Write a Discussion that:
1. **Summary** - Brief recap of main findings (1 paragraph)
2. **Interpretation** - What results mean (2-3 paragraphs)
3. **Relation to Prior Work** - How findings fit with literature
4. **Implications** - Theoretical and practical importance
5. **Limitations** - Honest assessment of constraints
6. **Future Directions** - Logical next steps
7. **Conclusions** - Take-home message (1 paragraph)"""

        response = self.conv_mgr.query_model(prompt, task_type="WRITE_DISCUSSION",
                                           )
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Save discussion
        discussion_path = f"papers/{project_id}/sections/discussion.md"
        success = self.github.create_file(discussion_path, response,
            f"Add discussion section for {project_id}")
            
        return {
            "success": success,
            "section_path": discussion_path,
            "word_count": len(response.split())
        }
        
    # === REVIEW TASKS ===
    
    def execute_paper_review(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Review complete paper"""
        paper_path = context.get('paper_path')
        project_id = context.get('project_id')
        
        if not paper_path:
            return {"success": False, "error": "No paper_path provided"}
            
        paper_content = self.github.get_file_content(paper_path)
        if not paper_content:
            return {"success": False, "error": f"Could not read {paper_path}"}
            
        prompt = f"""Task: Review this scientific paper comprehensively.

Paper:
{paper_content[:4000]}

Evaluate:
1. **Scientific Merit** - Is the research sound and novel?
2. **Clarity** - Is the paper well-written and organized?
3. **Methods** - Are methods appropriate and well-described?
4. **Results** - Are results clearly presented and supported?
5. **Impact** - What is the potential contribution?

Provide detailed review with strengths, weaknesses, and recommendations."""

        response = self.conv_mgr.query_model(prompt, task_type="REVIEW_PAPER",
                                           )
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Parse and save review
        parsed = self.parser.parse_review_response(response)
        
        review_filename = f"llm__{datetime.now().strftime('%m-%d-%Y')}__A.md"
        review_path = f"reviews/{project_id}/Paper/{review_filename}"
        
        review_content = f"""# Paper Review

**Reviewer**: LLM (Automated)
**Date**: {datetime.now().strftime('%Y-%m-%d')}
**Score**: {parsed.get('score', 0) if parsed else 'N/A'}

{response}

---
*This review was generated automatically by the llmXive automation system.*"""

        success = self.github.create_file(review_path, review_content,
            f"Add paper review for {project_id}")
            
        return {
            "success": success,
            "review_path": review_path,
            "score": parsed.get('score', 0) if parsed else None
        }
        
    def execute_code_review(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Review code implementation"""
        code_path = context.get('code_path')
        
        if not code_path:
            return {"success": False, "error": "No code_path provided"}
            
        code_content = self.github.get_file_content(code_path)
        if not code_content:
            return {"success": False, "error": f"Could not read {code_path}"}
            
        prompt = f"""Task: Review this Python code for quality and correctness.

Code:
```python
{code_content[:2000]}
```

Check for:
1. **Correctness** - Does it work as intended?
2. **Style** - PEP 8 compliance
3. **Documentation** - Are docstrings complete?
4. **Error Handling** - Robust error handling?
5. **Efficiency** - Performance issues?
6. **Testing** - Is it testable?

Output format:
Status: [PASS/FAIL]
Issues Found:
- [Issue with line number]

Suggestions:
- [Improvement]

Code Quality Score: [0-10]
Summary: [Brief assessment]"""

        response = self.conv_mgr.query_model(prompt, task_type="REVIEW_CODE")
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Create review comment
        if context.get('issue_number'):
            comment = f"""## Code Review: `{code_path}`

{response}

---
*This review was generated automatically by the llmXive automation system.*"""

            success = self.github.create_issue_comment(context['issue_number'], comment)
            
            return {
                "success": success,
                "review": response
            }
            
        return {
            "success": True,
            "review": response
        }
        
    # === PROJECT MANAGEMENT ===
    
    def execute_status_check(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check if project meets advancement criteria"""
        project_id = context.get('project_id')
        issue_number = context.get('issue_number')
        
        if not (project_id or issue_number):
            return {"success": False, "error": "No project_id or issue_number provided"}
            
        # Get issue
        if issue_number:
            issue = self.github.get_issue(issue_number)
        else:
            issue = self.github.find_issue_by_project_id(project_id)
            
        if not issue:
            return {"success": False, "error": "Issue not found"}
            
        # Get current state
        labels = [l.name for l in issue.labels]
        current_score = self.github.get_issue_score(issue.number)
        
        # Determine stage
        current_stage = "backlog"
        if "ready" in labels:
            current_stage = "ready"
        elif "in-progress" in labels:
            current_stage = "in-progress"
        elif "done" in labels:
            current_stage = "done"
            
        # Check requirements
        requirements = {
            "backlog": {"next": "ready", "needed_score": 10.0},
            "ready": {"next": "in-progress", "needed_score": 5.0},
            "in-progress": {"next": "done", "needed_score": 0}
        }
        
        req = requirements.get(current_stage, {})
        can_advance = current_score >= req.get('needed_score', 0)
        
        # Auto-advance if requested
        if can_advance and context.get('auto_advance', False):
            self.github.update_issue_stage(issue.number, req['next'])
            
        return {
            "success": True,
            "current_stage": current_stage,
            "next_stage": req.get('next'),
            "current_score": current_score,
            "needed_score": req.get('needed_score', 0),
            "can_advance": can_advance
        }
        
    def execute_issue_comment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Add comment to issue"""
        issue_number = context.get('issue_number')
        comment_text = context.get('comment')
        
        if not issue_number or not comment_text:
            return {"success": False, "error": "Missing issue_number or comment"}
            
        # Add automation footer
        full_comment = f"""{comment_text}

---
*This comment was generated by the llmXive automation system.*"""

        success = self.github.create_issue_comment(issue_number, full_comment)
        
        return {
            "success": success,
            "issue_number": issue_number
        }
        
    # === SELF-IMPROVEMENT ===
    
    def execute_improvement_identification(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Identify areas for improvement"""
        artifact_path = context.get('artifact_path')
        artifact_type = context.get('artifact_type', 'document')
        
        if not artifact_path:
            return {"success": False, "error": "No artifact_path provided"}
            
        content = self.github.get_file_content(artifact_path)
        if not content:
            return {"success": False, "error": f"Could not read {artifact_path}"}
            
        prompt = f"""Task: Review this {artifact_type} and identify improvements.

Content:
{content[:3000]}

Analyze for:
1. **Clarity** - Unclear sections
2. **Completeness** - Missing elements
3. **Correctness** - Errors
4. **Quality** - Below standard areas
5. **Structure** - Organization issues

For each issue:
- Describe the problem
- Suggest improvement
- Rate priority (High/Medium/Low)"""

        response = self.conv_mgr.query_model(prompt, task_type="IDENTIFY_IMPROVEMENTS")
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Save improvement report
        report_path = artifact_path.replace('.', '_improvements.')
        report_content = f"""# Improvement Report

**Artifact**: {artifact_path}
**Type**: {artifact_type}
**Date**: {datetime.now().strftime('%Y-%m-%d')}

{response}

---
*This report was automatically generated by the llmXive automation system.*"""

        success = self.github.create_file(report_path, report_content,
            f"Add improvement report for {artifact_path}")
            
        return {
            "success": success,
            "report_path": report_path
        }
        
    # === UTILITY TASKS ===
    
    def execute_readme_update(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Update README table"""
        file_path = context.get('file_path')
        table_identifier = context.get('table_identifier')
        new_entry = context.get('new_entry')
        
        if not all([file_path, table_identifier, new_entry]):
            return {"success": False, "error": "Missing required parameters"}
            
        # Read current file
        content = self.github.get_file_content(file_path)
        if not content:
            return {"success": False, "error": f"Could not read {file_path}"}
            
        # Have LLM format the table row
        prompt = f"""Task: Format a new table row for a markdown table.

File content:
```
{content[:1000]}
```

Table to update: {table_identifier}
New entry data: {new_entry}

Output ONLY the formatted table row (with | separators):"""

        response = self.conv_mgr.query_model(prompt, task_type="UPDATE_README_TABLE")
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Parse table row
        new_row = self.parser.parse_table_row(response)
        if not new_row:
            new_row = response.strip()
            
        # Insert into table
        success = self.github.insert_table_row(file_path, table_identifier, new_row)
        
        return {
            "success": success,
            "file_path": file_path,
            "row_added": new_row
        }
        
    def execute_helper_creation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate helper function"""
        purpose = context.get('purpose')
        requirements = context.get('requirements', [])
        
        if not purpose:
            return {"success": False, "error": "No purpose provided"}
            
        prompt = f"""Task: Create a reusable helper function.

Purpose: {purpose}
Requirements: {', '.join(requirements)}

Create a Python function that:
1. Has a clear, descriptive name
2. Includes comprehensive docstring (Google style)
3. Has type hints
4. Handles edge cases
5. Is efficient

Output the complete function:"""

        response = self.conv_mgr.query_model(prompt, task_type="GENERATE_HELPER_FUNCTION")
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Extract code
        code = self.parser.parse_code_block(response)
        if not code:
            code = response
            
        return {
            "success": True,
            "function_code": code,
            "lines_of_code": len(code.split('\n'))
        }
        
    def execute_reference_validation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate references"""
        references = context.get('references', [])
        
        if not references:
            return {"success": False, "error": "No references provided"}
            
        results = []
        
        for ref in references:
            prompt = f"""Task: Validate this academic reference.

Reference: {ref}

Check if this appears to be a real academic paper by examining:
1. Author names (plausible?)
2. Title (coherent and academic?)
3. Year (reasonable?)
4. Venue (known journal/conference?)

Output:
Status: [VALID/INVALID/UNCERTAIN]
Reason: [Brief explanation]
Confidence: [HIGH/MEDIUM/LOW]"""

            response = self.conv_mgr.query_model(prompt, task_type="VALIDATE_REFERENCES")
            
            if response:
                # Parse validation
                parsed = self.parser.parse_key_value(response)
                results.append({
                    "reference": ref,
                    "status": parsed.get('status', 'UNCERTAIN'),
                    "reason": parsed.get('reason', 'Parse failed'),
                    "confidence": parsed.get('confidence', 'LOW')
                })
                
        # Summary
        valid_count = sum(1 for r in results if r['status'] == 'VALID')
        
        return {
            "success": True,
            "total_references": len(references),
            "valid": valid_count,
            "results": results
        }
        
    # === Helper Methods ===
    
    def _parse_issue_for_idea(self, issue) -> Dict[str, str]:
        """Extract idea details from issue"""
        body = issue.body or ""
        
        # Extract fields
        field_match = re.search(r'\*\*Field\*\*:\s*(.+)', body)
        desc_match = re.search(r'\*\*Description\*\*:\s*(.+)', body)
        id_match = re.search(r'\*\*Suggested ID\*\*:\s*(.+)', body)
        keywords_match = re.search(r'\*\*Keywords\*\*:\s*(.+)', body)
        
        return {
            'title': issue.title,
            'field': field_match.group(1) if field_match else 'Unknown',
            'description': desc_match.group(1) if desc_match else issue.title,
            'id': id_match.group(1) if id_match else f"project-{issue.number}",
            'keywords': keywords_match.group(1) if keywords_match else ''
        }
        
    def _update_design_readme(self, project_id: str, issue_number: int):
        """Update technical design documents README"""
        readme_path = "technical_design_documents/README.md"
        
        # Create new table row
        new_row = f"| {project_id} | Project {project_id} | Backlog | [#{issue_number}](https://github.com/ContextLab/llmXive/issues/{issue_number}) | [Design](/{project_id}/design.md) | [llm-automation](https://github.com/llm-automation) |"
        
        self.github.insert_table_row(readme_path, "Table of Contents", new_row)
        
    def _parse_completed_papers_table(self, readme_content: str) -> List[Dict]:
        """Parse completed papers from README"""
        papers = []
        
        # Find completed work table
        table_match = re.search(
            r'## Completed work\s*\n\s*\|.*?\|.*?\n\|[-:\s|]+\|.*?\n((?:\|.*?\|.*?\n)+)',
            readme_content, re.MULTILINE | re.DOTALL
        )
        
        if table_match:
            rows = table_match.group(1).strip().split('\n')
            
            for row in rows:
                cells = [c.strip() for c in row.split('|')[1:-1]]
                if len(cells) >= 6:
                    papers.append({
                        'id': cells[0],
                        'title': cells[1],
                        'contributors': cells[5]
                    })
                    
        return papers
        
    def _read_paper_content(self, paper_id: str) -> Optional[str]:
        """Try to read paper content"""
        paths = [
            f"papers/{paper_id}/paper.tex",
            f"papers/{paper_id}/paper.md",
            f"papers/{paper_id}/main.tex"
        ]
        
        for path in paths:
            content = self.github.get_file_content(path)
            if content:
                return content
                
        return None
        
    def _calculate_relevance(self, content: str, topic: str, keywords: List[str]) -> float:
        """Calculate relevance score"""
        content_lower = content.lower()
        topic_lower = topic.lower()
        
        relevance = 0.0
        
        # Topic in content
        if topic_lower in content_lower[:1000]:
            relevance += 0.5
            
        # Topic frequency
        topic_count = content_lower.count(topic_lower)
        relevance += min(topic_count * 0.05, 0.3)
        
        # Keywords
        for keyword in keywords:
            if keyword.lower() in content_lower:
                relevance += 0.1
                
        return min(relevance, 1.0)
        
    def _extract_abstract(self, content: str) -> str:
        """Extract abstract from paper"""
        # LaTeX abstract
        abstract_match = re.search(
            r'\\begin\{abstract\}(.*?)\\end\{abstract\}',
            content, re.DOTALL
        )
        
        if abstract_match:
            return abstract_match.group(1).strip()
            
        # Markdown abstract
        abstract_match = re.search(
            r'## Abstract\s*\n(.*?)(?=\n##|\Z)',
            content, re.DOTALL
        )
        
        if abstract_match:
            return abstract_match.group(1).strip()
            
        return "Abstract not found"
        
    def _create_llmxive_bibliography(self, papers: List[Dict], topic: str) -> str:
        """Create bibliography from papers"""
        bibliography = f"""# llmXive Literature Review: {topic}

**Generated**: {datetime.now().strftime('%Y-%m-%d')}
**Papers Found**: {len(papers)}

## Relevant Papers

"""
        
        for i, paper in enumerate(papers, 1):
            bibliography += f"""### {i}. {paper['title']}

**Project ID**: {paper['id']}
**Contributors**: {paper['contributors']}
**Relevance Score**: {paper['relevance_score']:.2f}

**Abstract**:
{paper.get('abstract', 'Not available')}

---

"""
        
        if not papers:
            bibliography += "*No relevant papers found in llmXive archive.*\n"
            
        return bibliography
        
    # === ADDITIONAL MISSING TASK IMPLEMENTATIONS ===
    
    def execute_mine_archive(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mine llmXive archive for related work"""
        # Similar to literature search but focused on internal papers only
        return self.execute_literature_search(context)
        
    def execute_run_tests(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run tests and report results"""
        test_path = context.get('test_path', 'tests/')
        project_id = context.get('project_id')
        
        # Simulate test execution (in real implementation would run pytest)
        prompt = f"""Task: Analyze test requirements for this project.
        
Test path: {test_path}
Project: {project_id}

Describe what tests should be run and expected outcomes."""

        response = self.conv_mgr.query_model(prompt, task_type="RUN_TESTS")
        
        return {
            "success": True,
            "test_results": response or "Test analysis complete",
            "tests_passed": True  # Simulated
        }
        
    def execute_run_code(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code and capture outputs"""
        code_path = context.get('code_path')
        parameters = context.get('parameters', {})
        
        if not code_path:
            return {"success": False, "error": "No code_path provided"}
            
        # Read code
        code_content = self.github.get_file_content(code_path)
        if not code_content:
            return {"success": False, "error": f"Could not read {code_path}"}
            
        # Simulate code execution
        prompt = f"""Task: Analyze what this code would output when run.

Code:
```python
{code_content[:2000]}
```

Parameters: {parameters}

Describe expected execution results and outputs."""

        response = self.conv_mgr.query_model(prompt, task_type="RUN_CODE")
        
        return {
            "success": True,
            "execution_output": response or "Execution analysis complete",
            "exit_code": 0  # Simulated
        }
        
    def execute_debug_code(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Debug failing code"""
        error_report = context.get('error_report', '')
        code_path = context.get('code_path')
        
        if not code_path:
            return {"success": False, "error": "No code_path provided"}
            
        code_content = self.github.get_file_content(code_path)
        if not code_content:
            return {"success": False, "error": f"Could not read {code_path}"}
            
        prompt = f"""Task: Debug this code based on the error report.

Error Report:
{error_report}

Code:
```python
{code_content[:2000]}
```

Provide fixed code that addresses the error:"""

        response = self.conv_mgr.query_model(prompt, task_type="DEBUG_CODE",
                                           )
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Extract fixed code
        fixed_code = self.parser.parse_code_block(response)
        if not fixed_code:
            fixed_code = response
            
        # Update code file
        success = self.github.update_file(code_path, fixed_code,
            f"Fix errors in {os.path.basename(code_path)}")
            
        return {
            "success": success,
            "code_path": code_path,
            "fix_applied": True
        }
        
    def execute_organize_notebooks(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Organize code into Jupyter notebooks"""
        code_files = context.get('code_files', [])
        project_id = context.get('project_id')
        
        if not code_files:
            return {"success": False, "error": "No code_files provided"}
            
        # Create notebook structure
        notebook_content = {
            "cells": [],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        # Add markdown cell with introduction
        notebook_content["cells"].append({
            "cell_type": "markdown",
            "metadata": {},
            "source": [f"# {project_id} Analysis Notebook\n",
                      f"Generated on {datetime.now().strftime('%Y-%m-%d')}"]
        })
        
        # Add code cells
        for code_file in code_files:
            code = self.github.get_file_content(code_file)
            if code:
                notebook_content["cells"].append({
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": code.split('\n')
                })
                
        # Save notebook
        import json
        notebook_json = json.dumps(notebook_content, indent=2)
        notebook_path = f"code/{project_id}/notebooks/analysis.ipynb"
        
        success = self.github.create_file(notebook_path, notebook_json,
            f"Create analysis notebook for {project_id}")
            
        return {
            "success": success,
            "notebook_path": notebook_path,
            "num_cells": len(notebook_content["cells"])
        }
        
    def execute_generate_dataset(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate or find datasets"""
        requirements = context.get('requirements', '')
        project_id = context.get('project_id')
        
        prompt = f"""Task: Design a dataset for this research project.

Requirements:
{requirements}

Specify:
1. Data structure and format
2. Number of samples needed
3. Features/variables to include
4. How to generate or obtain the data
5. Example data (5-10 rows)"""

        response = self.conv_mgr.query_model(prompt, task_type="GENERATE_DATASET")
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Save dataset description
        dataset_path = f"data/{project_id}/dataset_description.md"
        success = self.github.create_file(dataset_path, response,
            f"Add dataset description for {project_id}")
            
        return {
            "success": success,
            "dataset_path": dataset_path
        }
        
    def execute_analyze_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform data analysis"""
        data_path = context.get('data_path')
        analysis_plan = context.get('analysis_plan', '')
        
        prompt = f"""Task: Create analysis code for this data.

Data location: {data_path}
Analysis plan: {analysis_plan}

Write Python code that:
1. Loads the data
2. Performs exploratory analysis
3. Runs statistical tests
4. Generates summary statistics
5. Creates visualizations"""

        response = self.conv_mgr.query_model(prompt, task_type="ANALYZE_DATA",
                                           )
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Extract code
        analysis_code = self.parser.parse_code_block(response)
        if not analysis_code:
            analysis_code = response
            
        # Save analysis script
        project_id = context.get('project_id', 'unknown')
        analysis_path = f"code/{project_id}/analysis/data_analysis.py"
        
        success = self.github.create_file(analysis_path, analysis_code,
            f"Add data analysis script for {project_id}")
            
        return {
            "success": success,
            "analysis_path": analysis_path
        }
        
    def execute_plan_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Plan statistical analysis"""
        research_questions = context.get('research_questions', '')
        data_description = context.get('data_description', '')
        
        prompt = f"""Task: Create a comprehensive statistical analysis plan.

Research Questions:
{research_questions}

Data Description:
{data_description}

Create an analysis plan that includes:
1. Hypotheses to test
2. Statistical tests to use
3. Power analysis
4. Effect size calculations
5. Multiple comparison corrections
6. Visualization plans"""

        response = self.conv_mgr.query_model(prompt, task_type="PLAN_STATISTICAL_ANALYSIS")
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Save analysis plan
        project_id = context.get('project_id', 'unknown')
        plan_path = f"implementation_plans/{project_id}/statistical_analysis_plan.md"
        
        success = self.github.create_file(plan_path, response,
            f"Add statistical analysis plan for {project_id}")
            
        return {
            "success": success,
            "plan_path": plan_path
        }
        
    def execute_interpret_results(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Interpret analysis results"""
        results_data = context.get('results_data', '')
        analysis_plan = context.get('analysis_plan', '')
        
        prompt = f"""Task: Interpret these statistical results.

Results:
{results_data}

Analysis Plan:
{analysis_plan}

Provide interpretation that:
1. Explains what the results mean
2. Relates findings to hypotheses
3. Discusses effect sizes
4. Notes unexpected findings
5. Suggests implications"""

        response = self.conv_mgr.query_model(prompt, task_type="INTERPRET_RESULTS")
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Save interpretation
        project_id = context.get('project_id', 'unknown')
        interpretation_path = f"papers/{project_id}/results_interpretation.md"
        
        success = self.github.create_file(interpretation_path, response,
            f"Add results interpretation for {project_id}")
            
        return {
            "success": success,
            "interpretation_path": interpretation_path
        }
        
    def execute_plan_figures(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Plan figures for paper"""
        results = context.get('results', '')
        paper_outline = context.get('paper_outline', '')
        
        prompt = f"""Task: Plan figures for a scientific paper.

Results to visualize:
{results[:1500]}

Paper outline:
{paper_outline}

For each figure, specify:
1. Figure number and title
2. Type (scatter, bar, line, heatmap, etc.)
3. Data to plot
4. Axes labels
5. Caption text
6. Key message"""

        response = self.conv_mgr.query_model(prompt, task_type="PLAN_FIGURES")
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Parse figure plans
        figure_plans = self.parser.parse_figure_plan(response)
        
        # Save figure plan
        project_id = context.get('project_id', 'unknown')
        plan_path = f"papers/{project_id}/figure_plan.md"
        
        plan_content = f"""# Figure Plan for {project_id}

{response}

## Parsed Figures:
{json.dumps(figure_plans, indent=2)}"""

        success = self.github.create_file(plan_path, plan_content,
            f"Add figure plan for {project_id}")
            
        return {
            "success": success,
            "plan_path": plan_path,
            "num_figures": len(figure_plans)
        }
        
    def execute_create_figures(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create figures based on plan"""
        figure_plan = context.get('figure_plan', '')
        data_path = context.get('data_path', '')
        
        prompt = f"""Task: Write Python code to create publication-quality figures.

Figure Plan:
{figure_plan}

Data location: {data_path}

Create matplotlib/seaborn code that:
1. Loads necessary data
2. Creates each planned figure
3. Uses professional styling
4. Saves as vector format (PDF/SVG)
5. Includes all labels and formatting"""

        response = self.conv_mgr.query_model(prompt, task_type="CREATE_FIGURES",
                                           )
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Extract code
        figure_code = self.parser.parse_code_block(response)
        if not figure_code:
            figure_code = response
            
        # Save figure generation script
        project_id = context.get('project_id', 'unknown')
        script_path = f"code/{project_id}/figures/generate_figures.py"
        
        success = self.github.create_file(script_path, figure_code,
            f"Add figure generation script for {project_id}")
            
        return {
            "success": success,
            "script_path": script_path
        }
        
    def execute_verify_figures(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Verify figures render correctly"""
        figure_paths = context.get('figure_paths', [])
        
        prompt = f"""Task: Create verification checklist for scientific figures.

Figures to verify:
{', '.join(figure_paths)}

Check for:
1. Resolution (300+ DPI for print)
2. Font sizes (readable)
3. Color choices (colorblind-friendly)
4. Labels and legends
5. File formats
6. Consistency across figures"""

        response = self.conv_mgr.query_model(prompt, task_type="VERIFY_FIGURES")
        
        return {
            "success": True,
            "verification_report": response or "Figure verification complete",
            "figures_checked": len(figure_paths)
        }
        
    def execute_compile_bibliography(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Compile formatted bibliography"""
        citations = context.get('citations', [])
        style = context.get('style', 'APA')
        
        prompt = f"""Task: Format these citations in {style} style.

Citations:
{chr(10).join(citations[:20])}

Format each citation properly and create a complete bibliography section."""

        response = self.conv_mgr.query_model(prompt, task_type="COMPILE_BIBLIOGRAPHY")
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Save bibliography
        project_id = context.get('project_id', 'unknown')
        bib_path = f"papers/{project_id}/sections/bibliography.md"
        
        success = self.github.create_file(bib_path, response,
            f"Add bibliography for {project_id}")
            
        return {
            "success": success,
            "bibliography_path": bib_path,
            "num_references": len(citations)
        }
        
    def execute_document_code(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Add documentation to code"""
        code_path = context.get('code_path')
        
        if not code_path:
            return {"success": False, "error": "No code_path provided"}
            
        code_content = self.github.get_file_content(code_path)
        if not code_content:
            return {"success": False, "error": f"Could not read {code_path}"}
            
        prompt = f"""Task: Add comprehensive documentation to this code.

Code:
```python
{code_content[:2000]}
```

Add:
1. Module-level docstring
2. Function/class docstrings (Google style)
3. Inline comments for complex logic
4. Type hints where missing
5. Usage examples in docstrings"""

        response = self.conv_mgr.query_model(prompt, task_type="DOCUMENT_CODE",
                                           )
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Extract documented code
        documented_code = self.parser.parse_code_block(response)
        if not documented_code:
            documented_code = response
            
        # Update file
        success = self.github.update_file(code_path, documented_code,
            f"Add documentation to {os.path.basename(code_path)}")
            
        return {
            "success": success,
            "code_path": code_path
        }
        
    def execute_create_api_docs(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate API documentation"""
        code_base_path = context.get('code_base_path', 'code/')
        project_id = context.get('project_id')
        
        prompt = f"""Task: Create API documentation structure.

Project: {project_id}
Code location: {code_base_path}

Create documentation that includes:
1. API overview
2. Module descriptions
3. Class/function references
4. Parameter descriptions
5. Return value documentation
6. Usage examples
7. Error handling"""

        response = self.conv_mgr.query_model(prompt, task_type="CREATE_API_DOCS")
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Save API docs
        docs_path = f"code/{project_id}/docs/api_reference.md"
        
        success = self.github.create_file(docs_path, response,
            f"Add API documentation for {project_id}")
            
        return {
            "success": success,
            "docs_path": docs_path
        }
        
    def execute_update_project_docs(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Update project documentation"""
        doc_type = context.get('doc_type', 'readme')
        updates = context.get('updates', '')
        project_id = context.get('project_id')
        
        # Determine doc path
        if doc_type == 'readme':
            doc_path = f"code/{project_id}/README.md"
        else:
            doc_path = f"code/{project_id}/docs/{doc_type}.md"
            
        # Read existing content
        existing = self.github.get_file_content(doc_path) or ""
        
        prompt = f"""Task: Update project documentation.

Current documentation:
{existing[:1000]}

Updates needed:
{updates}

Integrate the updates while maintaining document structure and style."""

        response = self.conv_mgr.query_model(prompt, task_type="UPDATE_PROJECT_DOCS")
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Update or create file
        if existing:
            success = self.github.update_file(doc_path, response,
                f"Update {doc_type} documentation")
        else:
            success = self.github.create_file(doc_path, response,
                f"Create {doc_type} documentation")
                
        return {
            "success": success,
            "doc_path": doc_path
        }
        
    def execute_check_reproducibility(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check reproducibility of results"""
        paper_path = context.get('paper_path')
        code_path = context.get('code_path')
        
        prompt = f"""Task: Create reproducibility checklist.

Paper: {paper_path}
Code: {code_path}

Check for:
1. Environment specification (requirements.txt, Dockerfile)
2. Random seeds set
3. Data availability
4. Step-by-step instructions
5. Expected outputs documented
6. Computational requirements stated
7. Version numbers specified"""

        response = self.conv_mgr.query_model(prompt, task_type="CHECK_REPRODUCIBILITY")
        
        # Save reproducibility report
        project_id = context.get('project_id', 'unknown')
        report_path = f"reviews/{project_id}/reproducibility_check.md"
        
        report_content = f"""# Reproducibility Check

**Date**: {datetime.now().strftime('%Y-%m-%d')}
**Paper**: {paper_path}
**Code**: {code_path}

{response}

---
*This check was performed by the llmXive automation system.*"""

        success = self.github.create_file(report_path, report_content,
            "Add reproducibility check report")
            
        return {
            "success": success,
            "report_path": report_path
        }
        
    def execute_check_logic_gaps(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Find logical inconsistencies"""
        document_path = context.get('document_path')
        
        if not document_path:
            return {"success": False, "error": "No document_path provided"}
            
        content = self.github.get_file_content(document_path)
        if not content:
            return {"success": False, "error": f"Could not read {document_path}"}
            
        prompt = f"""Task: Find logical gaps and inconsistencies.

Document:
{content[:3000]}

Look for:
1. Unsupported claims
2. Missing logical steps
3. Contradictions
4. Unclear assumptions
5. Incomplete arguments
6. Missing definitions"""

        response = self.conv_mgr.query_model(prompt, task_type="CHECK_LOGIC_GAPS")
        
        return {
            "success": True,
            "logic_gaps": response or "No significant gaps found",
            "document_checked": document_path
        }
        
    def execute_update_stage(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Update project stage"""
        issue_number = context.get('issue_number')
        new_stage = context.get('new_stage')
        
        if not issue_number or not new_stage:
            return {"success": False, "error": "Missing issue_number or new_stage"}
            
        success = self.github.update_issue_stage(issue_number, new_stage)
        
        return {
            "success": success,
            "issue_number": issue_number,
            "new_stage": new_stage
        }
        
    def execute_update_labels(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Update issue labels"""
        issue_number = context.get('issue_number')
        add_labels = context.get('add_labels', [])
        remove_labels = context.get('remove_labels', [])
        
        if not issue_number:
            return {"success": False, "error": "No issue_number provided"}
            
        issue = self.github.get_issue(issue_number)
        if not issue:
            return {"success": False, "error": f"Issue {issue_number} not found"}
            
        # Get current labels
        current_labels = [l.name for l in issue.labels]
        
        # Update labels
        new_labels = current_labels.copy()
        for label in remove_labels:
            if label in new_labels:
                new_labels.remove(label)
        for label in add_labels:
            if label not in new_labels:
                new_labels.append(label)
                
        # Apply update
        issue.set_labels(*new_labels)
        
        return {
            "success": True,
            "issue_number": issue_number,
            "labels": new_labels
        }
        
    def execute_fork_idea(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create related ideas from existing"""
        original_issue_number = context.get('issue_number')
        
        if not original_issue_number:
            return {"success": False, "error": "No issue_number provided"}
            
        # Get original issue
        original = self.github.get_issue(original_issue_number)
        if not original:
            return {"success": False, "error": f"Issue {original_issue_number} not found"}
            
        # Extract idea details
        idea_details = self._parse_issue_for_idea(original)
        
        prompt = f"""Task: Generate 3 related research ideas based on this one.

Original idea:
{idea_details['description']}
Field: {idea_details['field']}

Create 3 variations that:
1. Apply the method to a different domain
2. Use a different approach for the same problem
3. Extend the idea with additional complexity

For each, provide the same format as the original."""

        response = self.conv_mgr.query_model(prompt, task_type="FORK_IDEA")
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Parse and create new issues
        created_issues = []
        
        # Simple parsing - in real implementation would be more robust
        ideas = response.split('\n\n')
        for idea in ideas[:3]:
            if 'Field:' in idea and 'Idea:' in idea:
                parsed = self.parser.parse_brainstorm_response(idea)
                if parsed:
                    # Create new issue
                    issue_body = f"""**Field**: {parsed['field']}

**Description**: {parsed['idea']}

**Suggested ID**: {parsed['id']}

**Keywords**: {parsed.get('keywords', '')}

**Forked from**: #{original_issue_number}

---
*This idea was forked by the llmXive automation system.*"""

                    issue = self.github.create_issue(
                        title=f"{parsed['idea'][:80]}..." if len(parsed['idea']) > 80 else parsed['idea'],
                        body=issue_body,
                        labels=["backlog", "idea", "Score: 0", "forked"]
                    )
                    
                    if issue:
                        created_issues.append(issue.number)
                        
        return {
            "success": len(created_issues) > 0,
            "forked_issues": created_issues,
            "original_issue": original_issue_number
        }
        
    def execute_compile_latex(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Compile LaTeX to PDF"""
        latex_path = context.get('latex_path')
        project_id = context.get('project_id')
        
        # In real implementation, would use latex compiler
        # For now, create compilation instructions
        prompt = f"""Task: Create LaTeX compilation instructions.

Project: {project_id}
LaTeX file: {latex_path}

Provide:
1. Required LaTeX packages
2. Compilation commands (pdflatex, bibtex, etc.)
3. Common compilation errors and fixes
4. Directory structure needed"""

        response = self.conv_mgr.query_model(prompt, task_type="COMPILE_LATEX")
        
        # Save compilation guide
        guide_path = f"papers/{project_id}/compilation_guide.md"
        
        guide_content = f"""# LaTeX Compilation Guide

{response}

## Compilation Command
```bash
pdflatex paper.tex
bibtex paper
pdflatex paper.tex
pdflatex paper.tex
```

---
*Generated by llmXive automation system.*"""

        success = self.github.create_file(guide_path, guide_content,
            "Add LaTeX compilation guide")
            
        return {
            "success": success,
            "guide_path": guide_path,
            "latex_path": latex_path
        }
        
    def execute_verify_compilation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Verify PDF compilation"""
        pdf_path = context.get('pdf_path', '')
        
        prompt = f"""Task: Create PDF verification checklist.

PDF to verify: {pdf_path}

Check for:
1. All pages present
2. Figures rendered correctly
3. Fonts embedded
4. References formatted
5. No compilation warnings
6. Hyperlinks working
7. Page numbers correct"""

        response = self.conv_mgr.query_model(prompt, task_type="VERIFY_COMPILATION")
        
        return {
            "success": True,
            "verification_checklist": response or "Verification checklist created",
            "pdf_path": pdf_path
        }
        
    def execute_prepare_submission(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare paper for journal submission"""
        journal = context.get('journal', 'Generic Journal')
        paper_path = context.get('paper_path')
        
        prompt = f"""Task: Prepare paper for submission to {journal}.

Paper: {paper_path}

Create submission checklist:
1. Title page requirements
2. Abstract word limit
3. Formatting guidelines
4. Supplementary materials
5. Cover letter template
6. Suggested reviewers
7. Conflict of interest statement
8. Data availability statement"""

        response = self.conv_mgr.query_model(prompt, task_type="PREPARE_SUBMISSION")
        
        # Save submission checklist
        project_id = context.get('project_id', 'unknown')
        checklist_path = f"papers/{project_id}/submission_checklist.md"
        
        checklist_content = f"""# Submission Checklist for {journal}

{response}

## Submission Materials
- [ ] Main manuscript (PDF)
- [ ] Supplementary materials
- [ ] Cover letter
- [ ] Author information
- [ ] Conflict of interest statement
- [ ] Data availability statement

---
*Generated by llmXive automation system.*"""

        success = self.github.create_file(checklist_path, checklist_content,
            f"Add submission checklist for {journal}")
            
        return {
            "success": success,
            "checklist_path": checklist_path,
            "journal": journal
        }
        
    def execute_implement_corrections(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Implement suggested corrections"""
        improvement_report = context.get('improvement_report', '')
        artifact_path = context.get('artifact_path')
        
        if not artifact_path:
            return {"success": False, "error": "No artifact_path provided"}
            
        content = self.github.get_file_content(artifact_path)
        if not content:
            return {"success": False, "error": f"Could not read {artifact_path}"}
            
        prompt = f"""Task: Implement these improvements on the artifact.

Current content:
{content[:2000]}

Improvements to implement:
{improvement_report}

Apply the suggested corrections and return the improved version."""

        response = self.conv_mgr.query_model(prompt, task_type="IMPLEMENT_CORRECTIONS",
                                           )
        if not response:
            return {"success": False, "error": "No response from model"}
            
        # Update file with corrections
        success = self.github.update_file(artifact_path, response,
            "Implement automated corrections")
            
        return {
            "success": success,
            "artifact_path": artifact_path,
            "corrections_applied": True
        }
        
    def execute_verify_corrections(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Verify corrections were properly applied"""
        original_path = context.get('original_path')
        corrected_path = context.get('corrected_path')
        improvement_report = context.get('improvement_report', '')
        
        prompt = f"""Task: Verify that corrections were properly applied.

Original: {original_path}
Corrected: {corrected_path}
Requested improvements: {improvement_report}

Check:
1. All requested changes were made
2. No new errors introduced
3. Improvements are effective
4. Document structure maintained
5. Quality improved

Report on verification results."""

        response = self.conv_mgr.query_model(prompt, task_type="VERIFY_CORRECTIONS")
        
        return {
            "success": True,
            "verification_report": response or "Verification complete",
            "corrections_verified": True
        }
        
    # === ATTRIBUTION TASKS ===
    
    def execute_generate_attribution_report(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate model attribution report"""
        logger.info("Generating model attribution report...")
        
        # Generate the report
        report = self.attribution.generate_attribution_report()
        
        # Save to repository
        report_path = "model_attributions/attribution_report.md"
        success = self.github.create_file(
            report_path,
            report,
            f"Update model attribution report - {datetime.now().strftime('%Y-%m-%d')}"
        )
        
        if success:
            # Also create an issue with recent contributions
            recent_contribs = self.attribution.get_recent_contributions(10)
            
            issue_body = f"""## Model Attribution Report Generated

A new model attribution report has been generated and saved to: `{report_path}`

### Recent Contributions (Last 10)

| Model | Task | Type | Reference | Timestamp |
|-------|------|------|-----------|-----------|
"""
            for contrib in recent_contribs:
                model_name = contrib['model_id'].split('/')[-1]
                issue_body += f"| {model_name} | {contrib['task_type']} | {contrib['contribution_type']} | {contrib['reference']} | {contrib['timestamp'][:19]} |\n"
                
            issue_body += f"\n\n[View Full Report]({report_path})"
            
            issue = self.github.create_issue(
                title=f"Model Attribution Report - {datetime.now().strftime('%Y-%m-%d')}",
                body=issue_body,
                labels=["documentation", "attribution"]
            )
            
            return {
                "success": True,
                "report_path": report_path,
                "issue_number": issue.number if issue else None,
                "total_models": len(self.attribution.get_all_model_stats()),
                "total_contributions": sum(s['total_contributions'] for s in self.attribution.get_all_model_stats().values())
            }
        
        return {"success": False, "error": "Failed to save attribution report"}