import requests
import html2text
import json
from bs4 import BeautifulSoup
from groq import Groq
from urllib.parse import urljoin

GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

def fetch_html(url):
    try:
        response = requests.get(url)
        response.raise_for_status() 
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching HTML from {url}: {e}")
        return None

def convert_html_to_markdown(html_content):
    try:
        markdown = html2text.HTML2Text()
        markdown.ignore_links = False 
        return markdown.handle(html_content)
    except Exception as e:
        print(f"Error converting HTML to Markdown: {e}")
        return None

def extract_fire_related_news(content, date):
    """Extract fire-related news articles using Groq API."""
    try:
        chat_completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{
                "role": "user",
                "content": f"Identify fire-related news articles from this content for {date}. Provide the links and concise summaries for fire-related events only. Skip unrelated mentions of fire.",
            }]
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Error with Groq API: {e}")
        return None

def crawl_page(url):
    html_content = fetch_html(url)
    if html_content:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        links = soup.find_all('a', href=True)
        
        article_links = [urljoin(url, link['href']) for link in links if '/news' in link['href']]
        
        return article_links
    return []

def main():
    try:
        with open("websites.txt", "r") as file:
            urls = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print("Error: 'websites.txt' not found.")
        return

    fire_incidents = {}

    date_of_interest = "2024-11-21"

    for url in urls:
        print(f"Processing URL: {url}")
        
        article_links = crawl_page(url)
        if not article_links:
            print(f"No articles found on {url}")
            continue
        
        for article_url in article_links:
            print(f"Processing article: {article_url}")
            
            article_html_content = fetch_html(article_url)
            if not article_html_content:
                continue

            markdown_text = convert_html_to_markdown(article_html_content)
            if not markdown_text:
                continue

            fire_related_news = extract_fire_related_news(markdown_text, date_of_interest)

            if fire_related_news:
                if url not in fire_incidents:
                    fire_incidents[url] = []
                fire_incidents[url].append({
                    "url": article_url,
                    "fire_incidents": fire_related_news.strip()
                })

    try:
        with open("fire_incidents_office.json", "w") as json_file:
            json.dump(fire_incidents, json_file, indent=4)
        print("Fire-related incidents saved to 'fire_incidents.json'.")
    except Exception as e:
        print(f"Error saving JSON file: {e}")

if __name__ == "__main__":
    main()
