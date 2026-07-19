"""
Streamlit web application for the accessibility usability study.

This app implements the interactive interface for participants,
handling task completion, error logging, and SUS questionnaire.
"""
import streamlit as st
from pathlib import Path
import sys
from datetime import datetime
import json
import uuid

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from simulator.interfaces.traditional import TraditionalInterface
from simulator.interfaces.explainable import ExplainableInterface
from simulator.counterbalance import LatinSquareCounterbalancer
from simulator.xai_overlay import RuleBasedXAIOverlayGenerator
from simulator.session_logger import SessionLogger
from simulator.metrics_collector import MetricsCollector
from utils.logger import get_logger

logger = get_logger(__name__)

def init_session_state():
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 'intro'
    if 'sequence' not in st.session_state:
        # Default sequence, overridden by counterbalancer
        st.session_state.sequence = 'traditional_explainable'
    if 'errors' not in st.session_state:
        st.session_state.errors = []
    if 'completion_times' not in st.session_state:
        st.session_state.completion_times = {}
    if 'explanation_engagement' not in st.session_state:
        st.session_state.explanation_engagement = 0.0

def setup_page():
    st.set_page_config(page_title="Usability Study", layout="wide")
    st.title("Computer System Usability Study")
    st.markdown("This study evaluates the usability of different interface types.")

def determine_sequence(participant_id: str):
    """
    Determine the sequence of interfaces using Latin Square Counterbalancing.
    """
    counterbalancer = LatinSquareCounterbalancer()
    sequence = counterbalancer.get_sequence(participant_id)
    st.session_state.sequence = sequence
    return sequence

def render_intro():
    st.header("Introduction")
    st.write("Welcome! Please complete the tasks presented to you.")
    if st.button("Start Study"):
        st.session_state.current_step = 'task1'
        st.session_state.start_time = datetime.now()
        st.rerun()

def render_sus_questionnaire():
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
    
    sus_scores = []
    for i, q in enumerate(sus_questions):
        val = st.slider(f"{i+1}. {q}", 1, 5, 3, key=f"sus_{i}")
        sus_scores.append(val)
    
    if st.button("Submit SUS"):
        # Calculate SUS score
        # Odd items: score = rating - 1
        # Even items: score = 5 - rating
        total = 0
        for i, score in enumerate(sus_scores):
            if i % 2 == 0: # Odd index (1, 3, 5...) -> 0, 2, 4...
                total += (score - 1)
            else: # Even index (2, 4, 6...) -> 1, 3, 5...
                total += (5 - score)
        
        final_sus = total * 2.5
        
        st.session_state.sus_score = final_sus
        st.session_state.current_step = 'complete'
        st.rerun()

def render_interface_task():
    st.header("Task")
    
    # Determine current interface based on sequence and step
    sequence = st.session_state.sequence
    step = st.session_state.current_step
    
    # Simple logic: first task is first in sequence, second task is second
    # For this demo, we assume 2 tasks per participant
    
    if step == 'task1':
        first_interface = sequence.split('_')[0]
        interface_type = first_interface
    elif step == 'task2':
        first_interface = sequence.split('_')[0]
        interface_type = 'explainable' if first_interface == 'traditional' else 'traditional'
    else:
        interface_type = 'traditional' # Fallback

    # Initialize interfaces
    traditional_interface = TraditionalInterface()
    explainable_interface = ExplainableInterface()
    
    # Generate XAI overlay if needed
    overlay_data = None
    if interface_type == 'explainable':
        generator = RuleBasedXAIOverlayGenerator()
        overlay_data = generator.generate_overlay({'task_difficulty': 'medium'})
        explainable_interface.set_overlay(overlay_data)
    
    # Render interface
    st.write(f"Current Interface: **{interface_type}**")
    
    start_time = datetime.now()
    
    # Simulate task interaction
    if interface_type == 'traditional':
        result = traditional_interface.render_task()
    else:
        result = explainable_interface.render_task()
    
    # Measure time
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Log metrics
    st.session_state.completion_times[interface_type] = duration
    
    # Simulate error count (0 or 1 for demo)
    error_count = 0 # In real app, this would be tracked by user actions
    st.session_state.errors.append({'interface': interface_type, 'count': error_count})
    
    # Simulate explanation engagement time (only for explainable)
    if interface_type == 'explainable':
        engagement = 5.0 # Placeholder for real measurement logic
        st.session_state.explanation_engagement = engagement
    
    if st.button("Complete Task"):
        if step == 'task1':
            st.session_state.current_step = 'task2'
            st.rerun()
        else:
            st.session_state.current_step = 'sus'
            st.rerun()

def render_complete():
    st.header("Study Complete")
    st.success("Thank you for participating!")
    
    # Log final session
    logger.info(f"Session {st.session_state.session_id} completed.")
    
    # Prepare data for logging
    session_data = {
        'participant_id': st.session_state.session_id,
        'disability_type': 'none', # Placeholder
        'interface_type': st.session_state.sequence.split('_')[0], # Primary
        'sequence': st.session_state.sequence,
        'start_time': st.session_state.start_time.isoformat() if st.session_state.start_time else None,
        'end_time': datetime.now().isoformat(),
        'error_count': sum(e['count'] for e in st.session_state.errors),
        'explanation_engagement_time_seconds': st.session_state.explanation_engagement,
        'sus_score': st.session_state.sus_score,
        'status': 'complete',
        'completion_times': st.session_state.completion_times
    }
    
    # Save to raw data
    logger = SessionLogger()
    logger.log_session(session_data)

def main():
    init_session_state()
    setup_page()
    
    # Determine sequence at start if not set
    if st.session_state.current_step == 'intro' and 'sequence' not in st.session_state:
        determine_sequence(st.session_state.session_id)
    
    if st.session_state.current_step == 'intro':
        render_intro()
    elif st.session_state.current_step in ['task1', 'task2']:
        render_interface_task()
    elif st.session_state.current_step == 'sus':
        render_sus_questionnaire()
    elif st.session_state.current_step == 'complete':
        render_complete()

if __name__ == "__main__":
    main()
