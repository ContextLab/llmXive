import streamlit as st
from pathlib import Path
import sys
from datetime import datetime
import json
import uuid

# Ensure code path is accessible
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from config.settings import get_settings
from utils.logger import get_logger
from simulator.counterbalance import LatinSquareCounterbalancer
from simulator.metrics_collector import MetricsCollector
from simulator.session_logger import SessionLogger
from simulator.interfaces.traditional import TraditionalInterface
from simulator.interfaces.explainable import ExplainableInterface
from simulator.xai_generator import XAIOverlayGenerator

# SUS Constants
SUS_ITEMS = 10
SUS_MAX_SCORE = 5
SUS_MIN_SCORE = 1

def calculate_sus_score(responses: list) -> float:
    """
    Calculate System Usability Scale (SUS) score.
    Responses must be integers 1-5.
    Logic:
      - If > 1 missing items (None or empty), return -1 (Reject).
      - If <= 1 missing item, impute with mean of other responses.
      - Formula: (Sum of adjusted scores) * 2.5
    """
    valid_responses = [r for r in responses if r is not None and r != '']
    missing_count = SUS_ITEMS - len(valid_responses)

    if missing_count > 1:
        return -1.0  # Signal to reject session

    if missing_count == 1:
        # Impute missing value with mean of other responses
        mean_val = sum(valid_responses) / len(valid_responses)
        # Fill the missing spot (we don't need to know which index for the math,
        # just that the sum increases by the mean)
        # Actually, the formula is:
        # Sum(odd: r-1) + Sum(even: 5-r)
        # If we impute r with mean, it works out.
        # Let's reconstruct the full list with imputation.
        # We need to know which index was missing to apply the formula correctly?
        # No, the formula is linear.
        # Total Score = Sum( (r_i - 1) for i in odd ) + Sum( (5 - r_i) for i in even )
        # If we add a missing r_k with mean m:
        # Contribution = (m-1) if odd, (5-m) if even.
        # Since we don't know the index, we assume the missing item is at a random position?
        # EC-001 says "impute missing value with mean of participant's other responses".
        # Standard practice: fill the gap, then calculate.
        # Let's just append the mean to the list of valid responses to get 10 items.
        # But we need the order.
        # Simplified approach for simulation: Assume missing item is at the end or average the effect?
        # Better: The prompt implies we have the list of responses in order.
        # Let's assume the input `responses` is a list of 10 items, some None.
        
        # Re-calculate with full list
        full_responses = list(responses)
        mean_val = sum([r for r in full_responses if r is not None]) / len([r for r in full_responses if r is not None])
        for i in range(len(full_responses)):
            if full_responses[i] is None:
                full_responses[i] = mean_val
        responses = full_responses
    else:
        # No missing
        pass

    # Calculate Score
    total = 0.0
    for i in range(SUS_ITEMS):
        val = responses[i]
        if i % 2 == 0:  # Odd index (1, 3, 5... in 1-based, 0, 2, 4... in 0-based) -> Item 1, 3, 5, 7, 9
            # Formula: r - 1
            total += (val - 1)
        else:  # Even index (2, 4, 6... in 1-based, 1, 3, 5... in 0-based) -> Item 2, 4, 6, 8, 10
            # Formula: 5 - r
            total += (SUS_MAX_SCORE - val)
    
    return total * 2.5

def run_session_flow(logger, settings):
    """
    Orchestrates the full study session:
    1. Counterbalance assignment
    2. Interface rendering (Traditional/XAI)
    3. Metrics collection
    4. SUS Questionnaire
    5. Logging
    """
    session_id = str(uuid.uuid4())
    participant_id = st.session_state.get('participant_id', f"P-{session_id[:8]}")
    
    # 1. Counterbalancing
    counterbalancer = LatinSquareCounterbalancer()
    sequence = counterbalancer.get_sequence(participant_id)
    st.session_state['interface_sequence'] = sequence
    
    st.write(f"**Session ID:** {session_id}")
    st.write(f"**Interface Sequence:** {' -> '.join(sequence)}")
    
    metrics_collector = MetricsCollector()
    session_logger = SessionLogger()
    xai_generator = XAIOverlayGenerator()
    
    all_metrics = []
    sus_scores = []
    session_complete = True

    for idx, interface_type in enumerate(sequence):
        st.subheader(f"Task {idx+1}: {interface_type} Interface")
        
        # Initialize Interface
        if interface_type == "Traditional":
            interface = TraditionalInterface()
            xai_overlays = None
        else:
            interface = ExplainableInterface()
            xai_overlays = xai_generator.generate_overlays(difficulty="medium") # Default simulation
        
        # Render Interface (Simulated)
        # In a real app, this would show interactive widgets.
        # Here we simulate the interaction and collect metrics.
        st.info(f"Rendering {interface_type} interface with {len(xai_overlays) if xai_overlays else 0} overlays.")
        
        # Simulate user interaction (blocking until user clicks "Complete Task")
        if st.button(f"Complete {interface_type} Task", key=f"btn_{idx}"):
            # Collect Metrics
            start_time = datetime.now()
            # Simulate work time (random for demo, but in real app this is measured)
            # For this task, we assume the user clicked, so we record the time difference
            # In a real scenario, we'd start a timer on button press "Start Task"
            # Here we just record a placeholder duration for the script to run.
            duration = 10.0 # Placeholder
            errors = 0 # Placeholder
            sus_response = None # Placeholder for SUS collected later
            
            # If Explainable, collect engagement time
            engagement_time = 0.0
            if interface_type == "Explainable":
                engagement_time = 5.0 # Placeholder
            
            metrics = {
                "session_id": session_id,
                "participant_id": participant_id,
                "interface_type": interface_type,
                "completion_time": duration,
                "error_count": errors,
                "explanation_engagement_time": engagement_time,
                "timestamp": datetime.now().isoformat()
            }
            
            metrics_collector.add_metrics(metrics)
            st.success(f"Task {idx+1} completed. Time: {duration}s, Errors: {errors}")
        
        # SUS Questionnaire Logic (Collected at the end of the session, but we prepare here)
        # We will collect SUS at the very end of the loop or after all tasks.
    
    # 2. SUS Questionnaire
    st.subheader("System Usability Scale (SUS)")
    st.write("Please rate the following statements (1 = Strongly Disagree, 5 = Strongly Agree):")
    
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
    
    sus_responses = []
    for i, q in enumerate(sus_questions):
        key = f"sus_{i}"
        val = st.slider(q, min_value=1, max_value=5, value=3, key=key)
        sus_responses.append(val)
    
    if st.button("Submit SUS"):
        sus_score = calculate_sus_score(sus_responses)
        if sus_score < 0:
            st.error("Session Rejected: Too many missing SUS items (>1).")
            session_complete = False
        else:
            st.success(f"SUS Score: {sus_score:.2f}")
            sus_scores.append(sus_score)
            
            # 3. Final Logging
            log_data = {
                "session_id": session_id,
                "participant_id": participant_id,
                "sequence": sequence,
                "metrics": metrics_collector.get_all_metrics(),
                "sus_score": sus_scores[0] if sus_scores else None,
                "status": "complete" if session_complete else "rejected",
                "timestamp": datetime.now().isoformat()
            }
            
            session_logger.log_session(log_data)
            st.balloons()
            st.success("Session data saved to data/raw/.")

def main():
    st.set_page_config(page_title="Accessibility Study Simulator", layout="wide")
    st.title("Accessibility & Usability Study Simulator")
    st.write("Select a participant profile to begin the session.")
    
    settings = get_settings()
    logger = get_logger("app")
    logger.info("Simulator app started.")

    if st.button("Start Session"):
        run_session_flow(logger, settings)

if __name__ == "__main__":
    main()