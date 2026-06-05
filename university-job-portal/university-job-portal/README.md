# University Job Portal

A React + TypeScript application for browsing and applying to university job postings worldwide.

## Features

- **Cascading dropdowns** — Country → University → Job posting
- **8 countries** with 30+ universities and 50+ job postings
- **Progress indicator** showing completion state
- **Success screen** with a summary of the submitted application
- Fully typed with TypeScript
- Responsive layout (mobile-friendly)

## Getting Started

### Prerequisites
- Node.js 18+
- npm 9+

### Install & Run

```bash
npm install
npm run dev
```

Then open [http://localhost:5173](http://localhost:5173) in your browser.

### Build for Production

```bash
npm run build
npm run preview
```

## Project Structure

```
src/
├── components/
│   ├── SelectField.tsx     # Reusable labelled select dropdown
│   ├── ProgressBar.tsx     # Step progress indicator
│   └── SuccessScreen.tsx   # Post-submission confirmation view
├── data.ts                 # Countries, universities, and job postings
├── App.tsx                 # Main app with state management
├── App.css                 # All styles
└── main.tsx                # React entry point
```

## Extending the Data

All data lives in `src/data.ts`. To add more entries:

- Add a new country to the `countries` array with a unique `code`
- Add universities with the matching `countryCode`
- Add job postings with the matching `universityId`
