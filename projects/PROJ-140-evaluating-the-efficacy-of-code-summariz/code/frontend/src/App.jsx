import React, { useEffect, useState } from 'react';
import ParticipantForm from './ParticipantForm';
import { run_calibration } from './utils/latency_calibrator'; // Assumed wrapper for the calibrator module
import './App.css';

/**
 * App Component
 * 
 * Main entry point for the frontend.
 * 
 * Responsibilities:
 * 1. Run latency calibration on startup (FR-003, T012a).
 * 2. Render the ParticipantForm for data collection.
 */
const App = () => {
  const [calibrationStatus, setCalibrationStatus] = useState('pending');

  useEffect(() => {
    // T012a: Integrate latency calibrator into application startup flow
    const initApp = async () => {
      try {
        // Run the calibration check to ensure timestamp precision <= 100ms
        const result = await run_calibration();
        
        if (result.precision_ms <= 100) {
          setCalibrationStatus('passed');
          console.log(`Timestamp precision check passed: ${result.precision_ms}ms`);
        } else {
          setCalibrationStatus('failed');
          console.error(`Timestamp precision check FAILED: ${result.precision_ms}ms > 100ms`);
          // In a strict production environment, we might block rendering here
          // alert("System clock precision is insufficient for this study.");
        }
      } catch (err) {
        setCalibrationStatus('error');
        console.error("Calibration failed to run:", err);
      }
    };

    initApp();
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Code Summarization Bug Localization Study</h1>
        {calibrationStatus === 'pending' && <p>Running system checks...</p>}
        {calibrationStatus === 'passed' && <p className="status-ok">System Ready</p>}
        {calibrationStatus === 'failed' && <p className="status-warning">System Check Warning</p>}
        {calibrationStatus === 'error' && <p className="status-error">System Check Error</p>}
      </header>
      
      <main>
        <ParticipantForm />
      </main>
    </div>
  );
};

export default App;
