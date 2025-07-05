"""Integration module for using mock models with the existing automation system."""

from pathlib import Path
from typing import Optional, Dict, Any
import logging

from ..model_manager import ModelManager
from ..conversation_manager import ConversationManager
from .mock_model_manager import MockModelManager

logger = logging.getLogger(__name__)


class TestModelManager(ModelManager):
    """Model manager that uses mock models for testing."""
    
    def __init__(self, scenario_path: str, **kwargs):
        """Initialize test model manager with mock models.
        
        Args:
            scenario_path: Path to test scenario YAML file
            **kwargs: Additional arguments (ignored)
        """
        # Don't call super().__init__() to avoid loading real models
        self.mock_manager = MockModelManager(scenario_path)
        self.current_model = None
        self.current_model_name = None
        self.current_model_version = "mock-v1.0"
        self.tokenizer = None  # Mock tokenizer not needed
    
    def select_model(self, task_type: Optional[str] = None) -> str:
        """Select a mock model based on current scenario step.
        
        Args:
            task_type: Optional task type hint
            
        Returns:
            Model name
        """
        model = self.mock_manager.get_model()
        self.current_model = model
        self.current_model_name = model.model_id
        logger.info(f"Selected mock model: {self.current_model_name}")
        return self.current_model_name
    
    def generate_response(self, prompt: str, max_length: int = 2000) -> str:
        """Generate response using mock model.
        
        Args:
            prompt: Input prompt
            max_length: Maximum response length
            
        Returns:
            Generated response
        """
        if not self.current_model:
            self.select_model()
        
        response = self.current_model.generate(prompt, max_length)
        
        # Record in mock manager
        self.mock_manager.record_response(
            model_id=self.current_model_name,
            task_type=self._extract_task_type(prompt),
            prompt=prompt,
            response=response
        )
        
        # Advance scenario step
        self.mock_manager.advance_step()
        
        return response
    
    def _extract_task_type(self, prompt: str) -> str:
        """Extract task type from prompt."""
        # Simple extraction logic - can be enhanced
        task_keywords = {
            'brainstorm': 'BRAINSTORM',
            'technical design': 'CREATE_TECHNICAL_DESIGN',
            'review': 'REVIEW',
            'implementation plan': 'CREATE_IMPLEMENTATION_PLAN',
            'generate code': 'GENERATE_CODE',
            'write': 'WRITE',
            'test': 'TEST'
        }
        
        prompt_lower = prompt.lower()
        for keyword, task_type in task_keywords.items():
            if keyword in prompt_lower:
                return task_type
        
        return 'UNKNOWN'
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about current mock model."""
        return {
            'name': self.current_model_name,
            'version': self.current_model_version,
            'type': 'mock',
            'scenario': self.mock_manager.scenario['name']
        }


class TestConversationManager(ConversationManager):
    """Conversation manager that works with mock models."""
    
    def __init__(self, model_manager: TestModelManager):
        """Initialize test conversation manager.
        
        Args:
            model_manager: TestModelManager instance
        """
        self.model_manager = model_manager
        self.conversation_history = []
    
    def query_model(self, task_type: str, prompt: str, 
                   validation_fn: Optional[callable] = None) -> str:
        """Query mock model for response.
        
        Args:
            task_type: Type of task
            prompt: Formatted prompt
            validation_fn: Optional validation function
            
        Returns:
            Model response
        """
        # Select appropriate model for task
        self.model_manager.select_model(task_type)
        
        # Generate response
        response = self.model_manager.generate_response(prompt)
        
        # Validate if function provided
        if validation_fn and not validation_fn(response):
            logger.warning(f"Response failed validation for {task_type}")
            # In test mode, we'll accept it anyway
        
        # Record conversation
        self.conversation_history.append({
            'task_type': task_type,
            'prompt': prompt,
            'response': response,
            'model': self.model_manager.current_model_name
        })
        
        return response
    
    def format_prompt(self, task_type: str, context: Dict[str, Any]) -> str:
        """Format prompt for mock model.
        
        Args:
            task_type: Type of task
            context: Task context
            
        Returns:
            Formatted prompt
        """
        # Simple prompt formatting for tests
        prompt_parts = [f"Task: {task_type}"]
        
        if 'project_id' in context:
            prompt_parts.append(f"Project ID: {context['project_id']}")
        
        if 'content' in context:
            prompt_parts.append(f"Content: {context['content']}")
        
        if 'requirements' in context:
            prompt_parts.append(f"Requirements: {context['requirements']}")
        
        return "\n".join(prompt_parts)


def create_test_environment(scenario_path: str) -> tuple:
    """Create a complete test environment with mock models.
    
    Args:
        scenario_path: Path to scenario YAML file
        
    Returns:
        Tuple of (TestModelManager, TestConversationManager, ScenarioController)
    """
    from .scenario_controller import ScenarioController
    
    # Create model manager with scenario
    model_manager = TestModelManager(scenario_path)
    
    # Create conversation manager
    conversation_manager = TestConversationManager(model_manager)
    
    # Create scenario controller
    scenario_controller = ScenarioController(model_manager.mock_manager.scenario)
    
    return model_manager, conversation_manager, scenario_controller


def run_test_scenario(scenario_path: str, task_executor_class, 
                     github_handler, max_steps: Optional[int] = None) -> Dict[str, Any]:
    """Run a complete test scenario.
    
    Args:
        scenario_path: Path to scenario YAML file
        task_executor_class: TaskExecutor class to use
        github_handler: GitHub handler instance
        max_steps: Maximum number of steps to execute
        
    Returns:
        Test results dictionary
    """
    # Create test environment
    model_manager, conversation_manager, scenario_controller = create_test_environment(scenario_path)
    
    # Create task executor with test components
    task_executor = task_executor_class(
        github_handler=github_handler,
        model_manager=model_manager,
        conversation_manager=conversation_manager
    )
    
    # Run scenario steps
    results = {
        'executed_steps': 0,
        'successful_steps': 0,
        'failed_steps': 0,
        'errors': [],
        'final_state': None
    }
    
    steps_to_run = max_steps or len(scenario_controller.steps)
    
    for i in range(steps_to_run):
        step = scenario_controller.get_current_step()
        if not step:
            break
        
        logger.info(f"Executing step {step['number']}: {step['description']}")
        
        try:
            # Get task type
            task_type = step.get('task_type', 'UNKNOWN')
            
            # Build context from scenario state
            context = {
                'project_id': scenario_controller.project_state['project_id'],
                'issue_number': scenario_controller.project_state.get('issue_number'),
                'stage': scenario_controller.project_state['stage'],
                'score': scenario_controller.project_state['score']
            }
            
            # Execute task
            result = task_executor.execute_task(task_type, context)
            
            # Update scenario state based on result
            if result.get('success'):
                results['successful_steps'] += 1
                
                # Update project state
                updates = {}
                if 'issue_number' in result:
                    updates['issue_number'] = result['issue_number']
                if 'score' in step.get('validates', {}):
                    updates['score'] = step['validates']['score']
                if 'stage' in step.get('validates', {}):
                    updates['stage'] = step['validates']['stage']
                
                scenario_controller.update_project_state(updates)
            else:
                results['failed_steps'] += 1
                results['errors'].append({
                    'step': step['number'],
                    'error': result.get('error', 'Unknown error')
                })
            
        except Exception as e:
            logger.error(f"Error executing step {step['number']}: {e}")
            results['failed_steps'] += 1
            results['errors'].append({
                'step': step['number'],
                'error': str(e)
            })
        
        results['executed_steps'] += 1
        
        # Advance to next step
        if not scenario_controller.advance_step():
            break
    
    # Get final state
    results['final_state'] = scenario_controller.get_execution_summary()
    
    return results