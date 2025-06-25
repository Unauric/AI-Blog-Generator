import os
import requests
import urllib.request
import urllib.parse
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
WORDPRESS_USERNAME = os.getenv("WORDPRESS_USERNAME")
WORDPRESS_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD")

missing_env = [var for var in ["OPENAI_API_KEY", "WORDPRESS_URL", "WORDPRESS_USERNAME", "WORDPRESS_APP_PASSWORD"] if not os.getenv(var)]
if missing_env:
    print(f"❌ Missing required environment variables: {', '.join(missing_env)}")
    sys.exit(1)

# OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def generate_blog():
    print("⏳ Generating blog with OpenAI...")
   # response = client.chat.completions.create(
   #     model="gpt-4o",
   #     messages=[
   #         {
   #             "role": "system",
   #             "content": "You are a helpful assistant that writes high-quality SEO-friendly blogs for a wine shop.",
   #         },
   #         {
   #             "role": "user",
   #             "content": "Write a blog post about 'Best red wines for summer under $50'.",
   #         },
   #     ],
   #     temperature=0.7,
   # )
   # content = response.choices[0].message.content
   # print("✅ Blog content generated.")
    return "aa"

def extract_title(content):
   # print("🔍 Extracting blog title...")
    # Try to find H1 or H2 tags
   # match = re.search(r"<h[12]>(.*?)</h[12]>", content, re.IGNORECASE)
   # if match:
   #     title = match.group(1).strip()
   # else:
        # Try markdown headers
   #     match = re.search(r"^#+\s*(.*)", content, re.MULTILINE)
   #     if match:
   #         title = match.group(1).strip()
   #     else:
   #         # Fallback: first line
   #         first_line = content.strip().splitlines()[0]
   #         title = re.sub(r'[*#<>]', '', first_line).strip()
   #         if not title:
   #             title = "Weekly Blog"
   # 
   # print("📌 Extracted title:", title)
    return "dummy title"

def check_wordpress_connection():
    """Test WordPress API connection"""
    print("🔍 Testing WordPress API connection...")
    
    url = f"{WORDPRESS_URL}/wp-json/wp/v2/posts"
    credentials = base64.b64encode(f"{WORDPRESS_USERNAME}:{WORDPRESS_APP_PASSWORD}".encode()).decode()
    
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json"
    }
    
    try:
        # Just get the first post to test connection
        resp = requests.get(f"{url}?per_page=1", headers=headers)
        if resp.status_code == 200:
            print("✅ WordPress API connection successful")
            return True
        else:
            print(f"❌ WordPress API connection failed: {resp.status_code}")
            print(f"Response: {resp.text}")
            return False
    except Exception as e:
        print(f"❌ WordPress connection error: {e}")
        return False

def post_to_wordpress(title, content, status="publish"):
    """Post content to WordPress"""
    print("🚀 Posting to WordPress...")
    
    url = f"{WORDPRESS_URL}/wp-json/wp/v2/posts"
    credentials = base64.b64encode(f"{WORDPRESS_USERNAME}:{WORDPRESS_APP_PASSWORD}".encode()).decode()
    
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json"
    }
    
    # Clean up content for WordPress
    # Remove any existing HTML structure tags if they exist
    clean_content = content
    if not clean_content.startswith('<'):
        # If content is markdown or plain text, convert line breaks to <p> tags
        paragraphs = clean_content.split('\n\n')
        clean_content = ''.join([f'<p>{p.strip()}</p>' for p in paragraphs if p.strip()])
    
    payload = {
        "title": title,
        "content": clean_content,
        "status": status,  # "publish", "draft", or "private"
        "author": 1,  # Usually 1 for admin, adjust if needed
        "categories": [],  # Add category IDs if you want
        "tags": []  # Add tag IDs if you want
    }
    
    print(f"📝 Title: {title}")
    print(f"📄 Content preview: {clean_content[:200]}...")
    
    try:
        resp = requests.post(url, headers=headers, json=payload)
        
        if resp.status_code == 201:
            post_data = resp.json()
            print(f"✅ Post created successfully!")
            print(f"📌 Post ID: {post_data['id']}")
            print(f"🔗 Post URL: {post_data['link']}")
            return post_data
        else:
            print(f"❌ Failed to create post: {resp.status_code}")
            print(f"Response: {resp.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error posting to WordPress: {e}")
        return None

def get_wordpress_categories():
    """Get available categories from WordPress"""
    print("📂 Fetching WordPress categories...")
    
    url = f"{WORDPRESS_URL}/wp-json/wp/v2/categories"
    credentials = base64.b64encode(f"{WORDPRESS_USERNAME}:{WORDPRESS_APP_PASSWORD}".encode()).decode()
    
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json"
    }
    
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            categories = resp.json()
            print("Available categories:")
            for cat in categories:
                print(f"  - {cat['name']} (ID: {cat['id']})")
            return categories
        else:
            print(f"❌ Failed to fetch categories: {resp.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error fetching categories: {e}")
        return []

def create_wordpress_category(name, description=""):
    """Create a new category in WordPress"""
    print(f"📂 Creating category: {name}")
    
    url = f"{WORDPRESS_URL}/wp-json/wp/v2/categories"
    credentials = base64.b64encode(f"{WORDPRESS_USERNAME}:{WORDPRESS_APP_PASSWORD}".encode()).decode()
    
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": name,
        "description": description
    }
    
    try:
        resp = requests.post(url, headers=headers, json=payload)
        if resp.status_code == 201:
            category = resp.json()
            print(f"✅ Category created: {category['name']} (ID: {category['id']})")
            return category
        else:
            print(f"❌ Failed to create category: {resp.status_code}")
            print(f"Response: {resp.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating category: {e}")
        return None

def run():
    print("⚙️ Starting WordPress auto-blogger...\n")
    
    # Step 1: Test WordPress connection
    if not check_wordpress_connection():
        print("❌ WordPress connection failed. Please check your credentials.")
        return False
    
    # Step 2: Generate content
    try:
        content = generate_blog()
        title = extract_title(content)
    except Exception as e:
        print(f"❌ Error generating content: {e}")
        return False
    
    # Step 3: Post to WordPress
    try:
        post_data = post_to_wordpress(title, content, status="publish")
        if post_data:
            print("\n✅ Blog post successfully published!")
            print(f"🔗 View at: {post_data['link']}")
            return True
        else:
            print("❌ Failed to publish post")
            return False
    except Exception as e:
        print(f"❌ Error during posting: {e}")
        return False

def run_batch(topics_list):
    """Run multiple blog posts from a list of topics"""
    print(f"🚀 Starting batch run for {len(topics_list)} topics...")
    
    if not check_wordpress_connection():
        print("❌ WordPress connection failed. Exiting batch run.")
        return
    
    success_count = 0
    for i, topic in enumerate(topics_list, 1):
        print(f"\n{'='*50}")
        print(f"📝 Processing {i}/{len(topics_list)}: {topic}")
        print('='*50)
        
        try:
            # Generate content for this topic
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that writes high-quality SEO-friendly blogs for a wine shop. Write engaging, informative content with proper HTML formatting.",
                    },
                    {
                        "role": "user",
                        "content": f"Write a comprehensive blog post about '{topic}'. Include proper headings, paragraphs, and make it SEO-friendly.",
                    },
                ],
                temperature=0.7,
            )
            
            content = response.choices[0].message.content
            title = extract_title(content) or topic
            
            # Post to WordPress
            post_data = post_to_wordpress(title, content, status="publish")
            
            if post_data:
                print(f"✅ Success! Published: {title}")
                success_count += 1
            else:
                print(f"❌ Failed to publish: {title}")
            
            # Add delay between posts to avoid rate limiting
            if i < len(topics_list):
                print("⏳ Waiting 10 seconds before next post...")
                time.sleep(10)
                
        except Exception as e:
            print(f"❌ Error processing '{topic}': {e}")
            continue
    
    print(f"\n🎉 Batch complete! Successfully published {success_count}/{len(topics_list)} posts")

if __name__ == "__main__":
    # Single post example
    # run()
    
    # Batch example - uncomment to use
    topics = [
        "Best red wines for summer under $50",
        "Wine pairing guide for grilled foods",
        "How to properly store wine at home",
        "Beginner's guide to wine tasting",
        "Top 10 wine regions every enthusiast should know"
    ]
    run_batch(topics)
