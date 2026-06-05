import React from 'react';

interface ProgressBarProps {
  totalSteps: number;
  currentStep: number;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ totalSteps, currentStep }) => {
  return (
    <div className="progress-bar" role="progressbar" aria-valuenow={currentStep} aria-valuemin={0} aria-valuemax={totalSteps}>
      {Array.from({ length: totalSteps }, (_, i) => (
        <div
          key={i}
          className={`progress-segment ${i < currentStep ? 'progress-segment--active' : ''}`}
        />
      ))}
    </div>
  );
};

export default ProgressBar;
