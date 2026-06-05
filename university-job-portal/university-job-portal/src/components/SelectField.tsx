import React from 'react';

interface Option {
  value: string;
  label: string;
}

interface SelectFieldProps {
  stepNumber: number;
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Option[];
  placeholder: string;
  disabled?: boolean;
  helperText?: string;
  isDone?: boolean;
}

const SelectField: React.FC<SelectFieldProps> = ({
  stepNumber,
  label,
  value,
  onChange,
  options,
  placeholder,
  disabled = false,
  helperText,
  isDone = false,
}) => {
  return (
    <div className={`field ${disabled ? 'field--disabled' : ''}`}>
      <label className="field__label">
        <span className={`step-badge ${isDone ? 'step-badge--done' : ''} ${!disabled && !isDone ? 'step-badge--active' : ''}`}>
          {isDone ? '✓' : stepNumber}
        </span>
        {label}
      </label>
      <div className="select-wrapper">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          className="select-input"
        >
          <option value="">{placeholder}</option>
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <span className="select-chevron" aria-hidden="true">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </span>
      </div>
      {helperText && !disabled && (
        <p className="field__helper">{helperText}</p>
      )}
    </div>
  );
};

export default SelectField;
