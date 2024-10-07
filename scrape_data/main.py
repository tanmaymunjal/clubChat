from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import json

BEARSDEN_WEBSITE = "https://alberta.campuslabs.ca/engage/organizations"

chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

driver.get(BEARSDEN_WEBSITE)


# Function to extract organization details
def extract_org_details(html):
    soup = BeautifulSoup(html, "html.parser")
    org_cards = soup.find_all("a", href=True)
    organizations = []
    for card in org_cards:
        org = {}
        img_tag = card.find("img")
        org["name"] = img_tag["alt"].strip() if img_tag else "Name not found"
        org["description"] = card.find("p", class_="DescriptionExcerpt").text.strip()
        org["link"] = "https://alberta.campuslabs.ca" + card["href"]
        org["image_url"] = img_tag["src"] if img_tag else "Image not found"
        organizations.append(org)
    return organizations


# Function to click "Load More" button and wait for new content
def load_more():
    try:
        load_more_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[.//span[contains(text(), 'Load More')]]")
            )
        )
        driver.execute_script("arguments[0].scrollIntoView();", load_more_button)
        load_more_button.click()
        time.sleep(2)  # Wait for new content to load
        return True
    except Exception as e:
        print(f"Error clicking 'Load More' button: {e}")
        return False


# Initial load
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "org-search-results"))
)
time.sleep(2)

all_organizations = []
load_count = 0
max_loads = 100  # Set a maximum number of loads to prevent infinite loops

while load_count < max_loads:
    print(f"Loading content... (Load {load_count + 1})")

    # Extract current page's organizations
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    org_search_results = soup.find("div", id="org-search-results")

    if org_search_results:
        new_orgs = extract_org_details(str(org_search_results))
        new_org_count = len(new_orgs) - len(all_organizations)
        all_organizations = new_orgs  # Update with all organizations seen so far
        print(f"Found {new_org_count} new organizations.")
    else:
        print("No organizations found.")
        break

    # Try to load more
    if not load_more():
        print("No more content to load.")
        break

    load_count += 1

# Save the extracted data to a JSON file
with open("all_organizations.json", "w", encoding="utf-8") as f:
    json.dump(all_organizations, f, ensure_ascii=False, indent=4)

print(
    f"Extracted details of {len(all_organizations)} organizations in total and saved to all_organizations.json"
)

driver.quit()
