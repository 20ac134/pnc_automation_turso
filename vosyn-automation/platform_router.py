import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from src.config import Config
from src.turso_data_manager import TursoDataManager
from src.playbooks.symplicity_playbook import SymplicityPlaybook
# When you build new playbooks, import them here:
from src.playbooks.twelve_twenty_playbook import TwelveTwentyPlaybook
from src.playbooks.targetconnect_playbook import TargetConnectPlaybook
# from src.playbooks.careerhub_playbook import CareerHubPlaybook
from src.playbooks.VIUPlaybook import VIUPlaybook
from src.playbooks.trivio_playbook import TrivioPlaybook
from src.playbooks.Msform_playbook import MSFormsPlaybook

import pandas as pd


# ------------------------------------------------------------------ #
#  PLATFORM DETECTION                                                  #
# ------------------------------------------------------------------ #

def detect_platform(url: str) -> str:
    """
    Detect which platform a portal uses just from its URL.
    Returns a platform key string.
    """
    url = url.lower()
    if 'studentemployment.viu.ca' in url:
        return 'viu'
    if 'trivio.usherbrooke.ca' in url:
        return 'trivio'
    symplicity_custom_domains = [
        # --- CONFIRMED SYMPLICITY ---
        'uregina-csm.symplicity.com',
        'royalroads-csm.symplicity.com',
        'careerhub.laurentian.ca',

        # --- CANADIAN UNIVERSITIES (custom domain) ---
        'excel.concordia.ca',           # Concordia
        'experience.unb.ca',            # UNB
        'experience.mta.ca',            # MTA
        'navigator.wlu.ca',             # WLU
        'ccr.trentu.ca',                # Trent
        'studentemployment.viu.ca',     # VIU
        'career360.smu.ca',             # SMU
        'mysuccess.lakeheadu.ca',       # Lakehead
        'trivio.usherbrooke.ca',        # Sherbrooke
        'cldc.telfer.uottawa.ca',       # Ottawa
        'careers.sso.queensu.ca',       # Queens
        'careerlink.usask.ca',          # Saskatchewan
        'crm.stuaff.mun.ca',            # MUN
        'experienceguelph.ca',          # Guelph
        'myexperience.sfu.ca',          # SFU
        'clnx.utoronto.ca',             # UToronto
        'laruche.polymtl.ca',           # PolyMTL
        'macarriere.hec.ca',            # HEC
        'outcomecampusconnect.poweredbymagnet.ca',  # Outcome Campus
        'hire.redeemer.ca',             # Redeemer
        'emplois.uqam.ca',              # UQAM
        'rc-utoronto-csm.symplicity.com', # UToronto Rotman
        'sauder-ubc-csm.symplicity.com',  # UBC Sauder
    ]
    if any(domain in url for domain in symplicity_custom_domains):
        return 'symplicity'

    # --- Explicit platform domains ---
    if 'symplicity.com' in url:
        return 'symplicity'
    if '12twenty.com' in url:
        return '12twenty'
    if 'targetconnect.net' in url:
        return 'targetconnect'
    if 'careerhub' in url or 'mycareerhub' in url or 'careershub' in url \
            or 'myadvantage' in url or 'unihub' in url \
            or 'mycareercentral' in url or 'myfuture' in url or 'methub' in url:
        return 'careerhub'
    if 'gradleaders.com' in url:
        return 'gradleaders'
    if 'mbafocus.com' in url:
        return 'mbafocus'
    if 'poweredbymagnet.ca' in url:
        return 'magnet'
    if 'wp-login.php' in url:
        return 'wordpress'
    if 'forms.office.com' in url:
        return 'msforms'

    # --- TargetConnect on custom domains ---
    # These universities use TargetConnect but with their own domain
    if '/unauth/employer/login' in url:
        return 'targetconnect'

    # --- Symplicity on custom domains ---
    # These universities run Symplicity but with their own domain
    # Identified by URL patterns common to Symplicity portals
    
    

    return 'unknown'


# ------------------------------------------------------------------ #
#  PLAYBOOK ROUTER                                                     #
# ------------------------------------------------------------------ #

# Map platform → playbook class
# Add new platforms here as you build their playbooks
PLATFORM_PLAYBOOK_MAP = {
    'symplicity':    SymplicityPlaybook,
    '12twenty':    TwelveTwentyPlaybook,     
     'targetconnect': TargetConnectPlaybook,   # not built yet
    # 'careerhub':   CareerHubPlaybook,         # not built yet
    'viu': VIUPlaybook,
    'trivio': TrivioPlaybook,
    'msforms': MSFormsPlaybook,
}

def get_playbook_class(url: str):
    """
    Given a portal URL, detect its platform and return
    the appropriate playbook class. Returns None if not supported yet.
    """
    platform = detect_platform(url)

    playbook_class = PLATFORM_PLAYBOOK_MAP.get(platform)

    if not playbook_class:
        print(f"Platform '{platform}' detected but no playbook built yet.")
        print(f"URL: {url}")
        return None, platform

    return playbook_class, platform


# ------------------------------------------------------------------ #
#  MAIN                                                                #
# ------------------------------------------------------------------ #

if __name__ == "__main__":

    print("=" * 60)
    print("Vosyn Portal Router")
    print("=" * 60)
    print()
    portal_map = {
        str(row["#"]): row["PortalKey"]
        for _, row in TursoDataManager().get_portal_urls_df().iterrows()
    }

    print("Available Portals:")
    for num, name in portal_map.items():
        # Show platform next to each portal
        try:
            url = Config.get_portal_url(name)
            platform = detect_platform(url)
            supported = "✓" if platform in PLATFORM_PLAYBOOK_MAP else "✗"
            print(f"{num:>3}. {name.upper():<20} [{platform}] {supported}")
        except:
            print(f"{num:>3}. {name.upper():<20} [url not found]")
    print()
    print("✓ = supported   ✗ = playbook not built yet")
    print()

    # Select portal
    while True:
        choice = input("Select portal number: ").strip()
        if choice in portal_map:
            selected_portal = portal_map[choice]
            break
        print("Invalid choice.")

    print()
    print(f"Selected: {selected_portal.upper()}")
    print()

    # Get portal URL and detect platform
    portal_url = Config.get_portal_url(selected_portal)
    platform   = detect_platform(portal_url)
    print(f"URL:      {portal_url}")
    print(f"Platform: {platform.upper()}")
    print()

    # Get playbook class
    PlaybookClass, platform = get_playbook_class(portal_url)

    if not PlaybookClass:
        print(f"Cannot proceed — no playbook built for '{platform}' yet.")
        print("Playbooks built so far: Symplicity")
        print("Coming soon: 12Twenty, TargetConnect, CareerHub")
        exit()

    # Fetch job from Excel
    em = TursoDataManager()
    df_runs = em.get_posting_runs_df()

    portal_runs = df_runs[
        (df_runs['PortalName'].str.lower() == selected_portal.lower()) &
        (df_runs['RunStatus'] == 'QUEUED')
    ]

    if portal_runs.empty:
        print(f"No queued runs found for {selected_portal}")
        exit()

    matching_run = portal_runs.iloc[0].to_dict()
    job_id       = matching_run['JobId']

    job = em.get_job(job_id)
    if not job:
        print(f"Job {job_id} not found in JobPosts sheet")
        exit()

    print(f"Job ID:   {job_id}")
    print(f"Title:    {job['Title']}")
    print(f"Location: {job['Location']}")
    print(f"Salary:   {job.get('Salary', '')}")
    print()

    # Get credentials
    credentials = Config.get_credentials(selected_portal)
    print(f"Username: {credentials['username']}")
    print()

    # Run the correct playbook
    playbook = PlaybookClass(
        portal_url=portal_url,
        credentials=credentials,
        job_data={
    "JobId":               job_id,
    "Title":               job["Title"],
    "Description":         job["Description"],
    "Location":            job.get("Location", ""),
    "City":                job.get("City", "Toronto"),
    "Country":             job.get("Country", "Canada"),
    "Salary":              job.get("Salary", ""),
    "JobType":             job.get("JobType", "Internship"),
    "Industry":            job.get("Industry", "Technology"),
    "JobFunction":         job.get("JobFunction", "Software Engineering"),
    "StudentGroup":        job.get("StudentGroup", "All Students"),
    "StartDate":           job.get("StartDate", ""),
    "ApplicationDeadline": job.get("ApplicationDeadline", ""),
    "portal_name":         selected_portal,
}
    )

    result = playbook.execute()
    print()
    print(f"Result: {result['status']}")
    print()
    print("=" * 60)
    print("COMPLETE")
    print("=" * 60)
