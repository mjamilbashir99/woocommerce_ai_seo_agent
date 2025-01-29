"""
WordPress SEO Optimizer
Created by Jamil Bashir (themindgauge.com)
LinkedIn: https://www.linkedin.com/in/mjamilbashir/
Twitter: https://x.com/mjamilbashir99

A tool for intelligent product description optimization using AI and SEO best practices.
"""

from wp_api import WordPressAPI
from openai import OpenAI
import os
from typing import Dict, List, Set
import time
from datetime import datetime
from models import OptimizationResult, OptimizationHistory
from dotenv import load_dotenv
import json
from pathlib import Path
from keyword_research import KeywordResearch

# Load environment variables
load_dotenv()

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

client = OpenAI(api_key=api_key)
optimization_history = OptimizationHistory()

print(f"OpenAI API Key: {os.getenv('OPENAI_API_KEY')[:10]}...")  # Only print first 10 chars for security

# Initialize keyword research
keyword_research = KeywordResearch()

def generate_seo_content(title: str, current_description: str, category: str = None) -> Dict:
    """Generate optimized SEO content using GPT-3.5 and keyword research"""
    
    # Get trending keywords
    suggested_keywords = keyword_research.get_keyword_suggestions(title, category)
    
    prompt = f"""
    Analyze this product and provide SEO optimization:
    Product Title: {title}
    Current Description: {current_description}
    Suggested Keywords: {', '.join(suggested_keywords)}

    Please provide:
    1. A list of 5-7 relevant keywords from the suggested keywords (comma-separated)
    2. An SEO meta description (150-160 characters)
    3. An optimized product description (200-500 words) that:
       - Naturally incorporates the chosen keywords
       - Focuses on benefits and features
       - Uses engaging, persuasive language
       - Maintains a professional tone
       - Includes a call to action
       - Uses HTML formatting (<p>, <strong>, <ul>, <li> tags)
       - Organizes content into clear sections
       - Highlights key features and benefits
       - Ends with a compelling call to action
       - Targets {os.getenv('TARGET_COUNTRY', 'worldwide')} audience

    Format the response exactly as:
    Keywords: [keywords here]
    Meta Description: [meta description here]
    Product Description:
    [HTML-formatted description here]
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system", 
                "content": "You are an expert e-commerce copywriter and SEO specialist. Format product descriptions with HTML tags for better structure and emphasis."
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1500
    )
    
    content = response.choices[0].message.content.strip()
    
    # Parse the response
    sections = content.split('\n\n')
    keywords = sections[0].replace('Keywords:', '').strip()
    meta_description = sections[1].replace('Meta Description:', '').strip()
    
    # Get the product description part (everything after "Product Description:")
    description_parts = content.split('Product Description:')
    product_description = description_parts[1].strip() if len(description_parts) > 1 else ""
    
    # If description doesn't start with HTML tags, wrap it in <p> tags
    if not product_description.strip().startswith('<'):
        product_description = f"<p>{product_description}</p>"
    
    return {
        'keywords': keywords,
        'meta_description': meta_description,
        'description': product_description
    }

def process_optimization(wp_api: WordPressAPI, max_products: int = None, start_page: int = 1, force_update: bool = False):
    """Process product optimization
    
    Args:
        wp_api: WordPress API instance
        max_products: Maximum number of products to process (None for all)
        start_page: Page number to start from
        force_update: If True, will update products even if previously processed
    """
    page = start_page
    per_page = 10
    products_processed = 0
    processed_ids = set() if force_update else optimization_history.get_processed_ids()

    while True:
        try:
            products = wp_api.get_products(per_page=per_page, page=page)
            
            if not products:
                print(f"No more products found. Total processed: {products_processed}")
                break

            for product in products:
                try:
                    if max_products and products_processed >= max_products:
                        print(f"Reached maximum products limit: {max_products}")
                        return optimization_history.get_results()

                    product_id = product['id']
                    
                    # Skip if already processed (unless force_update is True)
                    if product_id in processed_ids:
                        print(f"Skipping already processed product: {product['name']}")
                        continue

                    # Extract product info
                    title = product['name']
                    
                    # Skip if already optimized recently (within last 30 days)
                    last_updated = product.get('date_modified', '')
                    if is_recently_optimized(last_updated):
                        print(f"Skipping recently updated product: {title}")
                        continue

                    # Get current meta data
                    current_meta = {item['key']: item['value'] for item in product.get('meta_data', [])}
                    old_meta_description = current_meta.get('_yoast_wpseo_metadesc', '')
                    old_keywords = current_meta.get('_yoast_wpseo_focuskw', '')

                    # Generate optimized content
                    seo_content = generate_seo_content(title, product['description'], product.get('category', ''))

                    # Update product
                    update_data = {
                        'description': seo_content['description'],
                        'meta_data': [
                            {
                                'key': '_yoast_wpseo_metadesc',
                                'value': seo_content['meta_description']
                            },
                            {
                                'key': '_yoast_wpseo_focuskw',
                                'value': seo_content['keywords'].split(',')[0]
                            }
                        ]
                    }
                    wp_api.update_product(product_id, update_data)

                    # Record the optimization result
                    result = OptimizationResult(
                        product_id=product_id,
                        product_name=title,
                        old_description=product['description'],
                        new_description=seo_content['description'],
                        old_meta_description=old_meta_description,
                        meta_description=seo_content['meta_description'],
                        old_keywords=old_keywords,
                        keywords=seo_content['keywords'],
                        status="success",
                        timestamp=datetime.now()
                    )
                    optimization_history.add_result(result)

                    products_processed += 1
                    print(f"Processed {products_processed} products. Current: {title}")

                except Exception as e:
                    print(f"Error processing product {product.get('name', '')}: {str(e)}")
                    # Record failed optimization
                    result = OptimizationResult(
                        product_id=product['id'],
                        product_name=product.get('name', ''),
                        old_description=product.get('description', ''),
                        new_description='',
                        meta_description='',
                        keywords='',
                        status=f"error: {str(e)}",
                        timestamp=datetime.now()
                    )
                    optimization_history.add_result(result)
                    continue

            page += 1
            
        except Exception as e:
            print(f"Error fetching products page {page}: {str(e)}")
            break

    print(f"Optimization complete. Total products processed: {products_processed}")
    return optimization_history.get_results()

def is_recently_optimized(last_updated: str, days: int = 30) -> bool:
    """Check if product was optimized recently"""
    if not last_updated:
        return False
    
    try:
        from datetime import datetime, timezone
        last_update_date = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        difference = now - last_update_date
        return difference.days < days
    except:
        return False

class OptimizationHistory:
    def __init__(self):
        self.results: List[OptimizationResult] = []
        self.history_file = Path("optimization_history.json")
        self.load_history()

    def load_history(self):
        """Load optimization history from file"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    # Convert JSON data back to OptimizationResult objects
                    self.results = [
                        OptimizationResult(
                            **{**item, 
                               'timestamp': datetime.fromisoformat(item['timestamp'])
                            }
                        ) 
                        for item in data
                    ]
            except Exception as e:
                print(f"Error loading history: {e}")

    def save_history(self):
        """Save optimization history to file"""
        try:
            # Convert OptimizationResult objects to dictionaries
            data = [
                {**result.dict(), 
                 'timestamp': result.timestamp.isoformat()
                } 
                for result in self.results
            ]
            with open(self.history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")

    def add_result(self, result: OptimizationResult):
        self.results.append(result)
        self.save_history()  # Save after each new result

    def get_results(self) -> List[OptimizationResult]:
        return self.results

    def get_processed_ids(self) -> Set[int]:
        """Get set of already processed product IDs"""
        return {r.product_id for r in self.results} 