# Vosyn Job Posting Automation

Automated job posting system for 21 Canadian university portals.

## Setup

1. Install Python 3.10+
2. Create virtual environment: `python -m venv venv`
3. Activate venv:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Fill in credentials, `TURSO_DATABASE_URL`, and `TURSO_AUTH_TOKEN` in `.env`
6. Run the app once or run `python TestSetup.py` to create the default tables: `job_posts`, `posting_runs`, `job_templates`, `portal_urls`, and `application_tracking`

## Environment Variables (.env)

# Vosyn Portal Credentials
# IMPORTANT: Fill in your actual credentials, never commit this file!
LAURENTIAN_USER=careers@vosyn.ai LAURENTIAN_PASS=@HRvoSYn123*!

SFU_USER=careers@vosyn.ai SFU_PASS=@HRvoSYn123*!

CONCORDIA_USER=careers@vosyn.ai CONCORDIA_PASS=@HRvoSYn123*!

SASKATCHEWAN_USER=careers@vosyn.ai SASKATCHEWAN_PASS=@HRvoSYn123*!

UNB_USER=careers@vosyn.ai UNB_PASS=@HRvoSYn123*!

MTA_USER=careers@vosyn.ai MTA_PASS=@HRvoSYn123*!

WLU_USER=careers@vosyn.ai WLU_PASS=@HRvoSYn123*!

REGINA_USER=careers@vosyn.ai REGINA_PASS=@HRvoSYn123*!

ROYALROADS_USER=careers@vosyn.ai ROYALROADS_PASS=@HRvoSYn123*!

TALENTHQ_USER=careers@vosyn.ai TALENTHQ_PASS=@HRvoSYn123*!

OUTCOMECAMPUSCONNECT_USER=careers@vosyn.ai OUTCOMECAMPUSCONNECT_PASS=@HRvoSYn123*!

GUELPH_USER=careers@vosyn.ai GUELPH_PASS=@HRvoSYn123*!

QUEENS_USER=careers@vosyn.ai QUEENS_PASS=@HRvoSYn123*!

MUN_USER=careers@vosyn.ai MUN_PASS=@HRvoSYn123*!

OTTAWA_USER=careers@vosyn.ai OTTAWA_PASS=@HRvoSYn123*!

POLYMTL_USER=careers@vosyn.ai POLYMTL_PASS=@HRvoSYn123*!

HEC_USER=careers@vosyn.ai HEC_PASS=@HRvoSYn123*!

TRENTU_USER=careers@vosyn.ai TRENTU_PASS=@HRvoSYn123*!

SHERBROOKE_USER=careers@vosyn.ai SHERBROOKE_PASS=@HRvoSYn123*!

VIU_USER=careers@vosyn.ai VIU_PASS=@HRvoSYn123*!

UCN_USER = careers@vosyn.ai UCN_PASS = @HRvoSYn123*!

# Turso/libSQL
TURSO_DATABASE_URL=libsql://your-database-your-org.turso.io
TURSO_AUTH_TOKEN=your_turso_auth_token

# Worker Configuration
WORKER_ID=WORKER_1
POLL_INTERVAL_SECONDS=30
MAX_RETRIES=3

# Screenshots
SCREENSHOT_DIR=screenshots

## Running the Worker

```bash
python src/main.py
```

## Running the automation Script

python -m src.playbooks.symplicity_playbook

## Turso Data Storage

The app reads and writes directly to Turso. Run the app once or run `python TestSetup.py` to create and verify the required tables.

## After Running the Automation

- The automation will navigate to the selected university portal and pre-fill the job posting form.

- Once completed, the system will indicate that the form has been filled and is ready for review.

- The user must review the populated fields and manually submit the posting.

- Execution logs will be generated inside the logs/ directory.

- Turso tables will be updated based on the posting status and tracking events.

## Project Structure

- `src/` - Main source code
  - `playbooks/` - Portal-specific automation scripts
  - `utils/` - Helper utilities
- `data/` - Optional local exports and placeholder files
- `screenshots/` - Proof of posting screenshots
- `logs/` - Worker logs
- `tests/` - Test files

## Portals Supported

### Symplicity (9 portals)
- Laurentian, SFU, Concordia, Saskatchewan, UNB, MTA, WLU, Regina, Royal Roads

### Magnet (2 portals)
- TalentHQ, Outcome Campus Connect

### Custom (10 portals)
- Guelph, Queen's, Memorial, Ottawa, Polytechnique Montreal, HEC, Trent, Sherbrooke, VIU



## Security

- Never commit `.env` file
- Keep credentials secure
- Screenshots may contain sensitive info
