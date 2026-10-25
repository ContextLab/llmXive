"""
Unit and Integration tests for ``src.logger.interaction_logger``.

These tests verify that the logger correctly records millisecond-precision
timestamps, maintains per-task timing state, handles the 15-minute
abort threshold, and integrates correctly with the FastAPI endpoints.
"""

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import src.logger.interaction_logger as logger
from src.logger.interaction_logger import LOG_PATH, log_interaction, clear_logs
from src.interfaces.structured_harness import app as structured_app
from src.interfaces.chat_interface import app as chat_app

@pytest.fixture(autouse=True)
def clean_environment():
    """Ensure a fresh log file and clear in-memory state for each test."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    clear_logs()
    logger._task_state.clear()
    yield
    if LOG_PATH.exists():
        clear_logs()

def test_log_interaction_basic():
    """Verify that a single interaction is recorded with all required schema fields."""
    participant = "user_123"
    figure = "fig_001"
    interface = "structured"
    payload = {"edit": "set_color(axis, red)"}
    iteration = 1

    log_interaction(participant, figure, interface, payload, iteration)

    assert LOG_PATH.exists()
    lines = LOG_PATH.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    
    rec = json.loads(lines[0])
    # Schema fields
    assert rec["session_id"] == participant
    assert rec["task_id"] == figure
    assert rec["mode"] == interface
    assert rec["iteration"] == iteration
    assert rec["payload"] == json.dumps(payload, separators=(",", ":"))
    # Aliases required by downstream analysis
    assert rec["participant_id"] == participant
    assert rec["figure_id"] == figure
    assert rec["interface"] == interface
    # Common mandatory fields
    assert "log_id" in rec
    assert "timestamp_ms" in rec
    assert "task_start_ms" in rec
    assert "task_end_ms" in rec
    assert "response_image_path" in rec

def test_log_interaction_timing_consistency():
    """Verify that task_start_ms remains constant while task_end_ms updates."""
    participant = "user_123"
    figure = "fig_001"
    interface = "chat"
    
    # First interaction
    log_interaction(participant, figure, interface, {"msg": "hi"}, 1)
    
    # Simulate small delay
    time.sleep(0.01)
    
    # Second interaction
    log_interaction(participant, figure, interface, {"msg": "do it"}, 2)
    
    lines = LOG_PATH.read_text(encoding="utf-8").strip().splitlines()
    rec1 = json.loads(lines[0])
    rec2 = json.loads(lines[1])
    
    assert rec1["task_start_ms"] == rec2["task_start_ms"], "Start time must be consistent for the task"
    assert rec2["task_end_ms"] > rec1["task_end_ms"], "End time must increase"
    assert rec2["timestamp_ms"] == rec2["task_end_ms"], "Current timestamp must match task_end_ms"

def test_log_interaction_abort_status():
    """Verify that interactions exceeding 15 minutes are marked as aborted."""
    participant = "user_123"
    figure = "fig_001"
    interface = "structured"
    
    # Mock time to simulate a long duration
    start_time = 1000000000000 # some arbitrary epoch ms
    end_time = start_time + (16 * 60 * 1000) # 16 minutes later
    
    with patch("src.logger.interaction_logger._timestamp_ms") as mock_time:
        # First interaction at start_time
        mock_time.return_value = start_time
        log_interaction(participant, figure, interface, {"edit": "1"}, 1)
        
        # Second interaction at end_time
        mock_time.return_value = end_time
        log_interaction(participant, figure, interface, {"edit": "2"}, 2)
    
    lines = LOG_PATH.read_text(encoding="utf-8").strip().splitlines()
    rec1 = json.loads(lines[0])
    rec2 = json.loads(lines[1])
    
    assert "status" not in rec1, "First interaction should not be aborted"
    assert rec2["status"] == "aborted", "Interaction after 15 mins must be marked as aborted"
    assert rec2["task_start_ms"] == start_time
    assert rec2["task_end_ms"] == end_time

def test_structured_harness_integration():
    """Verify that a real edit via TestClient creates a valid log entry."""
    clear_logs()
    client = TestClient(structured_app)
    
    participant = "test_user_struct"
    figure = "fig_struct_1"
    payload = {"edit": "set_color(axis, blue)"}
    
    # The endpoint expects the request body to match EditRequest
    response = client.post("/edit", json={
        "participant_id": participant,
        "figure_id": figure,
        "interface": "structured",
        "payload": payload,
        "iteration": 1
    })
    
    assert response.status_code == 200
    
    # Verify the log file
    assert LOG_PATH.exists()
    lines = LOG_PATH.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    
    rec = json.loads(lines[0])
    assert rec["session_id"] == participant
    assert rec["task_id"] == figure
    assert rec["mode"] == "structured"
    assert rec["payload"] == json.dumps(payload, separators=(",", ":"))
    assert "task_start_ms" in rec
    assert "task_end_ms" in rec

def test_chat_interface_integration():
    """Verify that a real edit via TestClient for chat interface creates a valid log entry."""
    clear_logs()
    client = TestClient(chat_app)
    
    participant = "test_user_chat"
    figure = "fig_chat_1"
    payload = {"message": "Make the axis blue"}
    
    response = client.post("/edit", json={
        "participant_id": participant,
        "figure_id": figure,
        "interface": "chat",
        "payload": payload,
        "iteration": 1
    })
    
    assert response.status_code == 200
    
    # Verify the log file
    assert LOG_PATH.exists()
    lines = LOG_PATH.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    
    rec = json.loads(lines[0])
    assert rec["session_id"] == participant
    assert rec["task_id"] == figure
    assert rec["mode"] == "chat"
    assert rec["payload"] == json.dumps(payload, separators=(",", ":"))