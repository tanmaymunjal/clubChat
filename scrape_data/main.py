from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
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

# Wait for JavaScript to load (adjust the time as needed)
time.sleep(5)

html = driver.page_source

soup = BeautifulSoup(html, 'html.parser')

# Find the div with id "org-search-results"
org_search_results = soup.find('div', id='org-search-results')

if org_search_results:
    print("Found the div with id 'org-search-results'")
    
    # Extract organization details
    organizations = []
    org_cards = org_search_results.find_all('a', href=True)
    
    for card in org_cards:
        org = {}
        img_tag = card.find('img')
        org['name'] = img_tag['alt'].strip() if img_tag else "Name not found"
        org['description'] = card.find('p', class_="DescriptionExcerpt").text.strip()
        org['link'] = "https://alberta.campuslabs.ca" + card['href']
        org['image_url'] = card.find('img')['src']
        organizations.append(org)
        
    
    # Save the extracted data to a JSON file
    with open("organizations.json", "w", encoding="utf-8") as f:
        json.dump(organizations, f, ensure_ascii=False, indent=4)
    
    print(f"Extracted details of {len(organizations)} organizations and saved to organizations.json")
else:
    print("Div with id 'org-search-results' not found")

# You can still save the entire page if needed
with open("webpage.html", "w", encoding="utf-8") as file:
    file.write(soup.prettify())

driver.quit()