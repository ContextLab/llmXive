#!/usr/bin/env python3
"""
Configurable Pipeline Orchestrator for llmXive
Integrates the YAML-based pipeline configuration with the existing orchestration system
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import existing components
from scripts.pipeline_config_manager import PipelineConfigManager, PipelineState
from scripts.code_execution_manager import CodeExecutionManager

# Import original orchestrator for model clients
try:
    from scripts.llmxive_cli import APIModelClient, PromptLoader, ProjectManager
except ImportError:
    print("Warning: Could not import original orchestrator components")
    APIModelClient = None
    PromptLoader = None
    ProjectManager = None


class ConfigurablePipelineOrchestrator:
    """
    Enhanced pipeline orchestrator that uses YAML configuration
    for flexible pipeline definition and execution
    """
    
    def __init__(self, base_path: Path, config_path: Optional[Path] = None):
        self.base_path = base_path
        self.config_manager = PipelineConfigManager(
            config_path or (base_path / "pipeline_config.yaml"),
            base_path / "pipeline_schema.json"
        )
        
        # Initialize components
        self.api_client = APIModelClient() if APIModelClient else None
        self.prompt_loader = PromptLoader(base_path / "prompts") if PromptLoader else None
        self.project_manager = ProjectManager(base_path) if ProjectManager else None
        self.code_executor = CodeExecutionManager(base_path)
        
        # Load configuration
        self.config = self.config_manager.load_config()
        self.execution_log = []
        
    def run_pipeline(self, field: str = None, project_id: str = None) -> Dict[str, Any]:
        """
        Run the complete configurable pipeline
        """
        start_time = datetime.now()
        
        # Create project ID if not provided
        if not project_id:
            project_id = f"PROJ-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Initialize pipeline state
        self.config_manager.state = PipelineState()
        self.config_manager.state.set_variable('project_id', project_id)
        self.config_manager.state.set_variable('field', field or 'general')
        self.config_manager.state.set_variable('pipeline_start_time', start_time.isoformat())
        
        self.log_step("PIPELINE_START", project_id, f"Starting configurable pipeline with field: {field}")
        
        try:
            # Get execution order
            execution_order = self.config_manager.get_execution_order()
            total_steps = len(execution_order)
            
            self.log_step("EXECUTION_ORDER", project_id, f"Steps: {' -> '.join(execution_order)}")
            
            # Execute each step
            completed_steps = 0
            for step_index, step_name in enumerate(execution_order):
                # Check if step can be executed
                can_execute, reason = self.config_manager.can_execute_step(step_name)
                
                if not can_execute:
                    self.log_step("STEP_SKIPPED", project_id, f"{step_name}: {reason}")
                    continue
                
                # Execute the step
                step_result = self.execute_step(step_name, project_id)
                
                if step_result.get('success', False):
                    # Apply consequences
                    self.config_manager.apply_consequences(step_name, step_result)
                    completed_steps += 1
                    
                    # Update progress
                    progress = (completed_steps / total_steps) * 100
                    self.config_manager.state.set_variable('pipeline_progress', progress)
                    
                    self.log_step("STEP_COMPLETED", project_id, 
                                f"{step_name} completed ({completed_steps}/{total_steps}, {progress:.1f}%)")
                else:
                    # Handle step failure
                    self.config_manager.state.failed_steps.add(step_name)
                    error_msg = step_result.get('error', 'Unknown error')
                    
                    self.log_step("STEP_FAILED", project_id, f"{step_name}: {error_msg}")
                    
                    # Check if pipeline should continue or stop
                    if self.should_stop_on_failure(step_name):
                        self.log_step("PIPELINE_STOPPED", project_id, f"Critical step {step_name} failed")
                        break
                
                # Check for conditional branches
                self.check_conditional_branches(project_id)
            
            # Pipeline completion
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.config_manager.state.set_variable('pipeline_end_time', end_time.isoformat())
            self.config_manager.state.set_variable('pipeline_duration', duration)
            
            success = len(self.config_manager.state.failed_steps) == 0
            
            self.log_step("PIPELINE_COMPLETE", project_id, 
                         f"Duration: {duration:.1f}s, Success: {success}")
            
            return {
                'project_id': project_id,
                'success': success,
                'completed_steps': list(self.config_manager.state.completed_steps),
                'failed_steps': list(self.config_manager.state.failed_steps),
                'duration_seconds': duration,
                'variables': dict(self.config_manager.state.variables),
                'execution_log': self.execution_log[-20:]  # Last 20 entries
            }
            
        except Exception as e:
            self.log_step("PIPELINE_ERROR", project_id, str(e))
            return {
                'project_id': project_id,
                'success': False,
                'error': str(e),
                'completed_steps': list(self.config_manager.state.completed_steps),
                'failed_steps': list(self.config_manager.state.failed_steps),
                'execution_log': self.execution_log[-20:]
            }
    
    def execute_step(self, step_name: str, project_id: str) -> Dict[str, Any]:
        """
        Execute a single pipeline step based on its configuration
        """
        step_config = self.config['steps'].get(step_name, {})
        
        self.log_step("STEP_START", project_id, f"Executing {step_name}")
        
        step_start_time = time.time()
        
        try:
            # Get model for this step
            model_name = self.select_model_for_step(step_name)
            
            if not model_name:
                return {
                    'success': False,
                    'error': f'No suitable model found for step {step_name}'
                }
            
            # Handle special step types
            if step_name == 'code_execution':
                return self.execute_code_step(project_id, step_config)
            elif step_name.endswith('_compilation') or 'compile' in step_name:
                return self.execute_compilation_step(project_id, step_config)
            else:
                return self.execute_llm_step(step_name, project_id, step_config, model_name)
                
        except Exception as e:
            duration = time.time() - step_start_time
            return {
                'success': False,
                'error': str(e),
                'duration': duration,
                'step_name': step_name
            }
    
    def execute_llm_step(self, step_name: str, project_id: str, step_config: Dict, model_name: str) -> Dict[str, Any]:
        """Execute a step that uses an LLM"""
        # Load system prompt
        system_prompt_file = step_config.get('system_prompt')
        if system_prompt_file and self.prompt_loader:
            try:
                # Get variables for prompt substitution
                prompt_vars = dict(self.config_manager.state.variables)
                prompt_vars.update({
                    'project_id': project_id,
                    'step_name': step_name
                })
                
                prompt = self.prompt_loader.load_prompt(
                    system_prompt_file.replace('.md', ''), 
                    **prompt_vars
                )
            except Exception as e:
                prompt = f"Execute {step_name}: {step_config.get('description', '')}"
        else:
            prompt = f"Execute {step_name}: {step_config.get('description', '')}"
        
        # Call appropriate model
        try:
            if self.api_client:
                if model_name.startswith('claude'):
                    response = self.api_client.call_claude(prompt)
                elif model_name.startswith('gpt'):
                    response = self.api_client.call_openai(prompt)
                elif model_name.startswith('gemini'):
                    response = self.api_client.call_google(prompt)
                else:
                    response = self.api_client.call_claude(prompt)  # Default fallback
            else:
                # Simulate LLM response for testing
                response = f"Simulated response for {step_name}: {step_config.get('description', '')}"
            
            # Process step outputs
            self.process_step_outputs(step_name, response, project_id, step_config)
            
            # Extract score if this is a review step
            score = self.extract_review_score(response) if 'review' in step_name else None
            
            return {
                'success': True,
                'response': response,
                'review_score': score,
                'model_used': model_name,
                'step_name': step_name
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"LLM execution failed: {str(e)}",
                'step_name': step_name
            }
    
    def execute_code_step(self, project_id: str, step_config: Dict) -> Dict[str, Any]:
        """Execute code execution step"""
        project_path = self.base_path / project_id
        
        # Find main code file
        code_dir = project_path / 'code'
        if not code_dir.exists():
            return {
                'success': False,
                'error': 'Code directory not found',
                'step_name': 'code_execution'
            }
        
        # Look for main files
        main_files = ['main.py', 'run.py', 'analysis.py', 'script.py']
        main_file = None
        
        for filename in main_files:
            candidate = code_dir / filename
            if candidate.exists():
                main_file = candidate
                break
        
        if not main_file:
            # Look for any Python file
            py_files = list(code_dir.glob('*.py'))
            if py_files:
                main_file = py_files[0]
        
        if not main_file:
            return {
                'success': False,
                'error': 'No executable code file found',
                'step_name': 'code_execution'
            }
        
        # Execute the code
        timeout = step_config.get('timeout', 900)  # 15 minutes default
        
        try:
            exec_result = self.code_executor.execute_code(project_path, main_file, timeout=timeout)
            
            return {
                'success': exec_result['success'],
                'execution_result': exec_result,
                'step_name': 'code_execution'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Code execution failed: {str(e)}",
                'step_name': 'code_execution'
            }
    
    def execute_compilation_step(self, project_id: str, step_config: Dict) -> Dict[str, Any]:
        """Execute LaTeX compilation or similar"""
        # This is a placeholder - implement actual LaTeX compilation
        return {
            'success': True,
            'message': f"Compilation step simulated for project {project_id}",
            'step_name': 'latex_compilation'
        }
    
    def select_model_for_step(self, step_name: str) -> Optional[str]:
        """Select appropriate model for a step"""
        step_config = self.config['steps'].get(step_name, {})
        model_selection = step_config.get('model_selection', {})
        
        if self.config_manager.model_selector:
            return self.config_manager.model_selector.select_model(model_selection)
        
        # Fallback model selection
        preferred = model_selection.get('preferred_models', ['claude-sonnet-4'])
        return preferred[0] if preferred else 'claude-sonnet-4'
    
    def process_step_outputs(self, step_name: str, response: str, project_id: str, step_config: Dict):
        """Process and save step outputs"""
        outputs = step_config.get('outputs', [])
        
        for output_pattern in outputs:
            try:
                # Resolve output path
                output_paths = self.config_manager.file_router.resolve_output_paths(
                    [output_pattern], step_name
                )
                
                for output_path in output_paths:
                    # Save the response to the output file
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(response)
                    
                    self.log_step("OUTPUT_SAVED", project_id, f"{step_name} -> {output_path}")
                    
            except Exception as e:
                self.log_step("OUTPUT_ERROR", project_id, f"{step_name} output error: {str(e)}")
    
    def extract_review_score(self, response: str) -> Optional[float]:
        """Extract numerical score from review response"""
        import re
        
        # Look for score patterns
        patterns = [
            r'SCORE:\s*([0-9]*\.?[0-9]+)',
            r'Score:\s*([0-9]*\.?[0-9]+)',
            r'score[:\s]+([0-9]*\.?[0-9]+)',
            r'([0-9]*\.?[0-9]+)\s*out of\s*10',
            r'([0-9]*\.?[0-9]+)/10'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                try:
                    score = float(match.group(1))
                    # Normalize to 0-1 scale if needed
                    if score > 1.0:
                        score = score / 10.0
                    return min(max(score, 0.0), 1.0)
                except ValueError:
                    continue
        
        return None
    
    def should_stop_on_failure(self, step_name: str) -> bool:
        """Determine if pipeline should stop on step failure"""
        # Critical steps that should stop the pipeline
        critical_steps = ['idea_generation', 'technical_design', 'code_generation']
        return step_name in critical_steps
    
    def check_conditional_branches(self, project_id: str):
        """Check and execute conditional branches"""
        branches = self.config.get('branches', {})
        
        for branch_name, branch_config in branches.items():
            condition = branch_config.get('condition', '')
            
            if self.config_manager.expression_evaluator.evaluate(condition):
                action = branch_config.get('action', 'continue')
                message = branch_config.get('message', f'Branch {branch_name} triggered')
                
                self.log_step("BRANCH_TRIGGERED", project_id, f"{branch_name}: {message}")
                
                if action == 'terminate':
                    self.config_manager.state.set_variable('pipeline_terminated', True)
                    self.config_manager.state.set_variable('termination_reason', message)
                elif action == 'branch':
                    # Execute branch steps
                    branch_steps = branch_config.get('steps', [])
                    for step_name in branch_steps:
                        if step_name in self.config['steps']:
                            self.execute_step(step_name, project_id)
    
    def log_step(self, step: str, project_id: str, details: str = ""):
        """Log pipeline step with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'project_id': project_id,
            'step': step,
            'details': details
        }
        
        self.execution_log.append(log_entry)
        
        # Also print for immediate feedback
        print(f"[{timestamp}] {project_id} - {step}: {details}")
        
        # Write to log file
        log_file = self.base_path / "pipeline_log.txt"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {project_id} - {step}: {details}\n")


def main():
    """Test the configurable pipeline orchestrator"""
    print("🚀 Testing Configurable Pipeline Orchestrator")
    print("=" * 60)
    
    base_path = Path(__file__).parent.parent
    orchestrator = ConfigurablePipelineOrchestrator(base_path)
    
    # Run a test pipeline
    result = orchestrator.run_pipeline(field="computer_science")
    
    print("\n📊 PIPELINE RESULTS:")
    print(f"  Project ID: {result['project_id']}")
    print(f"  Success: {result['success']}")
    print(f"  Completed Steps: {len(result['completed_steps'])}")
    print(f"  Failed Steps: {len(result['failed_steps'])}")
    print(f"  Duration: {result.get('duration_seconds', 0):.1f}s")
    
    if result['completed_steps']:
        print(f"  ✅ Completed: {', '.join(result['completed_steps'][:5])}")
    
    if result['failed_steps']:
        print(f"  ❌ Failed: {', '.join(result['failed_steps'])}")


if __name__ == "__main__":
    main()