import json
import math
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from src.data_synthesis.models import SyntheticVideoFrame
from src.utils.validation import validate_dataclass_instance

@dataclass
class AmbiguousEventContext:
    """
    Context data for an ambiguous event requiring resolution.
    Captures the frame sequence and kinematic properties needed for decision.
    """
    frame_id: int
    timestamp: float
    detected_class: str
    confidence: float
    position_x: float
    position_y: float
    velocity_x: float
    velocity_y: float
    velocity_magnitude: float
    height_ratio: float  # Height relative to expected standing height
    is_on_ground: bool

@dataclass
class ResolvedEvent:
    """
    Result of resolving an ambiguous event.
    """
    frame_id: int
    original_label: str
    resolved_label: str
    resolution_reason: str
    confidence_score: float
    velocity_magnitude: float
    height_ratio: float

class AmbiguousEventResolver:
    """
    Implements deterministic rules for resolving ambiguous events based on
    velocity thresholds and kinematic analysis, as per Edge Cases in spec.

    Rules:
    - Fall detection: High downward velocity (> threshold) + low height ratio
    - Sitting detection: Low velocity + low height ratio
    - Jump detection: High upward velocity + specific trajectory
    """

    # Velocity thresholds (units per second, calibrated to synthetic video scale)
    VELOCITY_FALL_THRESHOLD = 1.5  # m/s downward
    VELOCITY_JUMP_THRESHOLD = 1.2  # m/s upward
    VELOCITY_SITTING_THRESHOLD = 0.3  # m/s (stationary)

    # Height thresholds (ratio of expected standing height)
    HEIGHT_FALL_THRESHOLD = 0.3  # < 30% of standing height
    HEIGHT_SITTING_THRESHOLD = 0.4  # < 40% of standing height

    # Time window for analysis (frames)
    ANALYSIS_WINDOW = 5

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize resolver with optional configuration overrides.

        Args:
            config: Optional dict with custom threshold values
        """
        self.config = config or {}
        self.velocity_fall_threshold = self.config.get(
            'velocity_fall_threshold', self.VELOCITY_FALL_THRESHOLD
        )
        self.velocity_jump_threshold = self.config.get(
            'velocity_jump_threshold', self.VELOCITY_JUMP_THRESHOLD
        )
        self.velocity_sitting_threshold = self.config.get(
            'velocity_sitting_threshold', self.VELOCITY_SITTING_THRESHOLD
        )
        self.height_fall_threshold = self.config.get(
            'height_fall_threshold', self.HEIGHT_FALL_THRESHOLD
        )
        self.height_sitting_threshold = self.config.get(
            'height_sitting_threshold', self.HEIGHT_SITTING_THRESHOLD
        )

    def _calculate_velocity_magnitude(self, frame: SyntheticVideoFrame) -> float:
        """
        Calculate the magnitude of velocity from frame data.

        Args:
            frame: SyntheticVideoFrame with velocity components

        Returns:
            Magnitude of velocity vector (m/s)
        """
        vx = getattr(frame, 'velocity_x', 0.0)
        vy = getattr(frame, 'velocity_y', 0.0)
        return math.sqrt(vx ** 2 + vy ** 2)

    def _is_on_ground(self, frame: SyntheticVideoFrame) -> bool:
        """
        Determine if a detected person is on the ground.

        Args:
            frame: SyntheticVideoFrame with position/height data

        Returns:
            True if person is on ground, False otherwise
        """
        height_ratio = getattr(frame, 'height_ratio', 1.0)
        return height_ratio < self.height_sitting_threshold

    def _get_velocity_direction(self, frame: SyntheticVideoFrame) -> str:
        """
        Determine the primary direction of motion.

        Args:
            frame: SyntheticVideoFrame with velocity components

        Returns:
            'downward', 'upward', 'horizontal', or 'stationary'
        """
        vy = getattr(frame, 'velocity_y', 0.0)

        if abs(vy) < self.velocity_sitting_threshold:
            return 'stationary'
        elif vy > 0:
            return 'downward'
        else:
            return 'upward'

    def resolve_ambiguous_event(
        self,
        frame: SyntheticVideoFrame,
        context_history: List[SyntheticVideoFrame]
    ) -> ResolvedEvent:
        """
        Resolve an ambiguous event using deterministic velocity thresholds.

        Args:
            frame: The current frame with ambiguous classification
            context_history: Previous frames for temporal analysis

        Returns:
            ResolvedEvent with deterministic label and reasoning
        """
        # Validate input
        validate_dataclass_instance(frame, SyntheticVideoFrame)

        frame_id = frame.frame_id
        detected_class = frame.detected_class
        confidence = frame.confidence

        # Calculate current state metrics
        velocity_magnitude = self._calculate_velocity_magnitude(frame)
        height_ratio = getattr(frame, 'height_ratio', 1.0)
        velocity_direction = self._get_velocity_direction(frame)
        is_on_ground = self._is_on_ground(frame)

        # Determine resolved label based on deterministic rules
        resolved_label = detected_class
        resolution_reason = "no_change"

        # Rule 1: Fall Detection - High downward velocity + low height
        if (velocity_direction == 'downward' and
            velocity_magnitude > self.velocity_fall_threshold and
            height_ratio < self.height_fall_threshold):
            resolved_label = "fall"
            resolution_reason = f"High downward velocity ({velocity_magnitude:.2f} m/s) + low height ratio ({height_ratio:.2f})"

        # Rule 2: Sitting Detection - Low velocity + low height
        elif (velocity_direction == 'stationary' and
              velocity_magnitude < self.velocity_sitting_threshold and
              height_ratio < self.height_sitting_threshold):
            resolved_label = "sitting"
            resolution_reason = f"Low velocity ({velocity_magnitude:.2f} m/s) + low height ratio ({height_ratio:.2f})"

        # Rule 3: Jump Detection - High upward velocity
        elif (velocity_direction == 'upward' and
              velocity_magnitude > self.velocity_jump_threshold):
            resolved_label = "jump"
            resolution_reason = f"High upward velocity ({velocity_magnitude:.2f} m/s)"

        # Rule 4: Standing/Normal - Default for low velocity, normal height
        elif (velocity_magnitude < self.velocity_sitting_threshold and
              height_ratio >= self.height_sitting_threshold):
            resolved_label = "standing"
            resolution_reason = f"Low velocity ({velocity_magnitude:.2f} m/s) + normal height ratio ({height_ratio:.2f})"

        # Rule 5: Moving - For moderate velocity with normal height
        elif velocity_magnitude >= self.velocity_sitting_threshold:
            resolved_label = "moving"
            resolution_reason = f"Moderate velocity ({velocity_magnitude:.2f} m/s)"

        return ResolvedEvent(
            frame_id=frame_id,
            original_label=detected_class,
            resolved_label=resolved_label,
            resolution_reason=resolution_reason,
            confidence_score=confidence,
            velocity_magnitude=velocity_magnitude,
            height_ratio=height_ratio
        )

    def resolve_batch(
        self,
        frames: List[SyntheticVideoFrame]
    ) -> List[ResolvedEvent]:
        """
        Resolve ambiguous events for a batch of frames.

        Args:
            frames: List of SyntheticVideoFrame objects

        Returns:
            List of ResolvedEvent objects
        """
        resolved_events = []

        for i, frame in enumerate(frames):
            # Use sliding window context
            start_idx = max(0, i - self.ANALYSIS_WINDOW)
            context_history = frames[start_idx:i]

            resolved = self.resolve_ambiguous_event(frame, context_history)
            resolved_events.append(resolved)

        return resolved_events

    def export_resolution_log(
        self,
        resolved_events: List[ResolvedEvent],
        output_path: Path
    ) -> None:
        """
        Export resolution decisions to a JSONL file for audit.

        Args:
            resolved_events: List of resolved events
            output_path: Path to output file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            for event in resolved_events:
                f.write(json.dumps(asdict(event)) + '\n')

def main():
    """
    Main entry point for standalone execution.
    Demonstrates the resolver with sample data.
    """
    # Create sample frames for demonstration
    sample_frames = [
        SyntheticVideoFrame(
            frame_id=1,
            timestamp=0.0,
            detected_class="person",
            confidence=0.95,
            position_x=100.0,
            position_y=200.0,
            velocity_x=0.1,
            velocity_y=-2.0,  # Fast downward
            height_ratio=0.25,  # Low height
            is_on_ground=False
        ),
        SyntheticVideoFrame(
            frame_id=2,
            timestamp=0.1,
            detected_class="person",
            confidence=0.92,
            position_x=100.0,
            position_y=200.0,
            velocity_x=0.0,
            velocity_y=0.05,  # Nearly stationary
            height_ratio=0.35,  # Low height
            is_on_ground=True
        ),
        SyntheticVideoFrame(
            frame_id=3,
            timestamp=0.2,
            detected_class="person",
            confidence=0.88,
            position_x=100.0,
            position_y=200.0,
            velocity_x=0.2,
            velocity_y=1.5,  # Upward
            height_ratio=0.8,  # Normal height
            is_on_ground=False
        )
    ]

    resolver = AmbiguousEventResolver()
    resolved_events = resolver.resolve_batch(sample_frames)

    # Print results
    print("Ambiguous Event Resolution Results:")
    print("-" * 60)
    for event in resolved_events:
        print(f"Frame {event.frame_id}: {event.original_label} -> {event.resolved_label}")
        print(f"  Reason: {event.resolution_reason}")
        print(f"  Velocity: {event.velocity_magnitude:.2f} m/s, Height: {event.height_ratio:.2f}")
        print("-" * 60)

    # Export to file
    output_path = Path("data/resolutions/ambiguous_events.jsonl")
    resolver.export_resolution_log(resolved_events, output_path)
    print(f"Resolution log exported to: {output_path}")

if __name__ == "__main__":
    main()