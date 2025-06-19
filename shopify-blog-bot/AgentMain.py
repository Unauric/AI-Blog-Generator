import os
import requests
import openai
from dotenv import load_dotenv
from AIPromptGenerator import get_prompt
import time
import re
import sys

# Load env
load_dotenv()

# Config

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_API_TOKEN = os.getenv("SHOPIFY_API_TOKEN")
SHOPIFY_PASSWORD = os.getenv("SHOPIFY_PASSWORD")
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE")

# 🔒 Sanity check for required env vars
missing_env = [var for var in ["OPENAI_API_KEY", "SHOPIFY_PASSWORD", "SHOPIFY_STORE"] if not os.getenv(var)]
if missing_env:
    print(f"❌ Missing required environment variables: {', '.join(missing_env)}")
    sys.exit(1)

# OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Example keywords (not yet used)
KEYWORDS = ["linen shirts", "summer outfits", "2025 fashion"]


def generate_blog():
    print("⏳ Generating blog with OpenAI...")
    response = client.chat.completions.create(
        model="gpt-4o",  # or gpt-3.5-turbo
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that writes high-quality SEO-friendly blogs for a wine shop.",
            },
            {
                "role": "user",
                "content": "Write a blog post about 'Best red wines for summer under $50'.",
            },
        ],
        temperature=0.7,
    )
    blog_content = response.choices[0].message.content
    print("✅ Blog content generated.")
    return blog_content


def extract_title(content):
    print("🔍 Extracting blog title...")
    match = re.search(r"<h2>(.*?)</h2>", content)
    title = match.group(1).strip() if match else "Weekly Blog"
    print("📌 Extracted title:", title)
    return title


def get_blog_id():
    url = f"https://{SHOPIFY_STORE}/admin/api/2025-04/blogs.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_PASSWORD,
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
    url = f"https://madeforwine.shop/admin/api/2025-04/blogs/{blog_id}/articles.json"

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

    try:
        print(f"🚀 Sending POST to: {url}")
        print(f"Payload:\n{json.dumps(payload, indent=2)[:1000]}...")  # Limit long content

        resp = requests.post(url, headers=headers, json=payload)
        print("Shopify response status:", resp.status_code)

        try:
            resp_data = resp.json()
            print("Shopify JSON response:", json.dumps(resp_data, indent=2)[:1000])
        except Exception:
            print("❌ Failed to decode JSON from response:", resp.text)
            raise

        if 'article' not in resp_data:
            print("❌ No 'article' key in response. Likely creation failed silently.")
            raise Exception("Blog post not created.")

        article = resp_data['article']
        print(f"✅ Blog post created with ID: {article['id']}, Title: {article['title']}")

    except requests.exceptions.RequestException as e:
        print("❌ RequestException:", e)
        raise


def run():
    print("⚙️ Starting automated blog post run...\n")
    content = generate_blog()
    title = extract_title(content)
    blog_id = get_blog_id()
    post_blog_to_shopify(title, content, blog_id)

    print("\n📝 Summary:")
    print(" - Title:", title)
    print(" - Blog ID:", blog_id)
    print(" - Content Preview:\n", content[:300], "...\n")
    print("✅ Done.")

    time.sleep(60)  # ⏱️ Corrected: Wait 60 seconds (not 360000)


if __name__ == "__main__":
    run()
