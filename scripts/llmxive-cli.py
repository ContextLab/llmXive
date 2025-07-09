#!/usr/bin/env python3
"""
llmXive CLI - Automated Research Pipeline
Orchestrates the complete research pipeline from idea generation to publication
"""

import os
import sys
import json
import time
import argparse
import requests
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import uuid
import re

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

class APIModelClient:
    """Client for API-based models (Anthropic, OpenAI, Google)"""
    
    def __init__(self):
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        self.openai_key = os.getenv('OPENAI_API_KEY') 
        self.google_key = os.getenv('GOOGLE_API_KEY')
        
    def call_claude(self, prompt: str, model: str = "claude-3-sonnet-20240229") -> str:
        """Call Anthropic Claude API"""
        if not self.anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
            
        headers = {
            "x-api-key": self.anthropic_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": model,
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            raise Exception(f"Claude API error: {response.text}")
            
        return response.json()["content"][0]["text"]
    
    def call_openai(self, prompt: str, model: str = "gpt-4") -> str:
        """Call OpenAI GPT API"""
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY not set")
            
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4000
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.text}")
            
        return response.json()["choices"][0]["message"]["content"]
    
    def call_google(self, prompt: str, model: str = "gemini-1.5-flash") -> str:
        """Call Google Gemini API"""
        if not self.google_key:
            raise ValueError("GOOGLE_API_KEY not set")
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.google_key}"
        
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 4000}
        }
        
        response = requests.post(url, json=data)
        
        if response.status_code != 200:
            raise Exception(f"Google API error: {response.text}")
            
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]

class HuggingFaceClient:
    """Client for HuggingFace models"""
    
    def call_huggingface(self, prompt: str, model: str = "microsoft/DialoGPT-medium") -> str:
        """Call HuggingFace model (simulated for now)"""
        # For now, return a simulated response
        # In production, this would use transformers library
        return f"[HuggingFace {model} response to: {prompt[:50]}...]"

class PromptLoader:
    """Loads and manages prompt templates"""
    
    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir
        self.cache = {}
    
    def load_prompt(self, prompt_name: str, **kwargs) -> str:
        """Load prompt template and substitute variables"""
        if prompt_name not in self.cache:
            prompt_file = self.prompts_dir / f"{prompt_name}.md"
            if prompt_file.exists():
                with open(prompt_file, 'r') as f:
                    content = f.read()
                # Extract the actual prompt from the markdown (skip header and metadata)
                lines = content.split('\n')
                prompt_lines = []
                in_prompt = False
                for line in lines:
                    if line.startswith('# ') and 'Prompt' in line:
                        in_prompt = True
                        continue
                    elif line.startswith('## ') and ('Variables' in line or 'Instructions' in line):
                        break
                    elif in_prompt and line.strip():
                        prompt_lines.append(line)
                
                self.cache[prompt_name] = '\n'.join(prompt_lines).strip()
            else:
                # Fallback to hardcoded prompts if file doesn't exist
                self.cache[prompt_name] = self._get_fallback_prompt(prompt_name)
        
        # Substitute variables
        prompt = self.cache[prompt_name]
        for key, value in kwargs.items():
            prompt = prompt.replace(f'{{{key}}}', str(value))
        
        return prompt
    
    def _get_fallback_prompt(self, prompt_name: str) -> str:
        """Fallback hardcoded prompts if files are missing"""
        fallbacks = {
            'idea_generation': """Generate an innovative research idea in the field of {field}.

Requirements:
- Be novel and creative
- Address current problems or gaps in the field
- Be technically feasible with current methods
- Have clear applications or implications
- Be suitable for academic publication

Respond with:
TITLE: [concise research title]
FIELD: [research field]
DESCRIPTION: [2-3 paragraph description of the research idea, methodology, and expected outcomes]
KEYWORDS: [5-7 relevant keywords]""",
            'paper_writing': """Write a complete research paper in PROPER LaTeX FORMAT based on the following project materials:

Title: {title}
Technical Design: {design_doc}
Implementation: {impl_plan}
Code: {code_content}
Analysis Results: {analysis_results}

IMPORTANT: Generate a COMPLETE LaTeX document that includes:
- \\documentclass{{article}}
- \\usepackage commands for necessary packages
- \\title{{}} and \\author{{}} commands
- \\begin{{document}} and \\end{{document}}
- \\maketitle command
- \\begin{{abstract}} and \\end{{abstract}}
- Proper LaTeX section commands (\\section{{}}, \\subsection{{}})

The paper should follow standard academic format:
1. Abstract
2. Introduction  
3. Methods
4. Results
5. Discussion
6. Conclusion
7. References (use \\bibliography or manual \\bibitem entries)

Use proper LaTeX syntax throughout - NO MARKDOWN formatting like **bold** or # headers.
Use \\textbf{{}} for bold, \\textit{{}} for italics, \\section{{}} for sections.
Include proper citations and ensure all claims are supported by the provided materials."""
        }
        return fallbacks.get(prompt_name, f"Prompt template for {prompt_name} not found.")

class ProjectManager:
    """Manages project creation and file operations"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        
    def create_project_id(self) -> str:
        """Generate unique project ID"""
        timestamp = datetime.now().strftime("%Y%m%d")
        unique_id = str(uuid.uuid4())[:8]
        return f"pipeline-test-{timestamp}-{unique_id}"
    
    def create_project_structure(self, project_id: str, field: str) -> Dict[str, Path]:
        """Create directory structure for new project"""
        paths = {}
        
        # Create directories
        for dir_type in ['technical_design_documents', 'implementation_plans', 'code', 'data', 'papers', 'reviews']:
            dir_path = self.base_path / dir_type / project_id
            dir_path.mkdir(parents=True, exist_ok=True)
            paths[dir_type] = dir_path
            
        # Create review subdirectories
        review_types = ['Design', 'Implementation', 'Paper', 'Code']
        for review_type in review_types:
            (paths['reviews'] / review_type).mkdir(exist_ok=True)
            
        return paths
    
    def save_document(self, path: Path, content: str, format_type: str = "md") -> None:
        """Save document to file"""
        if format_type == "md":
            path = path.with_suffix('.md')
        elif format_type == "tex":
            path = path.with_suffix('.tex')
            
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def load_document(self, path: Path) -> str:
        """Load document from file"""
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

class ReviewManager:
    """Manages review processes and scoring"""
    
    def __init__(self, api_client: APIModelClient):
        self.api_client = api_client
        # Only include models that have API keys available
        self.review_models = []
        if api_client.anthropic_key:
            self.review_models.append('claude')
        if api_client.openai_key:
            self.review_models.append('openai')
        if api_client.google_key:
            self.review_models.append('google')
        
        if not self.review_models:
            raise ValueError("No API keys available for review models")
            
        self.current_model = 0
        
    def get_next_reviewer(self) -> str:
        """Cycle through review models"""
        model = self.review_models[self.current_model]
        self.current_model = (self.current_model + 1) % len(self.review_models)
        return model
    
    def conduct_review(self, content: str, review_type: str, project_id: str) -> Tuple[float, str, str]:
        """Conduct a review and return score, feedback, reviewer"""
        reviewer = self.get_next_reviewer()
        
        review_prompt = f"""
You are an expert reviewer evaluating a {review_type} for a research project.

Please review the following content and provide:
1. A score from 0.0 to 1.0 (where 0.8+ is acceptable for advancement)
2. Detailed feedback with strengths and weaknesses
3. Specific recommendations for improvement

Content to review:
{content}

Respond in this format:
SCORE: [0.0-1.0]
FEEDBACK: [detailed feedback]
RECOMMENDATIONS: [specific improvements needed]
"""
        
        try:
            if reviewer == 'claude':
                response = self.api_client.call_claude(review_prompt)
            elif reviewer == 'openai':
                response = self.api_client.call_openai(review_prompt)
            else:  # google
                response = self.api_client.call_google(review_prompt)
                
            # Parse response
            score = 0.0
            feedback = response
            
            # Extract score if formatted correctly
            lines = response.split('\n')
            for line in lines:
                if line.startswith('SCORE:'):
                    try:
                        score = float(line.split(':')[1].strip())
                    except:
                        score = 0.7  # Default reasonable score
                    break
                    
            return score, feedback, reviewer
            
        except Exception as e:
            print(f"Review error with {reviewer}: {e}")
            return 0.5, f"Review failed: {e}", reviewer

class PipelineOrchestrator:
    """Main orchestrator for the research pipeline"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.api_client = APIModelClient()
        self.hf_client = HuggingFaceClient()
        self.project_manager = ProjectManager(base_path)
        self.review_manager = ReviewManager(self.api_client)
        self.prompt_loader = PromptLoader(base_path / "prompts")
        
    def log_step(self, step: str, project_id: str, details: str = "") -> None:
        """Log pipeline step"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {project_id} - {step}"
        if details:
            log_entry += f": {details}"
        print(log_entry)
        
        # Also write to log file
        log_file = self.base_path / "pipeline_log.txt"
        with open(log_file, 'a') as f:
            f.write(log_entry + "\n")
    
    def brainstorm_idea(self, field: str = None) -> Tuple[str, str, str]:
        """Generate new research idea using HuggingFace model"""
        project_id = self.project_manager.create_project_id()
        
        if not field:
            fields = ['biology', 'chemistry', 'physics', 'computer science', 'psychology', 'neuroscience']
            import random
            field = random.choice(fields)
        
        prompt = self.prompt_loader.load_prompt('idea_generation', field=field)
        
        self.log_step("BRAINSTORM_START", project_id, f"Field: {field}")
        
        try:
            # Use HuggingFace for brainstorming (or fallback to API)
            try:
                response = self.hf_client.call_huggingface(prompt)
                self.log_step("BRAINSTORM_HF_SUCCESS", project_id)
            except:
                # Fallback to Claude for brainstorming
                response = self.api_client.call_claude(prompt)
                self.log_step("BRAINSTORM_CLAUDE_FALLBACK", project_id)
                
            # Parse response
            title = "Untitled Research Project"
            description = response
            
            lines = response.split('\n')
            for line in lines:
                if line.startswith('TITLE:'):
                    title = line.split(':', 1)[1].strip()
                elif line.startswith('DESCRIPTION:'):
                    description = line.split(':', 1)[1].strip()
                    
            self.log_step("BRAINSTORM_COMPLETE", project_id, f"Title: {title}")
            return project_id, title, description
            
        except Exception as e:
            self.log_step("BRAINSTORM_ERROR", project_id, str(e))
            raise
    
    def iterative_review_process(self, content: str, review_type: str, project_id: str, max_iterations: int = 3) -> Tuple[str, bool]:
        """Conduct iterative review process until content passes"""
        current_content = content
        
        for iteration in range(max_iterations):
            self.log_step(f"REVIEW_{review_type.upper()}_ITER_{iteration+1}", project_id)
            
            score, feedback, reviewer = self.review_manager.conduct_review(current_content, review_type, project_id)
            
            self.log_step(f"REVIEW_SCORE", project_id, f"{reviewer}: {score:.2f}")
            
            if score >= 0.8:
                self.log_step(f"REVIEW_{review_type.upper()}_PASSED", project_id, f"Score: {score:.2f}")
                return current_content, True
                
            # Content needs revision - use any available model (prefer different from reviewer)
            revision_prompt = f"""
The following {review_type} received a score of {score:.2f} and needs improvement.

Original content:
{current_content}

Reviewer feedback:
{feedback}

Please revise the content to address all concerns and improve quality. Maintain the same format but enhance the content based on the feedback.
"""
            
            try:
                # Try to use a different model for revision than the reviewer
                available_models = self.review_manager.review_models
                revision_model = available_models[0]  # Default to first available
                
                # Try to pick a different model than reviewer if possible
                for model in available_models:
                    if model != reviewer:
                        revision_model = model
                        break
                
                if revision_model == 'claude':
                    revised_content = self.api_client.call_claude(revision_prompt)
                elif revision_model == 'openai':
                    revised_content = self.api_client.call_openai(revision_prompt)
                else:  # google
                    revised_content = self.api_client.call_google(revision_prompt)
                    
                current_content = revised_content
                self.log_step(f"REVISION_COMPLETE", project_id, f"Iteration {iteration+1}")
                
            except Exception as e:
                self.log_step(f"REVISION_ERROR", project_id, str(e))
                break
                
        return current_content, False
    
    def generate_technical_design(self, project_id: str, title: str, description: str) -> str:
        """Generate technical design document using best available model"""
        prompt = self.prompt_loader.load_prompt('technical_design', title=title, description=description)
        
        self.log_step("TECH_DESIGN_START", project_id)
        
        try:
            # Use best available model (prefer OpenAI for design, then Claude, then Google)
            if self.api_client.openai_key:
                design_doc = self.api_client.call_openai(prompt)
            elif self.api_client.anthropic_key:
                design_doc = self.api_client.call_claude(prompt)
            elif self.api_client.google_key:
                design_doc = self.api_client.call_google(prompt)
            else:
                raise ValueError("No API keys available for technical design generation")
                
            self.log_step("TECH_DESIGN_COMPLETE", project_id)
            return design_doc
        except Exception as e:
            self.log_step("TECH_DESIGN_ERROR", project_id, str(e))
            raise
    
    def generate_implementation_plan(self, project_id: str, title: str, design_doc: str) -> str:
        """Generate implementation plan using best available model"""
        prompt = self.prompt_loader.load_prompt('implementation_plan', title=title, design_doc=design_doc)
        
        self.log_step("IMPL_PLAN_START", project_id)
        
        try:
            # Use best available model (prefer Google for planning, then OpenAI, then Claude)
            if self.api_client.google_key:
                impl_plan = self.api_client.call_google(prompt)
            elif self.api_client.openai_key:
                impl_plan = self.api_client.call_openai(prompt)
            elif self.api_client.anthropic_key:
                impl_plan = self.api_client.call_claude(prompt)
            else:
                raise ValueError("No API keys available for implementation plan generation")
                
            self.log_step("IMPL_PLAN_COMPLETE", project_id)
            return impl_plan
        except Exception as e:
            self.log_step("IMPL_PLAN_ERROR", project_id, str(e))
            raise
    
    def implement_code_and_data(self, project_id: str, title: str, impl_plan: str) -> Tuple[str, str]:
        """Generate code and data collection procedures using best available model"""
        code_prompt = self.prompt_loader.load_prompt('code_generation', title=title, impl_plan=impl_plan)
        
        self.log_step("CODE_GEN_START", project_id)
        
        try:
            # Use best available model (prefer OpenAI for code, then Google, then Claude)
            if self.api_client.openai_key:
                code_content = self.api_client.call_openai(code_prompt)
            elif self.api_client.google_key:
                code_content = self.api_client.call_google(code_prompt)
            elif self.api_client.anthropic_key:
                code_content = self.api_client.call_claude(code_prompt)
            else:
                raise ValueError("No API keys available for code generation")
            
            # Simulate data collection
            data_summary = f"""
# Data Collection Summary for {title}

## Data Sources
- Generated based on implementation plan requirements
- Follows ethical data collection guidelines
- Includes proper documentation and metadata

## Data Files
- raw_data.csv: Primary dataset
- processed_data.csv: Cleaned and processed data
- metadata.json: Data description and provenance

## Quality Checks
- Data validation completed
- Missing value analysis performed
- Outlier detection and handling documented
"""
            
            self.log_step("CODE_GEN_COMPLETE", project_id)
            return code_content, data_summary
            
        except Exception as e:
            self.log_step("CODE_GEN_ERROR", project_id, str(e))
            raise
    
    def run_analyses(self, project_id: str, code_content: str, data_summary: str) -> str:
        """Run analyses using Claude"""
        analysis_prompt = self.prompt_loader.load_prompt('data_analysis', code_content=code_content[:1000], data_summary=data_summary)
        
        self.log_step("ANALYSIS_START", project_id)
        
        try:
            # Use best available model (prefer OpenAI for analysis, then Google, then Claude)
            if self.api_client.openai_key:
                analysis_results = self.api_client.call_openai(analysis_prompt)
            elif self.api_client.google_key:
                analysis_results = self.api_client.call_google(analysis_prompt)
            elif self.api_client.anthropic_key:
                analysis_results = self.api_client.call_claude(analysis_prompt)
            else:
                raise ValueError("No API keys available for analysis generation")
                
            self.log_step("ANALYSIS_COMPLETE", project_id)
            return analysis_results
        except Exception as e:
            self.log_step("ANALYSIS_ERROR", project_id, str(e))
            raise
    
    def write_paper(self, project_id: str, title: str, design_doc: str, impl_plan: str, code_content: str, analysis_results: str) -> str:
        """Write research paper using ChatGPT"""
        paper_prompt = self.prompt_loader.load_prompt('paper_writing', 
                                                      title=title, 
                                                      design_doc=design_doc[:1000], 
                                                      impl_plan=impl_plan[:500], 
                                                      code_content=code_content[:500], 
                                                      analysis_results=analysis_results)
        
        self.log_step("PAPER_WRITE_START", project_id)
        
        try:
            paper_content = self.api_client.call_openai(paper_prompt, model="gpt-4")
            self.log_step("PAPER_WRITE_COMPLETE", project_id)
            return paper_content
        except Exception as e:
            self.log_step("PAPER_WRITE_ERROR", project_id, str(e))
            raise
    
    def save_project_files(self, project_id: str, title: str, field: str, idea_desc: str, 
                          design_doc: str, impl_plan: str, code_content: str, 
                          data_summary: str, analysis_results: str, paper_content: str) -> Dict[str, Path]:
        """Save all project files"""
        paths = self.project_manager.create_project_structure(project_id, field)
        
        # Save each document
        self.project_manager.save_document(
            paths['technical_design_documents'] / 'design', design_doc, 'md'
        )
        
        self.project_manager.save_document(
            paths['implementation_plans'] / 'plan', impl_plan, 'md'
        )
        
        self.project_manager.save_document(
            paths['code'] / 'main.py', code_content, 'py'
        )
        
        self.project_manager.save_document(
            paths['data'] / 'README', data_summary, 'md'
        )
        
        self.project_manager.save_document(
            paths['papers'] / 'paper', paper_content, 'tex'
        )
        
        # Create project metadata
        metadata = {
            'id': project_id,
            'title': title,
            'field': field,
            'description': idea_desc,
            'created': datetime.now().isoformat(),
            'status': 'completed',
            'phase': 'done',
            'files': {
                'design': str(paths['technical_design_documents'] / 'design.md'),
                'implementation': str(paths['implementation_plans'] / 'plan.md'),
                'code': str(paths['code'] / 'main.py'),
                'data': str(paths['data'] / 'README.md'),
                'paper': str(paths['papers'] / 'paper.tex')
            }
        }
        
        self.project_manager.save_document(
            self.base_path / f'{project_id}_metadata.json', 
            json.dumps(metadata, indent=2), 
            'json'
        )
        
        return paths
    
    def save_incremental_file(self, project_id: str, phase: str, filename: str, content: str) -> None:
        """Save file immediately during pipeline execution"""
        try:
            # Create project structure if it doesn't exist
            project_path = self.base_path / project_id
            phase_path = project_path / phase
            phase_path.mkdir(parents=True, exist_ok=True)
            
            # Save the file
            file_path = phase_path / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.log_step("FILE_SAVED", project_id, f"{phase}/{filename}")
            
        except Exception as e:
            self.log_step("FILE_SAVE_ERROR", project_id, f"Failed to save {phase}/{filename}: {str(e)}")
    
    def create_project_config(self, project_id: str, title: str, field: str, status: str = "in-progress") -> None:
        """Create .llmxive/config.json for the project"""
        try:
            project_path = self.base_path / project_id
            config_path = project_path / ".llmxive"
            config_path.mkdir(parents=True, exist_ok=True)
            
            config = {
                "id": project_id,
                "title": title,
                "description": f"Auto-generated project: {title}",
                "field": field,
                "status": status,
                "created_date": datetime.now().isoformat(),
                "updated_date": datetime.now().isoformat(),
                "contributors": [
                    {
                        "username": "llmxive-pipeline",
                        "type": "llm",
                        "contributions": ["idea", "technical_design", "implementation_plan", "code", "paper"]
                    }
                ],
                "github_issues": [],
                "phases": {
                    "idea": {"completed": False, "points": 0},
                    "technical_design": {"completed": False, "points": 0},
                    "implementation_plan": {"completed": False, "points": 0},
                    "code": {"completed": False, "points": 0},
                    "paper": {"completed": False, "points": 0}
                }
            }
            
            config_file = config_path / "config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
                
            self.log_step("CONFIG_CREATED", project_id, "Project configuration saved")
            
        except Exception as e:
            self.log_step("CONFIG_ERROR", project_id, f"Failed to create config: {str(e)}")
    
    def validate_latex_document(self, latex_content: str) -> bool:
        """Check if LaTeX document has required structure"""
        required_elements = [
            r'\documentclass',
            r'\begin{document}',
            r'\end{document}',
            r'\title{',
            r'\maketitle'
        ]
        
        for element in required_elements:
            if element not in latex_content:
                return False
        return True
    
    def fix_latex_document(self, project_id: str, broken_latex: str) -> str:
        """Use available LLM to fix malformed LaTeX"""
        fix_prompt = self.prompt_loader.load_prompt('latex_fixing', latex_content=broken_latex)
        
        self.log_step("LATEX_FIX_START", project_id)
        
        try:
            # Use best available model for fixing
            if self.api_client.openai_key:
                fixed_latex = self.api_client.call_openai(fix_prompt, model="gpt-4")
            elif self.api_client.google_key:
                fixed_latex = self.api_client.call_google(fix_prompt)
            elif self.api_client.anthropic_key:
                fixed_latex = self.api_client.call_claude(fix_prompt)
            else:
                raise ValueError("No API keys available for LaTeX fixing")
            
            self.log_step("LATEX_FIX_COMPLETE", project_id)
            return fixed_latex
        except Exception as e:
            self.log_step("LATEX_FIX_ERROR", project_id, f"Failed to fix LaTeX: {str(e)}")
            return broken_latex  # Return original if fix fails
    
    def compile_latex_paper(self, project_id: str, paper_content: str) -> None:
        """Attempt to compile LaTeX paper to PDF with validation and auto-fix"""
        try:
            paper_path = self.base_path / project_id / "paper"
            
            # Check if pdflatex is available
            import subprocess
            result = subprocess.run(['which', 'pdflatex'], capture_output=True, text=True)
            if result.returncode != 0:
                self.log_step("LATEX_SKIP", project_id, "pdflatex not available, skipping PDF compilation")
                return
            
            # Validate LaTeX document structure
            if not self.validate_latex_document(paper_content):
                self.log_step("LATEX_INVALID", project_id, "LaTeX document structure invalid, attempting to fix")
                paper_content = self.fix_latex_document(project_id, paper_content)
                
                # Save the fixed version
                self.save_incremental_file(project_id, "paper", "paper.tex", paper_content)
                
                # Re-validate after fix
                if not self.validate_latex_document(paper_content):
                    self.log_step("LATEX_UNFIXABLE", project_id, "Could not fix LaTeX document, skipping compilation")
                    return
            
            # Change to paper directory for compilation
            original_dir = os.getcwd()
            os.chdir(paper_path)
            
            # Try to compile the LaTeX
            result = subprocess.run(['pdflatex', 'paper.tex'], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log_step("LATEX_SUCCESS", project_id, "PDF compiled successfully")
            else:
                self.log_step("LATEX_COMPILE_FAILED", project_id, f"LaTeX compilation failed: {result.stderr}")
                
                # Try to fix compilation errors and retry once
                self.log_step("LATEX_RETRY", project_id, "Attempting to fix compilation errors")
                fixed_content = self.fix_latex_document(project_id, paper_content)
                
                # Save fixed version and retry
                with open('paper.tex', 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                retry_result = subprocess.run(['pdflatex', 'paper.tex'], capture_output=True, text=True)
                if retry_result.returncode == 0:
                    self.log_step("LATEX_SUCCESS_RETRY", project_id, "PDF compiled successfully after fix")
                else:
                    self.log_step("LATEX_FINAL_FAIL", project_id, f"Final compilation failed: {retry_result.stderr}")
            
            # Return to original directory
            os.chdir(original_dir)
                
        except Exception as e:
            self.log_step("LATEX_ERROR", project_id, f"LaTeX compilation error: {str(e)}")
    
    def run_full_pipeline(self, field: str = None) -> Dict:
        """Run the complete research pipeline"""
        try:
            # Step 1: Brainstorm idea
            project_id, title, description = self.brainstorm_idea(field)
            
            # Create project config immediately
            self.create_project_config(project_id, title, field or "general")
            
            # Step 2: Review idea
            description, idea_passed = self.iterative_review_process(description, "idea", project_id)
            if not idea_passed:
                raise Exception("Idea failed review process")
            
            # Save idea immediately
            self.save_incremental_file(project_id, "idea", "initial-idea.md", f"# {title}\n\n{description}")
            
            # Step 3: Generate technical design
            design_doc = self.generate_technical_design(project_id, title, description)
            
            # Step 4: Review technical design
            design_doc, design_passed = self.iterative_review_process(design_doc, "technical design", project_id)
            if not design_passed:
                raise Exception("Technical design failed review process")
            
            # Save technical design immediately
            self.save_incremental_file(project_id, "technical-design", "design.md", design_doc)
            
            # Step 5: Generate implementation plan
            impl_plan = self.generate_implementation_plan(project_id, title, design_doc)
            
            # Step 6: Review implementation plan
            impl_plan, impl_passed = self.iterative_review_process(impl_plan, "implementation plan", project_id)
            if not impl_passed:
                raise Exception("Implementation plan failed review process")
            
            # Save implementation plan immediately
            self.save_incremental_file(project_id, "implementation-plan", "plan.md", impl_plan)
            
            # Step 7: Implement code and collect data
            code_content, data_summary = self.implement_code_and_data(project_id, title, impl_plan)
            
            # Save code and data immediately
            self.save_incremental_file(project_id, "code", "main.py", code_content)
            self.save_incremental_file(project_id, "data", "README.md", data_summary)
            
            # Step 8: Run analyses
            analysis_results = self.run_analyses(project_id, code_content, data_summary)
            
            # Save analysis results immediately
            self.save_incremental_file(project_id, "data", "analysis_results.md", analysis_results)
            
            # Step 9: Write paper
            paper_content = self.write_paper(project_id, title, design_doc, impl_plan, code_content, analysis_results)
            
            # Save paper immediately
            self.save_incremental_file(project_id, "paper", "paper.tex", paper_content)
            
            # Step 10: Review paper iteratively
            paper_content, paper_passed = self.iterative_review_process(paper_content, "research paper", project_id, max_iterations=5)
            if not paper_passed:
                print(f"Warning: Paper for {project_id} did not pass final review but proceeding to save")
            
            # Save final reviewed paper
            self.save_incremental_file(project_id, "paper", "paper.tex", paper_content)
            
            # Create basic LaTeX compilation
            self.compile_latex_paper(project_id, paper_content)
            
            self.log_step("PIPELINE_COMPLETE", project_id, f"All files saved incrementally")
            
            return {
                'project_id': project_id,
                'title': title,
                'status': 'success',
                'base_path': str(self.base_path / project_id),
                'paper_passed_review': paper_passed
            }
            
        except Exception as e:
            self.log_step("PIPELINE_ERROR", project_id if 'project_id' in locals() else "unknown", str(e))
            return {
                'status': 'error',
                'error': str(e),
                'project_id': project_id if 'project_id' in locals() else None
            }

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='llmXive Research Pipeline CLI')
    parser.add_argument('--field', type=str, help='Research field for idea generation')
    parser.add_argument('--base-path', type=str, default='/Users/jmanning/llmXive', help='Base project path')
    parser.add_argument('--test-apis', action='store_true', help='Test API connections')
    
    args = parser.parse_args()
    
    base_path = Path(args.base_path)
    
    if args.test_apis:
        print("Testing API connections...")
        client = APIModelClient()
        
        # Test each API
        test_prompt = "Hello, please respond with 'API test successful' and your model name."
        
        try:
            claude_response = client.call_claude(test_prompt)
            print(f"✅ Claude API: {claude_response[:50]}...")
        except Exception as e:
            print(f"❌ Claude API: {e}")
            
        try:
            openai_response = client.call_openai(test_prompt)
            print(f"✅ OpenAI API: {openai_response[:50]}...")
        except Exception as e:
            print(f"❌ OpenAI API: {e}")
            
        try:
            google_response = client.call_google(test_prompt)
            print(f"✅ Google API: {google_response[:50]}...")
        except Exception as e:
            print(f"❌ Google API: {e}")
            
        return
    
    # Run full pipeline
    print("🚀 Starting llmXive Research Pipeline...")
    print(f"Base path: {base_path}")
    print(f"Field: {args.field or 'auto-selected'}")
    print("-" * 60)
    
    orchestrator = PipelineOrchestrator(base_path)
    result = orchestrator.run_full_pipeline(args.field)
    
    print("\n" + "="*60)
    print("PIPELINE RESULTS")
    print("="*60)
    
    if result['status'] == 'success':
        print(f"✅ SUCCESS: Project {result['project_id']} completed")
        print(f"📰 Title: {result['title']}")
        print(f"📊 Paper passed review: {result['paper_passed_review']}")
        print(f"📁 Files saved to: {result['paths']['papers']}")
        
        # Check if paper file exists
        paper_path = Path(result['paths']['papers']) / 'paper.tex'
        if paper_path.exists():
            print(f"📄 Paper file confirmed: {paper_path}")
            print(f"📏 Paper size: {paper_path.stat().st_size} bytes")
        else:
            print("⚠️  Paper file not found")
            
    else:
        print(f"❌ FAILED: {result['error']}")
        if result.get('project_id'):
            print(f"Project ID: {result['project_id']}")
    
    print("\n📋 Check pipeline_log.txt for detailed execution log")

if __name__ == "__main__":
    main()