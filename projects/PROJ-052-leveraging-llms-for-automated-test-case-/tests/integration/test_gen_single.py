"""
Integration test for User Story 1: LLM Test Generation Pipeline.

Task: T014
Description: Verify that a known bug description produces a syntactically valid Java file.
"""
import os
import sys
import tempfile
import json
import pytest
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data_loader import extract_bug_fix_description
from code.llm_generator import generate_test_code, validate_syntax_java, load_model
from code.config import get_model_path, get_output_dir, ensure_directories


# Use a fixed, small sample of Defects4J data for this integration test.
# In a real run, this would be fetched from the dataset, but for the test
# we simulate a single known bug description that we know exists in the dataset.
# We use a known bug from 'lang' project: lang-1
SAMPLE_BUG_DESCRIPTION = {
    "project_id": "lang",
    "bug_id": "1",
    "description": "NullPointerException thrown when using StringTokenizer with null string",
    "commit_diff": "diff --git a/src/main/java/org/apache/commons/lang/StringUtils.java b/src/main/java/org/apache/commons/lang/StringUtils.java\nindex 123..456 100644\n--- a/src/main/java/org/apache/commons/lang/StringUtils.java\n+++ b/src/main/java/org/apache/commons/lang/StringUtils.java\n@@ -10,7 +10,7 @@ public class StringUtils {\n-    if (str == null) return 0;\n+    if (str == null) return -1;\n ..."
}

# A known valid Java template to simulate a successful generation if the model fails or times out.
# The test verifies that the *validation* logic works on a valid file.
VALID_JAVA_TEMPLATE = """
import org.junit.Test;
import static org.junit.Assert.*;

public class TestStringUtilsBug1 {
    @Test
    public void testNullString() {
        // This test verifies the fix for NullPointerException
        try {
            String result = null;
            // Simulated assertion
            assertNotNull("Result should not be null after fix", result);
        } catch (Exception e) {
            fail("Exception thrown: " + e.getMessage());
        }
    }
}
"""

@pytest.fixture(scope="module")
def model_path():
    """Load the model once for the test session."""
    path = get_model_path()
    if not path or not Path(path).exists():
        pytest.skip("Model file not found at configured path. Skipping integration test.")
    return path

@pytest.fixture(scope="module")
def loaded_model(model_path):
    """Load the LLM model."""
    return load_model(model_path)

def test_generate_single_valid_java(loaded_model):
    """
    Integration test: Given a known bug description, generate a Java file and verify syntax.
    
    Steps:
    1. Extract prompt from bug description.
    2. Generate test code using the loaded model.
    3. Write the output to a temporary file.
    4. Validate the syntax using javac.
    5. Assert that the validation passes.
    """
    # 1. Prepare the prompt
    prompt = extract_bug_fix_description(SAMPLE_BUG_DESCRIPTION)
    assert prompt is not None
    assert len(prompt) > 0

    # 2. Generate test code
    # We use a very short timeout for the test to avoid hanging if the model is slow.
    # In a real pipeline, this would be longer.
    try:
        generated_code = generate_test_code(loaded_model, prompt, max_tokens=200, timeout=60)
    except Exception as e:
        # If generation fails (e.g., timeout, model error), we create a valid placeholder
        # to test the validation logic specifically, as the task is about the pipeline's
        # ability to produce valid Java.
        # However, per strict constraints, we should not fake data. 
        # If the model fails, we skip the test or mark it as failed due to environment.
        # For this specific integration test, if the model is unavailable or fails,
        # we simulate a valid output to test the *validation* step, which is the core of T014.
        # But the prompt says "verifying that a known bug description produces...".
        # If generation fails, the test fails.
        pytest.fail(f"Generation failed: {str(e)}")

    # 3. Write to a temporary file
    output_dir = get_output_dir()
    ensure_directories()
    
    # Create a unique filename
    test_file_path = Path(output_dir) / f"generated_{SAMPLE_BUG_DESCRIPTION['project_id']}_{SAMPLE_BUG_DESCRIPTION['bug_id']}.java"
    
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(generated_code)

    # 4. Validate syntax
    is_valid, error_msg = validate_syntax_java(test_file_path)

    # 5. Assert
    assert is_valid, f"Generated Java file has syntax errors: {error_msg}"
    
    # Clean up
    if test_file_path.exists():
        test_file_path.unlink()

def test_validation_of_valid_template(loaded_model):
    """
    Helper test to ensure the validation logic itself works on a known valid Java file.
    This ensures that if T014 fails, it's not because of a broken validator.
    """
    output_dir = get_output_dir()
    ensure_directories()
    
    test_file_path = Path(output_dir) / "validation_check_template.java"
    
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(VALID_JAVA_TEMPLATE)

    is_valid, error_msg = validate_syntax_java(test_file_path)
    
    # Assert that our known valid template passes
    assert is_valid, f"Validator incorrectly rejected a valid template: {error_msg}"
    
    # Clean up
    if test_file_path.exists():
        test_file_path.unlink()

    # Also test that an invalid template is rejected
    invalid_template = """
    public class InvalidTest {
        public void test() {
            // Missing semicolon
            int x = 5
        }
    }
    """
    invalid_file = Path(output_dir) / "invalid_check.java"
    with open(invalid_file, 'w', encoding='utf-8') as f:
        f.write(invalid_template)
    
    is_valid_invalid, error_msg_invalid = validate_syntax_java(invalid_file)
    assert not is_valid_invalid, "Validator should reject invalid Java"
    
    if invalid_file.exists():
        invalid_file.unlink()

    if test_file_path.exists():
        test_file_path.unlink()