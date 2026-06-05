"""
Vosyn Automation - Automated Project Setup Script
Run this after creating your project directory and activating venv
"""

import os
import sys
from pathlib import Path

def create_directory_structure():
    """Create all necessary directories"""
    print("Creating directory structure...")
    
    directories = [
        'src',
        'src/playbooks',
        'src/utils',
        'tests',
        'data',
        'screenshots',
        'logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f" Created: {directory}/")
    
    # Create __init__.py files
    init_files = [
        'src/__init__.py',
        'src/playbooks/__init__.py',
        'src/utils/__init__.py',
        'tests/__init__.py'
    ]
    
    for init_file in init_files:
        Path(init_file).touch()
        print(f" Created: {init_file}")


''''def create_gitignore():
    """Create .gitignore file"""
    print("\nCreating .gitignore...")
    
    gitignore_content = """# Python
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/

# Environment variables (IMPORTANT - keeps credentials safe)
.env

# Local data exports
data/*
!data/.gitkeep

# Screenshots
screenshots/*.png
!screenshots/.gitkeep

# Logs
logs/*.log
!logs/.gitkeep

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
"""
    
    with open('.gitignore', 'w') as f:
        f.write(gitignore_content)
    
    print(" Created: .gitignore")

'''
def create_env_template():
    """Create .env template file"""
    print("\nCreating .env template...")
    env_path = Path('.env')
    if env_path.exists():
        print(" Skipped: .env already exists")
        return
    
    env_content = """# Vosyn Portal Credentials
# IMPORTANT: Fill in your actual credentials, never commit this file!

# Symplicity Portals
LAURENTIAN_USER=your_username_here
LAURENTIAN_PASS=your_password_here

SFU_USER=your_username_here
SFU_PASS=your_password_here

CONCORDIA_USER=your_username_here
CONCORDIA_PASS=your_password_here

SASKATCHEWAN_USER=your_username_here
SASKATCHEWAN_PASS=your_password_here

UNB_USER=your_username_here
UNB_PASS=your_password_here

MTA_USER=your_username_here
MTA_PASS=your_password_here

WLU_USER=your_username_here
WLU_PASS=your_password_here

REGINA_USER=your_username_here
REGINA_PASS=your_password_here

ROYALROADS_USER=your_username_here
ROYALROADS_PASS=your_password_here

# Magnet Portals
TALENTHQ_USER=your_username_here
TALENTHQ_PASS=your_password_here

OUTCOMECAMPUSCONNECT_USER=your_username_here
OUTCOMECAMPUSCONNECT_PASS=your_password_here

# Custom Portals
GUELPH_USER=your_username_here
GUELPH_PASS=your_password_here

QUEENS_USER=your_username_here
QUEENS_PASS=your_password_here

MUN_USER=your_username_here
MUN_PASS=your_password_here

OTTAWA_USER=your_username_here
OTTAWA_PASS=your_password_here

POLYMTL_USER=your_username_here
POLYMTL_PASS=your_password_here

HEC_USER=your_username_here
HEC_PASS=your_password_here

TRENTU_USER=your_username_here
TRENTU_PASS=your_password_here

SHERBROOKE_USER=your_username_here
SHERBROOKE_PASS=your_password_here

VIU_USER=your_username_here
VIU_PASS=your_password_here

# Worker Configuration
WORKER_ID=WORKER_1
POLL_INTERVAL_SECONDS=30
MAX_RETRIES=3

# Turso/libSQL
TURSO_DATABASE_URL=libsql://your-database-your-org.turso.io
TURSO_AUTH_TOKEN=your_turso_auth_token

# Screenshots
SCREENSHOT_DIR=screenshots
"""
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(" Created: .env (template - FILL IN YOUR CREDENTIALS!)")


def create_readme():
    """Create README.md"""
    print("\nCreating README.md...")
    
    readme_content = """# Vosyn Job Posting Automation

Automated job posting system for 21 Canadian university portals.

## Setup

1. Install Python 3.10+
2. Create virtual environment: `python -m venv venv`
3. Activate venv:
   - Windows: `venv\\Scripts\\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Fill in credentials, `TURSO_DATABASE_URL`, and `TURSO_AUTH_TOKEN` in `.env`
6. Run the app once or run `python TestSetup.py` to create the default tables: `job_posts`, `posting_runs`, `job_templates`, `portal_urls`, and `application_tracking`

## Running the Worker

```bash
python src/main.py
```

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

## Development

Day 1: Setup and prerequisites
Day 2-3: Core infrastructure (Turso data manager, config, base playbook)
Day 4-5: First playbook (Symplicity)
Day 6: Worker loop
Day 7: Testing

## Security

- Never commit `.env` file
- Keep credentials secure
- Screenshots may contain sensitive info
"""
    
    with open('README.md', 'w') as f:
        f.write(readme_content)
    
    print(" Created: README.md")


def create_keepfiles():
    """Create .gitkeep files for empty directories"""
    print("\nCreating .gitkeep files...")
    
    keepfiles = [
        'data/.gitkeep',
        'screenshots/.gitkeep',
        'logs/.gitkeep'
    ]
    
    for keepfile in keepfiles:
        Path(keepfile).touch()
        print(f" Created: {keepfile}")


def check_requirements():
    """Check if requirements.txt exists and is populated"""
    print("\nChecking requirements.txt...")
    
    if Path('requirements.txt').exists():
        with open('requirements.txt', 'r') as f:
            content = f.read()
            if content.strip():
                print(" requirements.txt already exists with packages")
            else:
                print("  requirements.txt is empty - run 'pip freeze > requirements.txt' after installing packages")
    else:
        print("  requirements.txt not found - will be created when you run 'pip freeze > requirements.txt'")


def main():
    """Main setup function"""
    print("=" * 60)
    print("Vosyn Automation - Project Setup")
    print("=" * 60)
    print()
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("  WARNING: You don't appear to be in a virtual environment!")
        print("   It's recommended to create and activate one first:")
        print("   1. python -m venv venv")
        print("   2. venv\\Scripts\\activate (Windows) or source venv/bin/activate (Mac/Linux)")
        print()
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return
    
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print()
    
    # Run setup steps
    create_directory_structure()
    #create_gitignore()
    create_env_template()
    create_readme()
    create_keepfiles()
    check_requirements()
    
    print()
    print("=" * 60)
    print(" Setup Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Install packages: pip install -r requirements.txt")
    print("2. Save requirements: pip freeze > requirements.txt")
    print("3. Fill in your credentials in .env file")
    print("4. Confirm TURSO_DATABASE_URL and TURSO_AUTH_TOKEN point to Turso")
    print("5. Run test: python TestSetup.py")
    print()
    print("Ready for Day 2! ")


if __name__ == "__main__":
    main()
