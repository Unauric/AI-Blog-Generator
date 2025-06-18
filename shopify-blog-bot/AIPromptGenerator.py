def get_prompt(keywords):
    return f"""
Write a 600-word blog post for a Shopify store based on the keywords: {", ".join(keywords)}.
Include a catchy title, <h2> subheadings, and <p> tags for paragraphs. No bullet points. the post does not need to include all keywords.
"""
