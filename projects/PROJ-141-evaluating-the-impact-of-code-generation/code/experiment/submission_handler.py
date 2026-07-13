"""
Submission Handler for Code Generation Experiment (T019)

Implements code submission streaming as UTF-8 with unique submission ID per problem.
Handles streaming reception, validation, and storage of code submissions.
"""
import os
import sys
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from io import BytesIO

# Import from existing project modules
from config.settings import get_experiment_config, get_logging_config
from logs.experiment import log_experiment_event, get_logger
from data.models import Submission
from data.db_schema import get_connection

# Configure logger
logger = get_logger("submission_handler")


class SubmissionError(Exception):
    """Custom exception for submission handling errors."""
    pass


class SubmissionHandler:
    """
    Handles code submission streaming and storage.
    
    Features:
    - UTF-8 streaming reception
    - Unique submission ID generation per problem
    - Validation of code content
    - Database storage with timestamp recording
    """
    
    def __init__(self):
        self.config = get_experiment_config()
        self.max_code_size_bytes = self.config.get('max_code_size_bytes', 1024 * 1024)  # 1MB default
        self.encoding = 'utf-8'
        
    def generate_submission_id(self) -> str:
        """Generate a unique submission ID using UUID4."""
        return str(uuid.uuid4())
    
    def validate_code_content(self, code_content: str) -> Tuple[bool, Optional[str]]:
        """
        Validate code content for streaming.
        
        Args:
            code_content: The code string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not code_content:
            return False, "Code content cannot be empty"
        
        if len(code_content) > self.max_code_size_bytes:
            return False, f"Code exceeds maximum size of {self.max_code_size_bytes} bytes"
        
        try:
            # Validate UTF-8 encoding
            code_content.encode(self.encoding)
        except UnicodeEncodeError as e:
            return False, f"Invalid UTF-8 encoding: {str(e)}"
        
        return True, None
    
    def stream_code_submission(
        self,
        participant_id: str,
        problem_id: str,
        session_id: str,
        code_stream: BytesIO,
        condition: str
    ) -> Dict[str, Any]:
        """
        Stream and process a code submission.
        
        Args:
            participant_id: Unique participant identifier
            problem_id: Problem being solved
            session_id: Current session identifier
            code_stream: BytesIO stream containing UTF-8 code
            condition: Experimental condition (LLM-assisted or baseline)
            
        Returns:
            Dictionary with submission_id, status, and metadata
        """
        submission_id = self.generate_submission_id()
        timestamp = datetime.now(timezone.utc)
        
        try:
            # Read and decode UTF-8 stream
            code_content = code_stream.read().decode(self.encoding)
            
            # Validate content
            is_valid, error_msg = self.validate_code_content(code_content)
            if not is_valid:
                raise SubmissionError(error_msg)
            
            # Create submission record
            submission = Submission(
                submission_id=submission_id,
                participant_id=participant_id,
                problem_id=problem_id,
                session_id=session_id,
                code_content=code_content,
                condition=condition,
                submission_time=timestamp,
                code_size_bytes=len(code_content.encode(self.encoding)),
                encoding=self.encoding
            )
            
            # Store in database
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO submissions (
                    submission_id, participant_id, problem_id, session_id,
                    code_content, condition, submission_time, code_size_bytes, encoding
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                submission.submission_id,
                submission.participant_id,
                submission.problem_id,
                submission.session_id,
                submission.code_content,
                submission.condition,
                submission.submission_time.isoformat(),
                submission.code_size_bytes,
                submission.encoding
            ))
            
            conn.commit()
            conn.close()
            
            # Log the submission event
            log_experiment_event(
                event_type="code_submission",
                participant_id=participant_id,
                session_id=session_id,
                metadata={
                    "submission_id": submission_id,
                    "problem_id": problem_id,
                    "condition": condition,
                    "code_size_bytes": submission.code_size_bytes,
                    "timestamp": timestamp.isoformat()
                }
            )
            
            logger.info(f"Code submission recorded: {submission_id} for problem {problem_id}")
            
            return {
                "status": "success",
                "submission_id": submission_id,
                "problem_id": problem_id,
                "timestamp": timestamp.isoformat(),
                "code_size_bytes": submission.code_size_bytes
            }
            
        except SubmissionError as e:
            logger.error(f"Submission validation failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "submission_id": submission_id
            }
        except Exception as e:
            logger.error(f"Unexpected error during submission: {str(e)}")
            return {
                "status": "error",
                "error": f"Internal server error: {str(e)}",
                "submission_id": submission_id
            }
    
    def get_submission_by_id(self, submission_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a submission by its ID.
        
        Args:
            submission_id: The unique submission identifier
            
        Returns:
            Dictionary with submission data or None if not found
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM submissions WHERE submission_id = ?
            """, (submission_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving submission {submission_id}: {str(e)}")
            return None
    
    def get_submissions_by_problem(self, problem_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all submissions for a specific problem.
        
        Args:
            problem_id: The problem identifier
            
        Returns:
            List of submission dictionaries
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM submissions WHERE problem_id = ?
                ORDER BY submission_time ASC
            """, (problem_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            if rows:
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            
            return []
            
        except Exception as e:
            logger.error(f"Error retrieving submissions for problem {problem_id}: {str(e)}")
            return []
    
    def get_submissions_by_participant(self, participant_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all submissions for a specific participant.
        
        Args:
            participant_id: The participant identifier
            
        Returns:
            List of submission dictionaries
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM submissions WHERE participant_id = ?
                ORDER BY submission_time ASC
            """, (participant_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            if rows:
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            
            return []
            
        except Exception as e:
            logger.error(f"Error retrieving submissions for participant {participant_id}: {str(e)}")
            return []


def main():
    """
    Main function to demonstrate submission handling capabilities.
    This can be used for testing and validation.
    """
    print("Submission Handler Module - T019 Implementation")
    print("=" * 50)
    
    # Initialize handler
    handler = SubmissionHandler()
    
    # Generate unique submission ID
    submission_id = handler.generate_submission_id()
    print(f"Generated submission ID: {submission_id}")
    
    # Test validation
    test_code = "def hello_world():\n    print('Hello, World!')\n"
    is_valid, error = handler.validate_code_content(test_code)
    print(f"Validation result: {is_valid}, Error: {error}")
    
    # Test with invalid content
    invalid_code = "This is not valid UTF-8: \xff\xfe"
    try:
        is_valid, error = handler.validate_code_content(invalid_code)
        print(f"Invalid code validation: {is_valid}, Error: {error}")
    except Exception as e:
        print(f"Exception during validation: {e}")
    
    print("\nSubmission handler ready for experiment integration.")
    print("Use stream_code_submission() to process actual submissions.")


if __name__ == "__main__":
    main()
