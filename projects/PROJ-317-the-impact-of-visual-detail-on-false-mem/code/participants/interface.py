import logging
import time
import random
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from config import get_stimuli_dir

logger = logging.getLogger(__name__)

@dataclass
class SessionConfig:
    stimulus_duration: float = 5.0
    distractor_duration: float = 30.0
    question_duration: float = 10.0

@dataclass
class StimulusPresentation:
    image_path: Path
    duration: float

@dataclass
class DistractorTaskResult:
    correct: bool
    response_time: float

@dataclass
class RecognitionQuestion:
    question_id: str
    text: str
    is_lure: bool
    options: List[str]

@dataclass
class RecognitionResult:
    question_id: str
    selected_option: str
    is_correct: bool
    response_time: float

class SimulatedParticipantInterface:
    def __init__(self, config: SessionConfig):
        self.config = config
        self.results: List[RecognitionResult] = []
    
    def present_stimulus(self, image_path: Path) -> StimulusPresentation:
        logger.info(f"Presenting stimulus: {image_path}")
        # Simulate display time
        time.sleep(self.config.stimulus_duration)
        return StimulusPresentation(image_path, self.config.stimulus_duration)
    
    def run_distractor_task(self) -> DistractorTaskResult:
        logger.info("Running distractor task...")
        start = time.time()
        # Simulate arithmetic task
        time.sleep(random.uniform(5, 15))
        duration = time.time() - start
        # Random correctness for simulation
        correct = random.random() > 0.3
        return DistractorTaskResult(correct, duration)
    
    def ask_question(self, question: RecognitionQuestion) -> RecognitionResult:
        logger.info(f"Question: {question.text}")
        start = time.time()
        # Simulate response
        time.sleep(random.uniform(1, 5))
        duration = time.time() - start
        
        # Simulate answer (random for now)
        selected = random.choice(question.options)
        # Simplified correctness check
        is_correct = (selected == "Yes") if not question.is_lure else (selected == "No")
        
        return RecognitionResult(question.question_id, selected, is_correct, duration)

def main():
    """Run a simulated session."""
    config = SessionConfig()
    interface = SimulatedParticipantInterface(config)
    
    # Simulate one trial
    img_path = get_stimuli_dir() / "mock_img_000.png"
    if img_path.exists():
        interface.present_stimulus(img_path)
        interface.run_distractor_task()
        q = RecognitionQuestion("q1", "Did you see a red car?", False, ["Yes", "No"])
        result = interface.ask_question(q)
        print(f"Result: {result.selected_option} (Correct: {result.is_correct})")
    else:
        logger.warning("No stimulus image found. Run loader first.")

if __name__ == "__main__":
    main()