"""Test the mock model system."""

import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from testing import MockModelManager, MockModel, ScenarioController


class TestMockModelManager:
    """Test the MockModelManager class."""
    
    def test_load_scenario(self):
        """Test loading a scenario file."""
        scenario_path = Path(__file__).parent / 'scenarios' / 'full_pipeline_test.yaml'
        manager = MockModelManager(scenario_path)
        
        assert manager.scenario['name'] == 'Full Pipeline Test'
        assert len(manager.scenario['models']) == 4
        assert len(manager.scenario['steps']) == 39
    
    def test_get_model(self):
        """Test getting mock models."""
        scenario_path = Path(__file__).parent / 'scenarios' / 'full_pipeline_test.yaml'
        manager = MockModelManager(scenario_path)
        
        # Get specific model
        model = manager.get_model('enthusiastic_reviewer')
        assert isinstance(model, MockModel)
        assert model.model_id == 'enthusiastic_reviewer'
        assert model.personality == 'enthusiastic'
    
    def test_model_generation(self):
        """Test model response generation."""
        scenario_path = Path(__file__).parent / 'scenarios' / 'full_pipeline_test.yaml'
        manager = MockModelManager(scenario_path)
        
        model = manager.get_model('critical_reviewer')
        
        # Test review response
        prompt = "Please review this technical design document for edge case handling."
        response = model.generate(prompt)
        
        # The critical reviewer personality returns "critical" themed responses
        # but might not always use that exact word
        assert any(word in response.lower() for word in ['concern', 'issue', 'problem', 'critical'])
        assert 'edge case' in response.lower()
    
    def test_response_history(self):
        """Test response history tracking."""
        scenario_path = Path(__file__).parent / 'scenarios' / 'full_pipeline_test.yaml'
        manager = MockModelManager(scenario_path)
        
        model = manager.get_model('enthusiastic_reviewer')
        response = model.generate("Test prompt")
        
        # Record response
        manager.record_response(
            model_id='enthusiastic_reviewer',
            task_type='TEST',
            prompt='Test prompt',
            response=response
        )
        
        history = manager.get_response_history()
        assert len(history) == 1
        assert history[0]['model_id'] == 'enthusiastic_reviewer'


class TestScenarioController:
    """Test the ScenarioController class."""
    
    def test_scenario_initialization(self):
        """Test scenario controller initialization."""
        scenario_path = Path(__file__).parent / 'scenarios' / 'full_pipeline_test.yaml'
        manager = MockModelManager(scenario_path)
        controller = ScenarioController(manager.scenario)
        
        assert controller.name == 'Full Pipeline Test'
        assert controller.current_step_index == 0
        assert controller.project_state['project_id'] == 'test-synthetic-timeseries-2025'
        assert controller.project_state['score'] == 0.0
    
    def test_get_current_step(self):
        """Test getting current step."""
        scenario_path = Path(__file__).parent / 'scenarios' / 'full_pipeline_test.yaml'
        manager = MockModelManager(scenario_path)
        controller = ScenarioController(manager.scenario)
        
        step = controller.get_current_step()
        assert step['number'] == 1
        assert step['description'] == 'Generate project idea'
        assert step['task_type'] == 'BRAINSTORM'
    
    def test_response_generation(self):
        """Test response generation for different task types."""
        scenario_path = Path(__file__).parent / 'scenarios' / 'full_pipeline_test.yaml'
        manager = MockModelManager(scenario_path)
        controller = ScenarioController(manager.scenario)
        
        # Test brainstorm response
        response = controller.get_next_response('BRAINSTORM', {})
        assert response['task_type'] == 'BRAINSTORM'
        assert 'time series' in response['content'].lower()
        
        # Advance and test design response
        controller.advance_step()
        controller.advance_step()
        controller.advance_step()
        controller.advance_step()  # Skip to step 5
        
        response = controller.get_next_response('CREATE_TECHNICAL_DESIGN', {})
        assert 'Technical Design Document' in response['content']
    
    def test_project_state_updates(self):
        """Test updating project state."""
        scenario_path = Path(__file__).parent / 'scenarios' / 'full_pipeline_test.yaml'
        manager = MockModelManager(scenario_path)
        controller = ScenarioController(manager.scenario)
        
        # Update state
        controller.update_project_state({
            'issue_number': 123,
            'score': 2.5,
            'stage': 'ready'
        })
        
        assert controller.project_state['issue_number'] == 123
        assert controller.project_state['score'] == 2.5
        assert controller.project_state['stage'] == 'ready'
        
        # Check history
        assert len(controller.project_state['history']) == 1
    
    def test_checkpoints(self):
        """Test checkpoint save and restore."""
        scenario_path = Path(__file__).parent / 'scenarios' / 'full_pipeline_test.yaml'
        manager = MockModelManager(scenario_path)
        controller = ScenarioController(manager.scenario)
        
        # Make some changes
        controller.advance_step()
        controller.update_project_state({'score': 1.5})
        
        # Save checkpoint
        controller.save_checkpoint('test_checkpoint')
        
        # Make more changes
        controller.advance_step()
        controller.update_project_state({'score': 3.0})
        
        assert controller.current_step_index == 2
        assert controller.project_state['score'] == 3.0
        
        # Restore checkpoint
        controller.restore_checkpoint('test_checkpoint')
        
        assert controller.current_step_index == 1
        assert controller.project_state['score'] == 1.5


class TestIntegration:
    """Test integration between components."""
    
    def test_full_scenario_execution(self):
        """Test executing a few steps of the scenario."""
        scenario_path = Path(__file__).parent / 'scenarios' / 'full_pipeline_test.yaml'
        manager = MockModelManager(scenario_path)
        controller = ScenarioController(manager.scenario)
        
        # Execute first few steps
        for i in range(5):
            step = controller.get_current_step()
            model = manager.get_model(step.get('model'))
            
            # Get response
            response = controller.get_next_response(
                step.get('task_type', 'DEFAULT'),
                controller.project_state
            )
            
            # Simulate task execution
            if step.get('validates', {}).get('score') is not None:
                controller.update_project_state({
                    'score': step['validates']['score']
                })
            
            # Record in manager
            manager.record_response(
                model_id=model.model_id,
                task_type=step.get('task_type', 'DEFAULT'),
                prompt=f"Step {step['number']}",
                response=response['content']
            )
            
            # Advance
            if not controller.advance_step():
                break
        
        # Check results
        assert controller.current_step_index == 5
        assert len(manager.get_response_history()) == 5
        
        # Get execution summary
        summary = controller.get_execution_summary()
        assert summary['completed_steps'] == 5
        assert summary['scenario_name'] == 'Full Pipeline Test'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])