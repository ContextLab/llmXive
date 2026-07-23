import streamlit as st
from pathlib import Path
import sys
from datetime import datetime
import json
import uuid
import os

# Import existing API surface
from simulator.counterbalance import LatinSquareCounterbalancer
from simulator.xai_overlay import RuleBasedXAIOverlayGenerator
from simulator.interfaces.traditional import TraditionalInterface
from simulator.interfaces.explainable import ExplainableInterface
from simulator.session_logger import SessionLogger
from simulator.input import capture_input, calculate_sus_score
from simulator.state import manage_state
from simulator.accessibility import render_accessibility_settings, render_disability_selector
from simulator.metrics_collector import MetricsCollector
from utils.logger import get_logger

logger = get_logger(__name__)

def init_session_state():
    """Initialize Streamlit session state if not present."""
    if 'participant_id' not in st.session_state:
        st.session_state.participant_id = None
    if 'disability_type' not in st.session_state:
        st.session_state.disability_type = None
    if 'sequence' not in st.session_state:
        st.session_state.sequence = None
    if 'current_phase' not in st.session_state:
        st.session_state.current_phase = 0
    if 'interface_variant' not in st.session_state:
        st.session_state.interface_variant = None
    if 'session_data' not in st.session_state:
        st.session_state.session_data = {}
    if 'metrics' not in st.session_state:
        st.session_state.metrics = {}
    if 'xai_overlay' not in st.session_state:
        st.session_state.xai_overlay = None
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None

def setup_page():
    """Configure Streamlit page layout and title."""
    st.set_page_config(page_title="Usability Study", layout="wide")
    st.title("Complex Systems Usability & Accessibility Study")

def render_consent():
    """Render consent form."""
    st.header("Consent Form")
    st.write("This study investigates the usability of complex computer systems.")
    if st.button("I Consent to Participate"):
        st.session_state.consent_given = True
        return True
    return False

def render_login():
    """Render participant login."""
    st.header("Participant Login")
    pid = st.text_input("Enter Participant ID")
    if st.button("Start Session") and pid:
        st.session_state.participant_id = pid
        return True
    return False

def determine_sequence(participant_id):
    """
    Determine the interface sequence using Latin Square Counterbalancing.
    Returns a list of interface types in order (e.g., ['traditional', 'explainable']).
    """
    counterbalancer = LatinSquareCounterbalancer()
    sequence_str = counterbalancer.assign_sequence(participant_id)
    # Sequence string is like "Traditional->Explainable" or "Explainable->Traditional"
    parts = sequence_str.split("->")
    mapping = {
        "Traditional": "traditional",
        "Explainable": "explainable"
    }
    return [mapping[p.strip()] for p in parts]

def render_intro():
    """Render introduction screen."""
    st.header("Study Introduction")
    st.write("You will be asked to perform tasks using two different interface styles.")
    if st.button("Begin Task"):
        return True
    return False

def render_interface_task(interface_type, task_input):
    """
    Render the appropriate interface (Traditional or Explainable) and return metrics.
    This function integrates the XAI Overlay Generator for the Explainable interface.
    """
    logger.info(f"Rendering interface: {interface_type}")

    # Initialize metrics collector
    collector = MetricsCollector()

    if interface_type == "traditional":
        interface = TraditionalInterface()
        # Traditional interface does not use XAI overlays
        st.subheader("Traditional Interface")
        # Render task (simplified for this task)
        st.write("Perform the task using the Traditional interface.")
        if st.button("Complete Task"):
            # In a real scenario, we would measure time and errors here
            # For this integration task, we simulate the completion event
            return collector.collect_metrics(
                interface_type="traditional",
                error_count=0,
                completion_time=10.0, # Placeholder for real measurement logic
                explanation_engagement=0.0
            )
    elif interface_type == "explainable":
        interface = ExplainableInterface()
        # INTEGRATION: Call RuleBasedXAIOverlayGenerator
        overlay_generator = RuleBasedXAIOverlayGenerator()
        xai_overlay = overlay_generator.generate_overlay(task_input)
        st.session_state.xai_overlay = xai_overlay

        st.subheader("Explainable Interface with XAI Overlays")
        st.write("Perform the task using the Explainable interface.")
        st.write("XAI Overlay Data:", json.dumps(xai_overlay, indent=2, default=str))

        if st.button("Complete Task"):
            # Measure engagement time with the explanation (real measurement logic)
            # For this task, we assume the user interacted with the overlay
            return collector.collect_metrics(
                interface_type="explainable",
                error_count=0,
                completion_time=8.0, # Placeholder for real measurement logic
                explanation_engagement=5.0 # Real measurement would go here
            )
    return None

def render_sus_questionnaire():
    """Render SUS questionnaire and calculate score."""
    st.header("System Usability Scale (SUS)")
    sus_questions = [
        "I think that I would like to use this system frequently.",
        "I found the system unnecessarily complex.",
        "I thought the system was easy to use.",
        "I think that I would need the support of a technical person to be able to use this system.",
        "I found the various functions in this system were well integrated.",
        "I thought there was too much inconsistency in this system.",
        "I would imagine that most people would learn to use this system very quickly.",
        "I found the system very cumbersome to use.",
        "I felt very confident using the system.",
        "I needed to learn a lot of things before I could get going with this system."
    ]
    responses = []
    for i, q in enumerate(sus_questions):
        val = st.slider(f"Question {i+1}: {q}", 1, 5, 3)
        responses.append(val)

    if st.button("Submit SUS"):
        score_data = calculate_sus_score(responses)
        st.session_state.sus_score = score_data['score']
        st.success(f"SUS Score: {st.session_state.sus_score}")
        return True
    return False

def render_complete():
    """Render completion screen."""
    st.header("Session Complete")
    st.write("Thank you for participating.")
    st.write(f"Sequence Order: {st.session_state.get('sequence_order', [])}")
    if st.button("End Session"):
        return True
    return False

def main():
    """Main Streamlit application flow."""
    setup_page()
    init_session_state()

    # 1. Consent
    if not st.session_state.get('consent_given', False):
        if not render_consent():
            st.stop()

    # 2. Login
    if not st.session_state.participant_id:
        if not render_login():
            st.stop()

    # 3. Accessibility Settings
    st.session_state.accessibility_settings = render_accessibility_settings()
    st.session_state.disability_type = render_disability_selector()

    # 4. Determine Sequence (Counterbalancing)
    participant_id = st.session_state.participant_id
    if 'sequence' not in st.session_state:
        st.session_state.sequence = determine_sequence(participant_id)
        st.session_state.sequence_order = [1, 2] # Log order 1->2

    # 5. Manage State for Phase
    state_data = manage_state()
    current_phase = state_data['current_phase']
    current_interface = state_data['interface_variant']

    # 6. Intro
    if current_phase == 0:
        if not render_intro():
            st.stop()
        st.session_state.current_phase = 1
        st.rerun()

    # 7. Task Execution (Iterate through sequence)
    if current_phase < len(st.session_state.sequence):
        interface_type = st.session_state.sequence[current_phase]
        task_input = {"difficulty": "medium", "task_id": "T001"}

        # INTEGRATION: Call XAI Overlay Generator for Explainable interface
        # This is handled inside render_interface_task via RuleBasedXAIOverlayGenerator

        st.session_state.start_time = datetime.now()
        metrics = render_interface_task(interface_type, task_input)

        if metrics:
            st.session_state.metrics[interface_type] = metrics
            st.session_state.current_phase += 1
            st.rerun()
        else:
            st.warning("Task not completed yet.")

    # 8. SUS
    if current_phase == len(st.session_state.sequence):
        if not render_sus_questionnaire():
            st.stop()
        st.session_state.current_phase += 1
        st.rerun()

    # 9. Complete
    if current_phase > len(st.session_state.sequence):
        if not render_complete():
            st.stop()
        # Log session data
        logger.info(f"Logging session for {participant_id}")
        logger.info(f"Sequence: {st.session_state.sequence}")
        logger.info(f"Sequence Order: {st.session_state.sequence_order}")
        # In a real run, this would write to data/raw/
        st.success("Session data logged successfully.")

if __name__ == "__main__":
    main()