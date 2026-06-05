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
PORTAL_USER=your_portal_email
PORTAL_PASS=your_portal_password

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

## Migrating Existing Supabase Data to Turso

If Turso is empty, keep your Turso variables in `.env` and add the old Supabase/Postgres URL under a separate name:

```env
OLD_DATABASE_URL=postgresql://postgres.your_project:your_password@your_pooler_host:5432/postgres
```

Then run:

```bash
python scripts/migrate_supabase_to_turso.py
```

The script copies `job_posts`, `posting_runs`, `job_templates`, `portal_urls`, and `application_tracking` into Turso using upserts.

## After Running the Script

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
