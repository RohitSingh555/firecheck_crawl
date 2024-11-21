import requests
import html2text
import json
from groq import Groq

GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

# Step 1: Fetch HTML content
def fetch_html(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching HTML from {url}: {e}")
        return None

# Step 2: Convert HTML to Markdown
def convert_html_to_markdown(html_content):
    try:
        markdown = html2text.HTML2Text()
        markdown.ignore_links = False  # Keep hyperlinks in the markdown
        return markdown.handle(html_content)
    except Exception as e:
        print(f"Error converting HTML to Markdown: {e}")
        return None

# Step 3: Extract fire-related news
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

# Main script logic
def main():
    # Read URLs from websites.txt
    try:
        with open("websites.txt", "r") as file:
            urls = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print("Error: 'websites.txt' not found.")
        return

    # Initialize the JSON output
    fire_incidents = {}

    # Process each URL
    for url in urls:
        print(f"Processing URL: {url}")
        
        # Fetch HTML
        html_content = fetch_html(url)
        if not html_content:
            continue

        # Convert to Markdown
        markdown_text = convert_html_to_markdown(html_content)
        if not markdown_text:
            continue

        # Extract fire-related news
        date_of_interest = "2024-11-21"  # Update to desired date
        fire_related_news = extract_fire_related_news(markdown_text, date_of_interest)

        # Store the response
        if fire_related_news:
            fire_incidents[url] = [{
                "url": url,
                "fire_incidents": fire_related_news.strip()
            }]

    # Save results to fire_incidents.json
    try:
        with open("fire_incidents.json", "w") as json_file:
            json.dump(fire_incidents, json_file, indent=4)
        print("Fire-related incidents saved to 'fire_incidents.json'.")
    except Exception as e:
        print(f"Error saving JSON file: {e}")

if __name__ == "__main__":
    main()
