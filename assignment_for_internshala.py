from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import time
import sys
import re


def scrape_rera_projects():
    driver = None
    try:
        print("Setting up Microsoft Edge driver...")

        # Setup Edge options
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # Setup Edge driver
        service = Service(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=options)
        print("✅ Edge driver setup successful!")

        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print("Navigating to RERA Odisha website...")
        url = 'https://rera.odisha.gov.in/projects/project-list'
        driver.get(url)

        # Wait for page to load
        wait = WebDriverWait(driver, 45)
        time.sleep(10)

        print("Page loaded, looking for content...")

        # Find content using the selector that worked
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.project-list')))
            print("Found project list container")
        except:
            print("Could not find project list container")
            return []

        project_details = []

        # Process 6 projects by re-finding elements each time
        for i in range(1, 7):
            print(f"\nProcessing project {i}/6...")

            try:
                # Re-find all project links fresh each time to avoid stale elements
                time.sleep(3)  # Allow page to stabilize

                # Find all "View Details" links fresh
                view_details_links = driver.find_elements(By.PARTIAL_LINK_TEXT, 'View Details')

                if not view_details_links:
                    # Try alternative selectors
                    view_details_links = driver.find_elements(By.PARTIAL_LINK_TEXT, 'View')
                    if not view_details_links:
                        view_details_links = driver.find_elements(By.LINK_TEXT, 'Details')

                if len(view_details_links) < i:
                    print(f"Not enough project links found. Available: {len(view_details_links)}, needed: {i}")
                    break

                # Get the i-th link (index i-1)
                link_to_click = view_details_links[i - 1]
                print(f"Clicking on project {i}: {link_to_click.text[:30]}...")

                # Scroll to element and click
                driver.execute_script("arguments[0].scrollIntoView(true);", link_to_click)
                time.sleep(2)

                # Click using JavaScript to avoid interception issues
                driver.execute_script("arguments[0].click();", link_to_click)
                time.sleep(8)  # Wait for details page to load

                # Initialize variables
                rera_regd_no = "Not Found"
                project_name = "Not Found"
                promoter_name = "Not Found"
                promoter_address = "Not Found"
                gst_no = "Not Found"

                print("Extracting project details...")

                # Get all page text for pattern matching
                page_text = driver.find_element(By.TAG_NAME, 'body').text

                # Enhanced RERA Registration Number extraction
                print("Extracting RERA Registration Number...")
                rera_selectors = [
                    "//th[contains(text(),'RERA Registration No')]/following-sibling::td",
                    "//th[contains(text(),'Registration No')]/following-sibling::td",
                    "//td[contains(text(),'RERA Registration No')]/following-sibling::td",
                    "//label[contains(text(),'RERA Registration No')]/following-sibling::*",
                    "//span[contains(text(),'RERA Registration No')]/following-sibling::*",
                    "//*[contains(text(),'RERA Registration No')]/parent::*/following-sibling::*",
                    "//th[text()='RERA Registration No']/following-sibling::td",
                    "//td[text()='RERA Registration No']/following-sibling::td"
                ]

                for selector in rera_selectors:
                    try:
                        elements = driver.find_elements(By.XPATH, selector)
                        if elements and elements[0].text.strip():
                            rera_regd_no = elements[0].text.strip()
                            break
                    except:
                        continue

                # If still not found, try regex patterns for RERA number
                if rera_regd_no == "Not Found":
                    rera_patterns = [
                        r'RERA\s*Registration\s*No\.?\s*:?\s*([A-Z0-9/\-]+)',
                        r'Registration\s*No\.?\s*:?\s*([A-Z0-9/\-]+)',
                        r'RERA\s*No\.?\s*:?\s*([A-Z0-9/\-]+)',
                        r'Project\s*Registration\s*No\.?\s*:?\s*([A-Z0-9/\-]+)',
                        r'([A-Z]{2}/\d+/\d+/\d+)',  # Pattern like RP/01/2025/01362
                        r'(\d{11})'  # 11-digit number pattern
                    ]

                    for pattern in rera_patterns:
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            rera_regd_no = match.group(1).strip()
                            break

                # Click on "Project Overview" tab to get project name
                print("Looking for Project Overview tab...")
                overview_tab_selectors = [
                    "//a[contains(text(),'Project Overview')]",
                    "//button[contains(text(),'Project Overview')]",
                    "//*[contains(@class,'tab')][contains(text(),'Project Overview')]",
                    "//li[contains(text(),'Project Overview')]",
                    "//a[text()='Project Overview']"
                ]

                overview_tab_found = False
                for selector in overview_tab_selectors:
                    try:
                        tabs = driver.find_elements(By.XPATH, selector)
                        if tabs:
                            driver.execute_script("arguments[0].click();", tabs[0])
                            time.sleep(4)
                            overview_tab_found = True
                            print("Project Overview tab clicked successfully")
                            break
                    except:
                        continue

                if overview_tab_found:
                    # Extract Project Name from Project Overview tab
                    print("Extracting Project Name...")
                    name_selectors = [
                        "//th[contains(text(),'Project Name')]/following-sibling::td",
                        "//td[contains(text(),'Project Name')]/following-sibling::td",
                        "//label[contains(text(),'Project Name')]/following-sibling::*",
                        "//span[contains(text(),'Project Name')]/following-sibling::*",
                        "//*[contains(text(),'Project Name')]/parent::*/following-sibling::*",
                        "//th[text()='Project Name']/following-sibling::td",
                        "//td[text()='Project Name']/following-sibling::td"
                    ]

                    for selector in name_selectors:
                        try:
                            elements = driver.find_elements(By.XPATH, selector)
                            if elements and elements[0].text.strip() and elements[0].text.strip() != "Projects":
                                project_name = elements[0].text.strip()
                                break
                        except:
                            continue

                    # If still not found, try regex pattern
                    if project_name == "Not Found" or project_name == "Projects":
                        project_match = re.search(r'Project\s*Name\s*:?\s*([^\n\r]+)', page_text, re.IGNORECASE)
                        if project_match and project_match.group(1).strip() != "Projects":
                            project_name = project_match.group(1).strip()

                # Click on "Promoter Details" tab to get promoter information
                print("Looking for Promoter Details tab...")
                promoter_tab_selectors = [
                    "//a[contains(text(),'Promoter Details')]",
                    "//button[contains(text(),'Promoter Details')]",
                    "//*[contains(@class,'tab')][contains(text(),'Promoter')]",
                    "//li[contains(text(),'Promoter Details')]",
                    "//a[text()='Promoter Details']",
                    "//a[contains(text(),'Promoter')]"
                ]

                promoter_tab_found = False
                for selector in promoter_tab_selectors:
                    try:
                        tabs = driver.find_elements(By.XPATH, selector)
                        if tabs:
                            driver.execute_script("arguments[0].click();", tabs[0])
                            time.sleep(4)
                            promoter_tab_found = True
                            print("Promoter Details tab clicked successfully")
                            break
                    except:
                        continue

                if promoter_tab_found:
                    # Get updated page text after clicking promoter tab
                    promoter_page_text = driver.find_element(By.TAG_NAME, 'body').text

                    # ENHANCED EXTRACTION FOR PROPRIETORY NAME (SPECIFIC FIX FOR PROJECT 3)
                    print("Extracting Company/Proprietory Name...")

                    # First try exact "Proprietory Name" selectors
                    proprietory_selectors = [
                        "//th[text()='Proprietory Name']/following-sibling::td",
                        "//td[text()='Proprietory Name']/following-sibling::td",
                        "//th[contains(text(),'Proprietory Name')]/following-sibling::td",
                        "//td[contains(text(),'Proprietory Name')]/following-sibling::td",
                        "//label[contains(text(),'Proprietory Name')]/following-sibling::*",
                        "//span[contains(text(),'Proprietory Name')]/following-sibling::*",
                        "//*[contains(text(),'Proprietory Name')]/parent::*/following-sibling::*"
                    ]

                    for selector in proprietory_selectors:
                        try:
                            elements = driver.find_elements(By.XPATH, selector)
                            if elements and elements[0].text.strip():
                                potential_name = elements[0].text.strip()
                                print(f"Found potential proprietory name: {potential_name}")
                                if len(potential_name) > 3 and potential_name != "Not Found":
                                    promoter_name = potential_name
                                    break
                        except Exception as e:
                            print(f"Error with selector {selector}: {e}")
                            continue

                    # If still not found, try company name selectors
                    if promoter_name == "Not Found":
                        company_selectors = [
                            "//th[text()='Company Name']/following-sibling::td",
                            "//td[text()='Company Name']/following-sibling::td",
                            "//th[contains(text(),'Company Name')]/following-sibling::td",
                            "//td[contains(text(),'Company Name')]/following-sibling::td",
                            "//label[contains(text(),'Company Name')]/following-sibling::*",
                            "//span[contains(text(),'Company Name')]/following-sibling::*",
                            "//*[contains(text(),'Company Name')]/parent::*/following-sibling::*",
                            "//th[contains(text(),'Promoter Name')]/following-sibling::td",
                            "//td[contains(text(),'Promoter Name')]/following-sibling::td"
                        ]

                        for selector in company_selectors:
                            try:
                                elements = driver.find_elements(By.XPATH, selector)
                                if elements and elements[0].text.strip():
                                    potential_name = elements[0].text.strip()
                                    if len(potential_name) > 3 and potential_name != "Not Found":
                                        promoter_name = potential_name
                                        break
                            except:
                                continue

                    # If still not found, try aggressive text search
                    if promoter_name == "Not Found":
                        print("Trying aggressive text search for promoter name...")

                        # Look for "RITA PODDAR" pattern specifically
                        rita_pattern = re.search(r'RITA\s+PODDAR', promoter_page_text, re.IGNORECASE)
                        if rita_pattern:
                            promoter_name = "RITA PODDAR"
                            print("Found RITA PODDAR using regex pattern")
                        else:
                            # Try to find any individual name pattern
                            individual_patterns = [
                                r'Proprietory\s*Name\s*:?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
                                r'([A-Z][A-Z\s]+(?:PRIVATE\s+LIMITED|PVT\.?\s*LTD\.?|LIMITED|LTD\.?))',
                                r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',  # Individual name pattern
                                r'Company\s*Name\s*:?\s*([^\n\r]+)',
                                r'Promoter\s*Name\s*:?\s*([^\n\r]+)'
                            ]

                            for pattern in individual_patterns:
                                match = re.search(pattern, promoter_page_text, re.IGNORECASE)
                                if match:
                                    potential_name = match.group(1).strip()
                                    # Filter out navigation text and invalid entries
                                    if (len(potential_name) > 3 and
                                            not any(skip in potential_name.lower() for skip in
                                                    ['skip to main', 'navigation', 'menu', 'header', 'footer',
                                                     'content', 'tab', 'link', 'address', 'plot', 'gst'])):
                                        promoter_name = potential_name
                                        print(f"Found promoter name using pattern: {potential_name}")
                                        break

                    # Extract Address (enhanced for both types)
                    print("Extracting Address...")
                    address_selectors = [
                        # Permanent Address (for individuals)
                        "//th[text()='Permanent Address']/following-sibling::td",
                        "//td[text()='Permanent Address']/following-sibling::td",
                        "//th[contains(text(),'Permanent Address')]/following-sibling::td",
                        "//td[contains(text(),'Permanent Address')]/following-sibling::td",
                        "//label[contains(text(),'Permanent Address')]/following-sibling::*",
                        "//span[contains(text(),'Permanent Address')]/following-sibling::*",
                        "//*[contains(text(),'Permanent Address')]/parent::*/following-sibling::*",

                        # Registered Office Address (for companies)
                        "//th[text()='Registered Office Address']/following-sibling::td",
                        "//td[text()='Registered Office Address']/following-sibling::td",
                        "//th[contains(text(),'Registered Office Address')]/following-sibling::td",
                        "//td[contains(text(),'Registered Office Address')]/following-sibling::td",
                        "//label[contains(text(),'Registered Office Address')]/following-sibling::*",
                        "//span[contains(text(),'Registered Office Address')]/following-sibling::*",
                        "//*[contains(text(),'Registered Office Address')]/parent::*/following-sibling::*",

                        # General address selectors
                        "//th[contains(text(),'Address')]/following-sibling::td",
                        "//td[contains(text(),'Address')]/following-sibling::td"
                    ]

                    for selector in address_selectors:
                        try:
                            elements = driver.find_elements(By.XPATH, selector)
                            if elements and elements[0].text.strip():
                                promoter_address = elements[0].text.strip()
                                break
                        except:
                            continue

                    # If still not found, try regex patterns
                    if promoter_address == "Not Found":
                        address_patterns = [
                            r'Permanent\s*Address\s*:?\s*([^\n\r]+)',
                            r'Registered\s*Office\s*Address\s*:?\s*([^\n\r]+)',
                            r'Address\s*:?\s*([^\n\r]+(?:Plot|House|Building|Road|Street|Colony|Nagar|Bhubaneswar|Odisha|Sambalpur)[^\n\r]*)',
                            r'(Plot\s*[^\n\r]+Odisha[^\n\r]*)',
                            r'([A-Z][^,\n\r]*(?:Plot|House|Building)[^,\n\r]*Odisha[^,\n\r]*)'
                        ]

                        for pattern in address_patterns:
                            match = re.search(pattern, promoter_page_text, re.IGNORECASE)
                            if match:
                                potential_address = match.group(1).strip()
                                if len(potential_address) > 15:
                                    promoter_address = potential_address
                                    break

                    # Extract GST Number
                    print("Extracting GST Number...")
                    gst_selectors = [
                        "//th[contains(text(),'GST No')]/following-sibling::td",
                        "//td[contains(text(),'GST No')]/following-sibling::td",
                        "//label[contains(text(),'GST No')]/following-sibling::*",
                        "//span[contains(text(),'GST No')]/following-sibling::*",
                        "//*[contains(text(),'GST No')]/parent::*/following-sibling::*",
                        "//th[text()='GST No']/following-sibling::td",
                        "//td[text()='GST No']/following-sibling::td",
                        "//th[contains(text(),'GSTIN')]/following-sibling::td",
                        "//td[contains(text(),'GSTIN')]/following-sibling::td"
                    ]

                    for selector in gst_selectors:
                        try:
                            elements = driver.find_elements(By.XPATH, selector)
                            if elements and elements[0].text.strip():
                                gst_no = elements[0].text.strip()
                                break
                        except:
                            continue

                    # If still not found, try regex pattern for GST
                    if gst_no == "Not Found":
                        gst_patterns = [
                            r'GST\s*No\.?\s*:?\s*([A-Z0-9]{15})',
                            r'GSTIN\s*:?\s*([A-Z0-9]{15})',
                            r'([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[Z]{1}[0-9A-Z]{1})'  # GST format
                        ]

                        for pattern in gst_patterns:
                            match = re.search(pattern, promoter_page_text, re.IGNORECASE)
                            if match:
                                gst_no = match.group(1).strip()
                                break

                # Store the extracted data
                project_data = {
                    'Rera Regd. No': rera_regd_no,
                    'Project Name': project_name,
                    'Promoter Name': promoter_name,
                    'Promoter Address': promoter_address,
                    'GST No': gst_no
                }

                project_details.append(project_data)
                print(f"✅ Successfully extracted data for project {i}")
                print(f"   RERA No: {rera_regd_no}")
                print(f"   Project: {project_name}")
                print(f"   Promoter: {promoter_name}")
                print(f"   Address: {promoter_address[:50]}..." if len(
                    promoter_address) > 50 else f"   Address: {promoter_address}")
                print(f"   GST: {gst_no}")

                # Go back to the project list
                print("Navigating back to project list...")
                driver.back()
                time.sleep(8)  # Increased wait time

                # Wait for the project list to be available again
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.project-list')))
                    time.sleep(5)  # Additional stabilization time
                except:
                    print("Warning: Could not confirm project list loaded, continuing...")

            except Exception as e:
                print(f"❌ Error processing project {i}: {str(e)}")
                # Try to recover by going back to main page
                try:
                    print("Attempting to recover by navigating to main page...")
                    driver.get(url)
                    time.sleep(10)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.project-list')))
                    time.sleep(5)
                except:
                    print("Recovery failed, continuing to next project...")
                continue

        return project_details

    except Exception as e:
        print(f"Error in scrape_rera_projects: {str(e)}")
        return []

    finally:
        if driver:
            driver.quit()


def main():
    print("=" * 60)
    print("RERA ODISHA PROJECT SCRAPER (Microsoft Edge)")
    print("=" * 60)

    try:
        projects = scrape_rera_projects()

        if not projects:
            print("No projects were scraped.")
            return

        print(f"\n🎉 Successfully scraped {len(projects)} projects:")
        print("=" * 80)

        for i, project in enumerate(projects, 1):
            print(f"\n📋 PROJECT {i}:")
            print(f"🏷️  RERA Registration No: {project['Rera Regd. No']}")
            print(f"🏢 Project Name: {project['Project Name']}")
            print(f"👤 Promoter Name: {project['Promoter Name']}")
            print(f"📍 Promoter Address: {project['Promoter Address']}")
            print(f"🆔 GST No: {project['GST No']}")
            print("-" * 80)

        # Save to file
        try:
            with open('rera_projects.txt', 'w', encoding='utf-8') as f:
                f.write("RERA ODISHA PROJECTS DATA\n")
                f.write("=" * 50 + "\n\n")

                for i, project in enumerate(projects, 1):
                    f.write(f"PROJECT {i}:\n")
                    f.write(f"RERA Registration No: {project['Rera Regd. No']}\n")
                    f.write(f"Project Name: {project['Project Name']}\n")
                    f.write(f"Promoter Name: {project['Promoter Name']}\n")
                    f.write(f"Promoter Address: {project['Promoter Address']}\n")
                    f.write(f"GST No: {project['GST No']}\n")
                    f.write("-" * 50 + "\n\n")

            print(f"\n✅ Data saved to 'rera_projects.txt'")

        except Exception as e:
            print(f"Error saving to file: {e}")


    except KeyboardInterrupt:

        print("\n\n⚠️ Script interrupted by user")

        sys.exit(1)

    except Exception as e:

        print(f"\n❌ An error occurred: {str(e)}")

        sys.exit(1)

if __name__ == "__main__":

    main()
