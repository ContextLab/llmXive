"""
Integration test for Chat Simulator (T016a).
Verifies that chat transcripts are generated correctly for assigned participants.
"""
import json
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.experiment.chat_simulator import generate_chat_transcript, load_assignment_log, main
from code.utils.setup_paths import ensure_project_dirs

def test_generate_chat_transcript_llm():
    """Test LLM condition generates assistant responses."""
    transcript = generate_chat_transcript("test_user_1", "LLM")
    
    assert transcript["participant_id"] == "test_user_1"
    assert transcript["condition"] == "LLM"
    assert len(transcript["transcript"]) > 0
    
    # Check for assistant messages
    has_assistant = any(msg["role"] == "assistant" for msg in transcript["transcript"])
    assert has_assistant, "LLM condition should have assistant messages"

def test_generate_chat_transcript_human():
    """Test Human condition generates assistant responses."""
    transcript = generate_chat_transcript("test_user_2", "Human")
    
    assert transcript["participant_id"] == "test_user_2"
    assert transcript["condition"] == "Human"
    assert len(transcript["transcript"]) > 0
    
    has_assistant = any(msg["role"] == "assistant" for msg in transcript["transcript"])
    assert has_assistant, "Human condition should have assistant messages"

def test_generate_chat_transcript_none():
    """Test None condition generates no assistant responses."""
    transcript = generate_chat_transcript("test_user_3", "None")
    
    assert transcript["participant_id"] == "test_user_3"
    assert transcript["condition"] == "None"
    # None condition should have empty transcript or no assistant messages
    has_assistant = any(msg["role"] == "assistant" and msg["content"] != "" for msg in transcript["transcript"])
    assert not has_assistant, "None condition should not have assistant messages"

def test_full_pipeline_integration():
    """Test the full pipeline with a temporary assignment log."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create a mock assignment log
        assignment_data = [
            {"participant_id": "p1", "condition": "LLM"},
            {"participant_id": "p2", "condition": "Human"},
            {"participant_id": "p3", "condition": "None"}
        ]
        
        mock_assignment_path = tmp_path / "assignment_log.json"
        with open(mock_assignment_path, 'w') as f:
            json.dump(assignment_data, f)
        
        # Temporarily override the path in the module
        import code.experiment.chat_simulator as cs
        original_path = cs.ASSIGNMENT_LOG_PATH
        cs.ASSIGNMENT_LOG_PATH = mock_assignment_path
        
        # Create output path
        output_path = tmp_path / "chat_transcripts.json"
        cs.OUTPUT_PATH = output_path
        
        try:
            # Run the main function
            result = main()
            assert result == 0, "Main function should return 0"
            
            # Verify output exists
            assert output_path.exists(), "Output file should exist"
            
            # Verify content
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 3, "Should generate 3 transcripts"
            
            # Verify each condition
            conditions = {d["condition"] for d in data}
            assert conditions == {"LLM", "Human", "None"}, "Should have all conditions"
            
        finally:
            # Restore original path
            cs.ASSIGNMENT_LOG_PATH = original_path
            cs.OUTPUT_PATH = Path(__file__).parent.parent.parent / "data" / "raw" / "chat_transcripts.json"

if __name__ == "__main__":
    test_generate_chat_transcript_llm()
    test_generate_chat_transcript_human()
    test_generate_chat_transcript_none()
    test_full_pipeline_integration()
    print("All integration tests passed.")