
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from dotenv import load_dotenv
import os

# Load credentials from .env
load_dotenv()

# Get credentials
USERNAME = os.getenv('UNB_USER')
PASSWORD = os.getenv('UNB_PASS')

print("=" * 60)
print("UNB Login Test")
print("=" * 60)
print(f"Username: {USERNAME}")
print(f"Password: {'*' * len(PASSWORD)}")
print()

# Set up Chrome
options = Options()
options.add_argument('--start-maximized')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:

    print("[1/4] Opening UNB login page...")
    driver.get("https://experience.unb.ca/home/employers/login.htm")
    time.sleep(3)
    
   
    print("[2/4] Entering username...")
    username_field = driver.find_element(By.ID, "j_username")
    username_field.clear()
    username_field.send_keys(USERNAME)
    time.sleep(1)

    print("[3/4] Entering password...")
    password_field = driver.find_element(By.ID, "j_password")
    password_field.clear()
    password_field.send_keys(PASSWORD)
    time.sleep(1)

    print("[4/4] Clicking login button...")
    login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
    login_button.click()

    print()
    print("Waiting for login to complete...")
    time.sleep(5)

    current_url = driver.current_url
    print(f"Current URL: {current_url}")

    if "login" not in current_url.lower():
        print("LOGIN SUCCESS!")
        print()
        print("=" * 60)
        print("BROWSER IS OPEN - Look at it now!")
        print("=" * 60)
        print()
        print("Press Enter when done...")
        input()
    else:
        print("LOGIN FAILED - Still on login page")
        print("Check your credentials in .env file")
        print()
        print("Press Enter to close browser...")
        input()
    
except Exception as e:
    print(f"ERROR: {e}")
    print()
    print("Press Enter to close browser...")
    input()

finally:
    print("Closing browser...")
    driver.quit()
    print("Done!")