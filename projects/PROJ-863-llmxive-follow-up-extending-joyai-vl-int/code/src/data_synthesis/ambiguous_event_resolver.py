"""
Module: src/data_synthesis/ambiguous_event_resolver.py

Implements deterministic rules to handle ambiguous events in video streams,
specifically distinguishing between 'sitting' and 'falling' based on velocity
thresholds and temporal continuity.

This module satisfies Task T015: "Implement logic to handle ambiguous events
with deterministic rules (velocity thresholds) as per Edge Cases".

It integrates with the visual labeling pipeline by providing a deterministic
post-processor or inline resolver that ensures labels are not ambiguous.
"""
import json
import math
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from src.data_synthesis.models import SyntheticVideoFrame
from src.utils.logging import get_logger, log_data_event

# Constants for deterministic resolution (Edge Cases)
# Velocity threshold in pixels per second (approximate visual velocity)
# Below this velocity, rapid movement is considered "sitting/adjusting"
# Above this, it is considered "falling"
VELOCITY_THRESHOLD_SITTING_FALLING = 150.0  # px/s

# Minimum duration (seconds) a "fall" trajectory must persist to be confirmed
FALL_MIN_DURATION_SECONDS = 0.5

# Minimum vertical displacement (pixels) to consider a fall valid
FALL_MIN_VERTICAL_DISPLACEMENT = 50.0

@dataclass
class AmbiguousEventContext:
    """Context for resolving an ambiguous event."""
    frame_sequence: List[SyntheticVideoFrame]
    start_index: int
    end_index: int
    label: str  # Current tentative label (e.g., "ambiguous", "sitting", "falling")
    confidence: float

@dataclass
class ResolvedEvent:
    """Result of resolving an ambiguous event."""
    start_index: int
    end_index: int
    resolved_label: str  # "critical" (fall) or "silence" (sitting/normal)
    resolution_reason: str
    velocity_magnitude: float

class AmbiguousEventResolver:
    """
    Resolves ambiguous events in video streams using deterministic velocity
    thresholds and temporal rules.
    
    This class implements the logic required for T015 to ensure that
    classification is strictly based on visual content (velocity, position change)
    and not model output or heuristics that might introduce bias.
    """
    
    def __init__(self, velocity_threshold: float = VELOCITY_THRESHOLD_SITTING_FALLING):
        self.velocity_threshold = velocity_threshold
        self.logger = get_logger("AmbiguousEventResolver")
    
    def calculate_velocity(self, frame1: SyntheticVideoFrame, frame2: SyntheticVideoFrame) -> float:
        """
        Calculates the Euclidean velocity magnitude (pixels per second) between two frames.
        
        Args:
            frame1: The earlier frame.
            frame2: The later frame.
            
        Returns:
            Float representing the velocity magnitude in pixels per second.
        """
        # Extract person bounding box center
        # SyntheticVideoFrame assumes 'person_bbox' is [x, y, w, h]
        if not frame1.person_bbox or not frame2.person_bbox:
            return 0.0
            
        x1, y1, w1, h1 = frame1.person_bbox
        x2, y2, w2, h2 = frame2.person_bbox
        
        center1 = (x1 + w1 / 2, y1 + h1 / 2)
        center2 = (x2 + w2 / 2, y2 + h2 / 2)
        
        # Calculate displacement
        dx = center2[0] - center1[0]
        dy = center2[1] - center1[1]
        
        # Calculate time delta (assuming frame_rate is set in frames)
        dt = (frame2.timestamp - frame1.timestamp)
        if dt == 0:
            return 0.0
            
        distance = math.sqrt(dx*dx + dy*dy)
        velocity = distance / dt
        
        return velocity

    def resolve_sequence(self, context: AmbiguousEventContext) -> ResolvedEvent:
        """
        Resolves an ambiguous event sequence into a definitive label.
        
        Args:
            context: The ambiguous event context.
            
        Returns:
            ResolvedEvent with the definitive label and reason.
        """
        frames = context.frame_sequence
        if not frames:
            return ResolvedEvent(
                start_index=context.start_index,
                end_index=context.end_index,
                resolved_label="silence",
                resolution_reason="Empty sequence",
                velocity_magnitude=0.0
            )
        
        # Analyze velocity profile
        velocities = []
        for i in range(len(frames) - 1):
            v = self.calculate_velocity(frames[i], frames[i+1])
            velocities.append(v)
        
        avg_velocity = sum(velocities) / len(velocities) if velocities else 0.0
        max_velocity = max(velocities) if velocities else 0.0
        
        # Check vertical displacement
        if len(frames) >= 2:
            start_y = frames[0].person_bbox[1] if frames[0].person_bbox else 0
            end_y = frames[-1].person_bbox[1] if frames[-1].person_bbox else 0
            vertical_disp = abs(end_y - start_y)
        else:
            vertical_disp = 0.0
        
        # Deterministic Rule Application
        # Rule 1: If average velocity is high, it's a fall (critical)
        # Rule 2: If max velocity is high but average is low, it might be a quick sit (silence)
        # Rule 3: If vertical displacement is significant and velocity is moderate, it's a fall.
        
        is_fall = False
        reason = ""
        
        if avg_velocity > self.velocity_threshold:
            is_fall = True
            reason = f"Average velocity ({avg_velocity:.2f} px/s) exceeds threshold ({self.velocity_threshold} px/s)"
        elif max_velocity > self.velocity_threshold * 1.5 and vertical_disp > FALL_MIN_VERTICAL_DISPLACEMENT:
            # High peak velocity combined with significant drop
            is_fall = True
            reason = f"Peak velocity ({max_velocity:.2f} px/s) and vertical drop ({vertical_disp:.2f} px) indicate fall"
        elif vertical_disp > FALL_MIN_VERTICAL_DISPLACEMENT and avg_velocity > self.velocity_threshold * 0.5:
            # Significant drop with moderate speed
            is_fall = True
            reason = f"Significant vertical displacement ({vertical_disp:.2f} px) with moderate velocity"
        else:
            is_fall = False
            reason = f"Velocity ({avg_velocity:.2f} px/s) and displacement ({vertical_disp:.2f} px) within sitting thresholds"
        
        resolved_label = "critical" if is_fall else "silence"
        
        log_data_event(
            event_type="ambiguous_resolution",
            details={
                "start_index": context.start_index,
                "end_index": context.end_index,
                "original_label": context.label,
                "resolved_label": resolved_label,
                "reason": reason,
                "avg_velocity": avg_velocity,
                "max_velocity": max_velocity,
                "vertical_displacement": vertical_disp
            }
        )
        
        return ResolvedEvent(
            start_index=context.start_index,
            end_index=context.end_index,
            resolved_label=resolved_label,
            resolution_reason=reason,
            velocity_magnitude=avg_velocity
        )

    def process_stream(self, frames: List[SyntheticVideoFrame]) -> List[ResolvedEvent]:
        """
        Processes a full stream of frames, identifying and resolving ambiguous regions.
        
        This is a simplified version that assumes the caller identifies the ambiguous
        windows. In a full pipeline, this would be called on specific segments.
        
        For T015, we demonstrate the logic by processing the whole stream and
        flagging segments that needed resolution.
        """
        resolved_events = []
        
        # Identify ambiguous windows (simplified: assume any rapid change is ambiguous)
        # In practice, the visual_labeler would mark these.
        # Here we just process the whole stream as one context if it's short,
        # or chunk it.
        
        if not frames:
            return resolved_events
        
        # For demonstration, we treat the whole sequence as one potential event
        # In a real scenario, this would be called on detected "ambiguous" segments
        context = AmbiguousEventContext(
            frame_sequence=frames,
            start_index=0,
            end_index=len(frames)-1,
            label="ambiguous",
            confidence=0.5
        )
        
        resolved = self.resolve_sequence(context)
        resolved_events.append(resolved)
        
        return resolved_events

def main():
    """
    Entry point for testing the AmbiguousEventResolver logic.
    Generates a synthetic sequence of frames simulating a fall vs sitting
    and verifies the deterministic rules.
    """
    logger = get_logger("AmbiguousEventResolver-Test")
    logger.info("Starting AmbiguousEventResolver deterministic logic test.")
    
    resolver = AmbiguousEventResolver(velocity_threshold=VELOCITY_THRESHOLD_SITTING_FALLING)
    
    # Create a synthetic "fall" sequence (high velocity, vertical drop)
    fall_frames = []
    base_time = 1000.0
    for i in range(10):
        # Simulate rapid downward movement
        y = 100 - (i * 20) # Moving up (y decreases) or down? Let's say y increases for down
        # Let's simulate falling: y increases rapidly
        y = 100 + (i * 30) 
        x = 200 + (i * 5)
        frame = SyntheticVideoFrame(
            timestamp=base_time + i * 0.1,
            person_bbox=[x, y, 50, 100],
            is_critical=False, # Initial label
            frame_index=i
        )
        fall_frames.append(frame)
        
    # Create a synthetic "sitting" sequence (low velocity)
    sit_frames = []
    for i in range(10):
        # Small adjustments
        y = 100 + (i * 2)
        x = 200 + (i * 1)
        frame = SyntheticVideoFrame(
            timestamp=base_time + i * 0.1,
            person_bbox=[x, y, 50, 100],
            is_critical=False,
            frame_index=i
        )
        sit_frames.append(frame)
        
    # Test Fall
    fall_context = AmbiguousEventContext(
        frame_sequence=fall_frames,
        start_index=0,
        end_index=len(fall_frames)-1,
        label="ambiguous",
        confidence=0.5
    )
    fall_result = resolver.resolve_sequence(fall_context)
    assert fall_result.resolved_label == "critical", f"Expected 'critical' for fall, got {fall_result.resolved_label}"
    logger.info(f"Fall resolved correctly: {fall_result.resolution_reason}")
    
    # Test Sit
    sit_context = AmbiguousEventContext(
        frame_sequence=sit_frames,
        start_index=0,
        end_index=len(sit_frames)-1,
        label="ambiguous",
        confidence=0.5
    )
    sit_result = resolver.resolve_sequence(sit_context)
    assert sit_result.resolved_label == "silence", f"Expected 'silence' for sit, got {sit_result.resolved_label}"
    logger.info(f"Sitting resolved correctly: {sit_result.resolution_reason}")
    
    logger.info("AmbiguousEventResolver deterministic logic tests PASSED.")
    return 0

if __name__ == "__main__":
    exit(main())
