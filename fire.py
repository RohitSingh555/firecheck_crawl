from groq import Groq
import requests
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urljoin

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

GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)
visited_urls = set()

def clean_url(url):
    url = url.strip()
    if not re.match(r'^https?://', url): 
        url = 'http://' + url
    return url

def fetch_website_content(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(url, headers=headers)
        response.raise_for_status() 
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
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

def extract_links(content, base_url):
    soup = BeautifulSoup(content, "html.parser")
    links = soup.find_all('a', href=True)
    full_links = []
    for link in links:
        href = link['href']
        full_url = urljoin(base_url, href)
        if is_valid_url(full_url):
            full_links.append(full_url)
    return full_links

def is_valid_url(url):
    """Check if the URL is valid and not revisited, and relevant to news."""
    if url in visited_urls or not url.startswith(('http', 'https')):
        return False

    news_keywords = ["news", "article", "story", "press", "coverage"]
    return any(keyword in url.lower() for keyword in news_keywords)

def extract_fire_related_news(content, date):
    """Extract fire-related news articles using Groq API (Simulated via OpenAI)."""
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

def crawl(url, max_depth=3, current_depth=0):
    """Crawl a website starting from the given URL."""
    if current_depth > max_depth or url in visited_urls:
        return {}

    visited_urls.add(url)
    print(f"Crawling: {url}")

    content = fetch_website_content(url)
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

    links = extract_links(content, url)
    for link in links:
        fire_related_news.extend(crawl(link, max_depth, current_depth + 1))

    return {url: fire_related_news} 

def save_results_to_json(data, filename="fire_related_news.json"):
    """Save the collected fire-related news to a valid JSON file."""
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
            fire_related_news = crawl(url, max_depth=2) 
            all_fire_related_news.update(fire_related_news)

        save_results_to_json(all_fire_related_news)
