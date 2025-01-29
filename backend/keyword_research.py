"""
Smart Keyword Research Module
Developed by Jamil Bashir for The Mind Gauge
https://themindgauge.com

This module combines traditional keyword research with Google Trends data
to provide comprehensive keyword suggestions for e-commerce products.
"""

from typing import List, Dict
import requests
from pytrends.request import TrendReq
import os
from datetime import datetime, timedelta
import time
import json

class KeywordResearch:
    def __init__(self):
        self.country = os.getenv("TARGET_COUNTRY", "ALL")
        self.use_trends = os.getenv("USE_GOOGLE_TRENDS", "true").lower() == "true"
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
        
        # Add basic e-commerce modifiers
        modifiers = ['buy', 'online', 'uk', 'shop', 'best']
        base_terms = list(set(keywords))
        
        for term in base_terms:
            for mod in modifiers:
                keywords.append(f"{mod} {term}")
                keywords.append(f"{term} {mod}")
        
        return list(set(keywords))

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

    def get_keyword_suggestions(self, product_name: str, category: str = None) -> List[str]:
        """Get keyword suggestions including long-tail keywords"""
        if self.use_trends:
            # Use Google Trends data
            trending = self.get_trending_keywords(product_name, category)
            base_keywords = [kw['keyword'] for kw in trending[:5]]
        else:
            # Use basic keyword generation
            base_keywords = self.get_base_keywords(product_name, category)

        # Generate long-tail variations
        long_tail = []
        modifiers = ['best', 'top', 'cheap', 'premium', 'luxury', 'affordable', 
                    'buy', 'online', 'uk', 'shop', 'sale', 'discount']
        
        for kw in base_keywords:
            for mod in modifiers:
                long_tail.append(f"{mod} {kw}")
                long_tail.append(f"{kw} {mod}")

        all_keywords = list(set(base_keywords + long_tail))
        print(f"Generated {len(all_keywords)} keywords for '{product_name}' using {'Google Trends' if self.use_trends else 'basic generation'}")
        return all_keywords