"""Mock Model Manager for deterministic testing of the llmXive pipeline."""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class MockModelManager:
    """Manages mock models for deterministic pipeline testing."""
    
    def __init__(self, scenario_path: str):
        """Initialize mock model manager with a scenario file.
        
        Args:
            scenario_path: Path to YAML file containing test scenario
        """
        self.scenario_path = Path(scenario_path)
        self.scenario = self._load_scenario()
        self.current_step = 0
        self.model_instances = {}
        self.response_history = []
        self._initialize_models()
    
    def _load_scenario(self) -> Dict[str, Any]:
        """Load scenario configuration from YAML file."""
        if not self.scenario_path.exists():
            raise FileNotFoundError(f"Scenario file not found: {self.scenario_path}")
        
        with open(self.scenario_path, 'r') as f:
            scenario = yaml.safe_load(f)
        
        # Validate scenario structure
        required_keys = ['name', 'models', 'steps']
        for key in required_keys:
            if key not in scenario:
                raise ValueError(f"Scenario missing required key: {key}")
        
        return scenario
    
    def _initialize_models(self) -> None:
        """Initialize mock model instances from scenario."""
        for model_config in self.scenario['models']:
            model_id = model_config['id']
            self.model_instances[model_id] = MockModel(
                model_id=model_id,
                config=model_config,
                scenario_name=self.scenario['name']
            )
    
    def get_model(self, model_name: Optional[str] = None) -> 'MockModel':
        """Get a mock model instance.
        
        Args:
            model_name: Optional specific model to retrieve
            
        Returns:
            MockModel instance
        """
        if model_name and model_name in self.model_instances:
            return self.model_instances[model_name]
        
        # If no specific model requested, return based on current step
        if self.current_step < len(self.scenario['steps']):
            step = self.scenario['steps'][self.current_step]
            if 'model' in step:
                return self.model_instances[step['model']]
        
        # Default to first model
        return list(self.model_instances.values())[0]
    
    def list_models(self) -> List[Dict[str, str]]:
        """List available mock models.
        
        Returns:
            List of model information dictionaries
        """
        return [
            {
                'model_id': model_id,
                'name': model.name,
                'description': model.description
            }
            for model_id, model in self.model_instances.items()
        ]
    
    def get_current_model_name(self) -> str:
        """Get the name of the current model."""
        model = self.get_model()
        return model.model_id
    
    def get_current_model_version(self) -> str:
        """Get the version of the current model."""
        return "mock-v1.0"
    
    def get_model_response(self, model_id: str, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get a response from a specific model.
        
        Args:
            model_id: ID of the model to query
            prompt: Prompt to send to the model
            context: Optional context for the response
            
        Returns:
            Response dictionary with content and metadata
        """
        if model_id not in self.model_instances:
            raise ValueError(f"Model {model_id} not found")
        
        model = self.model_instances[model_id]
        
        # Check for expected responses in current step
        current_step = self.get_current_step()
        if current_step and 'expected_responses' in current_step:
            if model_id in current_step['expected_responses']:
                return current_step['expected_responses'][model_id]
        
        # Generate response based on model personality
        response = model.generate_response(prompt, context)
        
        # Add model metadata
        response['model_id'] = model_id
        response['model_name'] = model.name
        
        return response
    
    def advance_step(self) -> None:
        """Advance to the next step in the scenario."""
        self.current_step += 1
        logger.info(f"Advanced to step {self.current_step}")
    
    def get_current_step(self) -> Optional[Dict[str, Any]]:
        """Get the current step configuration.
        
        Returns:
            Current step dict or None if no steps or out of bounds
        """
        if 'steps' not in self.scenario or self.current_step >= len(self.scenario['steps']):
            return None
        
        return self.scenario['steps'][self.current_step]
    
    def reset(self) -> None:
        """Reset the scenario to the beginning."""
        self.current_step = 0
        self.response_history = []
        for model in self.model_instances.values():
            model.reset()
    
    def get_response_history(self) -> List[Dict[str, Any]]:
        """Get the complete response history."""
        return self.response_history
    
    def record_response(self, model_id: str, task_type: str, 
                       prompt: str, response: str) -> None:
        """Record a model response in history."""
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'step': self.current_step,
            'model_id': model_id,
            'task_type': task_type,
            'prompt': prompt[:200] + '...' if len(prompt) > 200 else prompt,
            'response': response
        }
        self.response_history.append(entry)


class MockModel:
    """A mock model that returns scripted responses."""
    
    def __init__(self, model_id: str, config: Dict[str, Any], scenario_name: str):
        """Initialize a mock model.
        
        Args:
            model_id: Unique identifier for this model
            config: Model configuration from scenario
            scenario_name: Name of the parent scenario
        """
        self.model_id = model_id
        self.config = config
        self.scenario_name = scenario_name
        self.name = config.get('name', model_id)
        self.description = config.get('description', '')
        self.responses = config.get('responses', {})
        self.personality = config.get('personality', 'neutral')
        self.call_count = 0
    
    def generate(self, prompt: str, max_length: int = 2000) -> str:
        """Generate a response based on the prompt.
        
        Args:
            prompt: Input prompt
            max_length: Maximum response length
            
        Returns:
            Generated response string
        """
        # Extract task type from prompt if possible
        task_type = self._extract_task_type(prompt)
        
        # Get response based on task type
        if task_type and task_type in self.responses:
            response = self._get_task_response(task_type, prompt)
        else:
            response = self._get_default_response(prompt)
        
        self.call_count += 1
        
        # Truncate if needed
        if len(response) > max_length:
            response = response[:max_length-3] + "..."
        
        return response
    
    def _extract_task_type(self, prompt: str) -> Optional[str]:
        """Extract task type from prompt."""
        # Look for task type markers in prompt
        task_markers = {
            'BRAINSTORM': ['brainstorm', 'generate.*idea', 'new.*project'],
            'CREATE_TECHNICAL_DESIGN': ['technical design', 'design document'],
            'REVIEW_TECHNICAL_DESIGN': ['review.*design', 'evaluate.*design'],
            'CREATE_IMPLEMENTATION_PLAN': ['implementation plan', 'planning'],
            'REVIEW_IMPLEMENTATION_PLAN': ['review.*plan', 'evaluate.*plan'],
            'GENERATE_CODE': ['generate.*code', 'write.*code', 'implement'],
            'RUN_TESTS': ['run.*test', 'execute.*test'],
            'WRITE_PAPER_SECTION': ['write.*section', 'paper.*section'],
            'REVIEW_PAPER': ['review.*paper', 'evaluate.*paper'],
        }
        
        prompt_lower = prompt.lower()
        for task_type, markers in task_markers.items():
            for marker in markers:
                if marker in prompt_lower:
                    return task_type
        
        return None
    
    def _get_task_response(self, task_type: str, prompt: str) -> str:
        """Get response for a specific task type."""
        task_responses = self.responses.get(task_type, {})
        
        # Check for personality-specific response
        if self.personality in task_responses:
            return self._format_response(task_responses[self.personality], prompt)
        
        # Check for default response for this task
        if 'default' in task_responses:
            return self._format_response(task_responses['default'], prompt)
        
        # Fallback to generic response
        return self._get_default_response(prompt)
    
    def _get_default_response(self, prompt: str) -> str:
        """Get a default response when no specific response is configured."""
        default_responses = {
            'enthusiastic': "This is excellent! I fully support this approach. The methodology is sound and the implementation looks great. Score: APPROVE (+0.5)",
            'critical': "I have some concerns about this approach. The edge cases haven't been fully considered. This needs more work before approval. Score: NEEDS_REVISION (-0.5)",
            'supportive': "Good work overall. I see a few minor areas for improvement, but nothing blocking. With small adjustments this will be ready. Score: APPROVE (+0.5)",
            'domain_expert': "From a technical perspective, this shows promise. The theoretical foundation is solid. Some implementation details could be refined. Score: APPROVE (+0.5)",
            'neutral': "I have reviewed this submission. It meets the basic requirements. Score: APPROVE (+0.5)"
        }
        
        return default_responses.get(self.personality, default_responses['neutral'])
    
    def _format_response(self, template: str, prompt: str) -> str:
        """Format a response template with context from the prompt."""
        # Simple template substitution - can be enhanced
        response = template
        
        # Extract some context from prompt for substitution
        if 'project_id' in prompt:
            # Try to extract project ID
            import re
            match = re.search(r'project[_-]id[:\s]+([a-zA-Z0-9-]+)', prompt, re.IGNORECASE)
            if match:
                response = response.replace('{project_id}', match.group(1))
        
        return response
    
    def reset(self) -> None:
        """Reset the model state."""
        self.call_count = 0
    
    def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a response with metadata.
        
        Args:
            prompt: Input prompt
            context: Optional context
            
        Returns:
            Response dictionary with content and metadata
        """
        content = self.generate(prompt)
        
        # Determine if this is a positive/negative review based on personality
        is_positive = True
        is_critical = False
        
        if self.personality == 'critical':
            is_positive = False
        elif self.personality == 'very_critical':
            is_positive = False
            is_critical = True
        elif self.personality == 'mixed':
            # Alternate between positive and negative
            is_positive = self.call_count % 2 == 0
        
        return {
            'content': content,
            'is_positive': is_positive,
            'is_critical': is_critical,
            'model_id': self.model_id,
            'model_name': self.name
        }
    
    def __repr__(self) -> str:
        """String representation of the mock model."""
        return f"MockModel(id={self.model_id}, personality={self.personality})"