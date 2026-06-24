from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import time
import random
import os
import shutil
import platform
import subprocess
import re
from datetime import datetime
from pathlib import Path
from abc import ABC, abstractmethod
import threading
import tempfile


_DRIVER_INIT_LOCK = threading.Lock()

class BasePortalPlaybook(ABC):
  
    
    def __init__(self, portal_url: str, credentials: dict, job_data: dict, screenshot_dir: str = "screenshots"):
        self.portal_url = portal_url
        self.credentials = credentials
        self.job_data = job_data
        self.screenshot_dir = Path(screenshot_dir)
        self.screenshot_dir.mkdir(exist_ok=True)
        self.driver = None
        self.wait = None
        self.run_id = None  # Set by API when running via frontend

    @staticmethod
    def _get_chrome_major_version() -> int | None:
        """Detect installed Chrome version across macOS, Windows, and Linux."""
        system_os = platform.system()

        if system_os == "Darwin":
            try:
                out = subprocess.check_output(
                    ["defaults", "read", "/Applications/Google Chrome.app/Contents/Info.plist", "CFBundleShortVersionString"],
                    stderr=subprocess.DEVNULL
                ).decode().strip()
                match = re.search(r"^(\d+)\.", out)
                if match:
                    return int(match.group(1))
            except Exception:
                pass

        elif system_os == "Windows":
            try:
                import winreg
                keys = [
                    (winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon"),
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Google Chrome")
                ]
                for root, path in keys:
                    try:
                        with winreg.OpenKey(root, path) as key:
                            try:
                                val, _ = winreg.QueryValueEx(key, "version")
                                match = re.search(r"^(\d+)\.", str(val))
                                if match:
                                    return int(match.group(1))
                            except FileNotFoundError:
                                pass
                    except Exception:
                        continue
            except Exception:
                pass

        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "google-chrome",
            "chromium-browser",
            "chromium",
        ]

        for cmd in candidates:
            try:
                out = subprocess.check_output(
                    [cmd, "--version"],
                    stderr=subprocess.DEVNULL
                ).decode()

                match = re.search(r"(\d+)\.\d+\.\d+", out)
                if match:
                    return int(match.group(1))
            except Exception:
                continue

        return None

    @staticmethod
    def _clear_uc_cache():
        """Clear undetected_chromedriver's downloaded binary cache after version conflicts."""
        system_os = platform.system()
        paths_to_clear = []
        home = Path.home()

        if system_os == "Darwin":
            paths_to_clear.append(home / "Library" / "Application Support" / "undetected_chromedriver")
        elif system_os == "Windows":
            appdata = os.environ.get("APPDATA")
            localappdata = os.environ.get("LOCALAPPDATA")
            if appdata:
                paths_to_clear.append(Path(appdata) / "undetected_chromedriver")
            if localappdata:
                paths_to_clear.append(Path(localappdata) / "undetected_chromedriver")
        else:
            paths_to_clear.append(home / ".config" / "undetected_chromedriver")
            paths_to_clear.append(home / ".local" / "share" / "undetected_chromedriver")

        for path in paths_to_clear:
            if path.exists():
                try:
                    print(f"Clearing stale chromedriver cache directory: {path}")
                    shutil.rmtree(path, ignore_errors=True)
                except Exception as e:
                    print(f"Could not clear cache at {path}: {e}")

    def setup_driver(self):
        user_data_dir = tempfile.mkdtemp(prefix="uc_profile_")
        options = uc.ChromeOptions()
        options.add_argument(f"--user-data-dir={user_data_dir}")
            
        width = random.randint(1200, 1920)
        height = random.randint(800, 1080)
        options.add_argument(f'--window-size={width},{height}')
        
        prefs = {"profile.default_content_setting_values.notifications": 2}
        options.add_experimental_option("prefs", prefs)

        chrome_version = self._get_chrome_major_version()
        if chrome_version:
            print(f"Detected Chrome version: {chrome_version}")
        else:
            print("Could not detect Chrome version, letting uc auto-detect")

        with _DRIVER_INIT_LOCK:
            try:
                self.driver = uc.Chrome(
                    options=options,
                    version_main=chrome_version,
                    driver_executable_path=None,
                    use_subprocess=True,
                )
            except Exception as e:
                print(f"Primary driver init failed: {e}")
                print("Initiating self-healing routine (clearing downloaded caches)...")
                self._clear_uc_cache()
                os.environ["UC_DRIVER_CACHE"] = "0"

                try:
                    self.driver = uc.Chrome(
                        options=options,
                        version_main=chrome_version,
                        driver_executable_path=None,
                        use_subprocess=True,
                    )
                except Exception as retry_error:
                    print(f"Secondary driver init failed: {retry_error}")
                    print("Attempting final fallback using framework auto-detection parameters...")
                    self.driver = uc.Chrome(
                        options=options,
                        driver_executable_path=None,
                        use_subprocess=True,
                    )
        
        self.wait = WebDriverWait(self.driver, 15)
        
       
        
        print(f"Browser initialized (window size: {width}x{height})")

    def human_delay(self, min_sec: float = 2, max_sec: float = 5):
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)

    def slow_type(self, element, text: str, min_delay: float = 0.05, max_delay: float = 0.15):
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(min_delay, max_delay))

   

    @abstractmethod
    def login(self):
        pass

    @abstractmethod
    def navigate_to_job_posting(self):
        pass

    @abstractmethod
    def fill_job_form(self):
        pass

    @abstractmethod
    def submit_and_capture_proof(self) -> dict:
        pass

    def execute(self) -> dict:
        try:
            print("=" * 60)
            print(f"Starting automation for {self.job_data.get('Title', 'Unknown Job')}")
            print(f"Portal: {self.portal_url}")
            print("=" * 60)
            
            print("\n[1/5] Setting up browser")
            self.setup_driver()
            self.human_delay(1, 2)
            
            print("\n[2/5] Logging in")
            self.login()
            self.human_delay(2, 4)
            
            print("\n[3/5] Navigating to job posting form")
            self.navigate_to_job_posting()
            self.human_delay(2, 3)
            
            print("\n[4/5] Filling job form")
            self.fill_job_form()
            self.human_delay(2, 3)
            
            print("\n[5/5] Submitting and capturing proof")
            result = self.submit_and_capture_proof()
            
            print("\n" + "=" * 60)
            print("SUCCESS!")
            print(f"Confirmation ID: {result.get('confirmation_id')}")
            print(f"Screenshot: {result.get('screenshot_path')}")
            print("=" * 60)
            
            return {
                'status': 'POSTED',
                'confirmation_id': result.get('confirmation_id'),
                'screenshot_path': result.get('screenshot_path')
            }
            
        except Exception as e:
            print("\n" + "=" * 60)
            print("FAILED!")
            print(f"Error: {str(e)}")
            print("=" * 60)
    
    
        
        finally:
            if self.driver:
                print("\nClosing browser")
                self.driver.quit()

    def safe_find_element(self, by, value, timeout: int = 10):
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.presence_of_element_located((by, value)))

    def safe_click(self, by, value, timeout: int = 10):
        wait = WebDriverWait(self.driver, timeout)
        element = wait.until(EC.element_to_be_clickable((by, value)))
        element.click()


#TESTING CODE 

if __name__ == "__main__":
   
    class TestPlaybook(BasePortalPlaybook):
        """Simple test implementation"""
        
        def login(self):
            print("  → Opening Google (test URL)")
            self.driver.get("https://www.google.com")
            self.human_delay(2, 3)
        
        def navigate_to_job_posting(self):
            print("  → Simulating navigation")
            self.human_delay(1, 2)
        
        def fill_job_form(self):
            print("  → Simulating form fill")
            # Find search box and type slowly
            search_box = self.driver.find_element(By.NAME, "q")
            self.slow_type(search_box, "Selenium automation test")
            self.human_delay(1, 2)
        
        def submit_and_capture_proof(self):
            print (" -> Done")
            return {
                'confirmation_id': "TEST_12345",
            }
    
    print("=" * 60)
    print("Testing Base Playbook")
    print("=" * 60)
    print()
    
    # Test data
    test_job = {
        'JobId': 'TEST_001',
        'Title': 'Test Job - Software Engineer',
        'Description': 'This is a test',
        'Location': 'Toronto, ON'
    }
    
    test_creds = {
        'username': 'test@example.com',
        'password': 'test123'
    }
    
    # Run test
    playbook = TestPlaybook(
        portal_url='https://www.google.com',
        credentials=test_creds,
        job_data=test_job
    )
    
    result = playbook.execute()
    
    print("\nResult:")
    print(f"Status: {result['status']}")
    print(f"Confirmation ID: {result.get('confirmation_id')}")
    print()
    print("Base playbook test complete!")
