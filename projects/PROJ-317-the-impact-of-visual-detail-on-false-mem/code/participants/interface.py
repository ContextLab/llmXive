import logging
import time
import random
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field

import yaml

from config import get_stimuli_metadata_dir, get_project_root
from utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class SessionConfig:
    """Configuration for a simulated participant session."""
    participant_id: str
    image_ids: List[str]
    distractor_count: int = 3
    recognition_count: int = 5
    presentation_time_ms: int = 5000
    distractor_time_ms: int = 10000

@dataclass
class StimulusPresentation:
    """Represents a single stimulus presentation event."""
    image_id: str
    image_path: str
    true_details: List[str]
    false_details: List[str]
    presentation_duration_ms: int

@dataclass
class DistractorTaskResult:
    """Result of a distractor task."""
    question: str
    correct_answer: int
    user_answer: int
    is_correct: bool
    time_taken_ms: int

@dataclass
class RecognitionQuestion:
    """A single recognition question."""
    question_id: str
    question_text: str
    is_lure: bool
    correct_answer: bool  # True if the detail was actually present

@dataclass
class RecognitionResult:
    """Result of a recognition question."""
    question_id: str
    user_answer: bool
    is_correct: bool
    response_time_ms: int

class SimulatedParticipantInterface:
    """
    Simulates a participant session: displays images, runs distractor tasks,
    and generates recognition questions based on true/false details.
    """

    # Mock object pool for generating false details (inversions)
    # Maps an object/attribute to a plausible distractor
    MOCK_OBJECT_POOL: Dict[str, str] = {
        'red': 'blue',
        'blue': 'red',
        'green': 'yellow',
        'yellow': 'green',
        'car': 'truck',
        'truck': 'car',
        'chair': 'table',
        'table': 'chair',
        'tree': 'bush',
        'bush': 'tree',
        'dog': 'cat',
        'cat': 'dog',
        'man': 'woman',
        'woman': 'man',
        'hat': 'cap',
        'cap': 'hat',
        'shirt': 'jacket',
        'jacket': 'shirt',
        'sun': 'moon',
        'moon': 'sun',
        'cloud': 'sky',
        'sky': 'cloud',
    }

    def __init__(self, config: SessionConfig):
        self.config = config
        self.logger = get_logger(__name__)
        self.metadata_dir = get_stimuli_metadata_dir()

    def _load_metadata(self, image_id: str) -> Optional[Dict[str, Any]]:
        """Load metadata for a specific image from YAML."""
        metadata_path = self.metadata_dir / f"{image_id}.yaml"
        if not metadata_path.exists():
            self.logger.warning(f"Metadata not found for image {image_id} at {metadata_path}")
            return None

        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load metadata for {image_id}: {e}")
            return None

    def _extract_true_details(self, metadata: Dict[str, Any]) -> List[str]:
        """
        Extract true details from the metadata.
        Expected format in YAML:
          details:
            - "a red car"
            - "a man wearing a hat"
        """
        details = []
        if 'details' in metadata and isinstance(metadata['details'], list):
            for item in metadata['details']:
                if isinstance(item, str):
                    details.append(item)
        return details

    def _generate_false_details(self, true_details: List[str]) -> List[str]:
        """
        Generate false (lure) details by inverting true details using the mock object pool.
        If an object/attribute in the true detail exists in the pool, replace it with the mapped value.
        If no mapping exists, append "fake_" prefix to the detail.
        """
        false_details = []
        for detail in true_details:
            modified_detail = detail
            found_mapping = False

            # Try to replace known objects/attributes
            for key, value in self.MOCK_OBJECT_POOL.items():
                if key in detail.lower():
                    # Case-insensitive replacement preserving case of the original word if possible
                    # Simple approach: replace exact word match or substring
                    # For simplicity, we do a case-insensitive replace of the key with value
                    # We'll assume the key appears as a whole word or part of the phrase
                    import re
                    pattern = re.compile(re.escape(key), re.IGNORECASE)
                    if pattern.search(modified_detail):
                        modified_detail = pattern.sub(value, modified_detail)
                        found_mapping = True
                        break

            if not found_mapping:
                # Fallback: if no mapping found, create a fake detail
                modified_detail = f"fake {detail}"

            false_details.append(modified_detail)

        return false_details

    def _generate_recognition_questions(
        self, true_details: List[str], false_details: List[str]
    ) -> List[RecognitionQuestion]:
        """
        Generate a list of recognition questions mixing true and false details.
        Ensures a mix of correct (true) and lure (false) questions.
        """
        questions = []
        question_id_counter = 1

        # Create list of (detail, is_lure) tuples
        detail_pairs = [
            (detail, False) for detail in true_details
        ] + [
            (detail, True) for detail in false_details
        ]

        # Shuffle to mix true and false
        random.shuffle(detail_pairs)

        # Select up to config.recognition_count
        selected = detail_pairs[:self.config.recognition_count]

        for detail, is_lure in selected:
            q_id = f"Q{question_id_counter:03d}"
            question_text = f"Was the following detail present in the image? '{detail}'"
            # If it's a lure, the correct answer is False (it was not present)
            # If it's true, the correct answer is True
            correct_answer = not is_lure

            questions.append(RecognitionQuestion(
                question_id=q_id,
                question_text=question_text,
                is_lure=is_lure,
                correct_answer=correct_answer
            ))
            question_id_counter += 1

        return questions

    def run_session(self) -> List[StimulusPresentation]:
        """
        Run the full simulated session for all configured images.
        Returns a list of StimulusPresentation objects containing the questions generated.
        """
        presentations = []

        for image_id in self.config.image_ids:
            self.logger.info(f"Processing image {image_id}")

            # Load metadata
            metadata = self._load_metadata(image_id)
            if not metadata:
                self.logger.warning(f"Skipping image {image_id} due to missing metadata")
                continue

            # Extract true details
            true_details = self._extract_true_details(metadata)
            if not true_details:
                self.logger.warning(f"No true details found in metadata for {image_id}")
                # Still generate questions with empty true details, which will result in only lures or empty
                true_details = []

            # Generate false details
            false_details = self._generate_false_details(true_details)

            # Generate recognition questions
            recognition_questions = self._generate_recognition_questions(true_details, false_details)

            # Simulate presentation time
            time.sleep(self.config.presentation_time_ms / 1000.0)

            # Store presentation record
            presentation = StimulusPresentation(
                image_id=image_id,
                image_path=str(self.metadata_dir.parent / "stimuli" / f"{image_id}.png"),
                true_details=true_details,
                false_details=false_details,
                presentation_duration_ms=self.config.presentation_time_ms
            )
            presentation.recognition_questions = recognition_questions  # type: ignore
            presentations.append(presentation)

        return presentations

def main():
    """Main entry point for running a simulated session."""
    logger = get_logger(__name__)
    logger.info("Starting simulated participant interface (T027 - Recognition Question Generator)")

    # Example configuration for testing
    config = SessionConfig(
        participant_id="SIM_001",
        image_ids=["img_001", "img_002"],  # These should exist in data/stimuli_metadata/
        distractor_count=3,
        recognition_count=5,
        presentation_time_ms=1000,  # Shortened for testing
        distractor_time_ms=1000
    )

    interface = SimulatedParticipantInterface(config)
    presentations = interface.run_session()

    logger.info(f"Session complete. Processed {len(presentations)} images.")
    for p in presentations:
        logger.info(f"Image {p.image_id}: Generated {len(p.recognition_questions)} questions")
        for q in p.recognition_questions:
            logger.info(f"  - {q.question_text} (Lure: {q.is_lure})")

    return presentations

if __name__ == "__main__":
    main()