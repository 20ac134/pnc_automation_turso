"""
Test Setup - Verify all dependencies are installed correctly
Run this after installing packages to confirm everything works
"""

import os
import sys

def test_python_version():
    """Check Python version"""
    print("Testing Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f" Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f" Python {version.major}.{version.minor}.{version.micro} - Need 3.10+")
        return False


def test_imports():
    """Test if all required packages can be imported"""
    print("\nTesting package imports...")
    
    packages = {
        'selenium': 'Selenium',
        'pandas': 'Pandas',
        'dotenv': 'Python-dotenv',
        'PIL': 'Pillow',
        'libsql': 'libSQL'
    }
    
    all_ok = True
    
    for package, name in packages.items():
        try:
            if package == 'dotenv':
                from dotenv import load_dotenv
            elif package == 'PIL':
                from PIL import Image
            else:
                __import__(package)
            
            # Get version if possible
            try:
                if package == 'dotenv':
                    import dotenv
                    mod = dotenv
                elif package == 'PIL':
                    import PIL
                    mod = PIL
                else:
                    mod = __import__(package)
                
                version = getattr(mod, '__version__', 'installed')
                print(f"{name}: {version}")
            except:
                print(f" {name}: installed")
                
        except ImportError:
            print(f"{name}: NOT INSTALLED")
            all_ok = False
    
    return all_ok


def test_webdriver():
    """Test Selenium WebDriver"""
    print("\nTesting Selenium WebDriver...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        print("  Installing ChromeDriver (first time may take a moment)...")
        
        # Set up driver
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run without opening window
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        
        # Test navigation
        driver.get("https://www.google.com")
        title = driver.title
        driver.quit()
        
        print(f" ChromeDriver working! (tested with: {title})")
        return True
        
    except Exception as e:
        print(f" ChromeDriver error: {e}")
        print("   Make sure Chrome browser is installed!")
        return False


def test_file_structure():
    """Check if project structure exists"""
    print("\nChecking project structure...")
    
    import os
    from pathlib import Path
    
    required_dirs = [
        'src',
        'src/playbooks',
        'src/utils',
        'tests',
        'data',
        'screenshots',
        'logs'
    ]
    
    required_files = [
        '.env',
        '.gitignore',
        'README.md'
    ]
    
    all_ok = True
    
    for directory in required_dirs:
        if Path(directory).exists():
            print(f"{directory}/")
        else:
            print(f" {directory}/ - MISSING")
            all_ok = False
    
    for file in required_files:
        if Path(file).exists():
            print(f" {file}")
        else:
            print(f"  {file} - missing (optional)")
    
    return all_ok


def test_turso_configuration():
    """Test Turso/libSQL configuration and expected tables."""
    print("\nTesting Turso configuration...")

    try:
        from pathlib import Path

        from dotenv import load_dotenv
        from src.turso_data_manager import TursoDataManager
        from src.tracking_manager import TrackingManager
        from src.turso_database import TursoConnection

        load_dotenv(Path(".env"))
        database_url = os.getenv("TURSO_DATABASE_URL")
        auth_token = os.getenv("TURSO_AUTH_TOKEN")
        if not database_url:
            print(" TURSO_DATABASE_URL is missing from .env")
            return False
        if not auth_token:
            print(" TURSO_AUTH_TOKEN is missing from .env")
            return False

        TursoDataManager()
        TrackingManager()
        expected_tables = {
            "job_posts",
            "posting_runs",
            "job_templates",
            "portal_urls",
            "application_tracking",
        }

        rows = TursoConnection.fetch_all("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
        """)

        existing_tables = {row["name"] for row in rows}
        missing_tables = sorted(expected_tables - existing_tables)
        if missing_tables:
            print(f" Missing Turso tables: {', '.join(missing_tables)}")
            return False

        print(" Turso connection and required tables are working!")
        return True

    except Exception as e:
        print(f"Turso configuration failed: {e}")
        return False


def print_summary(results):
    """Print summary of tests"""
    print("\n" + "=" * 60)
    print("SETUP TEST SUMMARY")
    print("=" * 60)
    
    all_passed = all(results.values())
    
    for test_name, passed in results.items():
        status = " PASS" if passed else " FAIL"
        print(f"{status} - {test_name}")
    
    print("=" * 60)
    
    if all_passed:
        print("\n All tests passed! You're ready for Day 2!")
        print("\nNext steps:")
        print("1. Fill in credentials in .env file")
        print("2. Manually test login to 3-5 portals")
        print("3. Confirm Turso data is visible in the dashboard or CLI")
        print("\nThen proceed to Day 2: Building the data manager")
    else:
        print("\n  Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Missing packages: pip install -r requirements.txt")
        print("- ChromeDriver issues: Make sure Chrome browser is installed")
        print("- Missing directories: Run setup_project.py")
    
    print()


def main():
    """Run all tests"""
    print("=" * 60)
    print("Vosyn Automation - Setup Verification")
    print("=" * 60)
    print()
    
    results = {}
    
    # Run tests
    results['Python Version'] = test_python_version()
    results['Package Imports'] = test_imports()
    results['Project Structure'] = test_file_structure()
    results['Turso Configuration'] = test_turso_configuration()
    results['Selenium WebDriver'] = test_webdriver()
    
    # Print summary
    print_summary(results)


if __name__ == "__main__":
    main()
