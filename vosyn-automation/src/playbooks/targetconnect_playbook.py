import sys
from pathlib import Path
from src.portal_helpers import PortalHelpers
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.turso_data_manager import TursoDataManager
from src.playbooks.base_playbook import BasePortalPlaybook
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
import time


class TargetConnectPlaybook(BasePortalPlaybook):
    """
    Playbook for TargetConnect portals used by UK universities.
    Covers: Oxford, Imperial, UCL, KCL, Glasgow, Cardiff, Dundee,
            Reading, Goldsmiths, St Andrews, Manchester, Bristol,
            Lancaster, Newcastle, Leicester, Kent, Arden
    """

    # ------------------------------------------------------------------ #
    #  DEFAULT VALUES FOR DROPDOWNS                                        #
    # ------------------------------------------------------------------ #

    DEFAULTS = {
        'opportunity_type': 'Internship/Work Experience',
        'salary_range':     'Competitive',
        'location':         'North America',
        'country':          'Unknown',
        'occupational_area':'Tech: IT, Data, AI & Machine Learning',
        'min_wage':         'Meets Relevant Employment Legislation of Country it is based in (outside the UK)',
        'positions':        '1',
        'start_date':       'Flexible',
    }

    # ------------------------------------------------------------------ #
    #  LOGIN                                                               #
    # ------------------------------------------------------------------ #

    def login(self):
        print(f"Navigating to: {self.portal_url}")
        self.driver.get(self.portal_url)
        self.human_delay(2, 3)

        # Find email/username field
        username_field = None
        username_keywords = ['email', 'username', 'user', 'login']

        all_inputs = self.driver.find_elements(By.TAG_NAME, "input")

        for field in all_inputs:
            try:
                if not field.is_displayed():
                    continue
                field_type = (field.get_attribute('type') or '').lower()
                field_id   = (field.get_attribute('id') or '').lower()
                field_name = (field.get_attribute('name') or '').lower()

                if field_type in ['hidden', 'submit', 'button', 'checkbox', 'radio']:
                    continue

                search_text = f"{field_id} {field_name}"
                for keyword in username_keywords:
                    if keyword in search_text:
                        username_field = field
                        print(f"Found username field: id='{field_id}'")
                        break

                if username_field:
                    break
            except:
                continue

        if not username_field:
            raise Exception("Could not find username/email field")

        print("Entering username")
        username_field.clear()
        self.slow_type(username_field, self.credentials['username'])
        self.human_delay(1, 2)

        # Find password field
        password_field = None
        for field in all_inputs:
            try:
                if not field.is_displayed():
                    continue
                if (field.get_attribute('type') or '').lower() == 'password':
                    password_field = field
                    break
            except:
                continue

        if not password_field:
            raise Exception("Could not find password field")

        print("Entering password")
        password_field.clear()
        self.slow_type(password_field, self.credentials['password'])
        self.human_delay(1, 2)

        # Click login button
        login_button = None
        button_keywords = ['login', 'sign in', 'log in', 'submit']

        for elem in self.driver.find_elements(By.TAG_NAME, "button") + \
                    self.driver.find_elements(By.XPATH, "//input[@type='submit']"):
            try:
                if not elem.is_displayed():
                    continue
                text = (elem.text or elem.get_attribute('value') or '').lower()
                if any(k in text for k in button_keywords):
                    login_button = elem
                    break
            except:
                continue

        if not login_button:
            try:
                login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            except:
                raise Exception("Could not find login button")

        print("Clicking login")
        try:
            login_button.click()
        except:
            self.driver.execute_script("arguments[0].click();", login_button)

        self.human_delay(3, 5)

        if "unauth" in self.driver.current_url.lower():
            raise Exception("Login failed - still on login page")

        print("Login successful!")

    # ------------------------------------------------------------------ #
    #  NAVIGATE TO JOB POSTING                                            #
    # ------------------------------------------------------------------ #

    def navigate_to_job_posting(self):
        print("Looking for 'Post opportunity' button")
        self.human_delay(2, 3)

        post_btn = None
        keywords = ['post opportunity','post internship', 'post a job', 'add opportunity',
                    'post job', 'new opportunity']

        for elem in self.driver.find_elements(By.TAG_NAME, "a") + \
                    self.driver.find_elements(By.TAG_NAME, "button"):
            try:
                if not elem.is_displayed():
                    continue
                text = (elem.text or '').lower()
                if any(k in text for k in keywords):
                    post_btn = elem
                    print(f"Found post button: '{elem.text.strip()}'")
                    break
            except:
                continue

        if not post_btn:
            # Try Opportunities menu
            try:
                opps_menu = self.driver.find_element(
                    By.XPATH, "//a[contains(text(),'Opportunities')] | //button[contains(text(),'Opportunities')]"
                )
                opps_menu.click()
                self.human_delay(1, 2)

                post_btn = self.driver.find_element(
                    By.XPATH, "//a[contains(text(),'Post')] | //a[contains(text(),'Add')]"
                )
            except:
                raise Exception("Could not find Post Opportunity button")

        self.driver.execute_script("arguments[0].scrollIntoView(true);", post_btn)
        self.human_delay(1, 2)

        try:
            post_btn.click()
        except:
            self.driver.execute_script("arguments[0].click();", post_btn)

        print("Clicked Post Opportunity")
        self.human_delay(3, 4)
        print("Job posting form loaded")

    # ------------------------------------------------------------------ #
    #  FILL JOB FORM                                                       #
    # ------------------------------------------------------------------ #

    def fill_job_form(self):
        print()
        print("=" * 60)
        print("FILLING TARGETCONNECT FORM")
        print("=" * 60)
        print()

        title       = self.job_data.get('Title', '')
        description = self.job_data.get('Description', '')
        salary      = self.job_data.get('Salary', '')
        requirements= self.job_data.get('Requirements', '')

        # ---- PAGE 1: Job Details ---- #
        print("--- Page 1: Job Details ---")

        # Opportunity type dropdown
        self._select_dropdown_by_label('Opportunity type', self.DEFAULTS['opportunity_type'])

        # Job title
        self._fill_field_by_label('Job title', title)

        # Opportunity description (rich text editor)
        self._fill_rich_text_by_label('Opportunity description', description)

        # Occupational area dropdown
        self._select_dropdown_by_label('Occupational area', self.DEFAULTS['occupational_area'])

        # Salary range dropdown
        self._select_dropdown_by_label('Salary range', self.DEFAULTS['salary_range'])

        # Additional salary info
        if salary:
            self._fill_field_by_label('Additional salary information', f"${salary}/hr CAD")

        # Location dropdown
        self._select_dropdown_by_label('Locations', self.DEFAULTS['location'])

        # Country dropdown
        self._select_dropdown_by_label('Countries', self.DEFAULTS['country'])

        # Number of positions
        self._select_dropdown_by_label('Number of positions', self.DEFAULTS['positions'])

        # Start date - click Flexible radio
        self._click_radio_by_label('Flexible')

        print()
        print("Clicking Next to go to Page 2")
        self._click_next()
        self.human_delay(2, 3)

        # ---- PAGE 2: Advertising Details ---- #
        print("--- Page 2: Advertising Details ---")

        # Set closing date to maximum
        try:
            max_date_link = self.driver.find_element(
                By.XPATH, "//a[contains(text(),'Set to the maximum date')]"
            )
            max_date_link.click()
            print("Set closing date to maximum")
            self.human_delay(1, 2)
        except:
            print("Could not set maximum date - skipping")

        # How to apply - check 'Via email'
        try:
            via_email = self.driver.find_element(
                By.XPATH, "//input[@type='checkbox']//following-sibling::*[contains(text(),'Via email')] | //label[contains(text(),'Via email')]//preceding-sibling::input"
            )
            if not via_email.is_selected():
                via_email.click()
            print("Selected 'Via email'")
        except:
            print("Could not find Via email checkbox - skipping")

        print()
        print("Clicking Next to go to Page 3")
        self._click_next()
        self.human_delay(2, 3)

        # ---- PAGE 3: Other Details ---- #
        print("--- Page 3: Other Details ---")

        # National Minimum Wage dropdown
        self._select_dropdown_by_label(
            'National Minimum Wage',
            self.DEFAULTS['min_wage']
        )

        # Terms checkbox
        try:
            terms_checkbox = self.driver.find_element(
                By.XPATH, "//input[@type='radio' and contains(@id,'terms')] | //input[@type='checkbox' and contains(@id,'terms')]"
            )
            if not terms_checkbox.is_selected():
                terms_checkbox.click()
            print("Accepted terms and conditions")
        except:
            # Try finding by label text
            try:
                terms = self.driver.find_element(
                    By.XPATH, "//label[contains(text(),'confirm')]//preceding-sibling::input | //label[contains(text(),'terms')]//preceding-sibling::input"
                )
                if not terms.is_selected():
                    terms.click()
                print("Accepted terms and conditions")
            except:
                print("WARNING: Could not find terms checkbox")

        print()
        print("=" * 60)
        print("FORM FILLED")
        print("=" * 60)

    # ------------------------------------------------------------------ #
    #  SUBMIT                                                              #
    # ------------------------------------------------------------------ #

    def submit_and_capture_proof(self) -> dict:
        print("Looking for submit button (NOT clicking it)")

        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self.human_delay(2, 3)

        try:
            submit_btn = None
            selectors = [
                "//button[contains(text(), 'Submit')]",
                "//input[@type='submit' and contains(@value, 'Submit')]",
                "//button[@type='submit']",
                "//a[contains(text(), 'Submit')]"
            ]

            for selector in selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for btn in buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            submit_btn = btn
                            break
                    if submit_btn:
                        break
                except:
                    continue

            if submit_btn:
                print("Submit button found (NOT clicking it)")
            else:
                print("Submit button not found")

        except Exception as e:
            print(f"Error finding submit button: {e}")

        print("FORM FILLED - waiting for review...")

        # If running from API with a run_id, wait for UI confirm
        # If running from terminal, wait for Enter
        import sys
        import time

        if self.run_id:
            # API mode — poll JOB_STORE for confirm
            from src.API.api import JOB_STORE, JOB_STORE_LOCK
            while True:
                time.sleep(2)
                with JOB_STORE_LOCK:
                    status = JOB_STORE.get(self.run_id, {}).get("status", "running")
                if status in ("completed", "failed"):
                    print("Confirmed via UI — closing browser")
                    break
        elif sys.stdin and sys.stdin.isatty():
            print("Press Enter when done reviewing")
            input()
        else:
            time.sleep(300)

        return {'confirmation_id': 'NOT_SUBMITTED'}
    # ------------------------------------------------------------------ #
    #  HELPER METHODS                                                      #
    # ------------------------------------------------------------------ #

    def _fill_field_by_label(self, label_text: str, value: str):
        """Find an input field by its label and fill it."""
        if not value:
            return
        try:
            field = self.driver.find_element(
                By.XPATH,
                f"//label[contains(normalize-space(text()),'{label_text}')]//following::input[1] | "
                f"//label[contains(normalize-space(text()),'{label_text}')]//following::textarea[1]"
            )
            PortalHelpers.robust_fill(self.driver, field, value)
            print(f"Filled '{label_text}': {value[:50]}")
        except Exception as e:
            print(f"Could not fill '{label_text}': {e}")

    def _select_dropdown_by_label(self, label_text: str, value: str):
        """Find a select dropdown by its label and select a value."""
        if not value:
            return
        try:
            select_elem = self.driver.find_element(
                By.XPATH,
                f"//label[contains(normalize-space(text()),'{label_text}')]//following::select[1]"
            )
            PortalHelpers.robust_fill(self.driver, select_elem, value)
            print(f"Selected '{label_text}': {value}")
        except Exception as e:
            print(f"Could not select '{label_text}': {e}")

    def _fill_rich_text_by_label(self, label_text: str, value: str):
        """Fill a rich text / contenteditable editor near a label."""
        if not value:
            return
        try:
            # Try Froala style
            editors = self.driver.find_elements(
                By.CSS_SELECTOR, "div.fr-element[contenteditable='true'], div[contenteditable='true']"
            )
            if editors:
                editor = editors[0]
                self.driver.execute_script("arguments[0].scrollIntoView(true);", editor)
                self.human_delay(0.5, 1)
                editor.click()
                self.human_delay(0.3, 0.5)
                editor.send_keys(value)
                print(f"Filled rich text '{label_text}': {value[:50]}")
            else:
                # Fallback to textarea
                self._fill_field_by_label(label_text, value)
        except Exception as e:
            print(f"Could not fill rich text '{label_text}': {e}")

    def _click_radio_by_label(self, label_text: str):
        """Click a radio button by its label."""
        try:
            radio = self.driver.find_element(
                By.XPATH,
                f"//label[contains(normalize-space(text()),'{label_text}')]//preceding-sibling::input[@type='radio'] | "
                f"//label[contains(normalize-space(text()),'{label_text}')]//input[@type='radio'] | "
                f"//input[@type='radio']//following-sibling::*[contains(text(),'{label_text}')]"
            )
            if not radio.is_selected():
                radio.click()
            print(f"Selected radio: '{label_text}'")
        except Exception as e:
            print(f"Could not select radio '{label_text}': {e}")

    def _click_next(self):
        """Click the Next button to proceed to the next page."""
        try:
            next_btn = self.driver.find_element(
                By.XPATH,
                "//button[contains(text(),'Next')] | //a[contains(text(),'Next')] | //input[@value='Next']"
            )
            self.driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
            self.human_delay(0.5, 1)
            next_btn.click()
            print("Clicked Next")
            self.human_delay(2, 3)
        except Exception as e:
            raise Exception(f"Could not find Next button: {e}")


# ------------------------------------------------------------------ #
#  MAIN                                                                #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    from src.config import Config
    from src.turso_data_manager import TursoDataManager
    import pandas as pd

    print("=" * 60)
    print("TargetConnect Playbook - UK Universities")
    print("=" * 60)
    print()

    em = TursoDataManager()
    df_jobs = em.get_job_posts_df()

    print("Available Jobs:")
    print("-" * 60)
    for i, row in df_jobs.iterrows():
        print(f"  {i+1:>3}. [{row['JobId']}] {row['Title']}")
    print()

    while True:
        choice = input(f"Select job (1-{len(df_jobs)}): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(df_jobs):
                selected_job = df_jobs.iloc[idx].to_dict()
                break
        except ValueError:
            pass
        print("Invalid choice.")

    print(f"\nSelected: {selected_job['Title']}\n")

    portal_map = {
        "1": "oxford", "2": "icl", "3": "ucl", "4": "standrews",
        "5": "kcl", "6": "manchester", "7": "glasgow", "8": "bristol",
        "9": "lancaster", "10": "cardiff", "11": "newcastle", "12": "dundee",
        "13": "leicester", "14": "reading", "15": "kent", "16": "arden",
        "17": "goldsmiths",
    }

    print("Available Portals:")
    for num, name in portal_map.items():
        print(f"  {num:>3}. {name.upper()}")
    print()

    while True:
        choice = input("Select portal number: ").strip()
        if choice in portal_map:
            selected_portal = portal_map[choice]
            break
        print("Invalid choice.")

    print(f"\nPortal: {selected_portal.upper()}\n")

    portal_url = Config.get_portal_url(selected_portal)
    credentials = Config.get_credentials(selected_portal)
    print(f"URL:      {portal_url}")
    print(f"Username: {credentials['username']}\n")

    playbook = TargetConnectPlaybook(
        portal_url=portal_url,
        credentials=credentials,
        job_data={
            "JobId": selected_job.get("JobId", ""),
            "Title": selected_job.get("Title", ""),
            "Description": selected_job.get("Description", ""),
            "Location": selected_job.get("Location", ""),
            "Salary": selected_job.get("Salary", ""),
            "Duration": "520 Hours (approximately 3 months)",
            "Requirements": selected_job.get("Requirements", ""),
            "portal_name": selected_portal,
        }
    )

    result = playbook.execute()
    print(f"\nResult: {result['status']}")
    print("=" * 60)
