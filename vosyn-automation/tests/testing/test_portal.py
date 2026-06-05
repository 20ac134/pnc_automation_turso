"""
Vosyn Portal Automated Test Harness
====================================
Runs through each Canadian portal and generates a detailed diagnostic report.

Tests each stage:
  1. URL Reachability  — can the browser reach the portal?
  2. Platform Detection — does detect_platform() return the correct platform?
  3. Login             — field detection, credential entry, button click, post-login state
  4. Navigation        — "Post a Job" button, category modal, "Post a New Job"
  5. Form Scan         — what fields exist, which match keywords, which required fields are unmapped

Outputs:
  - Console summary
  - Detailed report:  reports/portal_test_report_YYYYMMDD_HHMMSS.txt
  - Screenshots at each stage: screenshots/test_<portal>_<stage>_<timestamp>.png
"""

import sys
import time
import random
import traceback
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
#  PATH SETUP — mirror what the playbooks do
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.config import Config
from platform_router import detect_platform, PLATFORM_PLAYBOOK_MAP

# ---------------------------------------------------------------------------
#  CONFIGURATION
# ---------------------------------------------------------------------------

# Canadian portals to test (from the Turso portal_urls table)
# Excluding: nipissing (MS Forms), talenthq (Magnet), ucn (Magnet)
CANADIAN_PORTALS = [
    {"key": "laurentian",   "name": "Laurentian University",        "platform_expected": "symplicity"},
    {"key": "sfu",          "name": "Simon Fraser University",      "platform_expected": "symplicity"},
    {"key": "concordia",    "name": "Concordia University",         "platform_expected": "symplicity"},
    {"key": "mun",          "name": "Memorial University",          "platform_expected": "symplicity"},
    {"key": "guelph",       "name": "University of Guelph",        "platform_expected": "symplicity"},
    {"key": "saskatchewan", "name": "University of Saskatchewan",   "platform_expected": "symplicity"},
    {"key": "ottawa",       "name": "University of Ottawa",         "platform_expected": "symplicity"},
    {"key": "queens",       "name": "Queen's University",           "platform_expected": "symplicity"},
    {"key": "unb",          "name": "University of New Brunswick",  "platform_expected": "symplicity"},
    {"key": "regina",       "name": "University of Regina",         "platform_expected": "symplicity"},
    {"key": "polymtl",      "name": "Polytechnique Montréal",       "platform_expected": "symplicity"},
    {"key": "hec",          "name": "HEC Montréal",                 "platform_expected": "symplicity"},
    {"key": "mta",          "name": "Mount Allison University",     "platform_expected": "symplicity"},
    {"key": "royalroads",   "name": "Royal Roads University",       "platform_expected": "symplicity"},
    {"key": "trent",        "name": "Trent University",             "platform_expected": "symplicity"},
    {"key": "sherbrooke",   "name": "Université de Sherbrooke",     "platform_expected": "symplicity"},
    {"key": "viu",          "name": "Vancouver Island University",  "platform_expected": "symplicity"},
    {"key": "wlu",          "name": "Wilfrid Laurier University",   "platform_expected": "symplicity"},
    {"key": "smu",          "name": "Saint Mary's University",      "platform_expected": "symplicity"},
]

REPORT_DIR = PROJECT_ROOT / "reports"
SCREENSHOT_DIR = PROJECT_ROOT / "screenshots"

REPORT_DIR.mkdir(exist_ok=True)
SCREENSHOT_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
#  HELPERS
# ---------------------------------------------------------------------------

def take_screenshot(driver, portal_key: str, stage: str) -> str:
    """Save a screenshot and return the file path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_{portal_key}_{stage}_{timestamp}.png"
    filepath = SCREENSHOT_DIR / filename
    try:
        driver.save_screenshot(str(filepath))
        return str(filepath)
    except Exception:
        return "SCREENSHOT_FAILED"


def create_driver():
    """Create a fresh undetected-chromedriver instance."""
    options = uc.ChromeOptions()
    width = random.randint(1200, 1920)
    height = random.randint(800, 1080)
    options.add_argument(f"--window-size={width},{height}")
    prefs = {"profile.default_content_setting_values.notifications": 2}
    options.add_experimental_option("prefs", prefs)
    driver = uc.Chrome(options=options, version_main=147)
    wait = WebDriverWait(driver, 15)
    return driver, wait


def human_delay(min_s=1.0, max_s=3.0):
    time.sleep(random.uniform(min_s, max_s))


# ---------------------------------------------------------------------------
#  STAGE 1: URL REACHABILITY
# ---------------------------------------------------------------------------

def test_url_reachability(driver, url: str) -> dict:
    """Navigate to the portal URL and check if we get blocked or can load."""
    result = {
        "status": "UNKNOWN",
        "page_title": "",
        "final_url": "",
        "blocked": False,
        "error": None,
        "time_seconds": 0,
    }

    start = time.time()
    try:
        driver.get(url)
        human_delay(3, 5)

        result["final_url"] = driver.current_url
        result["page_title"] = driver.title

        page_source = driver.page_source.lower()

        # Check for Cloudflare / bot block
        if "you have been blocked" in page_source or "attention required" in page_source:
            result["status"] = "BLOCKED"
            result["blocked"] = True
        elif "access denied" in page_source:
            result["status"] = "BLOCKED"
            result["blocked"] = True
        elif "403 forbidden" in page_source:
            result["status"] = "BLOCKED"
            result["blocked"] = True
        else:
            result["status"] = "PASS"

    except Exception as e:
        result["status"] = "FAIL"
        result["error"] = str(e)

    result["time_seconds"] = round(time.time() - start, 2)
    return result


# ---------------------------------------------------------------------------
#  STAGE 2: PLATFORM DETECTION
# ---------------------------------------------------------------------------

def test_platform_detection(url: str, expected: str) -> dict:
    """Check if detect_platform() returns the expected platform."""
    detected = detect_platform(url)
    has_playbook = detected in PLATFORM_PLAYBOOK_MAP

    return {
        "status": "PASS" if detected == expected else "FAIL",
        "detected": detected,
        "expected": expected,
        "has_playbook": has_playbook,
    }


# ---------------------------------------------------------------------------
#  STAGE 3: LOGIN
# ---------------------------------------------------------------------------

def test_login(driver, wait, credentials: dict) -> dict:
    """Attempt to find login fields, enter credentials, and click login."""
    result = {
        "status": "UNKNOWN",
        "username_field_found": False,
        "username_field_info": "",
        "password_field_found": False,
        "password_field_info": "",
        "login_button_found": False,
        "login_button_info": "",
        "credentials_entered": False,
        "login_clicked": False,
        "post_login_url": "",
        "post_login_title": "",
        "still_on_login": False,
        "error": None,
        "time_seconds": 0,
    }

    start = time.time()

    try:
        # --- Find username field ---
        username_field = None
        username_keywords = ["username", "email", "user", "login", "j_username",
                             "userid", "employerid"]

        all_inputs = driver.find_elements(By.TAG_NAME, "input")

        for field in all_inputs:
            try:
                if not field.is_displayed():
                    continue
                field_type = (field.get_attribute("type") or "").lower()
                if field_type in ["hidden", "submit", "button", "checkbox", "radio"]:
                    continue

                field_id = (field.get_attribute("id") or "").lower()
                field_name = (field.get_attribute("name") or "").lower()
                field_placeholder = (field.get_attribute("placeholder") or "").lower()
                search_text = f"{field_id} {field_name} {field_placeholder}"

                for kw in username_keywords:
                    if kw in search_text:
                        username_field = field
                        result["username_field_info"] = (
                            f"id='{field_id}' name='{field_name}' "
                            f"type='{field_type}' placeholder='{field_placeholder}'"
                        )
                        break
                if username_field:
                    break
            except Exception:
                continue

        result["username_field_found"] = username_field is not None

        if not username_field:
            # Try broader: first visible text/email input
            for field in all_inputs:
                try:
                    if not field.is_displayed():
                        continue
                    ft = (field.get_attribute("type") or "").lower()
                    if ft in ["text", "email"]:
                        username_field = field
                        fid = (field.get_attribute("id") or "").lower()
                        fname = (field.get_attribute("name") or "").lower()
                        result["username_field_info"] = (
                            f"FALLBACK: id='{fid}' name='{fname}' type='{ft}'"
                        )
                        result["username_field_found"] = True
                        break
                except Exception:
                    continue

        # --- Find password field ---
        password_field = None
        for field in all_inputs:
            try:
                if not field.is_displayed():
                    continue
                ft = (field.get_attribute("type") or "").lower()
                fid = (field.get_attribute("id") or "").lower()
                fname = (field.get_attribute("name") or "").lower()

                if ft == "password" or "password" in fid or "password" in fname:
                    password_field = field
                    result["password_field_info"] = (
                        f"id='{fid}' name='{fname}' type='{ft}'"
                    )
                    break
            except Exception:
                continue

        result["password_field_found"] = password_field is not None

        # --- Enter credentials ---
        if username_field and password_field:
            try:
                username_field.clear()
                for char in credentials["username"]:
                    username_field.send_keys(char)
                    time.sleep(random.uniform(0.03, 0.08))
                human_delay(0.5, 1)

                password_field.clear()
                for char in credentials["password"]:
                    password_field.send_keys(char)
                    time.sleep(random.uniform(0.03, 0.08))
                human_delay(0.5, 1)

                result["credentials_entered"] = True
            except Exception as e:
                result["error"] = f"Credential entry failed: {e}"
                result["status"] = "FAIL"
                result["time_seconds"] = round(time.time() - start, 2)
                return result

        # --- Find and click login button ---
        login_button = None
        button_keywords = ["login", "sign in", "submit", "log in",
                           "connexion", "se connecter"]

        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        all_links = driver.find_elements(By.TAG_NAME, "a")
        all_submits = driver.find_elements(By.XPATH, "//input[@type='submit']")

        for elem in all_buttons + all_submits + all_links:
            try:
                if not elem.is_displayed():
                    continue
                elem_text = (elem.text or "").lower()
                elem_value = (elem.get_attribute("value") or "").lower()
                elem_id = (elem.get_attribute("id") or "").lower()
                search_text = f"{elem_text} {elem_value} {elem_id}"

                for kw in button_keywords:
                    if kw in search_text:
                        login_button = elem
                        result["login_button_info"] = (
                            f"text='{elem_text}' value='{elem_value}' "
                            f"id='{elem_id}' tag='{elem.tag_name}'"
                        )
                        break
                if login_button:
                    break
            except Exception:
                continue

        if not login_button:
            # Fallback: type=submit button
            try:
                login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
                result["login_button_info"] = "FALLBACK: button[type=submit]"
            except Exception:
                try:
                    login_button = driver.find_element(By.XPATH, "//input[@type='submit']")
                    result["login_button_info"] = "FALLBACK: input[type=submit]"
                except Exception:
                    pass

        result["login_button_found"] = login_button is not None

        # --- Click login ---
        if login_button and result["credentials_entered"]:
            try:
                try:
                    login_button.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", login_button)
                result["login_clicked"] = True
                human_delay(3, 5)
            except Exception as e:
                result["error"] = f"Login click failed: {e}"

        # --- Check post-login state ---
        result["post_login_url"] = driver.current_url
        result["post_login_title"] = driver.title

        url_lower = driver.current_url.lower()
        if "login" in url_lower or "signin" in url_lower or "sign-in" in url_lower:
            result["still_on_login"] = True

        # Determine overall status
        if not result["username_field_found"]:
            result["status"] = "FAIL"
            result["error"] = result.get("error") or "Username field not found"
        elif not result["password_field_found"]:
            result["status"] = "FAIL"
            result["error"] = result.get("error") or "Password field not found"
        elif not result["login_button_found"]:
            result["status"] = "FAIL"
            result["error"] = result.get("error") or "Login button not found"
        elif not result["credentials_entered"]:
            result["status"] = "FAIL"
            result["error"] = result.get("error") or "Could not enter credentials"
        elif not result["login_clicked"]:
            result["status"] = "FAIL"
            result["error"] = result.get("error") or "Could not click login"
        elif result["still_on_login"]:
            result["status"] = "FAIL"
            result["error"] = result.get("error") or "Still on login page after click"
        else:
            result["status"] = "PASS"

    except Exception as e:
        result["status"] = "FAIL"
        result["error"] = str(e)

    result["time_seconds"] = round(time.time() - start, 2)
    return result


# ---------------------------------------------------------------------------
#  STAGE 4: NAVIGATION — find "Post a Job"
# ---------------------------------------------------------------------------

def test_navigation(driver, wait) -> dict:
    """Try to find and click 'Post a Job', handle modal, find 'Post a New Job'."""
    result = {
        "status": "UNKNOWN",
        "post_job_button_found": False,
        "post_job_button_info": "",
        "post_job_clicked": False,
        "modal_appeared": False,
        "modal_button_clicked": False,
        "post_new_job_found": False,
        "post_new_job_clicked": False,
        "final_url": "",
        "error": None,
        "time_seconds": 0,
    }

    start = time.time()

    try:
        human_delay(2, 3)

        # --- Find "Post a Job" ---
        post_job_btn = None
        selectors = [
            "//button[normalize-space(text())='Post a Job']",
            "//a[normalize-space(text())='Post a Job']",
            "//button[contains(., 'Post a Job')]",
            "//a[contains(., 'Post a Job')]",
            "//*[contains(text(), 'Post a Job')]",
            "//button[contains(., 'Post')]",
            "//a[contains(., 'Post') and contains(@class, 'btn')]",
        ]

        for sel in selectors:
            try:
                elements = driver.find_elements(By.XPATH, sel)
                for elem in elements:
                    if elem.is_displayed() and elem.is_enabled():
                        post_job_btn = elem
                        result["post_job_button_info"] = (
                            f"text='{elem.text[:50]}' tag='{elem.tag_name}' "
                            f"selector='{sel}'"
                        )
                        break
                if post_job_btn:
                    break
            except Exception:
                continue

        result["post_job_button_found"] = post_job_btn is not None

        if not post_job_btn:
            result["status"] = "FAIL"
            result["error"] = "'Post a Job' button not found on dashboard"
            result["time_seconds"] = round(time.time() - start, 2)
            return result

        # --- Click "Post a Job" ---
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", post_job_btn)
            human_delay(1, 2)
            try:
                post_job_btn.click()
            except Exception:
                driver.execute_script("arguments[0].click();", post_job_btn)
            result["post_job_clicked"] = True
            human_delay(3, 4)
        except Exception as e:
            result["error"] = f"Failed to click 'Post a Job': {e}"
            result["status"] = "FAIL"
            result["time_seconds"] = round(time.time() - start, 2)
            return result

        # --- Check for modal ---
        try:
            modal = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class, 'modal') and contains(@class, 'visible')]")
                )
            )
            result["modal_appeared"] = True

            # Click first "Post" button in modal
            post_buttons = modal.find_elements(
                By.XPATH, ".//button[contains(text(), 'Post')] | .//a[contains(text(), 'Post')]"
            )
            for btn in post_buttons:
                if btn.is_displayed() and btn.is_enabled():
                    try:
                        btn.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", btn)
                    result["modal_button_clicked"] = True
                    human_delay(2, 3)
                    break

        except Exception:
            # No modal — that's okay, some portals skip the modal
            result["modal_appeared"] = False

        # --- Check for agreement ---
        try:
            accept_xpaths = [
                "//button[contains(text(), 'Accept')]",
                "//button[contains(text(), 'Agree')]",
                "//button[contains(text(), 'I Accept')]",
                "//a[contains(text(), 'Accept')]",
                "//input[@type='submit' and contains(@value, 'Accept')]",
            ]
            for xp in accept_xpaths:
                try:
                    btns = driver.find_elements(By.XPATH, xp)
                    for btn in btns:
                        if btn.is_displayed():
                            driver.execute_script("arguments[0].click();", btn)
                            human_delay(2, 3)
                            break
                except Exception:
                    continue
        except Exception:
            pass

        # --- Find "Post a New Job" ---
        try:
            post_new_selectors = [
                "//a[contains(text(), 'Post a New Job')]",
                "//button[contains(text(), 'Post a New Job')]",
                "//a[contains(text(), 'Post a New')]",
                "//button[contains(text(), 'Post a New')]",
            ]
            for sel in post_new_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, sel)
                    for elem in elements:
                        if elem.is_displayed():
                            result["post_new_job_found"] = True
                            try:
                                elem.click()
                            except Exception:
                                driver.execute_script("arguments[0].click();", elem)
                            result["post_new_job_clicked"] = True
                            human_delay(3, 4)
                            break
                    if result["post_new_job_clicked"]:
                        break
                except Exception:
                    continue
        except Exception:
            pass

        result["final_url"] = driver.current_url

        # Determine status
        if result["post_job_clicked"]:
            result["status"] = "PASS"
        else:
            result["status"] = "FAIL"

    except Exception as e:
        result["status"] = "FAIL"
        result["error"] = str(e)

    result["time_seconds"] = round(time.time() - start, 2)
    return result


# ---------------------------------------------------------------------------
#  STAGE 5: FORM SCAN
# ---------------------------------------------------------------------------

def test_form_scan(driver) -> dict:
    """Scan the job posting form and report all fields found."""
    result = {
        "status": "UNKNOWN",
        "total_inputs": 0,
        "total_textareas": 0,
        "total_selects": 0,
        "total_checkboxes": 0,
        "rich_text_editors": 0,
        "fields": [],           # list of {label, id, name, type, tag, required}
        "required_fields": [],
        "error": None,
        "time_seconds": 0,
    }

    start = time.time()

    try:
        human_delay(2, 3)
        driver.execute_script("window.scrollTo(0, 0);")
        human_delay(1, 2)

        all_inputs = driver.find_elements(By.TAG_NAME, "input")
        all_textareas = driver.find_elements(By.TAG_NAME, "textarea")
        all_selects = driver.find_elements(By.TAG_NAME, "select")
        all_checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
        froala_editors = driver.find_elements(
            By.CSS_SELECTOR, "div.fr-element.fr-view[contenteditable='true']"
        )

        result["total_inputs"] = len(all_inputs)
        result["total_textareas"] = len(all_textareas)
        result["total_selects"] = len(all_selects)
        result["total_checkboxes"] = len(all_checkboxes)
        result["rich_text_editors"] = len(froala_editors)

        for field in all_inputs + all_textareas + all_selects:
            try:
                if not field.is_displayed():
                    continue

                tag = (field.tag_name or "").lower()
                ftype = (field.get_attribute("type") or "").lower()

                if tag == "input" and ftype in ["hidden", "submit", "button"]:
                    continue

                fid = (field.get_attribute("id") or "")
                fname = (field.get_attribute("name") or "")
                fplaceholder = (field.get_attribute("placeholder") or "")

                # Try to get label
                label_text = ""
                if fid:
                    try:
                        label_el = driver.find_element(
                            By.XPATH, f"//label[@for='{fid}']"
                        )
                        label_text = (label_el.text or "").strip()
                    except Exception:
                        pass

                if not label_text:
                    try:
                        label_text = driver.execute_script("""
                            const el = arguments[0];
                            let node = el.previousElementSibling;
                            while (node) {
                                if (node.tagName === 'LABEL') return node.innerText;
                                node = node.previousElementSibling;
                            }
                            let parent = el.parentElement;
                            for (let i = 0; i < 3; i++) {
                                if (!parent) break;
                                const lbl = parent.querySelector('label');
                                if (lbl) return lbl.innerText;
                                parent = parent.parentElement;
                            }
                            return '';
                        """, field) or ""
                    except Exception:
                        pass

                is_required = "*" in label_text
                try:
                    if field.get_attribute("required"):
                        is_required = True
                    if field.get_attribute("aria-required") == "true":
                        is_required = True
                except Exception:
                    pass

                field_info = {
                    "label": label_text[:80],
                    "id": fid[:60],
                    "name": fname[:60],
                    "type": ftype,
                    "tag": tag,
                    "required": is_required,
                }
                result["fields"].append(field_info)

                if is_required:
                    result["required_fields"].append(field_info)

            except Exception:
                continue

        result["status"] = "PASS" if result["fields"] else "FAIL"

    except Exception as e:
        result["status"] = "FAIL"
        result["error"] = str(e)

    result["time_seconds"] = round(time.time() - start, 2)
    return result


# ---------------------------------------------------------------------------
#  REPORT GENERATOR
# ---------------------------------------------------------------------------

def generate_report(all_results: list) -> str:
    """Generate a detailed text report from all portal test results."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORT_DIR / f"portal_test_report_{timestamp}.txt"

    lines = []
    lines.append("=" * 80)
    lines.append("VOSYN PORTAL AUTOMATED TEST REPORT")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Portals tested: {len(all_results)}")
    lines.append("=" * 80)
    lines.append("")

    # --- Summary table ---
    pass_count = sum(1 for r in all_results if r["overall"] == "PASS")
    fail_count = sum(1 for r in all_results if r["overall"] == "FAIL")
    skip_count = sum(1 for r in all_results if r["overall"] == "SKIP")

    lines.append("SUMMARY")
    lines.append("-" * 80)
    lines.append(f"  PASS: {pass_count}   FAIL: {fail_count}   SKIP: {skip_count}")
    lines.append("")

    lines.append(f"{'Portal':<18} {'URL Check':<12} {'Platform':<12} {'Login':<12} {'Navigate':<12} {'Form':<12} {'Overall':<10}")
    lines.append("-" * 80)

    for r in all_results:
        lines.append(
            f"{r['portal_key']:<18} "
            f"{r['url_check']['status']:<12} "
            f"{r['platform']['status']:<12} "
            f"{r['login']['status']:<12} "
            f"{r['navigation']['status']:<12} "
            f"{r['form_scan']['status']:<12} "
            f"{r['overall']:<10}"
        )

    lines.append("")
    lines.append("")

    # --- Detailed results per portal ---
    for r in all_results:
        lines.append("=" * 80)
        lines.append(f"PORTAL: {r['portal_name']} ({r['portal_key']})")
        lines.append(f"URL: {r['url']}")
        lines.append(f"Overall: {r['overall']}")
        lines.append(f"Total time: {r['total_time']}s")
        lines.append("=" * 80)

        # URL Check
        u = r["url_check"]
        lines.append("")
        lines.append(f"  [1] URL REACHABILITY: {u['status']}  ({u['time_seconds']}s)")
        lines.append(f"      Final URL:    {u['final_url']}")
        lines.append(f"      Page title:   {u['page_title']}")
        lines.append(f"      Blocked:      {u['blocked']}")
        if u["error"]:
            lines.append(f"      Error:        {u['error']}")

        # Platform
        p = r["platform"]
        lines.append("")
        lines.append(f"  [2] PLATFORM DETECTION: {p['status']}")
        lines.append(f"      Expected:     {p['expected']}")
        lines.append(f"      Detected:     {p['detected']}")
        lines.append(f"      Has playbook: {p['has_playbook']}")

        # Login
        lg = r["login"]
        lines.append("")
        lines.append(f"  [3] LOGIN: {lg['status']}  ({lg['time_seconds']}s)")
        lines.append(f"      Username field found: {lg['username_field_found']}")
        lines.append(f"      Username field info:  {lg['username_field_info']}")
        lines.append(f"      Password field found: {lg['password_field_found']}")
        lines.append(f"      Password field info:  {lg['password_field_info']}")
        lines.append(f"      Login button found:   {lg['login_button_found']}")
        lines.append(f"      Login button info:    {lg['login_button_info']}")
        lines.append(f"      Credentials entered:  {lg['credentials_entered']}")
        lines.append(f"      Login clicked:        {lg['login_clicked']}")
        lines.append(f"      Post-login URL:       {lg['post_login_url']}")
        lines.append(f"      Post-login title:     {lg['post_login_title']}")
        lines.append(f"      Still on login page:  {lg['still_on_login']}")
        if lg["error"]:
            lines.append(f"      Error:                {lg['error']}")

        # Navigation
        n = r["navigation"]
        lines.append("")
        lines.append(f"  [4] NAVIGATION: {n['status']}  ({n['time_seconds']}s)")
        lines.append(f"      'Post a Job' found:     {n['post_job_button_found']}")
        lines.append(f"      'Post a Job' info:      {n['post_job_button_info']}")
        lines.append(f"      'Post a Job' clicked:   {n['post_job_clicked']}")
        lines.append(f"      Modal appeared:          {n['modal_appeared']}")
        lines.append(f"      Modal button clicked:    {n['modal_button_clicked']}")
        lines.append(f"      'Post a New Job' found:  {n['post_new_job_found']}")
        lines.append(f"      'Post a New Job' clicked:{n['post_new_job_clicked']}")
        lines.append(f"      Final URL:               {n['final_url']}")
        if n["error"]:
            lines.append(f"      Error:                   {n['error']}")

        # Form Scan
        f = r["form_scan"]
        lines.append("")
        lines.append(f"  [5] FORM SCAN: {f['status']}  ({f['time_seconds']}s)")
        lines.append(f"      Total inputs:       {f['total_inputs']}")
        lines.append(f"      Total textareas:    {f['total_textareas']}")
        lines.append(f"      Total selects:      {f['total_selects']}")
        lines.append(f"      Total checkboxes:   {f['total_checkboxes']}")
        lines.append(f"      Rich text editors:  {f['rich_text_editors']}")
        lines.append(f"      Visible fields:     {len(f['fields'])}")
        lines.append(f"      Required fields:    {len(f['required_fields'])}")
        if f["error"]:
            lines.append(f"      Error:              {f['error']}")

        if f["fields"]:
            lines.append("")
            lines.append("      ALL VISIBLE FIELDS:")
            lines.append(f"      {'Label':<40} {'ID':<25} {'Type':<10} {'Req':<5}")
            lines.append("      " + "-" * 80)
            for fld in f["fields"]:
                req_marker = " *" if fld["required"] else ""
                lines.append(
                    f"      {fld['label']:<40} {fld['id']:<25} "
                    f"{fld['type']:<10} {req_marker}"
                )

        if f["required_fields"]:
            lines.append("")
            lines.append("      REQUIRED FIELDS (need to be mapped):")
            for fld in f["required_fields"]:
                lines.append(
                    f"        * {fld['label']:<40} id='{fld['id']}' name='{fld['name']}'"
                )

        # Screenshots
        lines.append("")
        lines.append("      SCREENSHOTS:")
        for stage, path in r.get("screenshots", {}).items():
            lines.append(f"        {stage}: {path}")

        lines.append("")
        lines.append("")

    report_text = "\n".join(lines)

    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(report_text)

    return str(report_path)


# ---------------------------------------------------------------------------
#  MAIN TEST RUNNER
# ---------------------------------------------------------------------------

def run_all_tests():
    """Run automated tests for all Canadian portals."""

    print("=" * 70)
    print("VOSYN PORTAL AUTOMATED TEST HARNESS")
    print(f"Testing {len(CANADIAN_PORTALS)} Canadian portals")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()

    # Get credentials once
    try:
        credentials = Config.get_credentials("test")
    except ValueError:
        print("ERROR: No credentials found. Set PORTAL_USER and PORTAL_PASS in .env")
        return

    print(f"Using credentials: {credentials['username']}")
    print()

    all_results = []

    for i, portal in enumerate(CANADIAN_PORTALS):
        portal_key = portal["key"]
        portal_name = portal["name"]
        expected_platform = portal["platform_expected"]

        print(f"[{i+1}/{len(CANADIAN_PORTALS)}] Testing: {portal_name} ({portal_key})")
        print("-" * 50)

        # Get URL
        try:
            url = Config.get_portal_url(portal_key)
        except ValueError as e:
            print(f"  SKIP: {e}")
            all_results.append({
                "portal_key": portal_key,
                "portal_name": portal_name,
                "url": "NOT_FOUND",
                "overall": "SKIP",
                "total_time": 0,
                "url_check": {"status": "SKIP", "time_seconds": 0, "final_url": "", "page_title": "", "blocked": False, "error": str(e)},
                "platform": {"status": "SKIP", "detected": "", "expected": expected_platform, "has_playbook": False},
                "login": {"status": "SKIP", "time_seconds": 0, "username_field_found": False, "username_field_info": "", "password_field_found": False, "password_field_info": "", "login_button_found": False, "login_button_info": "", "credentials_entered": False, "login_clicked": False, "post_login_url": "", "post_login_title": "", "still_on_login": False, "error": None},
                "navigation": {"status": "SKIP", "time_seconds": 0, "post_job_button_found": False, "post_job_button_info": "", "post_job_clicked": False, "modal_appeared": False, "modal_button_clicked": False, "post_new_job_found": False, "post_new_job_clicked": False, "final_url": "", "error": None},
                "form_scan": {"status": "SKIP", "time_seconds": 0, "total_inputs": 0, "total_textareas": 0, "total_selects": 0, "total_checkboxes": 0, "rich_text_editors": 0, "fields": [], "required_fields": [], "error": None},
                "screenshots": {},
            })
            print()
            continue

        portal_start = time.time()
        driver = None
        screenshots = {}

        try:
            # --- Stage 2: Platform detection (no browser needed) ---
            print("  [2] Platform detection...", end=" ")
            platform_result = test_platform_detection(url, expected_platform)
            print(platform_result["status"])

            # --- Create browser ---
            print("  [*] Starting browser...")
            driver, wait = create_driver()

            # --- Stage 1: URL reachability ---
            print("  [1] URL reachability...", end=" ")
            url_result = test_url_reachability(driver, url)
            print(f"{url_result['status']} ({url_result['time_seconds']}s)")
            screenshots["01_url_check"] = take_screenshot(driver, portal_key, "01_url_check")

            if url_result["status"] == "BLOCKED":
                print(f"      BLOCKED by Cloudflare/WAF — skipping remaining stages")
                login_result = {"status": "SKIP", "time_seconds": 0, "username_field_found": False, "username_field_info": "", "password_field_found": False, "password_field_info": "", "login_button_found": False, "login_button_info": "", "credentials_entered": False, "login_clicked": False, "post_login_url": "", "post_login_title": "", "still_on_login": False, "error": "Blocked at URL stage"}
                nav_result = {"status": "SKIP", "time_seconds": 0, "post_job_button_found": False, "post_job_button_info": "", "post_job_clicked": False, "modal_appeared": False, "modal_button_clicked": False, "post_new_job_found": False, "post_new_job_clicked": False, "final_url": "", "error": "Blocked at URL stage"}
                form_result = {"status": "SKIP", "time_seconds": 0, "total_inputs": 0, "total_textareas": 0, "total_selects": 0, "total_checkboxes": 0, "rich_text_editors": 0, "fields": [], "required_fields": [], "error": "Blocked at URL stage"}
            else:
                # --- Stage 3: Login ---
                print("  [3] Login...", end=" ")
                login_result = test_login(driver, wait, credentials)
                print(f"{login_result['status']} ({login_result['time_seconds']}s)")
                screenshots["02_login"] = take_screenshot(driver, portal_key, "02_post_login")

                if login_result["status"] != "PASS":
                    print(f"      Error: {login_result.get('error', 'Unknown')}")
                    nav_result = {"status": "SKIP", "time_seconds": 0, "post_job_button_found": False, "post_job_button_info": "", "post_job_clicked": False, "modal_appeared": False, "modal_button_clicked": False, "post_new_job_found": False, "post_new_job_clicked": False, "final_url": "", "error": "Login failed"}
                    form_result = {"status": "SKIP", "time_seconds": 0, "total_inputs": 0, "total_textareas": 0, "total_selects": 0, "total_checkboxes": 0, "rich_text_editors": 0, "fields": [], "required_fields": [], "error": "Login failed"}
                else:
                    # --- Stage 4: Navigation ---
                    print("  [4] Navigation...", end=" ")
                    nav_result = test_navigation(driver, wait)
                    print(f"{nav_result['status']} ({nav_result['time_seconds']}s)")
                    screenshots["03_navigation"] = take_screenshot(driver, portal_key, "03_navigation")

                    if nav_result["status"] != "PASS":
                        print(f"      Error: {nav_result.get('error', 'Unknown')}")
                        form_result = {"status": "SKIP", "time_seconds": 0, "total_inputs": 0, "total_textareas": 0, "total_selects": 0, "total_checkboxes": 0, "rich_text_editors": 0, "fields": [], "required_fields": [], "error": "Navigation failed"}
                    else:
                        # --- Stage 5: Form scan ---
                        print("  [5] Form scan...", end=" ")
                        form_result = test_form_scan(driver)
                        print(f"{form_result['status']} — {len(form_result['fields'])} fields, {len(form_result['required_fields'])} required")
                        screenshots["04_form"] = take_screenshot(driver, portal_key, "04_form")

            total_time = round(time.time() - portal_start, 2)

            # Determine overall
            statuses = [url_result["status"], platform_result["status"],
                        login_result["status"], nav_result["status"],
                        form_result["status"]]

            if all(s == "PASS" for s in statuses):
                overall = "PASS"
            elif any(s == "BLOCKED" for s in statuses):
                overall = "BLOCKED"
            elif any(s == "FAIL" for s in statuses):
                overall = "FAIL"
            else:
                overall = "PARTIAL"

            print(f"  >> Overall: {overall} ({total_time}s)")

            all_results.append({
                "portal_key": portal_key,
                "portal_name": portal_name,
                "url": url,
                "overall": overall,
                "total_time": total_time,
                "url_check": url_result,
                "platform": platform_result,
                "login": login_result,
                "navigation": nav_result,
                "form_scan": form_result,
                "screenshots": screenshots,
            })

        except Exception as e:
            print(f"  CRASH: {e}")
            traceback.print_exc()
            total_time = round(time.time() - portal_start, 2)
            all_results.append({
                "portal_key": portal_key,
                "portal_name": portal_name,
                "url": url,
                "overall": "CRASH",
                "total_time": total_time,
                "url_check": {"status": "CRASH", "time_seconds": 0, "final_url": "", "page_title": "", "blocked": False, "error": str(e)},
                "platform": {"status": "CRASH", "detected": "", "expected": expected_platform, "has_playbook": False},
                "login": {"status": "CRASH", "time_seconds": 0, "username_field_found": False, "username_field_info": "", "password_field_found": False, "password_field_info": "", "login_button_found": False, "login_button_info": "", "credentials_entered": False, "login_clicked": False, "post_login_url": "", "post_login_title": "", "still_on_login": False, "error": str(e)},
                "navigation": {"status": "CRASH", "time_seconds": 0, "post_job_button_found": False, "post_job_button_info": "", "post_job_clicked": False, "modal_appeared": False, "modal_button_clicked": False, "post_new_job_found": False, "post_new_job_clicked": False, "final_url": "", "error": str(e)},
                "form_scan": {"status": "CRASH", "time_seconds": 0, "total_inputs": 0, "total_textareas": 0, "total_selects": 0, "total_checkboxes": 0, "rich_text_editors": 0, "fields": [], "required_fields": [], "error": str(e)},
                "screenshots": screenshots,
            })

        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

        print()

    # --- Generate report ---
    print("=" * 70)
    print("GENERATING REPORT...")
    report_path = generate_report(all_results)
    print(f"Report saved: {report_path}")
    print()

    # --- Console summary ---
    print("FINAL SUMMARY")
    print("-" * 70)
    for r in all_results:
        status_icon = {"PASS": "✓", "FAIL": "✗", "BLOCKED": "⊘", "SKIP": "—", "CRASH": "💥", "PARTIAL": "◐"}.get(r["overall"], "?")
        print(f"  {status_icon} {r['portal_key']:<18} {r['overall']:<10} ({r['total_time']}s)")

    pass_count = sum(1 for r in all_results if r["overall"] == "PASS")
    print()
    print(f"  {pass_count}/{len(all_results)} portals fully passing")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
