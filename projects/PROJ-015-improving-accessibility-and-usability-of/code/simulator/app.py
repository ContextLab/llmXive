import streamlit as st
from pathlib import Path
import sys
from datetime import datetime
import json
import uuid

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from simulator.validator import validate_session, load_schema
from simulator.session_logger import log_session
from simulator.accessibility import render_accessibility_settings, render_disability_selector
from simulator.input import capture_input, calculate_sus_score
from simulator.state import init_state, increment_phase, switch_sequence, manage_state
from simulator.metrics_collector import MetricsCollector
from simulator.tasks.gene_task import render_task, validate_task_completion, calculate_task_metrics
from simulator.interfaces.traditional import TraditionalInterface
from simulator.interfaces.explainable import ExplainableInterface
from simulator.counterbalance import LatinSquareCounterbalancer
from utils.logger import get_logger

logger = get_logger(__name__)

def setup_page():
    st.set_page_config(page_title="Gene Regulation Accessibility Study", layout="wide")
    st.title("Gene Regulation Interface Usability Study")
    init_state()

def render_intro():
    st.markdown("""
    ### Welcome to the Study
    This study evaluates the usability of gene regulation interfaces for people with disabilities.
    Please read the consent form below carefully.
    """)

def render_consent():
    st.markdown("### Consent Form")
    st.info("I understand that my participation is voluntary and that I can withdraw at any time.")
    consent = st.checkbox("I consent to participate in this study.")
    return consent

def render_login():
    st.text_input("Participant ID (leave blank to generate random ID)")
    return st.text_input("Participant ID (leave blank to generate random ID)")

def render_disability_type_selection():
    return render_disability_selector()

def determine_sequence():
    if 'counterbalancer' not in st.session_state:
        st.session_state.counterbalancer = LatinSquareCounterbalancer()
    return st.session_state.counterbalancer.get_sequence(st.session_state.participant_id)

def render_interface(interface_type: str, task_input: dict):
    if interface_type == "traditional":
        return TraditionalInterface().render(task_input)
    else:
        return ExplainableInterface().render(task_input)

def render_interface_task(interface_variant: str):
    task_input = {
        "gene_data": "sample_gene_expression_data",
        "target": "upregulate"
    }
    return render_interface(interface_variant, task_input)

def render_sus_questionnaire():
    st.subheader("System Usability Scale (SUS)")
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
        st.write(f"{i+1}. {q}")
        resp = st.slider(f"Rating (1-5) for question {i+1}", 1, 5, 3, key=f"sus_{i}")
        responses.append(resp)
    return responses

def render_complete():
    st.success("Thank you for participating!")
    st.markdown("Your session has been recorded.")

def generate_recruitment_link():
    return "https://example.com/recruit"

def submit_session_data(session_data: dict):
    """
    Submits session data after validating it against the schema.
    Raises ValueError if validation fails.
    """
    logger.info("Validating session data before submission...")
    try:
        is_valid = validate_session(session_data)
        if not is_valid:
            error_msg = f"Session validation failed for participant {session_data.get('participant_id', 'unknown')}. Data does not conform to schema."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Session data validated successfully. Writing to data/raw/...")
        log_session(session_data)
        logger.info("Session data written successfully.")
        return True
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during submission: {str(e)}")
        raise

def main():
    setup_page()
    
    if 'step' not in st.session_state:
        st.session_state.step = 'intro'
    
    if st.session_state.step == 'intro':
        render_intro()
        if st.button("Read Consent"):
            st.session_state.step = 'consent'
            st.rerun()
    
    elif st.session_state.step == 'consent':
        consent = render_consent()
        if consent:
            st.session_state.consent_status = True
            st.session_state.step = 'login'
            st.rerun()
        elif st.button("Decline"):
            st.info("You have declined to participate. Thank you.")
            st.stop()
    
    elif st.session_state.step == 'login':
        p_id = render_login()
        if not p_id:
            p_id = str(uuid.uuid4())[:8]
        st.session_state.participant_id = p_id
        st.session_state.step = 'disability'
        st.rerun()
    
    elif st.session_state.step == 'disability':
        disability_type = render_disability_type_selection()
        st.session_state.disability_type = disability_type
        st.session_state.step = 'accessibility'
        st.rerun()
    
    elif st.session_state.step == 'accessibility':
        render_accessibility_settings()
        if st.button("Start Task"):
            st.session_state.step = 'task'
            st.session_state.current_sequence = determine_sequence()
            st.session_state.current_phase = 0
            manage_state()
            st.rerun()
    
    elif st.session_state.step == 'task':
        interface_variant = manage_state()
        render_interface_task(interface_variant)
        
        if st.button("Complete Task"):
            # Collect metrics
            collector = MetricsCollector()
            metrics = collector.calculate_task_metrics()
            
            # Collect SUS
            sus_responses = render_sus_questionnaire()
            sus_result = calculate_sus_score(sus_responses)
            
            # Capture input
            input_data = capture_input()
            
            # Prepare session data
            session_data = {
                "participant_id": st.session_state.participant_id,
                "disability_type": st.session_state.disability_type,
                "interface_type": interface_variant,
                "consent_status": st.session_state.consent_status,
                "metrics": metrics,
                "sus_score": sus_result['score'],
                "status": "complete",
                "timestamp": datetime.now().isoformat(),
                "input_events": input_data.get('input_events', [])
            }
            
            try:
                submit_session_data(session_data)
                st.session_state.step = 'complete'
                st.rerun()
            except ValueError as e:
                st.error(f"Submission failed: {str(e)}")
                st.stop()
    
    elif st.session_state.step == 'complete':
        render_complete()

if __name__ == "__main__":
    main()