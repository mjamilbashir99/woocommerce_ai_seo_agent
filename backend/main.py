from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from wp_api import WordPressAPI
from worker import process_optimization, optimization_history
import os
from dotenv import load_dotenv
import openai
from keyword_research import KeywordResearch

# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="WordPress SEO Optimizer")
templates = Jinja2Templates(directory="templates")

# Initialize WordPress API with consumer key/secret
wp_api = WordPressAPI(
    base_url=os.getenv("WP_BASE_URL"),
    consumer_key=os.getenv("WC_CONSUMER_KEY"),
    consumer_secret=os.getenv("WC_CONSUMER_SECRET")
)

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "results": optimization_history.get_results()}
    )

@app.get("/optimize-content/")
def optimize_content(
    background_tasks: BackgroundTasks,
    max_products: int = None,
    start_page: int = 1,
    force_update: bool = False,
    use_trends: bool = None
):
    """Start the content optimization process"""
    if use_trends is not None:
        os.environ["USE_GOOGLE_TRENDS"] = str(use_trends).lower()
        # Reinitialize keyword research with new setting
        global keyword_research
        keyword_research = KeywordResearch()

    background_tasks.add_task(
        process_optimization, 
        wp_api, 
        max_products=max_products,
        start_page=start_page,
        force_update=force_update
    )
    return {
        "status": "success",
        "message": f"Content optimization started in the background. Max products: {max_products or 'All'}, "
                  f"Starting page: {start_page}, Force update: {force_update}, "
                  f"Using Google Trends: {os.getenv('USE_GOOGLE_TRENDS', 'true').lower() == 'true'}"
    }

@app.get("/results/")
def get_results():
    """Get optimization results"""
    return {
        "results": optimization_history.get_results()
    } 