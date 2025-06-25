import os
import requests
import urllib.parse
import openai
from dotenv import load_dotenv
import re
import sys
import json
import time

# Load env
load_dotenv()

# Config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SHOPIFY_API_TOKEN = os.getenv("SHOPIFY_API_TOKEN")
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE")

# 🔒 Sanity check
missing_env = [var for var in ["OPENAI_API_KEY", "SHOPIFY_API_TOKEN", "SHOPIFY_STORE"] if not os.getenv(var)]
if missing_env:
    print(f"❌ Missing required environment variables: {', '.join(missing_env)}")
    sys.exit(1)

# OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def generate_blog():
    return """
    <h2>Best Red Wines for Summer Under $50</h2>
    <p>Looking for great red wines that pair well with sunshine? Here are 5 amazing picks under $50.</p>
    <ul>
        <li>Pinot Noir</li>
        <li>Gamay</li>
        <li>Zinfandel</li>
        <li>Grenache</li>
        <li>Barbera</li>
    </ul>
    """

def extract_title(content):
    match = re.search(r"<h2>(.*?)</h2>", content)
    if match:
        return match.group(1).strip()
    return "Weekly Blog"

def get_blog_id():
    url = f"https://{SHOPIFY_STORE}/admin/api/2024-10/blogs.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_API_TOKEN,
        "Content-Type": "application/json",
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    blogs = resp.json().get("blogs", [])
    for blog in blogs:
        if blog["handle"] == "news":
            return blog["id"]
    raise Exception("❌ Blog with handle 'news' not found.")

def get_latest_article(blog_id):
    url = f"https://{SHOPIFY_STORE}/admin/api/2024-10/blogs/{blog_id}/articles.json?limit=1&order=created_at+desc"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_API_TOKEN,
        "Content-Type": "application/json",
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    articles = resp.json().get("articles", [])
    if not articles:
        raise Exception("❌ No articles found to edit.")
    return articles[0]

def update_article(article_id, blog_id, title, content):
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2023-10/blogs/{blog_id}/articles/{article_id}.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": SHOPIFY_API_KEY
    }
    payload = {
        "article": {
            "title": title,
            "body_html": content
        }
    }

    response = requests.put(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        print("✅ Article updated successfully.")
    else:
        print(f"❌ Failed to update article. Status: {response.status_code}")
        print("Response:", response.text)
        raise Exception("❌ Update failed.")


def run():
    print("⚙️ Starting blog update script...")

    latest_article = get_latest_article()
    article_id = latest_article['id']
    blog_id = latest_article['blog_id']  # Needed for PUT request
    print(f"📝 Updating article ID {article_id}...")

    title, content = generate_blog_content()  # Assume this returns title and HTML body
    update_article(article_id, blog_id, title, content)


if __name__ == "__main__":
    run()
