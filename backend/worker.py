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

def generate_seo_content(title: str, current_description: str, category: str = None, images: List[Dict] = None) -> Dict:
    """Generate optimized SEO content using GPT-3.5 and keyword research"""
    
    # Get trending keywords
    suggested_keywords = keyword_research.get_keyword_suggestions(title, category)
    
    # Add image information to the prompt if available
    image_prompt = ""
    if images:
        image_prompt = "\nProduct Images:\n"
        for img in images:
            image_prompt += f"- {img.get('name', 'Product image')}\n"
    
    prompt = f"""
    Analyze this product and provide SEO optimization:
    Product Title: {title}
    Current Description: {current_description}{image_prompt}
    Suggested Keywords: {', '.join(suggested_keywords)}

    Please provide:
    1. A list of 5-7 relevant keywords from the suggested keywords (comma-separated)
    2. An SEO meta description (150-160 characters)
    3. An optimized product description (200-500 words)
    4. SEO-optimized alt tags for each product image that:
       - Describe the image content clearly
       - Include relevant keywords naturally
       - Are concise but descriptive (8-12 words)
       - Consider product features and benefits
       - Follow format: "Image [number]: [description]"

    Format the response exactly as:
    Keywords: [keywords here]
    Meta Description: [meta description here]
    Product Description:
    [HTML-formatted description here]
    Image Alt Tags:
    [numbered list of alt tags]
    """

    # Add more specific instructions to maintain existing structure
    system_prompt = """
    You are an expert e-commerce copywriter and SEO specialist. 
    When optimizing product descriptions:
    1. Keep any existing HTML structure if present
    2. Maintain product specifications and technical details
    3. Only enhance the marketing language and SEO aspects
    4. Do not remove existing product features or specifications
    5. If the original description has tables or lists, preserve them
    6. Add new content only to enhance, not replace existing information
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system", 
                "content": system_prompt
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
    
    # Preserve existing description structure if it exists
    if current_description and current_description.strip():
        # Extract existing HTML structure
        import re
        existing_structure = re.findall(r'<table.*?</table>|<div.*?</div>|<ul.*?</ul>', 
                                      current_description, re.DOTALL)
        
        # Combine new content with existing structure
        if existing_structure:
            product_description = f"{product_description}\n{''.join(existing_structure)}"
    
    # If description doesn't start with HTML tags, wrap it in <p> tags
    if not product_description.strip().startswith('<'):
        product_description = f"<p>{product_description}</p>"
    
    # Parse image alt tags from response
    alt_tags = {}
    if 'Image Alt Tags:' in content:
        alt_section = content.split('Image Alt Tags:')[1].strip()
        for line in alt_section.split('\n'):
            if line.startswith('Image'):
                try:
                    num = line.split(':')[0].replace('Image', '').strip()
                    desc = line.split(':', 1)[1].strip()
                    alt_tags[num] = desc
                except:
                    continue

    return {
        'keywords': keywords,
        'meta_description': meta_description,
        'description': product_description,
        'image_alt_tags': alt_tags
    }

def process_optimization(wp_api: WordPressAPI, max_products: int = None, start_page: int = 1, force_update: bool = False):
    """Process product optimization"""
    try:
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

                        # Get current image alt tags
                        old_image_alts = {}
                        if 'images' in product:
                            for idx, img in enumerate(product['images'], 1):
                                old_image_alts[str(idx)] = img.get('alt', '')

                        # Generate optimized content with images
                        seo_content = generate_seo_content(
                            title, 
                            product['description'], 
                            product.get('category', ''),
                            product.get('images', [])
                        )

                        # Get product permalink/link
                        product_link = product.get('permalink', '')
                        if not product_link:
                            # Construct link if permalink not available
                            base_url = os.getenv("WP_BASE_URL").rstrip('/')
                            product_link = f"{base_url}/product/{product.get('slug', '')}"

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

                        # Update product images with new alt tags
                        if 'images' in product and seo_content.get('image_alt_tags'):
                            updated_images = []
                            for idx, img in enumerate(product['images'], 1):
                                img_copy = img.copy()
                                if str(idx) in seo_content['image_alt_tags']:
                                    img_copy['alt'] = seo_content['image_alt_tags'][str(idx)]
                                updated_images.append(img_copy)
                            
                            update_data['images'] = updated_images

                        wp_api.update_product(product_id, update_data)

                        # Record success with image alts
                        result = OptimizationResult(
                            product_id=product_id,
                            product_name=title,
                            product_link=product_link,
                            old_description=product['description'],
                            new_description=seo_content['description'],
                            old_meta_description=old_meta_description,
                            meta_description=seo_content['meta_description'],
                            old_keywords=old_keywords,
                            keywords=seo_content['keywords'],
                            old_image_alts=old_image_alts,
                            new_image_alts=seo_content.get('image_alt_tags'),
                            status="success",
                            timestamp=datetime.now()
                        )
                        optimization_history.add_result(result)

                        products_processed += 1
                        print(f"Processed {products_processed} products. Current: {title}")

                    except Exception as e:
                        print(f"Error processing product {product.get('name', '')}: {str(e)}")
                        # Record failure with link
                        product_link = product.get('permalink', '') or f"{os.getenv('WP_BASE_URL').rstrip('/')}/product/{product.get('slug', '')}"
                        result = OptimizationResult(
                            product_id=product['id'],
                            product_name=product.get('name', ''),
                            product_link=product_link,
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

    except Exception as e:
        print(f"Critical error in optimization process: {str(e)}")
        return []

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
                self.results = []

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
        """Add a new optimization result"""
        self.results.append(result)
        self.save_history()  # Save after each new result

    def get_results(self) -> List[OptimizationResult]:
        """Get all optimization results"""
        return self.results

    def get_processed_ids(self) -> Set[int]:
        """Get set of already processed product IDs"""
        return {r.product_id for r in self.results}

    def clear_history(self):
        """Clear optimization history"""
        self.results = []
        if self.history_file.exists():
            self.history_file.unlink() 

def migrate_history_entries():
    """Add product links to existing history entries"""
    base_url = os.getenv("WP_BASE_URL").rstrip('/')
    
    for result in optimization_history.results:
        if not hasattr(result, 'product_link') or not result.product_link:
            # Get product details to find the slug
            try:
                product = wp_api.get_product(result.product_id)
                if product:
                    result.product_link = product.get('permalink', '') or f"{base_url}/product/{product.get('slug', '')}"
            except:
                # If we can't get the product details, construct a basic URL
                result.product_link = f"{base_url}/?p={result.product_id}"
    
    # Save the updated history
    optimization_history.save_history()

# Add this to your startup code
if __name__ == "__main__":
    migrate_history_entries() 