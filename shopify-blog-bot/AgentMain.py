import os
import requests
import openai
from dotenv import load_dotenv
from AIPromptGenerator import get_prompt
import time
import re
import sys
import json

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
   ## print("⏳ Generating blog with OpenAI...")
   ## response = client.chat.completions.create(
   ##     model="gpt-4o",
   ##     messages=[
   ##         {
   ##            "role": "system",
   ##             "content": "You are a helpful assistant that writes high-quality SEO-friendly blogs for a wine shop.",
   ##         },
   ##         {
   ##             "role": "user",
   ##            "content": "Write a blog post about 'Best red wines for summer under $50'.",
   ##         },
   ##     ],
   ##     temperature=0.7,
   ## )
   ## content = response.choices[0].message.content
   ## print("✅ Blog content generated.")
    
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
    ##print("🔍 Extracting blog title...")
    ##match = re.search(r"<h2>(.*?)</h2>", content)
    ##if match:
    ##    title = match.group(1).strip()
    ##else:
        # Try fallback: first markdown or plain line
    ##    first_line = content.strip().splitlines()[0]
    ##    title = re.sub(r'[*#<>]', '', first_line).strip()
    ##    if not title:
    ##        title = "Weekly Blog"
    ## print("📌 Extracted title:", title)
    return "dummy tittle"

def get_blog_id():
    url = f"https://{SHOPIFY_STORE}/admin/api/2025-04/blogs.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_API_TOKEN,
        "Content-Type": "application/json",
    }

    print("🌐 Fetching blog list from Shopify...")
    resp = requests.get(url, headers=headers)
    print("Status:", resp.status_code)
    print("Response:", resp.text)
    resp.raise_for_status()

    blogs = resp.json().get("blogs", [])
    for blog in blogs:
        print(f" - id: {blog['id']}, handle: {blog['handle']}")
    for blog in blogs:
        if blog["handle"] == "news":
            print(f"✅ Found blog 'news' with id: {blog['id']}")
            return blog["id"]
    raise Exception("❌ Blog with handle 'news' not found.")

def post_blog_to_shopify(title, body_html, blog_id):

 url = f"https://{SHOPIFY_STORE}/admin/api/2025-04/blogs/{blog_id}/articles"

 payload = {
    "article": {
        "title": title,
        "body_html": body_html,
        "published": True
    }
 }

 headers = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": SHOPIFY_API_TOKEN
 }

# Disable redirect to detect 302 fallback
 resp = requests.post(url, headers=headers, json=payload, allow_redirects=False)

 print("Status:", resp.status_code)
 print("Headers:", resp.headers)
 print("Body:", resp.text)

 try:
    data = resp.json()
    article = data.get("article")
     if not article:
        raise Exception("❌ Article missing in response.")
    print("✅ Created article:", article["title"])
except Exception as e:
    print("❌ Failed to create article:", str(e))


def run():
    print("⚙️ Starting automated blog post run...\n")
    content = generate_blog()
    title = extract_title(content)
    blog_id = get_blog_id()
    post_blog_to_shopify(title, content, blog_id)

    print("\n📝 Summary:")
    print(" - Title:", title)
    print(" - Blog ID:", blog_id)
    print(" - Preview:\n", content[:300], "...\n")
    print("✅ Done.")

    time.sleep(60)

if __name__ == "__main__":
    run()
