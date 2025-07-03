"""Prompt engineering system for efficient context presentation"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class PromptContext:
    """Context information for prompt building"""
    task_type: str
    project_state: Dict[str, List[Dict]]
    repository_instructions: Dict[str, str]
    recent_activity: List[Dict]
    constraints: Dict[str, Any]


class PromptTemplate(ABC):
    """Abstract base class for prompt templates"""
    
    @abstractmethod
    def build(self, context: PromptContext) -> str:
        """Build prompt from context"""
        pass


class PromptBuilder:
    """Efficiently builds prompts for different task types"""
    
    def __init__(self, max_context_length: int = 4096):
        """
        Initialize prompt builder
        
        Args:
            max_context_length: Maximum prompt length in tokens (approximate)
        """
        self.max_context_length = max_context_length
        self.instruction_cache = {}
        self.templates = self._initialize_templates()
        
    def build_task_prompt(self, task_type: str, context: Dict[str, Any]) -> str:
        """
        Build optimized prompt for a specific task
        
        Args:
            task_type: Type of task to perform
            context: Task-specific context information
            
        Returns:
            Formatted prompt string
        """
        # Create prompt context
        prompt_context = PromptContext(
            task_type=task_type,
            project_state=context.get("project_state", {}),
            repository_instructions=self._get_cached_instructions(),
            recent_activity=context.get("recent_activity", []),
            constraints=context.get("constraints", {})
        )
        
        # Get appropriate template
        template = self.templates.get(task_type, self.templates["default"])
        
        # Build prompt
        prompt = template.build(prompt_context)
        
        # Truncate if needed
        if len(prompt) > self.max_context_length * 4:  # Rough char to token estimate
            prompt = self._truncate_prompt(prompt)
            
        return prompt
    
    def _initialize_templates(self) -> Dict[str, PromptTemplate]:
        """Initialize task-specific prompt templates"""
        return {
            "brainstorm_ideas": BrainstormIdeasTemplate(),
            "develop_technical_design": TechnicalDesignTemplate(),
            "write_review": ReviewTemplate(),
            "implement_research": ImplementationTemplate(),
            "generate_paper": PaperGenerationTemplate(),
            "validate_references": ReferenceValidationTemplate(),
            "default": DefaultTemplate()
        }
    
    def _get_cached_instructions(self) -> Dict[str, str]:
        """Get cached repository instructions"""
        if not self.instruction_cache:
            self.instruction_cache = {
                "overview": self._compress_text(REPOSITORY_OVERVIEW),
                "workflow": self._compress_text(WORKFLOW_INSTRUCTIONS),
                "standards": self._compress_text(QUALITY_STANDARDS)
            }
        return self.instruction_cache
    
    def _compress_text(self, text: str) -> str:
        """Compress text while maintaining key information"""
        # Simple compression - remove extra whitespace and redundancy
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)
    
    def _truncate_prompt(self, prompt: str) -> str:
        """Truncate prompt to fit context window"""
        # Keep beginning and end, truncate middle
        target_length = self.max_context_length * 4
        if len(prompt) <= target_length:
            return prompt
            
        keep_start = int(target_length * 0.7)
        keep_end = int(target_length * 0.25)
        
        return (
            prompt[:keep_start] +
            "\n\n[... context truncated for length ...]\n\n" +
            prompt[-keep_end:]
        )


class BrainstormIdeasTemplate(PromptTemplate):
    """Template for brainstorming new research ideas"""
    
    def build(self, context: PromptContext) -> str:
        backlog_count = len(context.project_state.get("Backlog", []))
        recent_ideas = context.project_state.get("Backlog", [])[-5:]
        
        return f"""You are an AI research scientist working on the llmXive project.

TASK: Generate novel, creative research ideas for the project backlog.

CONTEXT:
- Current backlog size: {backlog_count} ideas
- Project focuses on: large language models, cognitive science, neuroscience, psychology, computational neuroscience, and education

RECENT IDEAS (avoid repetition):
{self._format_recent_ideas(recent_ideas)}

REQUIREMENTS:
1. Generate 3-5 highly creative, cutting-edge research ideas
2. Each idea should be interdisciplinary and novel
3. Ideas must be technically feasible but intellectually ambitious
4. Include a brief description and key research questions
5. Format as GitHub issue title and body

OUTPUT FORMAT:
For each idea, provide:
- Title: [Concise, descriptive title]
- Body: [Detailed description with research questions and approach]

Be bold, creative, and push the boundaries of current science!"""
    
    def _format_recent_ideas(self, ideas: List[Dict]) -> str:
        if not ideas:
            return "No recent ideas"
        return "\n".join([f"- {idea['title']}" for idea in ideas])


class TechnicalDesignTemplate(PromptTemplate):
    """Template for developing technical design documents"""
    
    def build(self, context: PromptContext) -> str:
        issue = context.constraints.get("target_issue", {})
        
        return f"""You are developing a technical design document for the llmXive project.

TASK: Create a comprehensive technical design for the following research idea.

IDEA:
Title: {issue.get('title', 'Unknown')}
Description: {issue.get('body', 'No description')}

DESIGN DOCUMENT REQUIREMENTS:
1. Project Overview (2-3 paragraphs)
2. Research Questions and Hypotheses
3. Methodology
   - Theoretical framework
   - Implementation approach
   - Evaluation metrics
4. Technical Architecture
   - System components
   - Data requirements
   - Computational requirements
5. Expected Outcomes
6. Risk Assessment
7. Timeline and Milestones

GUIDELINES:
- Be specific and technically detailed
- Include concrete implementation steps
- Consider computational constraints
- Suggest evaluation criteria
- Maintain scientific rigor

Generate a complete technical design document in markdown format."""


class ReviewTemplate(PromptTemplate):
    """Template for writing reviews"""
    
    def build(self, context: PromptContext) -> str:
        document = context.constraints.get("document_content", "")
        doc_type = context.constraints.get("document_type", "design")
        
        return f"""You are a peer reviewer for the llmXive project.

TASK: Provide a thorough review of the following {doc_type} document.

DOCUMENT:
{document[:2000]}... [truncated if needed]

REVIEW REQUIREMENTS:
1. Summary (1-2 paragraphs)
2. Strengths (3-5 points)
3. Weaknesses (3-5 points)
4. Specific Suggestions for Improvement
5. Overall Assessment (Accept/Revise/Reject)
6. Score: 0.5 points (as an LLM reviewer)

REVIEW CRITERIA:
- Scientific rigor and validity
- Technical feasibility
- Novelty and innovation
- Clarity and completeness
- Potential impact

Be constructive, specific, and maintain high standards."""


class ImplementationTemplate(PromptTemplate):
    """Template for implementing research code"""
    
    def build(self, context: PromptContext) -> str:
        design = context.constraints.get("design_document", "")
        
        return f"""You are implementing research code for the llmXive project.

TASK: Create a minimal viable implementation based on the technical design.

DESIGN SUMMARY:
{design[:1500]}... [truncated if needed]

IMPLEMENTATION REQUIREMENTS:
1. Core functionality only (MVP)
2. Clean, well-documented Python code
3. Modular design with clear interfaces
4. Basic unit tests
5. README with usage instructions

CODE STRUCTURE:
- Main implementation module
- Helper functions
- Configuration handling
- Basic CLI interface
- Test suite

OUTPUT FORMAT:
Provide complete Python code files with appropriate structure.
Focus on correctness and clarity over optimization."""


class PaperGenerationTemplate(PromptTemplate):
    """Template for generating research papers"""
    
    def build(self, context: PromptContext) -> str:
        results = context.constraints.get("results", {})
        references = context.constraints.get("references", [])
        
        return f"""You are writing a research paper for the llmXive project.

TASK: Generate a complete research paper based on the provided results.

PAPER STRUCTURE:
1. Abstract (150-250 words)
2. Introduction
3. Methods
4. Results
5. Discussion
6. References

RESULTS SUMMARY:
{json.dumps(results, indent=2)[:1000]}... [truncated if needed]

REQUIREMENTS:
- Follow standard academic paper format
- Include all sections listed above
- Cite relevant work appropriately
- Maintain scientific writing standards
- Generate LaTeX format output

IMPORTANT:
- Do NOT hallucinate results or references
- All claims must be supported by provided data
- Mark any gaps that need human verification

Generate the complete paper in LaTeX format."""


class ReferenceValidationTemplate(PromptTemplate):
    """Template for validating references"""
    
    def build(self, context: PromptContext) -> str:
        references = context.constraints.get("references", [])
        
        return f"""You are validating references for the llmXive project.

TASK: Verify the following references and flag any issues.

REFERENCES TO VALIDATE:
{self._format_references(references)}

VALIDATION CHECKLIST:
1. Does the reference appear to be real?
2. Are authors, title, venue, and year plausible?
3. Is the citation format correct?
4. Any obvious errors or inconsistencies?

For each reference, provide:
- Status: VALID / SUSPICIOUS / INVALID
- Reason: Brief explanation if not valid
- Suggested correction if applicable

Be thorough but reasonable in your assessment."""
    
    def _format_references(self, references: List[str]) -> str:
        if not references:
            return "No references provided"
        return "\n".join([f"{i+1}. {ref}" for i, ref in enumerate(references[:20])])


class DefaultTemplate(PromptTemplate):
    """Default template for unspecified tasks"""
    
    def build(self, context: PromptContext) -> str:
        return f"""You are an AI assistant working on the llmXive project.

TASK: {context.task_type}

PROJECT CONTEXT:
{json.dumps(context.project_state, indent=2)[:1000]}

Please complete the requested task following llmXive guidelines and maintaining high quality standards.

Be specific, thorough, and scientifically rigorous in your response."""


# Repository instruction constants
REPOSITORY_OVERVIEW = """
llmXive is an automated system for scientific discovery driven by LLMs.
The project uses a board with columns: Backlog, Ready, In Progress, In Review, Done.
Ideas progress through stages based on review scores (LLM: 0.5 points, Human: 1 point).
10 points required to advance between major stages.
"""

WORKFLOW_INSTRUCTIONS = """
1. Backlog: Brainstorm and develop ideas
2. Ready: Ideas with approved technical designs (10+ points)
3. In Progress: Active implementation and paper writing
4. In Review: Completed work under review
5. Done: Finished projects with published papers
"""

QUALITY_STANDARDS = """
- All references must be validated
- Code must be tested and documented
- Papers follow standard academic format
- Maintain scientific rigor throughout
- No hallucinated results or citations
"""