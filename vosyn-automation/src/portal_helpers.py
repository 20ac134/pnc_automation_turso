import re
import time
import random
import json
import os
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select



class PortalHelpers:

    # ------------------------------------------------------------------ #
    #  TEXT NORMALISATION                                                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _norm(s: str) -> str:
        """Lowercase, strip punctuation/underscores, collapse spaces."""
        s = (s or "").lower()
        s = re.sub(r"[\W_]+", " ", s)
        return " ".join(s.split())

    # ------------------------------------------------------------------ #
    #  LABEL DETECTION                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_label_for_field(driver, field, field_id: str) -> str:
        """
        Try several strategies to find a human-readable label for a field:
        1. <label for="field_id">
        2. aria-label attribute
        3. placeholder attribute
        4. Nearest preceding <label> in the DOM
        5. Parent container text
        """
        # 1. Explicit <label for="...">
        if field_id:
            try:
                label = driver.find_element(By.XPATH, f"//label[@for='{field_id}']")
                text = (label.text or "").strip()
                if text:
                    return text
            except:
                pass

        # 2. aria-label
        try:
            aria = field.get_attribute("aria-label") or ""
            if aria.strip():
                return aria.strip()
        except:
            pass

        # 3. placeholder
        try:
            ph = field.get_attribute("placeholder") or ""
            if ph.strip():
                return ph.strip()
        except:
            pass

        # 4. Preceding sibling / parent label via JS
        # 4. Table cell sibling (Ottawa-style: label in sibling <td>)
        try:
            label_text = driver.execute_script("""
                const el = arguments[0];
                
                // Check if we're inside a table row
                let td = el.closest('td');
                if (td) {
                    let tr = td.closest('tr');
                    if (tr) {
                        // Get text from the first <td> in this row (usually the label)
                        let firstTd = tr.querySelector('td');
                        if (firstTd && firstTd !== td) {
                            let text = firstTd.innerText.trim();
                            if (text) return text;
                        }
                    }
                }
                
                // Walk up to find a label sibling
                let node = el.previousElementSibling;
                while (node) {
                    if (node.tagName === 'LABEL') return node.innerText;
                    node = node.previousElementSibling;
                }
                // Try parent
                let parent = el.parentElement;
                for (let i = 0; i < 3; i++) {
                    if (!parent) break;
                    const label = parent.querySelector('label');
                    if (label) return label.innerText;
                    parent = parent.parentElement;
                }
                return '';
            """, field)
            if label_text and label_text.strip():
                return label_text.strip()
        except:
            pass

        return ""

    # ------------------------------------------------------------------ #
    #  REQUIRED FIELD DETECTION                                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def is_required_field(label_text: str, field) -> bool:
        """Return True if the field appears to be required."""
        if "*" in (label_text or ""):
            return True
        try:
            if field.get_attribute("required"):
                return True
            if field.get_attribute("aria-required") == "true":
                return True
        except:
            pass
        return False

    # ------------------------------------------------------------------ #
    #  ROBUST FILL                                                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def robust_fill(driver, el, value: str):
        """
        Fill any input / textarea / select robustly:
        - Scrolls into view
        - Handles <select> by visible text or partial match
        - Skips readonly fields
        - Clears existing value before typing
        - Fires input/change/blur events for JS frameworks
        """
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(random.uniform(0.1, 0.3))

        try:
            el.click()
        except:
            driver.execute_script("arguments[0].click();", el)

        tag = (el.tag_name or "").lower()

        # --- SELECT ---
        if tag == "select":
            sel = Select(el)
            target = str(value).strip()
            # exact match
            try:
                sel.select_by_visible_text(target)
                return
            except:
                pass
            # partial match
            for opt in sel.options:
                if target.lower() in (opt.text or "").strip().lower():
                    sel.select_by_visible_text(opt.text)
                    return
            return

        # --- Skip readonly ---
        try:
            readonly = (el.get_attribute("readonly") or "").lower()
            if readonly in ["true", "readonly"]:
                return
        except:
            pass

        # --- Clear then type ---
        try:
            el.send_keys(Keys.CONTROL, "a")
            el.send_keys(Keys.BACKSPACE)
        except:
            pass

        # Fire JS events (for React / Vue / Angular portals)
        driver.execute_script(
            """
            const el = arguments[0];
            const val = arguments[1];
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            );
            if (nativeInputValueSetter) {
                nativeInputValueSetter.set.call(el, val);
            } else {
                el.value = val;
            }
            el.dispatchEvent(new Event('input',  { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            el.dispatchEvent(new Event('blur',   { bubbles: true }));
            """,
            el,
            str(value),
        )

    # ------------------------------------------------------------------ #
    #  AGREEMENT / T&C HANDLER                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def handle_agreement(driver, timeout: int = 5):
        """Click Accept / Agree buttons if a T&C dialog appears."""
        print("Checking for agreements...")

        accept_selectors = [
            "//button[contains(text(), 'Accept')]",
            "//button[contains(text(), 'Agree')]",
            "//button[contains(text(), 'I Accept')]",
            "//button[contains(text(), 'I Agree')]",
            "//a[contains(text(), 'Accept')]",
            "//a[contains(text(), 'Agree')]",
            "//input[@type='submit' and contains(@value, 'Accept')]",
            "//input[@type='submit' and contains(@value, 'Agree')]",
            "//button[contains(@class, 'accept')]",
            "//button[contains(@id, 'accept')]",
            "//button[contains(., 'Terms')]",
            "//button[contains(., 'Conditions')]",
        ]

        try:
            accept_button = None
            for selector in accept_selectors:
                try:
                    buttons = driver.find_elements(By.XPATH, selector)
                    for btn in buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            accept_button = btn
                            break
                    if accept_button:
                        break
                except:
                    continue

            if accept_button:
                print("Found agreement - Accepting")
                time.sleep(random.uniform(1, 2))
                try:
                    accept_button.click()
                except:
                    driver.execute_script("arguments[0].click();", accept_button)
                print("Agreement accepted")
                time.sleep(random.uniform(2, 3))
                return True
            else:
                print("No agreement found")
                return False

        except Exception as e:
            print(f"Error checking for agreement: {e}")
            return False

    # ------------------------------------------------------------------ #
    #  AI FALLBACK FIELD MAPPING                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def ai_map_fields(driver, job_data: dict) -> dict:
        """
        When keyword matching fails, scrape the form HTML and ask Claude
        to return a JSON mapping of { field_id_or_name : value_to_fill }.

        Returns: dict like {"job_title": "Backend Developer", ...}
        """
        print("  [AI] Scraping form HTML for AI field mapping...")

        # Grab only form HTML to keep token count low
        try:
            form_html = driver.execute_script("""
                const forms = document.querySelectorAll('form');
                if (forms.length > 0) {
                    return forms[0].innerHTML.substring(0, 8000);
                }
                return document.body.innerHTML.substring(0, 8000);
            """)
        except Exception as e:
            print(f"  [AI] Could not scrape HTML: {e}")
            return {}

        prompt = f"""You are a web form autofill assistant.

Here is the HTML of a job posting form:
<form_html>
{form_html}
</form_html>

Here is the job data to fill in:
<job_data>
Title: {job_data.get('Title', '')}
Description: {job_data.get('Description', '')}
Location: {job_data.get('Location', '')}
Salary: {job_data.get('Salary', '')}
Duration: {job_data.get('Duration', '4 months')}
Requirements: {job_data.get('Requirements', '')}
Number of Positions: 1
Address: 100 King Street West
City: Toronto
Postal Code: M5X 1A9
</job_data>

Analyse the form fields (inputs, textareas, selects) and map each field to the correct job data value.
Return ONLY a valid JSON object where:
- key = the field's `id` or `name` attribute (use `id` if both exist)
- value = the string value to fill in

Skip fields related to: email, phone, fax, website, contact name, hours per week, deadline dates.
Only include fields you are confident about.
Return ONLY the JSON object, no explanation."""

        try:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                print("  [AI] ANTHROPIC_API_KEY not set, skipping AI mapping")
                return {}

            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-haiku-4-5-20251001",  # lightweight + fast
                    "max_tokens": 500,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )

            data = response.json()
            raw = data["content"][0]["text"].strip()

            # Strip markdown fences if present
            raw = re.sub(r"^```json|^```|```$", "", raw, flags=re.MULTILINE).strip()

            mapping = json.loads(raw)
            print(f"  [AI] Mapped {len(mapping)} fields")
            return mapping

        except Exception as e:
            print(f"  [AI] AI mapping failed: {e}")
            return {}

    @staticmethod
    def apply_ai_mapping(driver, mapping: dict):
        """
        Given a {field_id: value} mapping from AI,
        find each field in the DOM and fill it.
        """
        if not mapping:
            return

        print(f"  [AI] Applying {len(mapping)} AI-mapped fields...")

        for field_key, value in mapping.items():
            if not value:
                continue
            try:
                # Try by id first, then name
                el = None
                try:
                    el = driver.find_element(By.ID, field_key)
                except:
                    pass
                if el is None:
                    try:
                        el = driver.find_element(By.NAME, field_key)
                    except:
                        pass

                if el and el.is_displayed():
                    PortalHelpers.robust_fill(driver, el, str(value))
                    print(f"    [AI] Filled '{field_key}' → '{str(value)[:50]}'")
                else:
                    print(f"    [AI] Field not found/visible: '{field_key}'")

            except Exception as e:
                print(f"    [AI] Error filling '{field_key}': {e}")