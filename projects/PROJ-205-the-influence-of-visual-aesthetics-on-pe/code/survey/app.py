import streamlit as st
import os
import sys
import random
import time
import hashlib
import uuid
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.helpers import (
    generate_user_id,
    hash_ip,
    format_timestamp,
    get_consent_log_path,
    log_consent_decision,
    get_submissions_csv_path,
    check_duplicate_ip,
    truncate_user_agent,
    prepare_submission_row,
    append_to_submissions_csv
)
from utils.config import get_consent_file_path, get_irb_protocol_id

# Constants
SESSION_TIMEOUT_SECONDS = 1800  # 30 minutes
MAX_USER_AGENT_LENGTH = 256

def get_project_root():
    return project_root

def init_session_state():
    if 'participant_id' not in st.session_state:
        st.session_state.participant_id = str(uuid.uuid4())
    if 'ratings' not in st.session_state:
        st.session_state.ratings = []
    if 'current_stimulus_index' not in st.session_state:
        st.session_state.current_stimulus_index = 0
    if 'session_status' not in st.session_state:
        st.session_state.session_status = 'active'
    if 'submission_status' not in st.session_state:
        st.session_state.submission_status = 'incomplete'
    if 'last_active' not in st.session_state:
        st.session_state.last_active = time.time()
    if 'consent_given' not in st.session_state:
        st.session_state.consent_given = False

def check_session_timeout():
    if time.time() - st.session_state.last_active > SESSION_TIMEOUT_SECONDS:
        st.session_state.session_status = 'timeout'
        st.session_state.submission_status = 'incomplete'
        return True
    return False

def update_last_active():
    st.session_state.last_active = time.time()

def extract_and_validate_ip():
    """
    Extract IP address from headers.
    Returns (ip_address, error_message).
    If IP cannot be captured, returns (None, "IP capture failed...").
    """
    ip_address = None
    error_message = None

    # Try Streamlit's context headers first
    if hasattr(st, 'context') and hasattr(st.context, 'headers'):
        ip_address = st.context.headers.get('X-Forwarded-For')
    
    # Fallback to experimental request headers
    if not ip_address and hasattr(st, 'experimental_request'):
        ip_address = st.experimental_request.headers.get('X-Forwarded-For')

    # Check if IP was found
    if not ip_address:
        error_message = "IP capture failed: X-Forwarded-For header missing. Please contact support."
        return None, error_message

    # Clean up IP (sometimes X-Forwarded-For contains multiple IPs, take the first)
    ip_address = ip_address.split(',')[0].strip()
    return ip_address, None

def show_consent_form():
    irb_text_path = get_consent_file_path()
    irb_protocol_id = get_irb_protocol_id()

    if not os.path.exists(irb_text_path):
        st.error(f"Consent file not found at {irb_text_path}")
        st.stop()

    with open(irb_text_path, 'r', encoding='utf-8') as f:
        irb_text = f.read()

    st.markdown(f"### IRB Protocol ID: {irb_protocol_id}")
    st.markdown(irb_text)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("I Agree", key="consent_agree"):
            st.session_state.consent_given = True
            log_consent_decision(
                st.session_state.participant_id,
                True,
                irb_protocol_id
            )
            st.rerun()
    with col2:
        if st.button("I Do Not Agree", key="consent_disagree"):
            log_consent_decision(
                st.session_state.participant_id,
                False,
                irb_protocol_id
            )
            st.switch_page("withdrawal.py")

def render_stimulus(stimulus_name):
    stimulus_path = project_root / "code" / "stimuli" / f"{stimulus_name}.html"
    if not stimulus_path.exists():
        st.error(f"Stimulus file not found: {stimulus_path}")
        return

    with open(stimulus_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    st.markdown(f"### Stimulus: {stimulus_name}")
    st.components.v1.html(html_content, height=600, scrolling=True)

def collect_ratings(stimulus_name):
    st.markdown(f"Please rate the credibility of the above content (1 = Not Credible, 7 = Very Credible):")
    credibility = st.slider(f"Credibility Rating for {stimulus_name}", 1, 7, 4, key=f"cred_{stimulus_name}")
    
    st.markdown(f"Please rate the professionalism of the above content (1 = Not Professional, 7 = Very Professional):")
    professionalism = st.slider(f"Professionalism Rating for {stimulus_name}", 1, 7, 4, key=f"prof_{stimulus_name}")
    
    return credibility, professionalism

def show_demographics():
    st.markdown("### Demographics")
    
    education_options = {
        "High School": 1,
        "Bachelor's": 2,
        "Master's": 3,
        "PhD": 4
    }
    
    selected_edu = st.selectbox(
        "Education Level",
        list(education_options.keys()),
        key="demographics_education"
    )
    
    age = st.number_input(
        "Age (years)",
        min_value=18,
        max_value=100,
        value=25,
        key="demographics_age"
    )
    
    return age, education_options[selected_edu]

def save_submission_logic():
    # Get IP and hash it immediately
    raw_ip, ip_error = extract_and_validate_ip()
    
    # T022b: Session Rejection Logic
    if ip_error:
        st.error(ip_error)
        st.stop()  # Terminate session immediately

    hashed_ip = hash_ip(raw_ip)
    
    # Check for duplicate
    duplicate_flag = check_duplicate_ip(hashed_ip)
    
    # Get demographics
    age, education = show_demographics()
    
    # Truncate user agent
    user_agent = st.experimental_request.headers.get('User-Agent', '')[:MAX_USER_AGENT_LENGTH]
    
    # Prepare submission data
    submission_data = []
    for rating_entry in st.session_state.ratings:
        row = prepare_submission_row(
            participant_id=st.session_state.participant_id,
            stimulus_id=rating_entry['stimulus'],
            credibility=rating_entry['credibility'],
            professionalism=rating_entry['professionalism'],
            timestamp=format_timestamp(),
            hashed_ip=hashed_ip,
            age=age,
            education=education,
            duplicate_flag=duplicate_flag,
            session_status=st.session_state.session_status,
            submission_status='complete',
            user_agent=user_agent
        )
        submission_data.append(row)
    
    # Append to CSV
    append_to_submissions_csv(submission_data)
    
    st.success("Thank you for your participation! Your data has been recorded.")
    st.balloons()

def main():
    st.set_page_config(page_title="Visual Aesthetics Survey", layout="wide")
    init_session_state()
    
    # Check for timeout
    if check_session_timeout():
        st.error("Your session has timed out due to inactivity.")
        st.stop()
    
    # Update activity timestamp
    update_last_active()
    
    # Show consent if not given
    if not st.session_state.consent_given:
        show_consent_form()
        return
    
    # Define Latin Square sequences
    sequences = [
        ["Professional", "Minimalist", "Low-Quality", "Neutral"],
        ["Minimalist", "Low-Quality", "Neutral", "Professional"],
        ["Low-Quality", "Neutral", "Professional", "Minimalist"],
        ["Neutral", "Professional", "Minimalist", "Low-Quality"]
    ]
    
    # Select sequence randomly
    if 'selected_sequence' not in st.session_state:
        st.session_state.selected_sequence = random.choice(sequences)
    
    current_sequence = st.session_state.selected_sequence
    
    # Render stimuli sequentially
    if st.session_state.current_stimulus_index < len(current_sequence):
        stimulus_name = current_sequence[st.session_state.current_stimulus_index]
        render_stimulus(stimulus_name)
        
        # Collect ratings
        credibility, professionalism = collect_ratings(stimulus_name)
        
        # Store ratings
        st.session_state.ratings.append({
            'stimulus': stimulus_name,
            'credibility': credibility,
            'professionalism': professionalism
        })
        
        # Move to next stimulus
        st.session_state.current_stimulus_index += 1
        st.rerun()
    else:
        # All stimuli shown, show demographics and submit
        st.markdown("### All stimuli presented. Please provide your demographics.")
        save_submission_logic()

if __name__ == "__main__":
    main()