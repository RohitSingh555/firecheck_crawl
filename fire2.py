from groq import Groq
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin

GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)

KEYWORDS = [
    "fire", "blaze", "wildfire", "arson", "inferno", "conflagration", "flames", "smoke",
    "burning", "ignition", "explosion", "firefighting", "extinguish", "embers", "scorched",
    "flammable", "hazard", "combustion", "sparks", "rescue", "evacuation", "firebreak",
    "controlled burn", "firestorm", "smoldering", "charred", "arsonist", "backdraft",
    "firetruck", "firefighter", "fire brigade", "fire department", "fire hazard",
    "incendiary", "fire alarm", "fire response", "fire suppression", "brushfire",
    "structure fire", "house fire", "apartment fire", "forest fire", "grassfire",
    "electrical fire", "chemical fire", "incident"
]

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
visited_urls = set()

def fetch_website_content_with_selenium(url):
    try:
        driver.get(url)
        time.sleep(3)
        
        if url == "https://www.azfamily.com/news/":
            search_icon = driver.find_element(By.CSS_SELECTOR, "queryly-nav-toggle pointer m-0 py-1 px-2")
            search_icon.click()
        else:
            search_icon = driver.find_element(By.CSS_SELECTOR, "queryly-nav-toggle pointer m-0 py-1 px-2")
            search_icon.click()
        
        time.sleep(2)
        search_input = driver.find_element(By.CSS_SELECTOR, "input.search-input-class")
        search_input.send_keys("fire")
        search_input.send_keys(Keys.RETURN)
        time.sleep(3)
        content = driver.page_source
        return content
    except Exception as e:
        print(f"Error with Selenium: {e}")
        return None

def extract_relevant_text(content):
    try:
        soup = BeautifulSoup(content, "html.parser")
        headlines = soup.find_all(["h1", "h2", "h3"], limit=10)
        paragraphs = soup.find_all("p", limit=50)
        text = "\n".join([h.get_text() for h in headlines]) + "\n" + \
               "\n".join([p.get_text() for p in paragraphs])
        return text.strip()
    except Exception as e:
        print(f"Error processing HTML content: {e}")
        return ""

def contains_fire_keywords(content):
    return any(keyword.lower() in content.lower() for keyword in KEYWORDS)

def extract_fire_related_news(content, date):
    try:
        chat_completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{
                "role": "user",
                "content": f"Identify fire-related news articles from this content for {date}. Provide the links and concise summaries for fire-related events only. Skip unrelated mentions of fire. That differentiate from these keywords: {KEYWORDS}\n\nContent:\n{content}",
            }]
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Error with Groq API: {e}")
        return None

def save_results_to_json(data, filename="fire_related_news.json"):
    try:
        try:
            with open(filename, "r") as file:
                existing_data = json.load(file)
        except FileNotFoundError:
            existing_data = {}
        except json.JSONDecodeError:
            existing_data = {}

        for url, incidents in data.items():
            if url not in existing_data:
                existing_data[url] = incidents
            else:
                existing_data[url].extend(incidents)

        with open(filename, "w") as file:
            json.dump(existing_data, file, indent=4)

    except Exception as e:
        print(f"Error saving results to JSON: {e}")

def crawl(url, visited_urls, max_depth=3, current_depth=0):
    if current_depth > max_depth or url in visited_urls:
        return {}

    visited_urls.add(url)
    print(f"Crawling: {url}")

    content = fetch_website_content_with_selenium(url)
    if not content:
        return {}

    relevant_content = extract_relevant_text(content)

    fire_related_news = []
    if contains_fire_keywords(relevant_content):
        date = "2024-11-21"
        filtered_content = extract_fire_related_news(relevant_content, date)

        if filtered_content:
            fire_related_news.append({
                "url": url,
                "fire_incidents": filtered_content
            })

        save_results_to_json({url: fire_related_news})

    return {url: fire_related_news}

if __name__ == "__main__":
    try:
        with open("websites.txt", "r") as file:
            seed_urls = [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        print("Error: The 'websites.txt' file was not found.")
        seed_urls = []

    if not seed_urls:
        print("No seed URLs found to crawl. Please provide valid URLs in 'websites.txt'.")
    else:
        all_fire_related_news = {}

        for url in seed_urls:
            fire_related_news = crawl(url, visited_urls, max_depth=2)
            all_fire_related_news.update(fire_related_news)

        save_results_to_json(all_fire_related_news)
