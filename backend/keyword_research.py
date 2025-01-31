"""
Smart Keyword Research Module
Developed by Jamil Bashir for The Mind Gauge
https://themindgauge.com

This module combines traditional keyword research with Google Trends data
to provide comprehensive keyword suggestions for e-commerce products.
"""

from typing import List, Dict
import requests
import os
from datetime import datetime, timedelta
import time
import json

# Try to import pytrends, but make it optional
try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False
    print("Google Trends functionality is disabled. To enable, install pytrends: pip install pytrends")

class KeywordResearch:
    def __init__(self):
        self.country = os.getenv("TARGET_COUNTRY", "ALL")
        self.use_trends = (
            os.getenv("USE_GOOGLE_TRENDS", "true").lower() == "true" 
            and PYTRENDS_AVAILABLE
        )
        self.pytrends = TrendReq(hl='en-GB') if self.use_trends else None
        self.cache_file = "keyword_trends_cache.json"
        self.cache = self.load_cache()

    def load_cache(self) -> Dict:
        """Load cached keyword data"""
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except:
            return {}

    def save_cache(self):
        """Save keyword data to cache"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f)

    def get_base_keywords(self, product_name: str, category: str = None) -> List[str]:
        """Get base keywords without Google Trends"""
        keywords = []
        
        # Add product name words
        keywords.extend(product_name.lower().split())
        
        # Add category words if available
        if category:
            keywords.extend(category.lower().split())
        
        # Add product-specific modifiers based on category
        modifiers = ['buy', 'online', 'uk', 'shop']
        if category:
            category_lower = category.lower()
            if 'clothing' in category_lower or 'fashion' in category_lower:
                modifiers.extend(['wear', 'style', 'fashion', 'trendy', 'outfit'])
            elif 'electronics' in category_lower:
                modifiers.extend(['best', 'review', 'specs', 'features', 'technical'])
            # Add more category-specific modifiers as needed
        
        base_terms = list(set(keywords))
        result_keywords = []
        
        for term in base_terms:
            result_keywords.append(term)
            for mod in modifiers:
                result_keywords.append(f"{mod} {term}")
                result_keywords.append(f"{term} {mod}")
        
        return list(set(result_keywords))

    def get_trending_keywords(self, product_name: str, category: str = None) -> List[Dict]:
        """Get trending keywords for a product"""
        cache_key = f"{product_name}_{category}_{self.country}"
        
        # Check cache first
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            cache_time = datetime.fromisoformat(cached_data['timestamp'])
            if datetime.now() - cache_time < timedelta(days=7):
                return cached_data['keywords']

        # Base keywords from product name
        base_keywords = product_name.lower().split()
        if category:
            base_keywords.extend(category.lower().split())

        try:
            # Get Google Trends data
            self.pytrends.build_payload(
                base_keywords,
                cat=0,
                timeframe='today 90-d',
                geo=self.country if self.country != 'ALL' else ''
            )
            
            related_queries = self.pytrends.related_queries()
            trending_keywords = []

            for kw in base_keywords:
                if kw in related_queries:
                    rising = related_queries[kw]['rising']
                    top = related_queries[kw]['top']
                    
                    if rising is not None:
                        for _, row in rising.iterrows():
                            trending_keywords.append({
                                'keyword': row['query'],
                                'score': int(row['value']),
                                'type': 'rising'
                            })
                    
                    if top is not None:
                        for _, row in top.iterrows():
                            trending_keywords.append({
                                'keyword': row['query'],
                                'score': int(row['value']),
                                'type': 'top'
                            })

            # Remove duplicates and sort by score
            seen = set()
            unique_keywords = []
            for kw in trending_keywords:
                if kw['keyword'] not in seen:
                    seen.add(kw['keyword'])
                    unique_keywords.append(kw)

            result = sorted(unique_keywords, key=lambda x: x['score'], reverse=True)

            # Cache the results
            self.cache[cache_key] = {
                'keywords': result,
                'timestamp': datetime.now().isoformat()
            }
            self.save_cache()

            return result

        except Exception as e:
            print(f"Error getting trending keywords: {e}")
            return []

    def get_keyword_suggestions(self, title: str, category: str = None) -> List[str]:
        """Get keyword suggestions with fallback options"""
        try:
            # Try to get trending keywords first
            trending_keywords = self._get_trending_keywords(title)
            if trending_keywords:
                return trending_keywords
        except Exception as e:
            print(f"Error getting trending keywords: {str(e)}")
            print("Falling back to basic keyword extraction...")
        
        # Fallback: Extract keywords from title and category
        return self._extract_basic_keywords(title, category)

    def _extract_basic_keywords(self, title: str, category: str = None) -> List[str]:
        """Extract basic keywords from title and category"""
        keywords = []
        
        # Clean and split title
        title_words = title.lower().replace('-', ' ').split()
        
        # Remove common stop words
        stop_words = {'and', 'or', 'the', 'a', 'an', 'in', 'on', 'at', 'for', 'to', 'of', 'with'}
        title_words = [word for word in title_words if word not in stop_words]
        
        # Add individual keywords
        keywords.extend(title_words)
        
        # Add 2-word combinations
        for i in range(len(title_words) - 1):
            keywords.append(f"{title_words[i]} {title_words[i+1]}")
        
        # Add category if provided
        if category:
            keywords.append(category.lower())
            # Add category + main product type
            if title_words:
                keywords.append(f"{category.lower()} {title_words[-1]}")
        
        # Remove duplicates and sort
        keywords = list(set(keywords))
        
        return keywords[:10]  # Return top 10 keywords

    def _get_trending_keywords(self, title: str) -> List[str]:
        """Get trending keywords if API is available"""
        if not os.getenv('USE_GOOGLE_TRENDS', 'false').lower() == 'true':
            return []
            
        try:
            # Your existing trending keywords code
            # If it fails, the function will return to get_keyword_suggestions
            # which will use _extract_basic_keywords as fallback
            pass
        except Exception as e:
            print(f"Trending keywords API error: {str(e)}")
            return []