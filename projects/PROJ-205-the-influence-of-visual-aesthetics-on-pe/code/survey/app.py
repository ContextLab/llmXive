"""
Main Streamlit application for the survey.
Implements the complete workflow: Consent -> Demographics -> Stimuli -> Ratings -> Submission.
"""

import streamlit as st
import os
import sys
import time
import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.helpers import (
    generate_user_id,
    hash_ip,
    format_timestamp,
    get_education_code,
    truncate_user_agent,
    prepare_submission_row,
    append_to_submissions_csv,
    get_submissions_csv_path,
    get_project_root,
    ensure_data_dirs
)
from utils.config import load_consent_text, get_irb_protocol_id
from survey.constants import METADATA_SCHEMA, LATIN_SQUARE_SEQUENCES
from survey.randomization import select_sequence

# --- Page Configuration ---
st.set_page_config(
    page_title="Visual Aesthetics Survey",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Helper Functions ---

def init_session_state():
    """Initialize session state variables if they don't exist."""
    if 'participant_id' not in st.session_state:
        st.session_state.participant_id = str(uuid.uuid4())
    if 'start_time' not in st.session_state:
        st.session_state.start_time = time.time()
    if 'current_stimulus_index' not in st.session_state:
        st.session_state.current_stimulus_index = 0
    if 'stimuli_sequence' not in st.session_state:
        # Will be set after demographics
        st.session_state.stimuli_sequence = []
    if 'ratings' not in st.session_state:
        st.session_state.ratings = {}
    if 'consent_given' not in st.session_state:
        st.session_state.consent_given = False
    if 'demographics_submitted' not in st.session_state:
        st.session_state.demographics_submitted = False

def extract_and_validate_ip():
    """Extract IP from headers and hash it."""
    # Try standard headers first
    forwarded = st.context.headers.get('X-Forwarded-For')
    real_ip = st.context.headers.get('X-Real-IP')
    
    ip_address = forwarded if forwarded else real_ip
    
    # Fallback for local testing or specific proxy configs
    if not ip_address:
        ip_address = st.context.headers.get('Remote-Addr', '127.0.0.1')
    
    if not ip_address:
        st.error("Session Rejected: Unable to verify identity.")
        st.stop()
    
    # Take the first IP if multiple are forwarded
    if ',' in ip_address:
        ip_address = ip_address.split(',')[0].strip()
    
    return hash_ip(ip_address)

def show_consent_form():
    """Display the IRB-approved consent form."""
    try:
        consent_text = load_consent_text()
        irb_id = get_irb_protocol_id()
    except Exception as e:
        st.error(f"Error loading consent form: {str(e)}")
        st.stop()

    st.markdown(f"### 📜 Informed Consent (IRB Protocol: {irb_id})")
    st.markdown("---")
    st.markdown(consent_text)
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("I Agree", type="primary"):
            st.session_state.consent_given = True
            st.session_state.demographics_submitted = False
            st.rerun()
    
    with col2:
        if st.button("I Do Not Agree"):
            # Redirect to withdrawal page
            st.session_state.consent_given = False
            st.switch_page("code/survey/withdrawal.py")

def show_demographics():
    """Render the demographic input form."""
    st.markdown("### 👤 Participant Information")
    st.markdown("Please provide the following information to help us analyze the data.")
    
    with st.form("demographics_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            age = st.number_input("Age", min_value=18, max_value=100, step=1, help="Your age in years")
        
        with col2:
            education = st.selectbox(
                "Highest Level of Education",
                options=["High School", "Some College", "Bachelor's Degree", "Master's Degree", "Doctorate"],
                help="Your highest completed level of education"
            )

        submitted = st.form_submit_button("Continue to Survey")
        
        if submitted:
            if age is None:
                st.error("Please enter your age.")
                return
            
            # Store demographics
            st.session_state.age = age
            st.session_state.education = education
            st.session_state.demographics_submitted = True
            
            # Initialize stimuli sequence
            stimuli_list = ["Professional", "Minimalist", "Low-Quality", "Neutral"]
            st.session_state.stimuli_sequence = select_sequence(stimuli_list, st.session_state.participant_id)
            
            st.rerun()

def render_stimulus(stimulus_name):
    """Render the HTML content for a specific stimulus."""
    stimulus_path = PROJECT_ROOT / "code" / "stimuli" / f"{stimulus_name}.html"
    
    if not stimulus_path.exists():
        st.error(f"Stimulus file not found: {stimulus_name}")
        return None
    
    with open(stimulus_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Use a container to ensure proper rendering
    st.markdown(f"### Stimulus: {stimulus_name}")
    st.markdown("---")
    st.components.v1.html(html_content, height=600, scrolling=True)
    st.markdown("---")

def show_ratings():
    """Render the rating inputs for the current stimulus."""
    stimulus_name = st.session_state.stimuli_sequence[st.session_state.current_stimulus_index]
    
    st.markdown(f"## Rate the following on Credibility and Professionalism")
    st.markdown(f"*Stimulus {st.session_state.current_stimulus_index + 1} of {len(st.session_state.stimuli_sequence)}*")
    
    render_stimulus(stimulus_name)
    
    col1, col2 = st.columns(2)
    
    with col1:
        credibility = st.slider(
            "Credibility",
            min_value=1,
            max_value=7,
            value=4,
            help="1 = Not at all credible, 7 = Extremely credible"
        )
    
    with col2:
        professionalism = st.slider(
            "Professionalism",
            min_value=1,
            max_value=7,
            value=4,
            help="1 = Not at all professional, 7 = Extremely professional"
        )
    
    if st.button("Next Stimulus", type="primary"):
        # Save ratings
        st.session_state.ratings[stimulus_name] = {
            "credibility": credibility,
            "professionalism": professionalism
        }
        
        # Move to next stimulus
        st.session_state.current_stimulus_index += 1
        
        if st.session_state.current_stimulus_index < len(st.session_state.stimuli_sequence):
            st.rerun()
        else:
            # All stimuli rated
            st.session_state.current_stimulus_index = -1 # Mark as complete
            st.rerun()

def validate_all_rated():
    """
    Validate that all stimuli have been rated.
    Returns True if all 4 stimuli are rated, False otherwise.
    """
    required_stimuli = {"Professional", "Minimalist", "Low-Quality", "Neutral"}
    rated_stimuli = set(st.session_state.ratings.keys())
    
    return required_stimuli.issubset(rated_stimuli)

def submit_survey():
    """Handle the final submission of survey data."""
    if not validate_all_rated():
        st.error("⚠️ Please rate all stimuli before submitting.")
        return False
    
    try:
        # Extract metadata
        hashed_ip = extract_and_validate_ip()
        user_agent = st.context.headers.get("User-Agent", "Unknown")
        browser_version = truncate_user_agent(user_agent)
        session_duration = int(time.time() - st.session_state.start_time)
        timestamp = format_timestamp(datetime.now())
        
        # Prepare submission row
        submission_row = prepare_submission_row(
            participant_id=st.session_state.participant_id,
            age=st.session_state.age,
            education=st.session_state.education,
            hashed_ip=hashed_ip,
            timestamp=timestamp,
            browser_version=browser_version,
            session_duration=session_duration,
            ratings=st.session_state.ratings
        )
        
        # Ensure directories exist
        ensure_data_dirs()
        
        # Append to CSV
        append_to_submissions_csv(submission_row)
        
        # Success message
        st.success("✅ Thank you for completing the survey! Your data has been recorded.")
        st.balloons()
        
        # Clear session state for next user (optional, but good practice)
        # st.session_state.clear()
        
        return True
        
    except Exception as e:
        st.error(f"❌ An error occurred during submission: {str(e)}")
        return False

def main():
    """Main application flow."""
    init_session_state()
    
    # Check consent
    if not st.session_state.consent_given:
        show_consent_form()
        return
    
    # Check demographics
    if not st.session_state.demographics_submitted:
        show_demographics()
        return
    
    # Check if all stimuli are rated
    if st.session_state.current_stimulus_index == -1:
        # All stimuli rated, show submission screen
        st.markdown("## 🎉 Survey Complete!")
        st.markdown("You have successfully rated all stimuli.")
        
        if st.button("Submit Survey Data", type="primary"):
            if submit_survey():
                # Optionally show a 'Thank You' page or end
                st.info("You may now close this tab.")
        else:
            # Auto-submit or show status
            st.info("Review your ratings below before submitting.")
            for stim, data in st.session_state.ratings.items():
                st.write(f"**{stim}**: Credibility {data['credibility']}/7, Professionalism {data['professionalism']}/7")
        
        return
    
    # Render current stimulus and ratings
    show_ratings()

if __name__ == "__main__":
    main()
