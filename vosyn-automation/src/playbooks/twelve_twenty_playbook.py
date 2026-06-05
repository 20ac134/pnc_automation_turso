import sys
from pathlib import Path
from src.portal_helpers import PortalHelpers
import pandas as pd
import re

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.turso_data_manager import TursoDataManager
from src.playbooks.base_playbook import BasePortalPlaybook
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime, timedelta
import time


class TwelveTwentyPlaybook(BasePortalPlaybook):

    # ------------------------------------------------------------------ #
    #  LOGIN                                                               #
    # ------------------------------------------------------------------ #

    def login(self):
        from selenium.webdriver.common.action_chains import ActionChains

        print(f"Navigating to: {self.portal_url}")
        self.driver.get(self.portal_url)
        self.human_delay(2, 3)

        # Fill Email Address field
        print("Entering email")
        try:
            email_field = self.wait.until(
                EC.element_to_be_clickable((By.XPATH,
                    "//input[@placeholder='Email Address' or @type='email' or contains(@id,'email')]"))
            )
            email_field.clear()
            self.slow_type(email_field, self.credentials['username'])
            self.human_delay(1, 2)
        except Exception as e:
            raise Exception(f"Could not find Email Address field: {e}")

        # Fill Password field
        print("Entering password")
        try:
            password_field = self.wait.until(
                EC.element_to_be_clickable((By.XPATH,
                    "//input[@placeholder='Password' or @type='password']"))
            )
            password_field.clear()
            self.slow_type(password_field, self.credentials['password'])
            self.human_delay(1, 2)
        except Exception as e:
            raise Exception(f"Could not find Password field: {e}")

        # Click with ActionChains - simulates real mouse movement
        print("Clicking Employer Log In with ActionChains")
        try:
            login_btn = self.wait.until(
                  EC.element_to_be_clickable((By.XPATH,
                    "//button[contains(., 'Employer Log In')]"
                    " | //button[contains(@class, 'submit-login-form')]"
                    " | //button[@type='button' and contains(@class, 'btn-school')]"
                    " | //button[@type='submit']"))
            )
            actions = ActionChains(self.driver)
            actions.move_to_element(login_btn)
            actions.pause(0.5)
            actions.click(login_btn)
            actions.perform()
        except Exception as e:
            raise Exception(f"Could not click login button: {e}")

        print("Waiting for dashboard")
        self.human_delay(3, 5)

        current_url = self.driver.current_url.lower()
        if "login" in current_url or "signin" in current_url:
            raise Exception("Login failed - still on login page")

        print("Login successful!")

    # ------------------------------------------------------------------ #
    #  NAVIGATE TO JOB POSTING                                            #
    # ------------------------------------------------------------------ #

    def navigate_to_job_posting(self):
        print("Step 1/3: Looking for 'Post a Job' / '+ POST' button")
        self.human_delay(2, 3)

        post_job_btn = None

        selectors = [
            "//button[normalize-space(text())='+ POST']",
            "//button[contains(text(), 'POST')]",
            "//a[normalize-space(text())='+ POST']",
            "//button[normalize-space(text())='Post a Job']",
            "//a[normalize-space(text())='Post a Job']",
            "//*[contains(@class,'btn') and contains(., 'POST')]",
            # Bradley — plain "Post" link with btn-school class
            "//a[contains(@class, 'btn-school') and contains(., 'Post')]",
            "//a[normalize-space()='Post' and contains(@class, 'btn')]",
            "//a[contains(@href, 'jobPostings/create')]",
            # Input button variants
            "//input[@type='button' and @value='Post a Job']",
            "//input[@type='button' and @value='Post A Job']",
            "//input[contains(@value, 'Post') and contains(@value, 'Job')]",
            "//input[contains(@class, 'btn_primary')]",
            # Post A Job variants
            "//button[normalize-space(text())='Post A Job']",
            "//a[normalize-space(text())='Post A Job']",
            # Post a New Job variants
            "//a[contains(., 'Post a New Job')]",
            "//button[contains(., 'Post a New Job')]",
            "//a[contains(., 'Post A New Job')]",
            "//button[contains(., 'Post A New Job')]",
        ]

        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    if elem.is_displayed() and elem.is_enabled():
                        post_job_btn = elem
                        print(f"Found post button: '{elem.text or elem.get_attribute('value')}'")
                        break
                if post_job_btn:
                    break
            except:
                continue

        # Fallback — scan all buttons and links
        if not post_job_btn:
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            all_links   = self.driver.find_elements(By.TAG_NAME, "a")
            for elem in all_buttons + all_links:
                try:
                    if elem.is_displayed():
                        text = (elem.text or '').lower()
                        value = (elem.get_attribute('value') or '').lower()
                        if 'post' in text and ('job' in text or text.strip() in ['+ post', 'post']):
                            post_job_btn = elem
                            print(f"Found post button (fallback): '{elem.text}'")
                            break
                        if 'post' in value and 'job' in value:
                            post_job_btn = elem
                            print(f"Found post button (fallback via value): '{value}'")
                            break
                except:
                    continue

        if not post_job_btn:
            raise Exception("Could not find Post a Job button")

        self.driver.execute_script("arguments[0].scrollIntoView(true);", post_job_btn)
        self.human_delay(1, 2)
        try:
            post_job_btn.click()
        except:
            self.driver.execute_script("arguments[0].click();", post_job_btn)

        print("Clicked Post a Job")
        self.human_delay(3, 4)

        # Step 2/3: Handle job category modal (if it appears)
        print("Step 2/3: Handling job category modal")
        self.handle_job_category_modal()
        self.human_delay(2, 3)

        # Step 3/3: Handle agreement (if it appears)
        print("Step 3/3: Checking for agreements")
        PortalHelpers.handle_agreement(self.driver)
        self.human_delay(2, 3)

        print("Job posting form loaded")

    def handle_job_category_modal(self):
        print("Looking for job category modal")
        time.sleep(3)

        try:
            # Check for any modal
            modals = self.driver.find_elements(By.XPATH,
                "//div[contains(@class, 'modal') and contains(@class, 'visible')]"
                " | //div[contains(@class, 'modal-dialog')]"
                " | //div[contains(@class, 'modal') and contains(@style, 'display: block')]"
            )

            if modals:
                print("Modal found")
                self.human_delay(2, 3)

                # Look for Post buttons inside modal
                post_buttons = self.driver.find_elements(By.XPATH,
                    "//div[contains(@class, 'modal')]//button[contains(text(), 'Post')]"
                    " | //div[contains(@class, 'modal')]//a[contains(text(), 'Post')]"
                )

                visible_buttons = []
                for btn in post_buttons:
                    try:
                        if btn.is_displayed() and btn.is_enabled():
                            visible_buttons.append(btn)
                    except:
                        pass

                if visible_buttons:
                    print(f"Found {len(visible_buttons)} 'Post' buttons in modal")
                    first_button = visible_buttons[0]
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", first_button)
                    self.human_delay(1, 1.5)
                    try:
                        first_button.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", first_button)
                    print("Category selected")
                    self.human_delay(2, 3)
                else:
                    print("No Post buttons in modal")
            else:
                print("No job category modal found — continuing")

        except Exception as e:
            print(f"Modal handling: {e}")

    # ------------------------------------------------------------------ #
    #  FILL JOB FORM                                                       #
    # ------------------------------------------------------------------ #

    def fill_job_form(self):
        print()
        print("=" * 60)
        print("SCANNING FORM AND AUTO-FILLING (12TWENTY)")
        print("=" * 60)
        print()

        title        = self.job_data.get('Title', '')
        description  = self.job_data.get('Description', '')
        location     = self.job_data.get('Location', '')
        salary       = self.job_data.get('Salary', '')
        duration     = self.job_data.get('Duration', '4 months')
        requirements = self.job_data.get('Requirements', '')

        keywords_mapping = {
            'Title':        ['job title', 'position title', 'position name', 'job name', 'title of position'],
            'Location':     ['job location', 'work location', 'location of work', 'city', 'location'],
            'Duration':     ['duration', 'term length', 'work term', 'contract length'],
            'Salary':       ['salaryamount', 'salary amount', 'hourly rate', 'wage', 'salary', 'compensation'],
            'Description':  ['job description', 'position description', 'description of opportunity', 'description'],
            'Requirements': ['job requirements', 'qualifications', 'required skills', 'job qualifications', 'opportunity requirements'],
            'Positions':    ['number of positions', 'number of openings', 'openings'],
            'Address':      ['address line one', 'address', 'street address'],
            'City':         ['city'],
            'Postal':       ['postal code', 'zip code', 'zip'],
            'Country':      ['country'],
            'State':        ['state', 'province'],
        }

        always_skip = [
            'email',
            'phone',
            'fax',
            'website',
            'semi-colon',
            'hoursperweek',
            'hours per week',
            'datedeadline',
            'date deadline',
            'deliverywebsite',
            'delivery website',
            'online_delivery',
            'contact first',
            'contact last',
            'contact title',
            'first name',
            'last name',
            'contact email',
            'contact name',
        ]

        data_to_fill = {
            'Title':        title,
            'Location':     location,
            'Duration':     duration,
            'Salary':       str(salary) if salary else '',
            'Description':  description,
            'Requirements': requirements,
            'Positions':    '1',
            'Address':      '100 King Street West',
            'City':         'Toronto',
            'Postal':       'M5X 1A9',
            'Country':      self.job_data.get('Country', 'Canada'),
            'State':        self.job_data.get('State', 'Ontario'),
        }

        self.driver.execute_script("window.scrollTo(0, 0);")
        self.human_delay(2, 3)

        all_inputs    = self.driver.find_elements(By.TAG_NAME, "input")
        all_textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
        all_selects   = self.driver.find_elements(By.TAG_NAME, "select")

        print(f"Found {len(all_inputs)} inputs, {len(all_textareas)} textareas, {len(all_selects)} selects")
        print()

        filled_fields   = []
        skipped_fields  = []
        required_missed = []

        for field in all_inputs + all_textareas + all_selects:
            try:
                if not field.is_displayed():
                    continue

                field_tag  = (field.tag_name or '').lower()
                field_type = (field.get_attribute('type') or '').lower()

                if field_tag == 'input' and field_type in ['hidden', 'submit', 'button', 'checkbox', 'radio', 'file']:
                    continue

                field_id          = (field.get_attribute('id') or '').lower()
                field_name        = (field.get_attribute('name') or '').lower()
                field_placeholder = (field.get_attribute('placeholder') or '').lower()

                label_text  = PortalHelpers.get_label_for_field(self.driver, field, field_id)
                is_required = PortalHelpers.is_required_field(label_text, field)

                search_string = PortalHelpers._norm(f"{label_text} {field_id} {field_name} {field_placeholder}")

                should_skip = False
                for skip_word in always_skip:
                    if PortalHelpers._norm(skip_word) in search_string:
                        skipped_fields.append(f"{label_text[:40] or field_name} (skip: '{skip_word}')")
                        should_skip = True
                        break

                if should_skip:
                    continue

                matched = False
                for field_key, keywords in keywords_mapping.items():
                    if not data_to_fill.get(field_key):
                        continue

                    for keyword in keywords:
                        if PortalHelpers._norm(keyword) in search_string:
                            value = data_to_fill[field_key]

                            try:
                                PortalHelpers.robust_fill(self.driver, field, str(value))

                                display_name = label_text[:40] or field_name or field_id
                                print(f"Filled '{field_key}': {display_name}")
                                print(f"  Value: {str(value)[:50]}")
                                print()

                                filled_fields.append(field_key)
                                data_to_fill[field_key] = ''
                                matched = True
                                break

                            except Exception as e:
                                print(f"Error filling {label_text[:40]}: {e}")

                    if matched:
                        break

                if not matched and is_required:
                    required_missed.append({
                        'label': label_text[:60] or field_name,
                        'id':    field_id,
                        'name':  field_name
                    })

            except:
                continue

        # Handle rich text editors
        print()
        print("Handling rich text editors")

        # Try Froala first
        rich_editors = self.driver.find_elements(
            By.CSS_SELECTOR, "div.fr-element.fr-view[contenteditable='true']"
        )

        # If no Froala, try generic contenteditable
        if not rich_editors:
            rich_editors = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div[contenteditable='true'], div.ql-editor, div.ProseMirror"
            )

        print(f"Found {len(rich_editors)} rich text editors")
        print()

        if len(rich_editors) >= 1 and data_to_fill.get('Description'):
            try:
                print("Filling Description (editor 1)")
                desc_editor = rich_editors[0]
                self.driver.execute_script("arguments[0].scrollIntoView(true);", desc_editor)
                self.human_delay(1, 2)
                desc_editor.click()
                self.human_delay(0.5, 1)
                desc_editor.send_keys(data_to_fill['Description'])
                print(f"  Value: {data_to_fill['Description'][:50]}")
                print()
                filled_fields.append('Description')
                data_to_fill['Description'] = ''
            except Exception as e:
                print(f"Description error: {e}")

        if len(rich_editors) >= 2 and data_to_fill.get('Requirements'):
            try:
                print("Filling Requirements (editor 2)")
                req_editor = rich_editors[1]
                self.driver.execute_script("arguments[0].scrollIntoView(true);", req_editor)
                self.human_delay(1, 2)
                req_editor.click()
                self.human_delay(0.5, 1)
                req_editor.send_keys(data_to_fill['Requirements'])
                print(f"  Value: {data_to_fill['Requirements'][:50]}")
                print()
                filled_fields.append('Requirements')
                data_to_fill['Requirements'] = ''
            except Exception as e:
                print(f"Requirements error: {e}")

        # --- Summary ---
        print()
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Fields filled:  {len(filled_fields)}")
        for f in filled_fields:
            print(f"  + {f}")
        print()
        print(f"Fields skipped: {len(skipped_fields)}")
        for f in skipped_fields:
            print(f"  - {f}")
        print()

        unfilled = [k for k, v in data_to_fill.items() if v]
        if unfilled:
            print(f"Warning - Excel data not placed: {', '.join(unfilled)}")

        if required_missed:
            print()
            print(f"WARNING: {len(required_missed)} required (*) fields not filled:")
            for f in required_missed:
                print(f"  ! '{f['label']}'  id='{f['id']}'  name='{f['name']}'")
            print()
            print("These fields need attention before submitting!")

        print("=" * 60)
        print()

        # --- Additional required fields ---

        # 1. Salary field
        print("Filling salary field")
        try:
            salary_input = self.driver.find_element(By.ID, "compensation_from_position_")
            salary_input.clear()
            salary_value = str(salary) if salary else "0"
            salary_input.send_keys(salary_value)
            print(f"  Filled salary: {salary_value}")
        except:
            print("  Salary field (Symplicity-style) not found — skipping")

        # 2. Position Type — check "Full Time"
        print("Selecting Position Type")
        try:
            position_checkbox = self.driver.find_element(
                By.ID, "dnf_class_values_job__job_type___3_check"
            )
            if not position_checkbox.is_selected():
                self.driver.execute_script("arguments[0].click();", position_checkbox)
            print("  Selected 'Full Time'")
        except:
            try:
                ft_label = self.driver.find_element(By.XPATH,
                    "//label[normalize-space()='Full-time' or normalize-space()='Full Time'"
                    " or normalize-space()='Full-Time']"
                )
                label_for = ft_label.get_attribute("for")
                if label_for:
                    radio = self.driver.find_element(By.ID, label_for)
                    self.driver.execute_script("arguments[0].click();", radio)
                    print("  Selected 'Full-time' via label")
                else:
                    self.driver.execute_script("arguments[0].click();", ft_label)
                    print("  Clicked 'Full-time' label directly")
            except:
                print("  Position Type not found — skipping")

        # 3. Automatic Application Packet Generation — select "Yes"
        print("Selecting Automatic Application Packet Generation")
        try:
            auto_packet_radio = self.driver.find_element(By.XPATH,
                "//input[@name='dnf_class_values[job][auto_gen_resume_book]' and @value='1']"
            )
            if not auto_packet_radio.is_selected():
                self.driver.execute_script("arguments[0].click();", auto_packet_radio)
            print("  Selected 'Yes'")
        except:
            print("  Auto packet generation not found — skipping")

        # 4. Policy Affirmation — check the checkbox
        print("Selecting Policy Affirmation")
        try:
            policy_checkbox = self.driver.find_element(
                By.ID, "dnf_class_values_job__policy_affirmed_1_check"
            )
            if not policy_checkbox.is_selected():
                self.driver.execute_script("arguments[0].click();", policy_checkbox)
            print("  Checked Policy Affirmation")
        except:
            print("  Policy Affirmation not found — skipping")

        print()
        print("=" * 60)

        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self.human_delay(2, 3)

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


# ================================================================== #
#  MAIN                                                                #
# ================================================================== #

if __name__ == "__main__":
    from src.config import Config
    from src.turso_data_manager import TursoDataManager
    import pandas as pd

    print("=" * 60)
    print("12Twenty Playbook")
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
        "1": "ttu", "2": "bradley", "3": "cmich", "4": "okstate",
        "5": "rice", "6": "siue", "7": "smu_us", "8": "du", "9": "wichita",
    }

    print("Available 12Twenty Portals:")
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

    playbook = TwelveTwentyPlaybook(
        portal_url=portal_url,
        credentials=credentials,
        job_data={
            "JobId": selected_job.get("JobId", ""),
            "Title": selected_job.get("Title", ""),
            "Description": selected_job.get("Description", ""),
            "Location": selected_job.get("Location", ""),
            "City": selected_job.get("City", "Toronto"),
            "Province": selected_job.get("Province", "ON"),
            "Salary": selected_job.get("Salary", ""),
            "HourlyRate": selected_job.get("HourlyRate", ""),
            "Duration": "520 Hours (approximately 3 months)",
            "Requirements": selected_job.get("Requirements", ""),
            "JobType": selected_job.get("JobType", "Internship"),
            "Industry": selected_job.get("Industry", "Technology"),
            "JobFunction": selected_job.get("JobFunction", ""),
            "StudentGroup": selected_job.get("StudentGroup", "All Students"),
            "Department": selected_job.get("Department", ""),
            "portal_name": selected_portal,
        }
    )

    result = playbook.execute()
    print(f"\nResult: {result['status']}")
    print("=" * 60)
    print("COMPLETE")
    print("=" * 60)
