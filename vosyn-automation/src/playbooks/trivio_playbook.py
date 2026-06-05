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
import time


class TrivioPlaybook(BasePortalPlaybook):

    # ------------------------------------------------------------------ #
    #  LOGIN — reuse Symplicity-style login                                #
    # ------------------------------------------------------------------ #

    def login(self):
        print(f"Navigating to: {self.portal_url}")
        self.driver.get(self.portal_url)
        self.human_delay(2, 3)

        # Step 0: Click "Connexion" under "Employeur" on landing page
        print("Looking for Employer login link")
        time.sleep(2)
        try:
            links = self.driver.find_elements(By.XPATH, "//a[normalize-space(text())='Connexion']")
            for link in links:
                try:
                    if link.is_displayed():
                        parent_text = self.driver.execute_script(
                            "return arguments[0].closest('li, div, section')?.innerText || '';", link
                        )
                        if 'employeur' in parent_text.lower():
                            self.driver.execute_script("arguments[0].click();", link)
                            print("Clicked 'Connexion' under Employeur")
                            self.human_delay(3, 4)
                            break
                except:
                    continue
        except Exception as e:
            print(f"Could not find Employer login link: {e}")

        # Now find username field
        username_field = None
        username_keywords = ['username', 'email', 'user', 'login', 'j_username', 'userid', 'employerid']

        all_inputs = self.driver.find_elements(By.TAG_NAME, "input")

        for field in all_inputs:
            try:
                if not field.is_displayed():
                    continue
                field_type = (field.get_attribute('type') or '').lower()
                field_id = (field.get_attribute('id') or '').lower()
                field_name = (field.get_attribute('name') or '').lower()
                field_placeholder = (field.get_attribute('placeholder') or '').lower()

                if field_type in ['hidden', 'submit', 'button', 'checkbox', 'radio']:
                    continue

                search_text = f"{field_id} {field_name} {field_placeholder}"
                for keyword in username_keywords:
                    if keyword in search_text:
                        username_field = field
                        print(f"Found username field: id='{field_id}' name='{field_name}' type='{field_type}'")
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

        print("Detecting password field")
        password_field = None
        for field in all_inputs:
            try:
                if not field.is_displayed():
                    continue
                field_type = (field.get_attribute('type') or '').lower()
                field_id = (field.get_attribute('id') or '').lower()
                field_name = (field.get_attribute('name') or '').lower()

                if field_type == 'password':
                    password_field = field
                    print(f"Found password field: id='{field_id}' name='{field_name}'")
                    break

                search_text = f"{field_id} {field_name}"
                if 'password' in search_text or 'passwd' in search_text or field_name == 'pass':
                    password_field = field
                    print(f"Found password field: id='{field_id}' name='{field_name}'")
                    break
            except:
                continue

        if not password_field:
            raise Exception("Could not find password field")

        print("Entering password")
        password_field.clear()
        self.slow_type(password_field, self.credentials['password'])
        self.human_delay(1, 2)

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
                        print(f"Found login button: '{elem_text or elem_value}' id='{elem_id}'")
                        break
                if login_button:
                    break
            except:
                continue

        if not login_button:
            try:
                login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                print("Found submit button (fallback)")
            except:
                try:
                    login_button = self.driver.find_element(By.XPATH, "//input[@type='submit']")
                    print("Found submit input (fallback)")
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
    #  NAVIGATION — Trivio-specific 5-step flow                           #
    # ------------------------------------------------------------------ #

    def navigate_to_job_posting(self):
        # Step 1: Click "Post a Job" on dashboard
        print("Step 1/5: Clicking 'Post a Job'")
        self.human_delay(2, 3)
        try:
            selectors = [
                "//a[normalize-space(text())='Post a Job']",
                "//button[normalize-space(text())='Post a Job']",
                "//a[contains(., 'Post a Job')]",
                "//button[contains(., 'Post a Job')]",
                "//a[normalize-space(text())='Post a job']",
                "//button[normalize-space(text())='Post a job']",
            ]

            clicked = False
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for el in elements:
                        if el.is_displayed() and el.is_enabled():
                            self.driver.execute_script("arguments[0].click();", el)
                            print("  Clicked 'Post a Job'")
                            clicked = True
                            break
                except:
                    continue
                if clicked:
                    break

            if not clicked:
                raise Exception("Could not find 'Post a Job' button")

        except Exception as e:
            print(f"  Step 1 failed: {e}")
            raise

        self.human_delay(3, 4)

        # Step 2: Modal — select "Post Here" under "Job" (not Coop)
        print("Step 2/5: Selecting 'Job' category in modal")
        time.sleep(3)
        try:
            # Look for the modal with "Please select where you would like to post the job"
            # We need the SECOND "Post Here" button (under "Job", not "Coop")
            post_here_buttons = self.driver.find_elements(By.XPATH,
                "//button[contains(., 'Post Here')] | //a[contains(., 'Post Here')]"
            )

            visible_buttons = []
            for btn in post_here_buttons:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        visible_buttons.append(btn)
                except:
                    pass

            if len(visible_buttons) >= 2:
                # Second button is "Job", first is "Coop"
                self.driver.execute_script("arguments[0].click();", visible_buttons[1])
                print("  Clicked 'Post Here' under Job")
            elif len(visible_buttons) == 1:
                self.driver.execute_script("arguments[0].click();", visible_buttons[0])
                print("  Clicked only 'Post Here' button found")
            else:
                # Try finding by looking for "Job" text near a Post Here button
                try:
                    job_post_btn = self.driver.find_element(By.XPATH,
                        "//*[contains(text(), 'Job')]/following::button[contains(., 'Post Here')][1]"
                        " | //*[contains(text(), 'Job')]/following::a[contains(., 'Post Here')][1]"
                    )
                    self.driver.execute_script("arguments[0].click();", job_post_btn)
                    print("  Clicked 'Post Here' near Job text")
                except:
                    print("  WARNING: Could not find 'Post Here' button")

        except Exception as e:
            print(f"  Step 2 failed: {e}")

        self.human_delay(3, 4)

        # Step 3: Terms and Conditions — click "Accept"
        print("Step 3/5: Handling Terms and Conditions")
        time.sleep(2)
        try:
            accept_selectors = [
                "//button[normalize-space(text())='Accept']",
                "//button[contains(., 'Accept')]",
                "//a[normalize-space(text())='Accept']",
                "//input[@type='submit' and @value='Accept']",
                "//input[@type='button' and @value='Accept']",
                # French variants
                "//button[contains(., 'Accepter')]",
                "//a[contains(., 'Accepter')]",
                "//input[@type='submit' and contains(@value, 'Accepter')]",
            ]

            clicked = False
            for selector in accept_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for el in elements:
                        if el.is_displayed():
                            self.driver.execute_script("arguments[0].click();", el)
                            print("  Clicked 'Accept'")
                            clicked = True
                            break
                except:
                    continue
                if clicked:
                    break

            if not clicked:
                print("  No Terms and Conditions found — continuing")

        except Exception as e:
            print(f"  Step 3 failed: {e}")

        self.human_delay(3, 4)

        # Step 4: Click "Post a New Job" (skip repost)
        print("Step 4/5: Clicking 'Post a New Job'")
        time.sleep(2)
        try:
            new_job_selectors = [
                "//a[contains(., 'Post a New Job')]",
                "//button[contains(., 'Post a New Job')]",
                "//a[contains(., 'Post a new Job')]",
                "//a[contains(., 'Post a new job')]",
                "//input[@type='button' and contains(@value, 'Post a New Job')]",
                "//input[@type='submit' and contains(@value, 'Post a New Job')]",
            ]

            clicked = False
            for selector in new_job_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for el in elements:
                        if el.is_displayed():
                            self.driver.execute_script("arguments[0].click();", el)
                            print("  Clicked 'Post a New Job'")
                            clicked = True
                            break
                except:
                    continue
                if clicked:
                    break

            if not clicked:
                # Brute force
                for el in self.driver.find_elements(By.XPATH, "//a | //button | //input"):
                    try:
                        text = (el.text or '').lower()
                        value = (el.get_attribute('value') or '').lower()
                        if el.is_displayed() and ('post a new job' in text or 'post a new job' in value):
                            self.driver.execute_script("arguments[0].click();", el)
                            print("  Clicked 'Post a New Job' via brute force")
                            clicked = True
                            break
                    except:
                        continue

            if not clicked:
                print("  WARNING: Could not find 'Post a New Job' button")

        except Exception as e:
            print(f"  Step 4 failed: {e}")

        self.human_delay(3, 4)

        # Step 5: Language selection page
        print("Step 5/5: Handling language selection")
        time.sleep(3)
        try:
            # Select "No" for "Is the job located in the province of Quebec?"
            no_radio = self.driver.find_elements(By.XPATH,
                "//input[@type='radio'][following-sibling::label[contains(., 'No')] or following::label[contains(., 'No')]]"
                " | //label[normalize-space()='No']/preceding-sibling::input[@type='radio']"
                " | //label[normalize-space()='No']/../input[@type='radio']"
            )

            if not no_radio:
                # Try by value
                no_radio = self.driver.find_elements(By.XPATH,
                    "//input[@type='radio' and (@value='No' or @value='no' or @value='N' or @value='0' or @value='false')]"
                )

            if no_radio:
                for radio in no_radio:
                    try:
                        if radio.is_displayed():
                            self.driver.execute_script("arguments[0].click();", radio)
                            print("  Selected 'No' for Quebec question")
                            break
                    except:
                        continue
            else:
                # Try clicking the label directly
                try:
                    no_label = self.driver.find_element(By.XPATH,
                        "//label[normalize-space()='No']"
                    )
                    self.driver.execute_script("arguments[0].click();", no_label)
                    print("  Clicked 'No' label for Quebec question")
                except:
                    print("  WARNING: Could not find Quebec 'No' option")

            self.human_delay(2, 3)

            # Select "French and English" for language
            lang_radio = self.driver.find_elements(By.XPATH,
                "//input[@type='radio'][following-sibling::label[contains(., 'French and English')] or following::label[contains(., 'French and English')]]"
                " | //label[contains(., 'French and English')]/preceding-sibling::input[@type='radio']"
                " | //label[contains(., 'French and English')]/../input[@type='radio']"
                " | //label[contains(., 'French and English')]"
            )

            if not lang_radio:
                # Try French text
                lang_radio = self.driver.find_elements(By.XPATH,
                    "//label[contains(., 'anglais et fran')]"
                    " | //label[contains(., 'Anglais et fran')]"
                    " | //label[contains(., 'English and French')]"
                )

            if lang_radio:
                for el in lang_radio:
                    try:
                        if el.is_displayed():
                            self.driver.execute_script("arguments[0].click();", el)
                            print("  Selected 'French and English'")
                            break
                    except:
                        continue
            else:
                print("  WARNING: Could not find language option")

            self.human_delay(1, 2)

            # Click "Next"
            next_selectors = [
                "//input[@id='nextBtn']",
                "//input[@type='submit' and @value='Next']",
                "//button[normalize-space(text())='Next']",
                "//input[@type='button' and @value='Next']",
                "//a[normalize-space(text())='Next']",
                # French
                "//input[@type='submit' and @value='Suivant']",
                "//button[normalize-space(text())='Suivant']",
            ]

            for selector in next_selectors:
                try:
                    btn = self.driver.find_element(By.XPATH, selector)
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        print("  Clicked 'Next'")
                        break
                except:
                    continue

        except Exception as e:
            print(f"  Step 5 failed: {e}")

        print("Waiting for job posting form")
        self.human_delay(3, 4)
        print("Job posting form loaded")

    # ------------------------------------------------------------------ #
    #  FILL JOB FORM — French field labels                                 #
    # ------------------------------------------------------------------ #

    def fill_job_form(self):
        print()
        print("=" * 60)
        print("SCANNING FORM AND AUTO-FILLING (TRIVIO - FRENCH)")
        print("=" * 60)
        print()

        title        = self.job_data.get('Title', '')
        description  = self.job_data.get('Description', '')
        location     = self.job_data.get('Location', '')
        salary       = self.job_data.get('Salary', '')
        duration     = self.job_data.get('Duration', '4 months')
        requirements = self.job_data.get('Requirements', '')

        keywords_mapping = {
            'Title':        ['titre du poste', 'titre de l', 'job title', 'position title', 'title of position'],
            'Location':     ['ville de l\'emploi', 'ville de l', 'job location', 'work location', 'lieu de travail'],
            'Duration':     ['duration', 'duree', 'durée', 'term length'],
            'Salary':       ['taux horaire', 'salaire', 'salary', 'hourly rate', 'wage'],
            'Description':  ['description du poste', 'description des t', 'job description', 'position description'],
            'Requirements': ['exigences', 'competences', 'compétences', 'qualifications', 'job requirements', 'job qualifications'],
            'Positions':    ['nombre de postes', 'number of positions', 'number of openings'],
            'City':         ['ville de l\'emploi', 'ville', 'city'],
        }

        always_skip = [
            'courriel',
            'email',
            'phone',
            'telephone',
            'téléphone',
            'fax',
            'website',
            'site web',
            'heures par semaine',
            'nombre d\'heures',
            'hours per week',
            'date limite',
            'date de début',
            'date deadline',
            'nom du client',
            'contact',
            'first name',
            'last name',
            'nom de l\'organisation',
            'site de l\'emploi',
        ]

        data_to_fill = {
            'Title':        title,
            'Location':     location,
            'Duration':     duration,
            'Salary':       str(salary) if salary else '',
            'Description':  description,
            'Requirements': requirements,
            'Positions':    '1',
            'City':         'Toronto',
        }

        self.driver.execute_script("window.scrollTo(0, 0);")
        self.human_delay(2, 3)

        all_inputs    = self.driver.find_elements(By.TAG_NAME, "input")
        all_textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
        all_selects   = self.driver.find_elements(By.TAG_NAME, "select")

        print(f"Found {len(all_inputs)} inputs and {len(all_textareas)} textareas")
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

        # Handle rich text editors (similar toolbar-based editors)
        print()
        print("Handling rich text editors")
        
        # Try Froala-style first
        rich_editors = self.driver.find_elements(
            By.CSS_SELECTOR, "div.fr-element.fr-view[contenteditable='true']"
        )
        
        # If no Froala, try generic contenteditable divs near the form
        if not rich_editors:
            rich_editors = self.driver.find_elements(
                By.CSS_SELECTOR, "div[contenteditable='true']"
            )

        print(f"Found {len(rich_editors)} rich text editors")
        print()

        # Map editors to fields based on order:
        # 1. Nature de l'organisation et/ou du service
        # 2. Description du poste et des tâches à effectuer
        # 3. Environnement de travail et avantages
        # 4. Exigences et/ou compétences particulières

        editor_mapping = [
            ('OrgDescription', "Company/org description"),
            ('Description', "Job description"),
            ('WorkEnvironment', "Work environment"),
            ('Requirements', "Requirements"),
        ]

        for i, (data_key, label) in enumerate(editor_mapping):
            if i >= len(rich_editors):
                break

            # Determine what value to fill
            if data_key == 'Description' and data_to_fill.get('Description'):
                value = data_to_fill['Description']
                data_to_fill['Description'] = ''
                filled_fields.append('Description')
            elif data_key == 'Requirements' and data_to_fill.get('Requirements'):
                value = data_to_fill['Requirements']
                data_to_fill['Requirements'] = ''
                filled_fields.append('Requirements')
            elif data_key == 'OrgDescription':
                value = self.job_data.get('OrgDescription', 'Vosyn inc. is a technology company based in Toronto.')
            elif data_key == 'WorkEnvironment':
                value = self.job_data.get('WorkEnvironment', 'Remote work environment with flexible hours.')
            else:
                continue

            try:
                editor = rich_editors[i]
                self.driver.execute_script("arguments[0].scrollIntoView(true);", editor)
                self.human_delay(1, 2)
                editor.click()
                self.human_delay(0.5, 1)
                editor.send_keys(str(value))
                print(f"Filled editor {i+1}: {label}")
                print(f"  Value: {str(value)[:50]}")
                print()
            except Exception as e:
                print(f"Error filling editor {i+1} ({label}): {e}")

        # --- Additional Trivio-specific fields ---

        # 1. Télétravail — select "Oui"
        print("Selecting Télétravail (Remote Work)")
        try:
            teletravail = self.driver.find_elements(By.XPATH,
                "//label[normalize-space()='Oui']/preceding-sibling::input[@type='radio']"
                " | //label[normalize-space()='Oui']/../input[@type='radio']"
            )
            if not teletravail:
                teletravail = self.driver.find_elements(By.XPATH,
                    "//input[@type='radio'][following-sibling::label[normalize-space()='Oui']]"
                    " | //input[@type='radio'][following::label[normalize-space()='Oui']]"
                )

            if teletravail:
                # Get the first "Oui" radio that's near "Télétravail"
                for radio in teletravail:
                    try:
                        if radio.is_displayed():
                            self.driver.execute_script("arguments[0].click();", radio)
                            print("  Selected 'Oui' (Yes)")
                            break
                    except:
                        continue
            else:
                # Try clicking the label
                try:
                    label = self.driver.find_element(By.XPATH,
                        "//label[normalize-space()='Oui']"
                    )
                    self.driver.execute_script("arguments[0].click();", label)
                    print("  Clicked 'Oui' label")
                except:
                    print("  Télétravail field not found")
        except Exception as e:
            print(f"  Télétravail error: {e}")

        # 2. Région de l'emploi — check "Canada (hors Québec)"
        print("Selecting Région de l'emploi")
        try:
            region_label = self.driver.find_elements(By.XPATH,
                "//label[contains(., 'Canada (hors Qu')]"
                " | //label[contains(., 'Canada (hors Q')]"
            )
            if region_label:
                self.driver.execute_script("arguments[0].click();", region_label[0])
                print("  Selected 'Canada (hors Québec)'")
            else:
                # Try finding the checkbox directly
                region_checkboxes = self.driver.find_elements(By.XPATH,
                    "//input[@type='checkbox'][following-sibling::label[contains(., 'Canada')]]"
                    " | //input[@type='checkbox'][following::label[contains(., 'Canada (hors')]]"
                )
                for cb in region_checkboxes:
                    try:
                        if cb.is_displayed() and not cb.is_selected():
                            self.driver.execute_script("arguments[0].click();", cb)
                            print("  Checked 'Canada (hors Québec)'")
                            break
                    except:
                        continue
        except Exception as e:
            print(f"  Région error: {e}")

        # 3. Niveau d'expérience — check "Aucune" (None)
        print("Selecting Niveau d'expérience")
        try:
            exp_label = self.driver.find_elements(By.XPATH,
                "//label[normalize-space()='Aucune']"
            )
            if exp_label:
                self.driver.execute_script("arguments[0].click();", exp_label[0])
                print("  Selected 'Aucune' (None)")
            else:
                exp_checkboxes = self.driver.find_elements(By.XPATH,
                    "//input[@type='checkbox'][following-sibling::label[normalize-space()='Aucune']]"
                    " | //input[@type='checkbox'][following::label[normalize-space()='Aucune']]"
                )
                for cb in exp_checkboxes:
                    try:
                        if cb.is_displayed():
                            self.driver.execute_script("arguments[0].click();", cb)
                            print("  Checked 'Aucune'")
                            break
                    except:
                        continue
        except Exception as e:
            print(f"  Experience error: {e}")

        # 4. Statut d'emploi — select full-time equivalent from dropdown
        print("Selecting Statut d'emploi")
        try:
            statut_selects = self.driver.find_elements(By.TAG_NAME, "select")
            for sel_elem in statut_selects:
                try:
                    label_text = PortalHelpers.get_label_for_field(self.driver, sel_elem, sel_elem.get_attribute('id') or '')
                    if 'statut' in label_text.lower() or 'emploi' in label_text.lower():
                        sel = Select(sel_elem)
                        # Try different French terms for full-time
                        for option_text in ['Temps plein', 'temps plein', 'Plein temps', 'Full-time', 'Full time']:
                            try:
                                sel.select_by_visible_text(option_text)
                                print(f"  Selected '{option_text}'")
                                break
                            except:
                                continue
                        else:
                            # Partial match
                            for opt in sel.options:
                                if 'plein' in (opt.text or '').lower() or 'full' in (opt.text or '').lower():
                                    sel.select_by_visible_text(opt.text)
                                    print(f"  Selected '{opt.text}'")
                                    break
                        break
                except:
                    continue
        except Exception as e:
            print(f"  Statut d'emploi error: {e}")

        # 5. Documents requis — check "Curriculum vitae"
        print("Selecting Documents requis")
        try:
            cv_label = self.driver.find_elements(By.XPATH,
                "//label[contains(., 'Curriculum vitae')]"
            )
            if cv_label:
                self.driver.execute_script("arguments[0].click();", cv_label[0])
                print("  Checked 'Curriculum vitae'")
            else:
                cv_checkbox = self.driver.find_elements(By.XPATH,
                    "//input[@type='checkbox'][following-sibling::label[contains(., 'Curriculum')]]"
                    " | //input[@type='checkbox'][following::label[contains(., 'Curriculum')]]"
                )
                for cb in cv_checkbox:
                    try:
                        if cb.is_displayed() and not cb.is_selected():
                            self.driver.execute_script("arguments[0].click();", cb)
                            print("  Checked 'Curriculum vitae'")
                            break
                    except:
                        continue
        except Exception as e:
            print(f"  Documents error: {e}")

        # 6. Langue de correspondance — select "Anglais" (English)
        print("Selecting Langue de correspondance")
        try:
            lang_selects = self.driver.find_elements(By.TAG_NAME, "select")
            for sel_elem in lang_selects:
                try:
                    label_text = PortalHelpers.get_label_for_field(self.driver, sel_elem, sel_elem.get_attribute('id') or '')
                    if 'langue' in label_text.lower() and 'correspondance' in label_text.lower():
                        sel = Select(sel_elem)
                        for option_text in ['English', 'Anglais', 'english', 'anglais']:
                            try:
                                sel.select_by_visible_text(option_text)
                                print(f"  Selected '{option_text}'")
                                break
                            except:
                                continue
                        else:
                            for opt in sel.options:
                                if 'english' in (opt.text or '').lower() or 'anglais' in (opt.text or '').lower():
                                    sel.select_by_visible_text(opt.text)
                                    print(f"  Selected '{opt.text}'")
                                    break
                        break
                except:
                    continue
        except Exception as e:
            print(f"  Langue error: {e}")

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
    print("Trivio Playbook - Sherbrooke")
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

    selected_portal = "sherbrooke"
    portal_url = Config.get_portal_url(selected_portal)
    credentials = Config.get_credentials(selected_portal)
    print(f"Portal:   Sherbrooke (Trivio)")
    print(f"URL:      {portal_url}")
    print(f"Username: {credentials['username']}\n")

    playbook = TrivioPlaybook(
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
