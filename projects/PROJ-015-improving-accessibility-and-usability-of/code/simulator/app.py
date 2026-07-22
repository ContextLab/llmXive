import streamlit as st
from pathlib import Path
import sys
from datetime import datetime
import json
import uuid
import os

# Local imports matching the API surface
from simulator.counterbalance import LatinSquareCounterbalancer
from simulator.interfaces.traditional import TraditionalInterface
from simulator.interfaces.explainable import ExplainableInterface
from simulator.xai_overlay import RuleBasedXAIOverlayGenerator
from simulator.session_logger import SessionLogger
from simulator.metrics_collector import MetricsCollector
from simulator.validator import validate_session
from utils.logger import get_logger

logger = get_logger(__name__)

# Constants for accessibility
ACCESSIBILITY_SETTINGS_KEY = "accessibility_settings"
DEFAULT_FONT_SIZE = 16
DEFAULT_CONTRAST = "normal"

def init_session_state():
    """Initialize Streamlit session state variables."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "participant_id" not in st.session_state:
        st.session_state.participant_id = None
    if "consent_given" not in st.session_state:
        st.session_state.consent_given = False
    if "current_interface" not in st.session_state:
        st.session_state.current_interface = None
    if "interface_sequence" not in st.session_state:
        st.session_state.interface_sequence = []
    if "start_time" not in st.session_state:
        st.session_state.start_time = None
    if "end_time" not in st.session_state:
        st.session_state.end_time = None
    if "metrics" not in st.session_state:
        st.session_state.metrics = {}
    if "disability_type" not in st.session_state:
        st.session_state.disability_type = None
    
    # Initialize accessibility settings if not present
    if ACCESSIBILITY_SETTINGS_KEY not in st.session_state:
        st.session_state[ACCESSIBILITY_SETTINGS_KEY] = {
            "font_size": DEFAULT_FONT_SIZE,
            "contrast": DEFAULT_CONTRAST,
            "high_contrast_mode": False,
            "keyboard_navigation": True
        }

def setup_page():
    """Configure the Streamlit page layout and title."""
    st.set_page_config(
        page_title="Usability Research Simulator",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.title("Complex Systems Usability Research")
    st.markdown("---")

def render_accessibility_settings():
    """Render accessibility configuration controls in the sidebar."""
    with st.sidebar:
        st.header("⚙️ Accessibility Settings")
        
        # Font Size Control
        font_size = st.slider(
            "Font Size (px)",
            min_value=12,
            max_value=24,
            value=st.session_state[ACCESSIBILITY_SETTINGS_KEY]["font_size"],
            step=1,
            help="Adjust the base font size for better readability."
        )
        
        # Contrast Mode
        contrast_options = ["normal", "high"]
        contrast = st.selectbox(
            "Contrast Mode",
            contrast_options,
            index=contrast_options.index(st.session_state[ACCESSIBILITY_SETTINGS_KEY]["contrast"]),
            help="Select a high contrast mode for better visual distinction."
        )
        
        # High Contrast Toggle
        high_contrast = st.checkbox(
            "Enable High Contrast Mode",
            value=st.session_state[ACCESSIBILITY_SETTINGS_KEY]["high_contrast_mode"],
            help="Apply a high-contrast color scheme to all UI elements."
        )
        
        # Keyboard Navigation
        keyboard_nav = st.checkbox(
            "Enable Keyboard Navigation Hints",
            value=st.session_state[ACCESSIBILITY_SETTINGS_KEY]["keyboard_navigation"],
            help="Show keyboard shortcuts and focus indicators."
        )
        
        # Update session state
        st.session_state[ACCESSIBILITY_SETTINGS_KEY] = {
            "font_size": font_size,
            "contrast": contrast,
            "high_contrast_mode": high_contrast,
            "keyboard_navigation": keyboard_nav
        }
        
        # Apply styles based on settings
        apply_accessibility_styles(
            font_size, 
            contrast, 
            high_contrast, 
            keyboard_nav
        )

def apply_accessibility_styles(font_size, contrast, high_contrast, keyboard_nav):
    """Apply CSS styles dynamically based on accessibility settings."""
    base_style = f"""
    <style>
    .stApp {{
        font-size: {font_size}px;
    }}
    .stTextInput > label, .stSelectbox > label, .stNumberInput > label {{
        font-size: {font_size + 2}px;
    }}
    """
    
    if high_contrast:
        base_style += """
        .stApp {
            background-color: #000000 !important;
            color: #FFFFFF !important;
        }
        .stButton > button {
            background-color: #FFFF00 !important;
            color: #000000 !important;
            border: 2px solid #FFFFFF !important;
        }
        .stTextInput > div > div > input {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border: 2px solid #FFFF00 !important;
        }
        .stMarkdown, .stHeader, .stTitle {
            color: #FFFF00 !important;
        }
        """
    elif contrast == "high":
        base_style += """
        .stApp {
            background-color: #1a1a1a !important;
            color: #f0f0f0 !important;
        }
        .stButton > button {
            background-color: #0066cc !important;
            color: #ffffff !important;
        }
        """
    
    if keyboard_nav:
        base_style += """
        .stButton > button:focus, 
        .stTextInput > div > div > input:focus,
        .stSelectbox > div > div > div:focus {
            outline: 3px solid #00FF00 !important;
            outline-offset: 2px;
        }
        """
    
    base_style += "</style>"
    st.markdown(base_style, unsafe_allow_html=True)

def render_consent():
    """Render the consent form and capture agreement."""
    if not st.session_state.consent_given:
        st.header("1. Informed Consent")
        st.write(
            "This study investigates the usability of complex computer systems "
            "for people with disabilities. Your participation is voluntary. "
            "You may withdraw at any time."
        )
        
        st.markdown("### Key Points:")
        st.write("- Data is anonymous and collected for research purposes only.")
        st.write("- You will be asked to complete tasks on two interface variants.")
        st.write("- You will complete a System Usability Scale (SUS) questionnaire.")
        
        if st.button("I Agree to Participate"):
            st.session_state.consent_given = True
            st.rerun()
        return False
    return True

def render_login():
    """Render the login screen for anonymous ID generation or selection."""
    st.header("2. Participant Identification")
    
    if st.session_state.participant_id is None:
        # Auto-generate anonymous ID if not provided
        anon_id = f"P{uuid.uuid4().hex[:8].upper()}"
        st.session_state.participant_id = anon_id
        st.info(f"Your anonymous ID is: **{anon_id}**")
        st.write("Please keep this ID safe if you need to resume later.")
        
        # Disability Type Selection (T012h dependency)
        st.subheader("Disability Type Selection")
        disability_options = [
            "None / No Disability",
            "Visual Impairment",
            "Motor/Physical Impairment",
            "Cognitive/Neurological Impairment",
            "Hearing Impairment",
            "Other"
        ]
        selected_disability = st.selectbox(
            "Select your disability type (for research logging only):",
            disability_options,
            key="disability_selector"
        )
        st.session_state.disability_type = selected_disability
        
        if st.button("Continue to Study"):
            st.rerun()
        return False
    return True

def determine_sequence():
    """Determine the interface sequence using the Latin Square Counterbalancer."""
    if not st.session_state.interface_sequence:
        counterbalancer = LatinSquareCounterbalancer()
        sequence = counterbalancer.assign_sequence(st.session_state.participant_id)
        st.session_state.interface_sequence = sequence
        logger.info(f"Assigned sequence {sequence} for {st.session_state.participant_id}")
    return st.session_state.interface_sequence

def render_intro():
    """Render the introduction and instructions for the current task."""
    st.header("3. Task Instructions")
    st.write(
        "You will be presented with a series of tasks to complete on a simulated system. "
        "Please try to complete them as accurately and quickly as possible."
    )
    
    if st.button("Start Task"):
        st.session_state.start_time = datetime.now()
        st.rerun()

def render_interface_task():
    """Render the main task interface, switching based on the sequence."""
    sequence = determine_sequence()
    # Sequence format: "traditional_explainable" or "explainable_traditional"
    parts = sequence.split("_")
    
    # Determine current phase based on start_time vs current time or explicit state
    # For simplicity in this demo, we assume a single pass or use a step counter
    if "task_step" not in st.session_state:
        st.session_state.task_step = 0
    
    current_phase_idx = st.session_state.task_step
    
    if current_phase_idx >= len(parts):
        # All tasks done
        return True
    
    current_interface_type = parts[current_phase_idx]
    
    # Accessibility settings are applied globally via CSS in render_accessibility_settings
    
    if current_interface_type == "traditional":
        st.subheader(f"Current Interface: Traditional (Step {current_phase_idx + 1})")
        interface = TraditionalInterface()
        result = interface.render()
    else:
        st.subheader(f"Current Interface: Explainable (Step {current_phase_idx + 1})")
        # Generate XAI overlay
        overlay_generator = RuleBasedXAIOverlayGenerator()
        overlay_data = overlay_generator.generate_overlay({"difficulty": "medium"})
        
        interface = ExplainableInterface()
        result = interface.render(overlay_data=overlay_data)
    
    # Capture metrics
    if result.get("completed"):
        end_time = datetime.now()
        duration = (end_time - st.session_state.start_time).total_seconds()
        
        # Collect metrics
        collector = MetricsCollector()
        metrics = collector.collect(
            interface_type=current_interface_type,
            duration_seconds=duration,
            error_count=result.get("errors", 0),
            explanation_engagement_time=result.get("engagement_time", 0.0)
        )
        
        st.session_state.metrics[current_interface_type] = metrics
        
        # Move to next step
        st.session_state.task_step += 1
        st.session_state.start_time = datetime.now() # Reset timer for next phase
        st.rerun()
    
    return False

def render_sus_questionnaire():
    """Render the System Usability Scale (SUS) questionnaire."""
    st.header("4. System Usability Scale (SUS)")
    st.write("Please rate your agreement with the following statements (1-5):")
    
    sus_questions = [
        "1. I think that I would like to use this system frequently.",
        "2. I found the system unnecessarily complex.",
        "3. I thought the system was easy to use.",
        "4. I think that I would need the support of a technical person to be able to use this system.",
        "5. I found the various functions in this system were well integrated.",
        "6. I thought there was too much inconsistency in this system.",
        "7. I would imagine that most people would learn to use this system very quickly.",
        "8. I found the system very cumbersome to use.",
        "9. I felt very confident using the system.",
        "10. I needed to learn a lot of things before I could get going with this system."
    ]
    
    sus_scores = []
    valid_response = True
    
    for i, question in enumerate(sus_questions):
        val = st.slider(
            question,
            min_value=1,
            max_value=5,
            key=f"sus_{i}"
        )
        sus_scores.append(val)
    
    if st.button("Submit SUS"):
        # Validate: reject if >1 missing (here we assume all are filled if slider used)
        # Imputation logic (T012d3/T017) would happen here if data were missing
        # For this task, we assume all are provided.
        
        # Calculate SUS Score (Standard Formula)
        # Odd items: score = rating - 1
        # Even items: score = 5 - rating
        # Sum scores * 2.5
        total = 0
        for i, score in enumerate(sus_scores):
            if i % 2 == 0: # Odd index (1, 3, 5...) -> 0-based even
                total += (score - 1)
            else: # Even index (2, 4, 6...) -> 0-based odd
                total += (5 - score)
        
        sus_final_score = total * 2.5
        st.success(f"Your SUS Score: {sus_final_score:.1f}")
        
        st.session_state.metrics["sus_score"] = sus_final_score
        st.session_state.metrics["sus_responses"] = sus_scores
        st.rerun()

def render_complete():
    """Render the completion screen and log the session."""
    st.header("5. Session Complete")
    st.success("Thank you for participating in this study!")
    
    # Log the session
    if "metrics" in st.session_state and st.session_state.metrics:
        logger.info("Logging session data...")
        
        # Prepare session data
        sequence = determine_sequence()
        session_data = {
            "participant_id": st.session_state.participant_id,
            "disability_type": st.session_state.disability_type,
            "sequence": sequence,
            "start_time": st.session_state.start_time.isoformat() if st.session_state.start_time else None,
            "end_time": datetime.now().isoformat(),
            "interface_metrics": st.session_state.metrics,
            "status": "complete"
        }
        
        # Validate and Log
        if validate_session(session_data):
            logger = SessionLogger()
            logger.log(session_data)
            st.write("Session data has been securely logged.")
        else:
            st.error("Session validation failed. Data not logged.")
    else:
        st.warning("No metrics collected.")

def main():
    """Main entry point for the Streamlit application."""
    init_session_state()
    setup_page()
    render_accessibility_settings()
    
    # Flow control
    if render_consent():
        if render_login():
            if render_intro():
                if not render_interface_task():
                    # If interface task returned False, it means we are done with tasks
                    render_sus_questionnaire()
                else:
                    # Still in task phase
                    pass
            else:
                # Intro not done
                pass
        else:
            # Login not done
            pass
    else:
        # Consent not given
        pass

if __name__ == "__main__":
    main()