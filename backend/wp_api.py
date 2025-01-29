import requests
from typing import Dict, List, Optional
from requests.auth import HTTPBasicAuth
import urllib3
import certifi
import os

# Suppress only the single InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Add at the top of the file
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

class WordPressAPI:
    def __init__(self, base_url: str, consumer_key: str, consumer_secret: str):
        self.base_url = base_url.rstrip('/')
        self.auth = HTTPBasicAuth(consumer_key, consumer_secret)
        self.wc_api_base = f"{self.base_url}/wp-json/wc/v3"
        self.session = requests.Session()
        self.session.verify = certifi.where()

    def get_products(self, per_page: int = 10, page: int = 1) -> List[Dict]:
        """Fetch WooCommerce products"""
        endpoint = f"{self.wc_api_base}/products"
        params = {
            'per_page': per_page,
            'page': page,
            'status': 'publish',  # Only get published products
            'orderby': 'date',    # Order by date
            'order': 'desc'       # Newest first
        }
        response = self.session.get(endpoint, auth=self.auth, params=params)
        response.raise_for_status()
        return response.json()

    def update_product(self, product_id: int, data: Dict) -> Dict:
        """Update a WooCommerce product"""
        endpoint = f"{self.wc_api_base}/products/{product_id}"
        response = self.session.put(
            endpoint, 
            auth=self.auth,
            json=data
        )
        response.raise_for_status()
        return response.json()

    def get_product(self, product_id: int) -> Dict:
        """Get a single WooCommerce product"""
        endpoint = f"{self.wc_api_base}/products/{product_id}"
        response = self.session.get(
            endpoint, 
            auth=self.auth
        )
        response.raise_for_status()
        return response.json() 