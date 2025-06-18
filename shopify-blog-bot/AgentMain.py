import os
import requests
import openai
from dotenv import load_dotenv
from AIPromptGenerator import get_prompt

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
        model="gpt-3.5-turbo",  # or gpt-3.5-turbo
        messages=[
            {"role": "system", "content": "You are a helpful assistant that writes high-quality SEO-friendly blogs for a wine shop."},
            {"role": "user", "content": "Write a blog post about 'Best red wines for summer under $50'."}
        ],
        temperature=0.7
    )

    blog_content = response.choices[0].message.content
    return blog_content


def get_blog_id():
    url = f"https://{SHOPIFY_API_KEY}:{SHOPIFY_PASSWORD}@{SHOPIFY_STORE}/admin/api/2024-01/blogs.json"
    resp = requests.get(url)
    resp.raise_for_status()
    blogs = resp.json().get("blogs", [])

    for blog in blogs:
        if blog["handle"] == "news":
            return blog["id"]

    raise Exception("❌ Blog with handle 'news' not found.")



def post_blog_to_shopify(title, content, blog_id):
    url = f"https://{SHOPIFY_API_KEY}:{SHOPIFY_PASSWORD}@{SHOPIFY_STORE}/admin/api/2024-01/blogs/{blog_id}/articles.json"
    payload = {
        "article": {
            "title": title,
            "body_html": content,
            "published": True  # Auto-publish
        }
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    print("✅ Blog posted:", title)



def extract_title(content):
    import re
    match = re.search(r"<h2>(.*?)</h2>", content)
    return match.group(1) if match else "Weekly Blog"

##@tasks.loop(days = 1)
def run():
    print("⏳ Generating blog...")
    content = generate_blog()
    title = extract_title(content)
    blog_id = get_blog_id()
    post_blog_to_shopify(title, content, blog_id)


if __name__ == "__main__":
    run()
