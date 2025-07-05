#!/usr/bin/env python
"""Demonstrate the mock pipeline testing system."""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from testing.mock_model_manager import MockModelManager
from testing.scenario_controller import ScenarioController

# For now, we'll demonstrate without the full integration
# from testing.test_model_integration import create_test_environment, run_test_scenario

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def demo_mock_system():
    """Demonstrate the mock testing system."""
    
    print("=== llmXive Mock Pipeline Testing Demo ===\n")
    
    # Path to test scenario
    scenario_path = Path(__file__).parent / 'tests' / 'scenarios' / 'full_pipeline_test.yaml'
    
    # Create test environment
    print("1. Creating test environment...")
    mock_manager = MockModelManager(str(scenario_path))
    scenario_controller = ScenarioController(mock_manager.scenario)
    
    print(f"   - Loaded scenario: {scenario_controller.name}")
    print(f"   - Total steps: {len(scenario_controller.steps)}")
    print(f"   - Mock models: {len(mock_manager.model_instances)}")
    
    # Demonstrate model responses
    print("\n2. Testing mock model responses...")
    
    # Test brainstorm
    print("\n   a) Brainstorm task:")
    model = mock_manager.get_model()
    prompt = "Please brainstorm a new research idea about time series analysis"
    response = model.generate(prompt)
    print(f"      Model: {model.model_id}")
    print(f"      Response preview: {response[:150]}...")
    
    # Test review (critical)
    print("\n   b) Critical review:")
    mock_manager.current_step = 7  # Jump to critical review step
    critical_model = mock_manager.get_model('critical_reviewer')
    prompt = "Please review this technical design document"
    response = critical_model.generate(prompt)
    print(f"      Model: {critical_model.model_id}")
    print(f"      Response preview: {response[:150]}...")
    
    # Demonstrate scenario execution
    print("\n3. Executing first 5 steps of scenario...")
    
    # Reset scenario
    mock_manager.reset()
    scenario_controller = ScenarioController(mock_manager.scenario)
    
    for i in range(5):
        step = scenario_controller.get_current_step()
        print(f"\n   Step {step['number']}: {step['description']}")
        print(f"   - Task type: {step.get('task_type', 'N/A')}")
        print(f"   - Model: {step.get('model', 'default')}")
        
        # Simulate execution
        if step.get('validates', {}).get('score') is not None:
            new_score = step['validates']['score']
            print(f"   - Score update: {scenario_controller.project_state['score']} -> {new_score}")
            scenario_controller.update_project_state({'score': new_score})
        
        if not scenario_controller.advance_step():
            break
    
    # Show project state
    print("\n4. Current project state:")
    state = scenario_controller.project_state
    print(f"   - Project ID: {state['project_id']}")
    print(f"   - Stage: {state['stage']}")
    print(f"   - Score: {state['score']}")
    print(f"   - Reviews: {len(state['reviews'])}")
    
    # Show model response history
    print("\n5. Mock model response history:")
    history = mock_manager.get_response_history()
    print(f"   - Total responses recorded: {len(history)}")
    
    # Demonstrate scoring updates through scenario
    print("\n6. Demonstrating scoring system:")
    
    # Jump to review steps
    mock_manager.current_step = 5
    scenario_controller.current_step_index = 5
    
    print("   - Initial score: 0.0")
    
    # Positive review (+0.5)
    step = scenario_controller.steps[5]
    print(f"   - Step 6: Positive review by LLM -> +0.5")
    scenario_controller.update_project_state({'score': 0.5})
    
    # Another positive review (+0.5)
    step = scenario_controller.steps[6]
    print(f"   - Step 7: Positive review by LLM -> +0.5")
    scenario_controller.update_project_state({'score': 1.0})
    
    # Critical review (reset to 0)
    step = scenario_controller.steps[7]
    print(f"   - Step 8: Critical review -> RESET TO 0")
    scenario_controller.update_project_state({'score': 0.0})
    
    print(f"   - Final score: {scenario_controller.project_state['score']}")
    
    print("\n=== Demo Complete ===")
    print("\nThe mock system is ready for integration with the full pipeline test!")
    print("Next steps:")
    print("1. Implement scoring system validation")
    print("2. Add artifact validators")
    print("3. Create pipeline orchestrator")
    print("4. Run complete 38-step test scenario")


if __name__ == '__main__':
    demo_mock_system()