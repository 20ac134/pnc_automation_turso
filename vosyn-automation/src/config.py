
import os
from pathlib import Path
from dotenv import load_dotenv
from src.turso_data_manager import TursoDataManager

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def load_portal_urls() -> dict:
    """Load portal URLs from Turso."""
    if not TursoDataManager.is_configured():
        print("Warning: Turso is not configured; portal URLs unavailable")
        return {}

    portal_urls = TursoDataManager().get_portal_url_map()
    if not portal_urls:
        print("Warning: No portal URLs found in Turso table 'portal_urls'")
    return portal_urls

class Config:
    """Central configuration for the application"""
    
    #  WORKER SETTINGS 
    
    WORKER_ID = os.getenv('WORKER_ID', 'WORKER_1')
    POLL_INTERVAL = int(os.getenv('POLL_INTERVAL_SECONDS', '30'))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    
    # FILE PATHS

    SCREENSHOT_DIR = os.getenv('SCREENSHOT_DIR', 'screenshots')
    
    # Ensure screenshot directory exists
    Path(SCREENSHOT_DIR).mkdir(exist_ok=True)
    
    #PORTAL URLS

    PORTAL_URLS = load_portal_urls()
    #CREDENTIAL MANAGEMENT
    
    @staticmethod
    def get_credentials(portal_name: str) -> dict:
        username = os.getenv('PORTAL_USER')
        password = os.getenv('PORTAL_PASS')

        if not username or not password:
            raise ValueError(
                "ERROR with credential, please check the cerendials."
            )
        
        return {
            'username': username,
            'password': password
        }
    
    @staticmethod
    def get_portal_url(portal_name: str) -> dict:
        """Get the login URL for a portal"""
        url = Config.PORTAL_URLS.get(portal_name.lower())
        if not url:
            Config.PORTAL_URLS = load_portal_urls()
            url = Config.PORTAL_URLS.get(portal_name.lower())
        if not url:
            raise ValueError(
                f"URL not found for portal: {portal_name}\n"
            f"Available portals: {list(Config.PORTAL_URLS.keys())}"
            )
        return url
        
    
    @staticmethod
    def has_credentials(portal_name: str) -> bool:
        """Check if credentials exist for a portal (without raising error)"""
       # portal_upper = portal_name.upper()
        username = os.getenv('PORTAL_USER')
        password = os.getenv('PORTAL_PASS')
        return bool(username and password)


#TESTING CODE
if __name__ == "__main__":
    """Test the config system"""
    print("=" * 60)
    print("Testing Config System")
    print("=" * 60)
    print()
    
   
    print("Test 1: Worker Settings")
    print(f"  Worker ID: {Config.WORKER_ID}")
    print(f"  Poll Interval: {Config.POLL_INTERVAL} seconds")
    print(f"  Max Retries: {Config.MAX_RETRIES}")
    print("   Worker settings loaded")
    print()
    
    
    print("Test 2: File Paths")
    print("  Data Storage: Turso")
    print(f"  Screenshot Dir: {Config.SCREENSHOT_DIR}")
    print("  Paths configured")
    print()
    
    
    print("Test 3: Portal URLs")
    try:
        url = Config.get_portal_url('laurentian')
        print(f"  Laurentian URL: {url}")
        print("   Portal URL lookup works")
    except ValueError as e:
        print(f"  Error: {e}")
    print()
    
   
    print("Test 4: Credentials")
    portals_to_test = ['laurentian', 'sfu', 'unb']
    
    for portal in portals_to_test:
        if Config.has_credentials(portal):
            try:
                creds = Config.get_credentials(portal)
                
                print(f"  {portal}: username={creds['username']}, password={'*' * len(creds['password'])}")
            except ValueError as e:
                print(f"   {portal}: {e}")
        else:
            print(f"   {portal}: No credentials set (add to .env)")
    print()
    
    
    print("Test 5: Available Portals")
    print(f"  Total portals configured: {len(Config.PORTAL_URLS)}")
    print(f"  Portals: {', '.join(Config.PORTAL_URLS.keys())}")
    print()
    
    print("=" * 60)
    print(" Config system ready!")
    print("=" * 60)
    print()
    print("Next: Create base_playbook.py")
