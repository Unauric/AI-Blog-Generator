import os
import requests
import openai
from dotenv import load_dotenv
from AIPromptGenerator import get_prompt
import time

load_dotenv()

# Config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_PASSWORD = os.getenv("SHOPIFY_PASSWORD")
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE")

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Example keywords
KEYWORDS = ["linen shirts", "summer outfits", "2025 fashion"]


def generate_blog():
    print("⏳ Generating blog...")

    response = client.chat.completions.create(
        model="gpt-4o",  # or gpt-3.5-turbo
        messages=[
            {"role": "system", "content": "You are a helpful assistant that writes high-quality SEO-friendly blogs for a wine shop."},
            {"role": "user", "content": "Write a blog post about 'Best red wines for summer under $50'."}
        ],
        temperature=0.7
    )

    blog_content = response.choices[0].message.content
    return blog_content


def get_blog_id():
    url = f"https://{SHOPIFY_STORE}/admin/api/2024-01/blogs.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_PASSWORD,
        "Content-Type": "application/json"
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    blogs = resp.json().get("blogs", [])
    print("Available blogs and handles:")
    for blog in blogs:
        print(f" - id: {blog['id']}, handle: {blog['handle']}")

    for blog in blogs:
        if blog["handle"] == "news":
            print(f"Found blog 'news' with id: {blog['id']}")
            return blog["id"]

    raise Exception("❌ Blog with handle 'news' not found.")


def post_blog_to_shopify(title, content, blog_id):
    url = f"https://{SHOPIFY_STORE}/admin/api/2024-01/blogs/{blog_id}/articles.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_PASSWORD,
        "Content-Type": "application/json"
    }
    payload = {
        "article": {
            "title": title,
            "body_html": content,
            "published": True  # Auto-publish
        }
    }

    resp = requests.post(url, headers=headers, json=payload)
    print("Shopify response status:", resp.status_code)
    print("Shopify response body:", resp.text)
    resp.raise_for_status()
    print("✅ Blog posted:", title)



def extract_title(content):
    import re
    match = re.search(r"<h2>(.*?)</h2>", content)
    return match.group(1) if match else "Weekly Blog"

def run():
    print("⏳ Generating blog...")
    content = generate_blog()
    title = extract_title(content)
    blog_id = get_blog_id()
    post_blog_to_shopify(title, content, blog_id)
    print("Using blog ID:", blog_id)
    print("Generated blog content:\n", content)
    print("Extracted title:", title)
    time.sleep(60)  # wait for 60 seconds



if __name__ == "__main__":
    run()
