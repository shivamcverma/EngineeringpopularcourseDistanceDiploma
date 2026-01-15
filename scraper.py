from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
import re
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

PCOMBA_O_URL="https://www.shiksha.com/engineering/colleges/distance-correspondence-diploma-courses-india"

def create_driver():
    options = Options()

    # Mandatory for GitHub Actions
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # Optional but good
    options.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # Important for Ubuntu runner
    options.binary_location = "/usr/bin/chromium"

    service = Service(ChromeDriverManager().install())

    return webdriver.Chrome(
        service=service,
        options=options
    )

# ---------------- UTILITIES ----------------
def scroll_to_bottom(driver, scroll_times=3, pause=1.5):
    for _ in range(scroll_times):
        driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
        time.sleep(pause)


def extract_course_data(driver):
    driver.get(PCOMBA_O_URL)
    time.sleep(5)
    wait = WebDriverWait(driver, 15)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    data = {}

    main = soup.find("div", id="EdContent_categoryPage")
    if not main:
        return data

    # --------------------------------
    # Views / Count
    # --------------------------------
    views = main.find("span", class_="_2b4b")
    data["views"] = views.get_text(strip=True) if views else None

    # --------------------------------
    # Title
    # --------------------------------
    h1 = main.find("h1")
    data["title"] = h1.get_text(strip=True) if h1 else None

    # --------------------------------
    # Intro Paragraph
    # --------------------------------
    intro_p = main.find("p")
    data["intro"] = intro_p.get_text(" ", strip=True) if intro_p else None

    # --------------------------------
    # Table of Contents
    # --------------------------------
    toc = []
    toc_block = main.find("ol", class_="newTocList")
    if toc_block:
        for li in toc_block.find_all("li"):
            a = li.find("a")
            if a:
                toc.append({
                    "text": a.get_text(strip=True),
                    
                })

    data["table_of_contents"] = toc

    # --------------------------------
    # Sections (h2 based)
    # --------------------------------
    sections = []

    for h2 in main.find_all("h2"):
        section = {
        
            "heading": h2.get_text(strip=True),
            "content": []
        }

        for sibling in h2.find_next_siblings():
            if sibling.name == "h2":
                break

            # Paragraph
            if sibling.name == "p":
                section["content"].append({
                    
                    "text": sibling.get_text(" ", strip=True)
                })

            # List
            elif sibling.name == "ul":
                items = [li.get_text(" ", strip=True) for li in sibling.find_all("li")]
                section["content"].append({
                
                    "items": items
                })

            # Table
            elif sibling.name == "table":
                table_data = []
                rows = sibling.find_all("tr")

                headers = [th.get_text(strip=True) for th in rows[0].find_all("th")]

                for row in rows[1:]:
                    cols = row.find_all("td")
                    if len(cols) == len(headers):
                        row_data = {
                            headers[i]: cols[i].get_text(" ", strip=True)
                            for i in range(len(headers))
                        }
                        table_data.append(row_data)

                section["content"].append({
                   
                    "data": table_data
                })

        sections.append(section)

    data["sections"] = sections

    # --------------------------------
    # Author Info
    # --------------------------------
    author_block = main.find("div", class_="_78c3")
    if author_block:
        author_name = author_block.find("a", class_="_9b27")
        author_img = author_block.find("img")
        updated = author_block.find("p", class_="_9ad6")

        data["author"] = {
            "name": author_name.get_text(strip=True) if author_name else None,
            "profile": author_name.get("href") if author_name else None,
            "image": author_img.get("src") if author_img else None,
            "updated_on": updated.get_text(strip=True) if updated else None
        }

    return data


def scrape_mba_colleges():
    driver = create_driver()

      

    try:
       data = {
              "Distance_Diploma":{
                   "overviews":extract_course_data(driver),
                   }
                }

    finally:
        driver.quit()
    
    return data



import os

TEMP_FILE = "popular_mba_data.tmp.json"
FINAL_FILE = "popular_mba_data.json"
UPDATE_INTERVAL = 6 * 60 * 60  # 6 hours

def auto_update_scraper():
    # Check last modified time
    # if os.path.exists(DATA_FILE):
    #     last_mod = os.path.getmtime(DATA_FILE)
    #     if time.time() - last_mod < UPDATE_INTERVAL:
    #         print("⏱️ Data is recent, no need to scrape")
    #         return

    print("🔄 Scraping started")
    data = scrape_mba_colleges()
    with open(TEMP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Atomic swap → replaces old file with new one safely
    os.replace(TEMP_FILE, FINAL_FILE)

    print("✅ Data scraped & saved successfully (atomic write)")

if __name__ == "__main__":

    auto_update_scraper()

