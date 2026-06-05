import React from 'react';

interface SuccessScreenProps {
  country: string;
  university: string;
  job: string;
  department: string;
  jobType: string;
  onReset: () => void;
}

const SuccessScreen: React.FC<SuccessScreenProps> = ({
  country,
  university,
  job,
  department,
  jobType,
  onReset,
}) => {
  return (
    <div className="success-screen">
      <div className="success-icon" aria-hidden="true">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
          <circle cx="16" cy="16" r="15" stroke="currentColor" strokeWidth="1.5" />
          <path d="M10 16.5l4 4 8-8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <h2 className="success-title">Application submitted</h2>
      <p className="success-subtitle">Your application has been received. We'll be in touch soon.</p>

      <div className="success-details">
        <div className="detail-row">
          <span className="detail-label">Country</span>
          <span className="detail-value">{country}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">University</span>
          <span className="detail-value">{university}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Position</span>
          <span className="detail-value">{job}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Department</span>
          <span className="detail-value">{department}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Type</span>
          <span className="detail-value">
            <span className={`type-badge type-badge--${jobType.toLowerCase()}`}>{jobType}</span>
          </span>
        </div>
      </div>

      <button className="btn-reset" onClick={onReset}>
        Submit another application
      </button>
    </div>
  );
};

export default SuccessScreen;
