import React, { useState, useEffect, useRef } from 'react';

/**
 * ParticipantForm Component
 * 
 * Collects interaction data for the bug localization study based on the API contract
 * defined in T018a (contracts/api_participant.md).
 * 
 * Features:
 * - Session management (start, heartbeat, end)
 * - Task display (code snippet, bug description)
 * - Interaction logging (line selection, timestamps)
 * - Latency calibration check (FR-003)
 * - Submission to backend API
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const ParticipantForm = ({ 
  sessionId, 
  participantId, 
  taskData, 
  onSuccess, 
  onError 
}) => {
  const [selectedLine, setSelectedLine] = useState(null);
  const [startTime, setStartTime] = useState(null);
  const [endTime, setEndTime] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [calibrationPassed, setCalibrationPassed] = useState(false);
  
  // Refs for timing precision
  const startTimestampRef = useRef(null);
  const lastHeartbeatRef = useRef(null);
  
  // Initialize session and check latency calibration
  useEffect(() => {
    const initializeSession = async () => {
      try {
        // 1. Start Session via API
        const startResponse = await fetch(`${API_BASE_URL}/api/participant/session/start`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            participant_id: participantId,
            session_id: sessionId
          })
        });
        
        if (!startResponse.ok) throw new Error('Failed to start session');
        
        // 2. Run Latency Calibration (FR-003: precision <= 100ms)
        const calibrationResult = await runLatencyCalibration();
        
        if (calibrationResult.passed) {
          setCalibrationPassed(true);
          setStartTime(Date.now());
          startTimestampRef.current = Date.now();
          
          // Start heartbeat
          const heartbeatInterval = setInterval(() => {
            lastHeartbeatRef.current = Date.now();
          }, 5000); // 5s heartbeat
          
          // Cleanup on unmount
          return () => clearInterval(heartbeatInterval);
        } else {
          setError('Latency calibration failed. Please use a more stable connection.');
          onError?.('Calibration failed');
        }
      } catch (err) {
        setError(err.message);
        onError?.(err);
      }
    };
    
    initializeSession();
  }, [participantId, sessionId, onError]);
  
  /**
   * Runs a quick latency calibration check
   * Measures round-trip time to server to ensure <= 100ms
   */
  const runLatencyCalibration = async () => {
    const start = performance.now();
    try {
      const response = await fetch(`${API_BASE_URL}/api/participant/ping`);
      const end = performance.now();
      const latency = end - start;
      
      // FR-003: Precision <= 100ms
      return { passed: latency <= 100, latency };
    } catch (e) {
      return { passed: false, latency: Infinity };
    }
  };
  
  /**
   * Handle line selection interaction
   */
  const handleLineClick = (lineNumber) => {
    if (!calibrationPassed) return;
    
    setSelectedLine(lineNumber);
    
    // Log interaction immediately to local state
    // (Will be sent on form submission)
  };
  
  /**
   * Submit interaction data to backend
   */
  const handleSubmit = async () => {
    if (selectedLine === null) {
      setError('Please select a line before submitting.');
      return;
    }
    
    if (!calibrationPassed) {
      setError('Session calibration not passed. Cannot submit.');
      return;
    }
    
    setIsSubmitting(true);
    setError(null);
    
    const submitTime = Date.now();
    setEndTime(submitTime);
    
    const interactionData = {
      participant_id: participantId,
      session_id: sessionId,
      task_id: taskData.task_id,
      condition: taskData.condition,
      code_snippet_id: taskData.code_snippet_id,
      selected_line: selectedLine,
      ground_truth_line: taskData.ground_truth_line, // For analysis only, not shown to user
      timestamp_start_ms: startTimestampRef.current,
      timestamp_end_ms: submitTime,
      duration_ms: submitTime - startTimestampRef.current,
      latency_check_ms: (await runLatencyCalibration()).latency
    };
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/participant/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(interactionData)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Submission failed');
      }
      
      const result = await response.json();
      onSuccess?.(result);
      
    } catch (err) {
      setError(err.message);
      onError?.(err);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  if (!calibrationPassed) {
    return (
      <div className="calibration-container">
        <h2>Session Initialization</h2>
        {error ? (
          <div className="error-message">
            <p>Error: {error}</p>
            <button onClick={() => window.location.reload()}>Retry</button>
          </div>
        ) : (
          <p>Calibrating connection precision...</p>
        )}
      </div>
    );
  }
  
  return (
    <div className="participant-form">
      <header>
        <h2>Bug Localization Task</h2>
        <div className="task-info">
          <span>Task ID: {taskData.task_id}</span>
          <span>Condition: {taskData.condition}</span>
        </div>
      </header>
      
      <main>
        <section className="bug-description">
          <h3>Bug Description</h3>
          <p>{taskData.description}</p>
        </section>
        
        <section className="code-viewer">
          <h3>Code Snippet</h3>
          <p>Click on the line you believe contains the bug:</p>
          <div className="code-lines">
            {taskData.code_lines.map((line, index) => (
              <div 
                key={index}
                className={`code-line ${selectedLine === index + 1 ? 'selected' : ''}`}
                onClick={() => handleLineClick(index + 1)}
              >
                <span className="line-number">{index + 1}</span>
                <span className="line-content">{line}</span>
              </div>
            ))}
          </div>
        </section>
        
        {error && (
          <div className="error-message">
            <p>{error}</p>
          </div>
        )}
        
        <div className="actions">
          <button 
            onClick={handleSubmit}
            disabled={selectedLine === null || isSubmitting}
            className="submit-btn"
          >
            {isSubmitting ? 'Submitting...' : 'Submit Selection'}
          </button>
        </div>
      </main>
    </div>
  );
};

export default ParticipantForm;