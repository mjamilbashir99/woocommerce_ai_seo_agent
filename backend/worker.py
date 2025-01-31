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

def generate_keywords(title: str, category: str, suggested_keywords: List[str]) -> str:
    """Generate optimized keywords"""
    prompt = f"""
    Product: {title}
    Category: {category or 'N/A'}
    Suggested Keywords: {', '.join(suggested_keywords[:10])}

    Generate 5-7 highly relevant, SEO-optimized keywords for this product.
    Include both short and long-tail keywords.
    Format: comma-separated list
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an SEO expert specializing in e-commerce keyword optimization."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=200
    )
    return response.choices[0].message.content.strip()

def generate_meta_description(title: str, keywords: str) -> str:
    """Generate conversion-focused meta description"""
    prompt = f"""
    Product: {title}
    Primary Keywords: {keywords}

    As a conversion optimization expert, write a compelling meta description that:
    1. Starts with a strong hook or value proposition
    2. Includes specific benefits or features that drive sales
    3. Uses proven psychological triggers (scarcity, social proof, etc.)
    4. Has a clear call-to-action that motivates clicks
    5. Incorporates primary keyword naturally (150-160 chars)
    6. Addresses customer pain points or desires
    7. Uses power words that increase CTR

    Make it irresistible for both search engines and shoppers.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an e-commerce conversion specialist focusing on writing meta descriptions that maximize click-through rates and sales."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=200
    )
    return response.choices[0].message.content.strip()

def generate_product_description(title: str, current_description: str, keywords: str, category: str) -> str:
    """Generate sales-optimized product description"""
    prompt = f"""
    Product: {title}
    Category: {category or 'N/A'}
    Target Keywords: {keywords}

    As a conversion copywriting expert, create a high-converting product description that:
    1. Opens with an attention-grabbing hook that addresses customer pain points
    2. Uses the AIDA formula (Attention, Interest, Desire, Action)
    3. Highlights unique selling propositions (USPs) and competitive advantages
    4. Includes social proof, testimonials, or trust indicators
    5. Addresses common objections and concerns
    6. Uses bullet points for scannable key features and benefits
    7. Incorporates emotional triggers and power words
    8. Ends with a strong call-to-action and urgency
    9. Naturally weaves in SEO keywords
    10. Uses persuasive HTML formatting (<strong> for benefits, <ul> for features)

    Focus on benefits over features, and always answer "What's in it for me?"
    Length: 300-500 words of persuasive copy.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert e-commerce conversion copywriter specializing in product descriptions that drive sales while maintaining SEO best practices."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )
    
    new_description = response.choices[0].message.content.strip()
    
    return new_description

def generate_image_alt_tags(title: str, images: List[Dict], primary_keyword: str) -> Dict[str, str]:
    """Generate conversion-focused image alt tags"""
    prompt = f"""
    Product: {title}
    Primary Keyword: {primary_keyword}
    Number of Images: {len(images)}

    As a visual marketing expert, create persuasive image alt tags that:
    1. Highlight key selling points visible in each image
    2. Include action words that drive engagement
    3. Mention product benefits shown in the image
    4. Use emotional or persuasive language when relevant
    5. Incorporate keywords naturally
    6. Follow accessibility best practices
    7. Help visualize the product's value

    Format each alt tag to drive both SEO and sales, numbered by image.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an e-commerce visual marketing specialist focusing on conversion-optimized image descriptions that boost SEO and sales."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=500
    )

    content = response.choices[0].message.content.strip()
    alt_tags = {}
    
    # Parse the response into a dictionary
    for line in content.split('\n'):
        if ':' in line:
            num, alt = line.split(':', 1)
            try:
                num = num.strip()
                alt_tags[num] = alt.strip()
            except:
                continue

    return alt_tags

def generate_seo_content(title: str, current_description: str, category: str = None, images: List[Dict] = None) -> Dict:
    """Generate optimized SEO content using multiple focused prompts"""
    try:
        # Get keyword suggestions and generate content
        suggested_keywords = keyword_research.get_keyword_suggestions(title, category)
        keywords = generate_keywords(title, category, suggested_keywords)
        print(f"Generated keywords for {title}")
        
        meta_description = generate_meta_description(title, keywords)
        print(f"Generated meta description for {title}")
        
        description = generate_product_description(title, current_description, keywords, category)
        print(f"Generated product description for {title}")

        # Generate alt tags if images exist
        image_alt_tags = {}
        if images:
            primary_keyword = keywords.split(',')[0].strip()
            image_alt_tags = generate_image_alt_tags(title, images, primary_keyword)
            print(f"Generated alt tags for {len(images)} images")

        return {
            'keywords': keywords,
            'meta_description': meta_description,
            'description': description,
            'image_alt_tags': image_alt_tags
        }
    except Exception as e:
        print(f"Error generating SEO content: {str(e)}")
        raise

def generate_meta_from_title(title: str) -> Dict[str, str]:
    """Generate meta description and keywords from product title"""
    prompt = f"""
    Product: {title}
    Generate:
    1. Meta Description: [150-160 chars]
    2. Keywords: [3-5 keywords]
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an SEO expert. Be concise."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=150
    )

    content = response.choices[0].message.content.strip()
    
    meta_desc = ""
    keywords = ""
    
    for line in content.split('\n'):
        if line.startswith('Meta Description:'):
            meta_desc = line.replace('Meta Description:', '').strip()
        elif line.startswith('Keywords:'):
            keywords = line.replace('Keywords:', '').strip()

    return {
        'meta_description': meta_desc,
        'keywords': keywords
    }

def get_variant_info(product: Dict) -> Dict[str, Dict[str, str]]:
    """Extract variant information from product"""
    variants = {}
    
    # Get variations if they exist
    if 'variations' in product:
        for idx, variation in enumerate(product['variations'], 1):
            color = ''
            size = ''
            
            # Get attributes like color, size etc.
            for attribute in variation.get('attributes', []):
                attr_name = attribute.get('name', '').lower()
                if 'color' in attr_name:
                    color = attribute.get('option', '')
                elif 'size' in attr_name:
                    size = attribute.get('option', '')
            
            variants[str(idx)] = {
                'color': color,
                'size': size
            }
    
    return variants

def generate_gallery_alt_tags(title: str, images: List[Dict], variants: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    """Generate alt tags and titles for gallery images using variant information"""
    image_texts = {}
    
    for idx, img in enumerate(images, 1):
        idx_str = str(idx)
        if idx == 1:
            # Main product image
            alt_tag = f"{title}"
            img_title = f"{title} - Main Product Image"
        else:
            # Gallery images - use variant info if available
            variant_info = variants.get(str(idx-1), {})  # idx-1 because first image is main
            color = variant_info.get('color', '')
            size = variant_info.get('size', '')
            
            variant_text = []
            if color:
                variant_text.append(color)
            if size:
                variant_text.append(size)
                
            if variant_text:
                variant_str = ' '.join(variant_text)
                alt_tag = f"{title} {variant_str}"
                img_title = f"{title} - {variant_str}"
            else:
                # Fallback if no variant info
                alt_tag = f"{title}"
                img_title = f"{title} - Gallery Image {idx}"
        
        image_texts[idx_str] = {
            'alt': alt_tag,
            'title': img_title
        }

    return image_texts

def process_optimization(wp_api: WordPressAPI, max_products: int = 10, start_page: int = 1, force_update: bool = False, dry_run: bool = True):
    """Process product optimization with pagination"""
    try:
        page = start_page
        per_page = 10  # Process 10 products per page
        products_processed = 0
        PRODUCT_LIMIT = max_products or 10  # Default to 10 if not specified
        processed_ids = set() if force_update else optimization_history.get_processed_ids()

        print(f"Running in {'preview' if dry_run else 'update'} mode")
        print(f"Processing page {page} (Products {(page-1)*per_page + 1} to {page*per_page})")

        while products_processed < PRODUCT_LIMIT:
            try:
                products = wp_api.get_products(per_page=per_page, page=page)
                
                if not products:
                    print("No more products found.")
                    break

                for product in products:
                    if products_processed >= PRODUCT_LIMIT:
                        break

                    try:
                        product_id = product['id']
                        
                        # Skip if already processed and not forcing update
                        if product_id in processed_ids and not force_update:
                            print(f"Skipping already processed product: {product.get('name', '')}")
                            continue

                        current_title = product['name']
                        current_slug = product.get('slug', '')
                        product_link = product.get('permalink', '') or f"{os.getenv('WP_BASE_URL').rstrip('/')}/product/{product.get('slug', '')}"

                        # Generate SEO-optimized title and slug first
                        title_data = generate_seo_title_and_slug(current_title, product.get('category', ''))
                        title = title_data['title']
                        new_slug = title_data['slug']
                        title_change_reason = title_data['reason']
                        
                        print(f"Optimizing title: {current_title} -> {title}")
                        print(f"Optimizing slug: {current_slug} -> {new_slug}")
                        print(f"Optimization reason: {title_change_reason}")

                        # Initialize update_data with the new title and slug
                        update_data = {
                            'name': title,
                            'slug': new_slug,
                            'description': '',
                            'meta_data': [],
                            'images': [],
                            'gallery_images': []
                        }

                        # Update product title and slug immediately if not in dry run mode
                        if not dry_run:
                            initial_update = {
                                'name': title,
                                'slug': new_slug
                            }
                            wp_api.update_product(product_id, initial_update)
                            print(f"Updated product title and slug")
                            
                            # Small delay to ensure title update is processed
                            time.sleep(1)

                        # Get current meta data
                        current_meta = {item['key']: item['value'] for item in product.get('meta_data', [])}
                        old_meta_description = current_meta.get('_yoast_wpseo_metadesc', '')
                        old_keywords = current_meta.get('_yoast_wpseo_focuskw', '')

                        # Generate meta data if empty
                        if not old_meta_description or not old_keywords:
                            print(f"Generating missing meta data for: {title}")
                            meta_data = generate_meta_from_title(title)
                            if not old_meta_description:
                                old_meta_description = meta_data['meta_description']
                            if not old_keywords:
                                old_keywords = meta_data['keywords']

                        # Get variant information
                        variants = get_variant_info(product)

                        # Get product and gallery images separately
                        product_images = []
                        gallery_images = []
                        
                        # Safely get and validate images
                        raw_images = product.get('images', [])
                        raw_gallery = product.get('gallery_images', [])
                        
                        # Validate product images
                        if isinstance(raw_images, list):
                            for img in raw_images:
                                if isinstance(img, dict) and isinstance(img.get('id'), (int, str)):
                                    product_images.append(img)
                        
                        # Validate gallery images
                        if isinstance(raw_gallery, list):
                            for img in raw_gallery:
                                if isinstance(img, dict) and isinstance(img.get('id'), (int, str)):
                                    gallery_images.append(img)
                        
                        # Get current image texts with validation
                        old_image_alts = {}
                        old_image_titles = {}
                        
                        # Process product images
                        for idx, img in enumerate(product_images, 1):
                            idx_str = str(idx)
                            if isinstance(img, dict):
                                old_image_alts[idx_str] = img.get('alt', '')
                                old_image_titles[idx_str] = img.get('title', '')
                        
                        # Process gallery images
                        start_idx = len(product_images) + 1
                        for idx, img in enumerate(gallery_images, start_idx):
                            idx_str = str(idx)
                            if isinstance(img, dict):
                                old_image_alts[idx_str] = img.get('alt', '')
                                old_image_titles[idx_str] = img.get('title', '')

                        # Generate SEO content first
                        seo_content = generate_seo_content(
                            title, 
                            product['description'], 
                            product.get('category', ''),
                            product_images
                        )

                        # Generate new alt tags and titles with validation
                        new_image_texts = generate_gallery_alt_tags(
                            title, 
                            product_images, 
                            variants
                        )
                        
                        # Safely create new image data
                        new_image_alts = {}
                        new_image_titles = {}
                        
                        for k, v in new_image_texts.items():
                            if isinstance(v, dict):
                                new_image_alts[k] = v.get('alt', '')
                                new_image_titles[k] = v.get('title', '')

                        # Update data preparation
                        update_data = {
                            'name': title,
                            'slug': new_slug,
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

                        # Update the images with new alt tags and titles
                        if not dry_run:
                            # Update product images
                            updated_product_images = []
                            for idx, img in enumerate(product_images, 1):
                                if isinstance(img, dict):
                                    idx_str = str(idx)
                                    img_copy = img.copy()
                                    if idx_str in new_image_texts:
                                        img_copy['alt'] = new_image_texts[idx_str]['alt']
                                        img_copy['title'] = new_image_texts[idx_str]['title']
                                        img_copy['name'] = new_image_texts[idx_str]['title']
                                    updated_product_images.append(img_copy)
                            
                            # Update gallery images
                            updated_gallery_images = []
                            start_idx = len(product_images) + 1
                            for idx, img in enumerate(gallery_images, start_idx):
                                if isinstance(img, dict):
                                    idx_str = str(idx)
                                    img_copy = img.copy()
                                    if idx_str in new_image_texts:
                                        img_copy['alt'] = new_image_texts[idx_str]['alt']
                                        img_copy['title'] = new_image_texts[idx_str]['title']
                                        img_copy['name'] = new_image_texts[idx_str]['title']
                                    updated_gallery_images.append(img_copy)
                            
                            update_data['images'] = updated_product_images
                            update_data['gallery_images'] = updated_gallery_images

                            # Add debug logging
                            print(f"Updating product {product_id} with new image data:")
                            print(f"Product images: {len(updated_product_images)}")
                            print(f"Gallery images: {len(updated_gallery_images)}")
                            for idx, img in enumerate(updated_product_images + updated_gallery_images, 1):
                                print(f"Image {idx} - Alt: {img.get('alt')}, Title: {img.get('title')}")

                        # Update product if not in dry run mode
                        if not dry_run:
                            wp_api.update_product(product_id, update_data)
                            status = "success"
                        else:
                            status = "preview"

                        # Record result
                        result = OptimizationResult(
                            product_id=product_id,
                            product_name=current_title,
                            new_product_name=title,
                            old_slug=current_slug,
                            new_slug=new_slug,
                            title_change_reason=title_change_reason,
                            product_link=product_link,
                            old_description=product['description'],
                            new_description=update_data['description'],
                            old_meta_description=old_meta_description,
                            meta_description=update_data['meta_data'][0]['value'],
                            old_keywords=old_keywords,
                            keywords=update_data['meta_data'][1]['value'],
                            old_image_alts=old_image_alts,
                            new_image_alts=new_image_alts,
                            old_image_titles=old_image_titles,
                            new_image_titles=new_image_titles,
                            images=product_images,
                            status=status,
                            timestamp=datetime.now()
                        )
                        optimization_history.add_result(result)

                        products_processed += 1
                        print(f"Processed product {products_processed} of {PRODUCT_LIMIT}: {title}")

                    except Exception as e:
                        print(f"Error processing product {product.get('name', '')}: {str(e)}")
                        continue

                if products_processed >= PRODUCT_LIMIT:
                    print(f"Reached product limit of {PRODUCT_LIMIT}")
                    break

                page += 1
                print(f"\nMoving to page {page} (Products {(page-1)*per_page + 1} to {page*per_page})")
                
            except Exception as e:
                print(f"Error fetching products page {page}: {str(e)}")
                break

        print(f"\nOptimization complete. Products processed: {products_processed}")
        print(f"Last page processed: {page-1}")
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

def generate_image_alt_tag(product_name: str, image_number: int, total_images: int, keywords: str) -> str:
    """Generate SEO-friendly alt tag for product image"""
    
    # Create variations for different image positions
    if image_number == 1:
        prefix = "Main view of"
    elif image_number == total_images:
        prefix = "Detailed view of"
    else:
        prefixes = [
            "Alternative view of",
            "Close-up of",
            "Style view of",
            "Feature detail of",
            "Lifestyle shot of",
            "Angle view of"
        ]
        prefix = prefixes[image_number % len(prefixes)]

    # Clean and format the product name and keyword
    product_name = product_name.strip()
    keyword = keywords.strip()

    # Combine elements into alt tag
    alt_tag = f"{prefix} {product_name} - {keyword}"

    return alt_tag

def generate_seo_title_and_slug(current_title: str, category: str = None) -> Dict[str, str]:
    """Generate sales-focused SEO title and slug"""
    prompt = f"""
    Current Title: {current_title}
    Category: {category or 'N/A'}

    As a senior e-commerce SEO specialist, create:
    1. A high-converting product title that:
       - Uses proven sales trigger words (Premium, Luxury, Professional)
       - Highlights key benefits/USPs
       - Creates urgency/exclusivity when relevant
       - Includes main product type (50-60 chars max)
       - Uses power words that drive emotional response
       - Follows marketplace best practices

    2. An SEO-optimized URL slug that:
       - Is concise and readable
       - Contains primary keyword
       - Uses hyphens between words
       - Excludes stop words
       - Is under 60 characters
       - Follows URL best practices

    Return in this format:
    New Title: [optimized title]
    Slug: [seo-friendly-slug]
    Reason: [explain optimization strategy]
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a senior e-commerce marketing specialist with expertise in conversion optimization and SEO. Focus on creating titles and URLs that maximize both rankings and sales."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=200
    )

    content = response.choices[0].message.content.strip()
    
    new_title = ""
    new_slug = ""
    reason = ""
    
    for line in content.split('\n'):
        if line.startswith('New Title:'):
            new_title = line.replace('New Title:', '').strip()
        elif line.startswith('Slug:'):
            new_slug = line.replace('Slug:', '').strip()
        elif line.startswith('Reason:'):
            reason = line.replace('Reason:', '').strip()

    return {
        'title': new_title,
        'slug': new_slug,
        'reason': reason
    }

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