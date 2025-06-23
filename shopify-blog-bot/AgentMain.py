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
    return "Best Red Wines for Summer Under $50"

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
    url = f"https://{SHOPIFY_STORE}/admin/api/2025-04/blogs/{blog_id}/articles.json"

    payload = {
        "article": {
            "title": title,
            "body_html": body_html,
            "published": True,
            "author": "Wine Expert",  # Optional: add author
            "tags": "wine, summer, red wine"  # Optional: add tags
        }
    }

    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": SHOPIFY_API_TOKEN
    }

    print(f"🚀 Sending POST to: {url}")
    print(f"Payload:\n{json.dumps(payload, indent=2)}")

    resp = requests.post(url, headers=headers, json=payload)
    print("Shopify response status:", resp.status_code)
    print("Response headers:", dict(resp.headers))

    try:
        resp_data = resp.json()
        print("Shopify JSON response:", json.dumps(resp_data, indent=2))
    except Exception as e:
        print(f"❌ Failed to decode JSON from Shopify: {e}")
        print("Raw response:", resp.text)
        raise Exception("❌ Failed to decode JSON from Shopify.")

    # Check if we have a successful response
    if resp.status_code not in [200, 201]:
        print(f"❌ Unexpected status code: {resp.status_code}")
        raise Exception(f"❌ Shopify API returned status {resp.status_code}")

    # Check for the created article in the response
    article = resp_data.get("article")
    if article:
        # Single article was created (expected response)
        print(f"✅ Blog post created with ID: {article['id']}, Title: {article['title']}")
        return article
    
    # Check if response contains articles array (unexpected but handle it)
    articles = resp_data.get("articles")
    if articles:
        print("⚠️ Received articles array instead of single article")
        # Try to find our article by title
        for article in articles:
            if article.get("title", "").strip().lower() == title.strip().lower():
                print(f"✅ Found matching article with ID: {article['id']}")
                return article
        
        print("❌ Could not find newly created article in response")
        raise Exception("❌ Article creation unclear - check Shopify admin panel")
    
    # If we get here, the response structure is unexpected
    print("❌ Unexpected response structure from Shopify")
    raise Exception("❌ Blog post creation response invalid.")

def run():
    print("⚙️ Starting automated blog post run...\n")
    content = generate_blog()
    title = extract_title(content)
    blog_id = get_blog_id()
    
    try:
        article = post_blog_to_shopify(title, content, blog_id)
        
        print("\n📝 Summary:")
        print(" - Title:", title)
        print(" - Blog ID:", blog_id)
        print(" - Article ID:", article.get('id'))
        print(" - Preview:\n", content[:300], "...\n")
        print("✅ Done.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Check your Shopify admin panel to see if the article was created.")
        return False

    time.sleep(60)
    return True

if __name__ == "__main__":
    run()
