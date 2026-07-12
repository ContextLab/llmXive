"""
Unit tests for the simulator module.

Tests cover:
1. Error injection logic
2. State rendering
3. Action execution
4. Completion detection
"""
import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Import the module under test
from evaluation.simulator import Simulator, SimulationState, SimulationResult
from agents.base_agent import StepResult

@pytest.fixture
def mock_taxonomy_data():
    """Mock taxonomy data for testing."""
    return [
        {
            "rule_id": "RULE-001",
            "type": "element_hidden",
            "selector": "#submit-btn",
            "description": "Submit button is hidden"
        },
        {
            "rule_id": "RULE-002",
            "type": "element_misleading",
            "selector": "#next-step",
            "misleading_text": "Go Back",
            "description": "Next button text is misleading"
        }
    ]

@pytest.fixture
def mock_task():
    """Mock benchmark task for testing."""
    return {
        "task_id": "TEST-001",
        "initial_html": "<html><body><button id='submit-btn'>Submit</button></body></html>",
        "expected_success_state": {
            "html_contains": "Success"
        },
        "error_injection": {
            "rule_id": "RULE-001",
            "inject_at_start": True
        }
    }

@pytest.fixture
def mock_agent():
    """Mock agent for testing."""
    agent = MagicMock()
    agent.step.return_value = {"type": "click", "target": "#submit-btn"}
    return agent

@pytest.mark.asyncio
async def test_simulator_initialization():
    """Test that simulator initializes correctly."""
    with patch('evaluation.simulator.PLAYWRIGHT_AVAILABLE', True):
        simulator = Simulator()
        assert simulator.browser is None
        assert simulator.page is None
        assert len(simulator.error_rules) == 0

@pytest.mark.asyncio
async def test_render_task(mock_task):
    """Test task rendering."""
    with patch('evaluation.simulator.PLAYWRIGHT_AVAILABLE', True):
        with patch('evaluation.simulator.async_playwright') as mock_pw:
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            mock_page.content.return_value = mock_task['initial_html']
            mock_page.query_selector_all.return_value = []
            mock_browser.new_page.return_value = mock_page
            
            mock_playwright_instance = AsyncMock()
            mock_playwright_instance.chromium.launch.return_value = mock_browser
            mock_pw.return_value.__aenter__.return_value = mock_playwright_instance
            
            simulator = Simulator()
            await simulator.initialize()
            
            state = await simulator.render_task(mock_task)
            
            assert state.task_id == mock_task['task_id']
            assert state.current_step == 0
            assert state.is_error_state == False

@pytest.mark.asyncio
async def test_error_injection(mock_task, mock_taxonomy_data):
    """Test error injection logic."""
    with patch('evaluation.simulator.PLAYWRIGHT_AVAILABLE', True):
        with patch('evaluation.simulator.async_playwright') as mock_pw:
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            mock_page.content.return_value = mock_task['initial_html']
            mock_page.query_selector_all.return_value = []
            mock_page.evaluate = AsyncMock()
            mock_browser.new_page.return_value = mock_page
            
            mock_playwright_instance = AsyncMock()
            mock_playwright_instance.chromium.launch.return_value = mock_browser
            mock_pw.return_value.__aenter__.return_value = mock_playwright_instance
            
            simulator = Simulator()
            simulator.error_rules = [
                {"rule_id": r["rule_id"], "type": r["type"], "selector": r["selector"], 
                 "description": r["description"], "misleading_text": r.get("misleading_text")}
                for r in mock_taxonomy_data
            ]
            
            await simulator.initialize()
            
            state = SimulationState(
                task_id=mock_task['task_id'],
                current_step=0,
                url="test",
                html_content=mock_task['initial_html'],
                is_error_state=False
            )
            
            # Inject error
            updated_state = await simulator.inject_error(state, mock_task)
            
            assert updated_state.is_error_state == True
            assert updated_state.error_type == "element_hidden"
            assert updated_state.error_message == "Submit button is hidden"
            # Verify JavaScript was called to hide element
            mock_page.evaluate.assert_called()

@pytest.mark.asyncio
async def test_execute_action_click():
    """Test click action execution."""
    with patch('evaluation.simulator.PLAYWRIGHT_AVAILABLE', True):
        with patch('evaluation.simulator.async_playwright') as mock_pw:
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            mock_page.click = AsyncMock()
            mock_browser.new_page.return_value = mock_page
            
            mock_playwright_instance = AsyncMock()
            mock_playwright_instance.chromium.launch.return_value = mock_browser
            mock_pw.return_value.__aenter__.return_value = mock_playwright_instance
            
            simulator = Simulator()
            await simulator.initialize()
            
            state = SimulationState(
                task_id="TEST",
                current_step=0,
                url="test",
                html_content="<html></html>",
                is_error_state=False
            )
            
            action = {"type": "click", "target": "#button"}
            result = await simulator._execute_action(action, state)
            
            assert result.success == True
            assert result.action_type == "click"
            assert result.target == "#button"
            mock_page.click.assert_called_once_with("#button")

@pytest.mark.asyncio
async def test_execute_action_type():
    """Test type action execution."""
    with patch('evaluation.simulator.PLAYWRIGHT_AVAILABLE', True):
        with patch('evaluation.simulator.async_playwright') as mock_pw:
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            mock_page.type = AsyncMock()
            mock_browser.new_page.return_value = mock_page
            
            mock_playwright_instance = AsyncMock()
            mock_playwright_instance.chromium.launch.return_value = mock_browser
            mock_pw.return_value.__aenter__.return_value = mock_playwright_instance
            
            simulator = Simulator()
            await simulator.initialize()
            
            state = SimulationState(
                task_id="TEST",
                current_step=0,
                url="test",
                html_content="<html></html>",
                is_error_state=False
            )
            
            action = {"type": "type", "target": "#input", "text": "hello"}
            result = await simulator._execute_action(action, state)
            
            assert result.success == True
            assert result.action_type == "type"
            assert result.target == "#input"
            mock_page.type.assert_called_once_with("#input", "hello")

@pytest.mark.asyncio
async def test_check_completion_success():
    """Test completion detection on success state."""
    with patch('evaluation.simulator.PLAYWRIGHT_AVAILABLE', True):
        simulator = Simulator()
        
        state = SimulationState(
            task_id="TEST",
            current_step=0,
            url="test",
            html_content="<html><body>Success: Task Complete</body></html>",
            is_error_state=False
        )
        
        task = {
            "expected_success_state": {
                "html_contains": "Success"
            }
        }
        
        assert simulator._check_completion(state, task) == True

@pytest.mark.asyncio
async def test_check_completion_failure():
    """Test completion detection on incomplete state."""
    with patch('evaluation.simulator.PLAYWRIGHT_AVAILABLE', True):
        simulator = Simulator()
        
        state = SimulationState(
            task_id="TEST",
            current_step=0,
            url="test",
            html_content="<html><body>Processing...</body></html>",
            is_error_state=False
        )
        
        task = {
            "expected_success_state": {
                "html_contains": "Success"
            }
        }
        
        assert simulator._check_completion(state, task) == False

@pytest.mark.asyncio
async def test_run_simulation_integration(mock_task, mock_agent):
    """Test full simulation run."""
    with patch('evaluation.simulator.PLAYWRIGHT_AVAILABLE', True):
        with patch('evaluation.simulator.async_playwright') as mock_pw:
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            mock_page.content.return_value = "<html><body>Success</body></html>"
            mock_page.query_selector_all.return_value = []
            mock_page.click = AsyncMock()
            mock_browser.new_page.return_value = mock_page
            
            mock_playwright_instance = AsyncMock()
            mock_playwright_instance.chromium.launch.return_value = mock_browser
            mock_pw.return_value.__aenter__.return_value = mock_playwright_instance
            
            # Mock taxonomy loader
            with patch('evaluation.simulator.TaxonomyLoader') as MockTaxonomyLoader:
                mock_loader = MagicMock()
                mock_loader.load.return_value = []
                MockTaxonomyLoader.return_value = mock_loader
                
                simulator = Simulator()
                await simulator.initialize()
                
                # Mock agent step to return success
                mock_agent.step.return_value = {"type": "click", "target": "#submit"}
                
                result = await simulator.run_simulation(mock_task, mock_agent, max_steps=5)
                
                assert result.task_id == mock_task['task_id']
                assert result.steps_executed > 0
                assert result.duration_seconds >= 0
                assert len(result.logs) > 0
                
                await simulator.close()

def test_simulation_state_serialization():
    """Test that SimulationState can be serialized to JSON."""
    from dataclasses import asdict
    
    state = SimulationState(
        task_id="TEST-001",
        current_step=1,
        url="http://example.com",
        html_content="<html></html>",
        is_error_state=True,
        error_type="element_hidden",
        error_message="Button hidden",
        visible_elements=["#btn1", "#btn2"]
    )
    
    serialized = asdict(state)
    assert isinstance(serialized, dict)
    assert serialized['task_id'] == "TEST-001"
    assert serialized['is_error_state'] == True

def test_simulation_result_serialization():
    """Test that SimulationResult can be serialized to JSON."""
    from dataclasses import asdict
    
    result = SimulationResult(
        task_id="TEST-001",
        success=True,
        steps_executed=5,
        final_state={},
        error_injected=True,
        error_type="element_hidden",
        duration_seconds=1.5,
        logs=[{"step": 1, "action": "click"}]
    )
    
    serialized = asdict(result)
    assert isinstance(serialized, dict)
    assert serialized['success'] == True
    assert serialized['steps_executed'] == 5
    assert len(serialized['logs']) == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])