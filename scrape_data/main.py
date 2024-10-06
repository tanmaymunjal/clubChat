from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

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
html = soup.prettify()

with open("webpage.html", "w", encoding="utf-8") as file:
    file.write(html)

driver.quit()