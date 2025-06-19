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


def post_blog_to_shopify(title, content, blog_id):
    url = f"https://{SHOPIFY_STORE}/admin/api/2025-04/blogs/{blog_id}/articles.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_PASSWORD,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "article": {
            "title": title,
            "body_html": content,
            "published": True,
        }
    }

    print("🚀 Sending POST request to Shopify to create article...")
    print("POST URL:", url)
    print("Payload:")
    print(payload)

    try:
        resp = requests.post(url, headers=headers, json=payload)
        print("Shopify response status:", resp.status_code)
        print("Shopify response body:", resp.text)
        resp.raise_for_status()
        print(f"✅ Blog titled '{title}' successfully posted.")
    except requests.exceptions.RequestException as e:
        print("❌ Failed to post blog to Shopify:", e)
        if resp is not None:
            print("Response body:", resp.text)
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
