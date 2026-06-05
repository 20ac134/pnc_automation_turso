import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.playbooks.base_playbook import BasePortalPlaybook
from src.portal_helpers import PortalHelpers
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time


class VIUPlaybook(BasePortalPlaybook):
    """
    Playbook for Vancouver Island University (VIU).
    
    VIU uses a Symplicity-based portal but with a different navigation flow:
    1. Login (standard Symplicity)
    2. Click briefcase icon button (btn--post--job) instead of "Post a Job" text
    3. Category modal → click "Post"
    4. "Select Experience Type" wizard → pick "Co-op - Optional" → click "Next"
    5. Fill the Co-op form (different fields from standard Symplicity)
    6. Pause for manual review
    """

    # ------------------------------------------------------------------ #
    #  LOGIN — same as Symplicity
    # ------------------------------------------------------------------ #

    def login(self):
        print(f"Navigating to: {self.portal_url}")
        self.driver.get(self.portal_url)
        self.human_delay(2, 3)

        # Find username field
        username_field = None
        username_keywords = ['username', 'email', 'user', 'login', 'j_username', 'userid', 'employerid']
        all_inputs = self.driver.find_elements(By.TAG_NAME, "input")

        for field in all_inputs:
            try:
                if not field.is_displayed():
                    continue
                field_type = (field.get_attribute('type') or '').lower()
                if field_type in ['hidden', 'submit', 'button', 'checkbox', 'radio']:
                    continue
                field_id = (field.get_attribute('id') or '').lower()
                field_name = (field.get_attribute('name') or '').lower()
                field_placeholder = (field.get_attribute('placeholder') or '').lower()
                search_text = f"{field_id} {field_name} {field_placeholder}"

                for keyword in username_keywords:
                    if keyword in search_text:
                        username_field = field
                        print(f"Found username field: id='{field_id}' name='{field_name}'")
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
                field_type = (field.get_attribute('type') or '').lower()
                if field_type == 'password':
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

        # Find and click login button
        print("Looking for login button")
        login_button = None
        button_keywords = ['login', 'sign in', 'submit', 'log in', 'connexion', 'se connecter']

        all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
        all_links = self.driver.find_elements(By.TAG_NAME, "a")
        all_submit_inputs = self.driver.find_elements(By.XPATH, "//input[@type='submit']")

        for elem in all_buttons + all_links + all_submit_inputs:
            try:
                if not elem.is_displayed():
                    continue
                elem_text = (elem.text or '').lower()
                elem_value = (elem.get_attribute('value') or '').lower()
                elem_id = (elem.get_attribute('id') or '').lower()
                search_text = f"{elem_text} {elem_value} {elem_id}"

                for keyword in button_keywords:
                    if keyword in search_text:
                        login_button = elem
                        break
                if login_button:
                    break
            except:
                continue

        if not login_button:
            try:
                login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            except:
                try:
                    login_button = self.driver.find_element(By.XPATH, "//input[@type='submit']")
                except:
                    raise Exception("Could not find login button")

        print("Clicking login button")
        try:
            login_button.click()
        except:
            self.driver.execute_script("arguments[0].click();", login_button)

        print("Waiting for dashboard")
        self.human_delay(3, 5)

        if "login" in self.driver.current_url.lower() or "signin" in self.driver.current_url.lower():
            raise Exception("Login failed - still on login page")

        print("Login successful!")

    # ------------------------------------------------------------------ #
    #  NAVIGATION — VIU-specific wizard flow
    # ------------------------------------------------------------------ #

    def navigate_to_job_posting(self):
        print("Step 1/4: Looking for briefcase 'Post a Job' icon button")
        self.human_delay(3, 5)

        # VIU uses an icon button with class btn--post--job
        post_job_btn = None
        selectors = [
            "//button[contains(@class, 'btn--post--job')]",
            "//button[contains(@class, 'post--job')]",
            "//button[normalize-space(text())='Post a Job']",
            "//a[normalize-space(text())='Post a Job']",
            "//button[contains(., 'Post a Job')]",
            "//a[contains(., 'Post a Job')]",
        ]

        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    if elem.is_displayed() and elem.is_enabled():
                        post_job_btn = elem
                        print(f"Found post job button via: {selector}")
                        break
                if post_job_btn:
                    break
            except:
                continue

        if not post_job_btn:
            raise Exception("Post a Job button not found")

        self.driver.execute_script("arguments[0].scrollIntoView(true);", post_job_btn)
        self.human_delay(1, 2)

        try:
            post_job_btn.click()
        except:
            self.driver.execute_script("arguments[0].click();", post_job_btn)

        print("Clicked 'Post a Job' icon")
        self.human_delay(3, 4)

        # Step 2: Handle category modal
        print("Step 2/4: Handling job category modal")
        try:
            # Look for modal with "Post" button
            modal_post_buttons = self.driver.find_elements(
                By.XPATH, "//button[contains(text(), 'Post')] | //a[contains(text(), 'Post')]"
            )
            for btn in modal_post_buttons:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        self.driver.execute_script("arguments[0].click();", btn)
                        print("Clicked 'Post' in modal")
                        self.human_delay(2, 3)
                        break
                except:
                    continue
        except Exception as e:
            print(f"Modal handling: {e}")

        # Handle agreement if present
        PortalHelpers.handle_agreement(self.driver)
        self.human_delay(2, 3)

        # Step 3: Select Experience Type wizard
        print("Step 3/4: Selecting Experience Type")
        try:
            # Find the Experience Type dropdown
            experience_select = None

            # Try by label
            try:
                experience_select = self.driver.find_element(
                    By.XPATH, "//select[preceding::*[contains(text(), 'Experience Type')]]"
                )
            except:
                pass

            if not experience_select:
                # Try all selects on the page
                all_selects = self.driver.find_elements(By.TAG_NAME, "select")
                for sel in all_selects:
                    try:
                        if sel.is_displayed():
                            experience_select = sel
                            break
                    except:
                        continue

            if experience_select:
                sel = Select(experience_select)
                # Try to select "Co-op - Optional" or similar
                target_options = ['co-op - optional', 'co-op', 'coop', 'co op']
                selected = False

                for opt in sel.options:
                    opt_text = (opt.text or '').strip().lower()
                    for target in target_options:
                        if target in opt_text:
                            sel.select_by_visible_text(opt.text.strip())
                            print(f"Selected Experience Type: {opt.text.strip()}")
                            selected = True
                            break
                    if selected:
                        break

                if not selected:
                    # Just select the first non-default option
                    if len(sel.options) > 1:
                        sel.select_by_index(1)
                        print(f"Selected first option: {sel.options[1].text}")

                self.human_delay(1, 2)
            else:
                print("Warning: Experience Type dropdown not found")

        except Exception as e:
            print(f"Experience Type selection error: {e}")

        # Step 4: Click "Next" button
        print("Step 4/4: Clicking 'Next' button")
        try:
            next_btn = None
            next_selectors = [
                "//button[normalize-space(text())='Next']",
                "//a[normalize-space(text())='Next']",
                "//button[contains(@class, 'btn') and contains(text(), 'Next')]",
                "//input[@type='submit' and @value='Next']",
            ]

            for selector in next_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            next_btn = elem
                            break
                    if next_btn:
                        break
                except:
                    continue

            if next_btn:
                try:
                    next_btn.click()
                except:
                    self.driver.execute_script("arguments[0].click();", next_btn)
                print("Clicked 'Next'")
            else:
                print("Warning: 'Next' button not found")

        except Exception as e:
            print(f"Next button error: {e}")

        self.human_delay(3, 4)
        print("Job posting form loaded")

    # ------------------------------------------------------------------ #
    #  FILL FORM — VIU Co-op specific fields
    # ------------------------------------------------------------------ #

    def fill_job_form(self):
        print()
        print("=" * 60)
        print("VIU CO-OP FORM — SCANNING AND AUTO-FILLING")
        print("=" * 60)
        print()

        title = self.job_data.get('Title', '')
        description = self.job_data.get('Description', '')
        location = self.job_data.get('Location', '')
        salary = self.job_data.get('Salary', '')
        requirements = self.job_data.get('Requirements', '')

        # VIU-specific keyword mapping
        keywords_mapping = {
            'Title': ['co-op job title', 'job title', 'position title', 'titre'],
            'Description': ['co-op opportunity description', 'job description', 'description'],
            'Salary': ['salaryamount', 'salary amount', 'amount'],
            'Positions': ['number of positions', 'positions'],
        }

        always_skip = [
            'email', 'phone', 'fax', 'website',
            'supervisor first', 'supervisor last', 'supervisor email',
            'supervisor job', 'organization', 'department',
            'address line', 'city', 'province', 'country', 'postal code',
            'go live date', 'applications open', 'expiry date',
            'hours per week',
        ]

        data_to_fill = {
            'Title': title,
            'Description': description,
            'Salary': str(salary) if salary else '',
            'Positions': '1',
        }

        self.driver.execute_script("window.scrollTo(0, 0);")
        self.human_delay(2, 3)

        all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
        all_textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
        all_selects = self.driver.find_elements(By.TAG_NAME, "select")

        print(f"Found {len(all_inputs)} inputs, {len(all_textareas)} textareas, {len(all_selects)} selects")
        print()

        filled_fields = []
        skipped_fields = []
        required_missed = []

        for field in all_inputs + all_textareas + all_selects:
            try:
                if not field.is_displayed():
                    continue

                field_tag = (field.tag_name or '').lower()
                field_type = (field.get_attribute('type') or '').lower()

                if field_tag == 'input' and field_type in ['hidden', 'submit', 'button', 'checkbox', 'radio', 'file']:
                    continue

                field_id = (field.get_attribute('id') or '').lower()
                field_name = (field.get_attribute('name') or '').lower()
                field_placeholder = (field.get_attribute('placeholder') or '').lower()

                label_text = PortalHelpers.get_label_for_field(self.driver, field, field_id)
                is_required = PortalHelpers.is_required_field(label_text, field)

                search_string = PortalHelpers._norm(f"{label_text} {field_id} {field_name} {field_placeholder}")

                # Check skip list
                should_skip = False
                for skip_word in always_skip:
                    if PortalHelpers._norm(skip_word) in search_string:
                        skipped_fields.append(f"{label_text[:40] or field_name} (skip: '{skip_word}')")
                        should_skip = True
                        break

                if should_skip:
                    continue

                # Try keyword matching
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
                        'id': field_id,
                        'name': field_name
                    })

            except:
                continue

        # Handle "Type of Co-op" dropdown
        print("Handling 'Type of Co-op' dropdown")
        try:
            all_selects = self.driver.find_elements(By.TAG_NAME, "select")
            for sel_elem in all_selects:
                try:
                    if not sel_elem.is_displayed():
                        continue
                    label = PortalHelpers.get_label_for_field(
                        self.driver, sel_elem, (sel_elem.get_attribute('id') or '').lower()
                    )
                    if 'type of co-op' in PortalHelpers._norm(label) or 'type of coop' in PortalHelpers._norm(label):
                        sel = Select(sel_elem)
                        # Try to find a reasonable option
                        for opt in sel.options:
                            opt_text = (opt.text or '').strip().lower()
                            if any(kw in opt_text for kw in ['4 month', '4-month', 'four month', 'standard']):
                                sel.select_by_visible_text(opt.text.strip())
                                print(f"Selected Type of Co-op: {opt.text.strip()}")
                                filled_fields.append('Type of Co-op')
                                break
                        else:
                            # Select first non-default option
                            if len(sel.options) > 1:
                                sel.select_by_index(1)
                                print(f"Selected first Co-op type: {sel.options[1].text}")
                                filled_fields.append('Type of Co-op')
                        break
                except:
                    continue
        except Exception as e:
            print(f"Type of Co-op error: {e}")

        # Handle rich text editors (Froala) for description
        print()
        print("Handling rich text editors")
        froala_editors = self.driver.find_elements(
            By.CSS_SELECTOR, "div.fr-element.fr-view[contenteditable='true']"
        )
        print(f"Found {len(froala_editors)} rich text editors")

        if len(froala_editors) >= 1 and data_to_fill.get('Description'):
            try:
                print("Filling Description (editor 1)")
                desc_editor = froala_editors[0]
                self.driver.execute_script("arguments[0].scrollIntoView(true);", desc_editor)
                self.human_delay(1, 2)
                desc_editor.click()
                self.human_delay(0.5, 1)
                desc_editor.send_keys(data_to_fill['Description'])
                print(f"  Value: {data_to_fill['Description'][:50]}")
                filled_fields.append('Description')
                data_to_fill['Description'] = ''
            except Exception as e:
                print(f"Description error: {e}")

        # Summary
        print()
        print("=" * 60)
        print("VIU FORM FILL SUMMARY")
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

        print("=" * 60)
        print()

        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self.human_delay(2, 3)

    # ------------------------------------------------------------------ #
    #  SUBMIT — same as Symplicity (find but don't click)
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
#  MAIN
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    from src.config import Config
    from src.turso_data_manager import TursoDataManager
    import pandas as pd

    print("=" * 60)
    print("VIU Playbook")
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

    selected_portal = "viu"
    portal_url = Config.get_portal_url(selected_portal)
    credentials = Config.get_credentials(selected_portal)
    print(f"Portal:   VIU")
    print(f"URL:      {portal_url}")
    print(f"Username: {credentials['username']}\n")

    playbook = VIUPlaybook(
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
