import os
import requests
import openai
from dotenv import load_dotenv
from AIPromptGenerator import get_prompt
import time
import json

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
            {"role": "system", "content": "You are a helpful assistant that writes high-quality SEO-friendly blogs for a wine shop. Always start your blog with an <h1> title tag."},
            {"role": "user", "content": "Write a blog post about 'Best red wines for summer under $50'. Start with an <h1> title and format the content with proper HTML tags."}
        ],
        temperature=0.7
    )
    blog_content = response.choices[0].message.content
    return blog_content

def get_blog_id():
    url = f"https://{SHOPIFY_STORE}/admin/api/2025-04/blogs.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_PASSWORD,
        "Content-Type": "application/json"
    }
    
    print(f"🔍 Fetching blogs from: {url}")
    print(f"🔑 Using store: {SHOPIFY_STORE}")
    
    try:
        resp = requests.get(url, headers=headers)
        print(f"📡 Blog fetch response status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"❌ Error fetching blogs: {resp.text}")
            return None
            
        resp.raise_for_status()
        blogs = resp.json().get("blogs", [])
        
        print("📋 Available blogs and handles:")
        for blog in blogs:
            print(f" - id: {blog['id']}, handle: {blog['handle']}, title: {blog.get('title', 'N/A')}")
        
        # Try to find 'news' blog first, then fall back to the first available blog
        for blog in blogs:
            if blog["handle"] == "news":
                print(f"✅ Found blog 'news' with id: {blog['id']}")
                return blog["id"]
        
        # If no 'news' blog, use the first available blog
        if blogs:
            first_blog = blogs[0]
            print(f"📝 Using first available blog: '{first_blog['handle']}' with id: {first_blog['id']}")
            return first_blog["id"]
            
        raise Exception("❌ No blogs found in your Shopify store.")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error while fetching blogs: {e}")
        return None
    except Exception as e:
        print(f"❌ Error fetching blogs: {e}")
        return None

def post_blog_to_shopify(title, content, blog_id):
    url = f"https://{SHOPIFY_STORE}/admin/api/2025-04/blogs/{blog_id}/articles.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_PASSWORD,
        "Content-Type": "application/json"
    }
    
    payload = {
        "article": {
            "title": title,
            "body_html": content,
            "published": True,  # Auto-publish
            "author": "AI Blog Generator"  # Optional: add author
        }
    }
    
    print(f"📤 Posting to URL: {url}")
    print(f"📝 Article title: {title}")
    print(f"📄 Content length: {len(content)} characters")
    print(f"🔧 Request method: POST")
    print(f"🔧 Headers: {headers}")
    print(f"🔧 Payload preview: {json.dumps({**payload, 'article': {**payload['article'], 'body_html': payload['article']['body_html'][:100] + '...'}}, indent=2)}")
    
    try:
        resp = requests.post(url, headers=headers, json=payload)
        print(f"📡 Shopify response status: {resp.status_code}")
        
        if resp.status_code in [200, 201]:
            response_data = resp.json()
            
            # Check if we got a single article (201 response) or articles array (200 response)
            if 'article' in response_data:
                article_id = response_data.get('article', {}).get('id')
                print(f"✅ Blog posted successfully! Article ID: {article_id}")
                print(f"✅ Title: {title}")
                return True
            elif 'articles' in response_data:
                # This might be a GET response instead of POST, let's check what happened
                print(f"⚠️  Received articles array instead of single article")
                print(f"⚠️  This suggests the API might be returning existing articles")
                print(f"📄 Response: {json.dumps(response_data, indent=2)}")
                
                # Let's try to verify if our article was actually created
                # by checking if there's a recent article with our title
                articles = response_data.get('articles', [])
                for article in articles:
                    if article.get('title') == title:
                        print(f"✅ Found our article! ID: {article.get('id')}")
                        return True
                
                print("❌ Our article was not found in the response")
                return False
            else:
                print(f"❌ Unexpected response format: {json.dumps(response_data, indent=2)}")
                return False
        else:
            print(f"❌ Failed to post blog. Status: {resp.status_code}")
            print(f"❌ Response: {resp.text}")
            
            # Try to parse error details
            try:
                error_data = resp.json()
                print(f"❌ Error details: {json.dumps(error_data, indent=2)}")
            except:
                pass
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error while posting blog: {e}")
        return False
    except Exception as e:
        print(f"❌ Error posting blog: {e}")
        return False

def extract_title(content):
    import re
    
    # Try to extract from h1 tag first
    h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", content, re.IGNORECASE)
    if h1_match:
        return h1_match.group(1).strip()
    
    # Fall back to h2 tag
    h2_match = re.search(r"<h2[^>]*>(.*?)</h2>", content, re.IGNORECASE)
    if h2_match:
        return h2_match.group(1).strip()
    
    # Fall back to first line if no headers found
    lines = content.split('\n')
    for line in lines:
        clean_line = re.sub(r'<[^>]+>', '', line).strip()
        if clean_line:
            return clean_line[:100]  # Limit title length
    
    return "Weekly Blog Post"

def test_article_creation():
    """Test creating a simple article to debug the issue"""
    blog_id = get_blog_id()
    if not blog_id:
        return False
    
    url = f"https://{SHOPIFY_STORE}/admin/api/2025-04/blogs/{blog_id}/articles.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_PASSWORD,
        "Content-Type": "application/json"
    }
    
    # Simple test payload
    test_payload = {
        "article": {
            "title": f"Test Article {int(time.time())}",
            "body_html": "<p>This is a test article created by the API.</p>",
            "published": False  # Don't publish test articles
        }
    }
    
    print(f"🧪 Testing article creation...")
    print(f"📤 URL: {url}")
    print(f"🔧 Headers: {json.dumps(headers, indent=2)}")
    print(f"🔧 Payload: {json.dumps(test_payload, indent=2)}")
    
    # Let's also test the exact request being sent
    print(f"🔍 Making POST request...")
    
    try:
        # Check if this is actually being sent as POST
        session = requests.Session()
        req = requests.Request('POST', url, headers=headers, json=test_payload)
        prepared = session.prepare_request(req)
        
        print(f"🔧 Prepared request method: {prepared.method}")
        print(f"🔧 Prepared request URL: {prepared.url}")
        print(f"🔧 Prepared request body: {prepared.body}")
        
        # Send the request
        resp = session.send(prepared, timeout=30, verify=True)
        
        print(f"📡 Response Status: {resp.status_code}")
        print(f"📡 Response Headers: {dict(resp.headers)}")
        print(f"📡 Response Body: {resp.text}")
        
        # Let's also try with requests.post to see if there's a difference
        print(f"\n🔄 Trying with direct requests.post...")
        resp2 = requests.post(
            url, 
            headers=headers, 
            json=test_payload,
            timeout=30,
            verify=True
        )
        
        print(f"📡 Direct POST Status: {resp2.status_code}")
        print(f"📡 Direct POST Response: {resp2.text[:500]}...")
        
        # Let's also try with explicit data parameter instead of json
        print(f"\n🔄 Trying with data parameter...")
        resp3 = requests.post(
            url, 
            headers=headers, 
            data=json.dumps(test_payload),
            timeout=30,
            verify=True
        )
        
        print(f"📡 Data POST Status: {resp3.status_code}")
        print(f"📡 Data POST Response: {resp3.text[:500]}...")
        
        if resp.status_code == 201 or resp2.status_code == 201 or resp3.status_code == 201:
            print(f"✅ Test article created successfully!")
            return True
        else:
            print(f"❌ Test article creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_shopify_connection():
    """Test if Shopify API credentials are working"""
    url = f"https://{SHOPIFY_STORE}/admin/api/2025-04/shop.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_PASSWORD,
        "Content-Type": "application/json"
    }
    
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            shop_data = resp.json()
            shop_name = shop_data.get('shop', {}).get('name', 'Unknown')
            print(f"✅ Shopify connection successful! Shop: {shop_name}")
            return True
        else:
            print(f"❌ Shopify connection failed. Status: {resp.status_code}")
            print(f"❌ Response: {resp.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing Shopify connection: {e}")
        return False

def run():
    print("🚀 Starting blog generation and upload process...")
    
    # Test Shopify connection first
    if not test_shopify_connection():
        print("❌ Aborting due to Shopify connection issues.")
        return
    
    # Test article creation with simple payload
    print("\n🧪 Testing article creation...")
    if not test_article_creation():
        print("❌ Basic article creation test failed. Check permissions and API setup.")
        return
    
    # Generate blog content
    print("\n⏳ Generating blog content...")
    content = generate_blog()
    
    if not content:
        print("❌ Failed to generate blog content.")
        return
    
    # Extract title
    title = extract_title(content)
    print(f"📝 Extracted title: {title}")
    
    # Get blog ID
    print("\n🔍 Getting blog ID...")
    blog_id = get_blog_id()
    
    if not blog_id:
        print("❌ Failed to get blog ID.")
        return
    
    print(f"📋 Using blog ID: {blog_id}")
    
    # Post to Shopify
    print("\n📤 Posting to Shopify...")
    success = post_blog_to_shopify(title, content, blog_id)
    
    if success:
        print("\n🎉 Process completed successfully!")
        print(f"📝 Blog title: {title}")
        print(f"📄 Content preview: {content[:200]}...")
    else:
        print("\n❌ Failed to post blog to Shopify.")
    
    # Optional: wait before finishing
    # time.sleep(60)  # wait for 60 seconds

if __name__ == "__main__":
    run()
