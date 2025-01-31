from fastapi import FastAPI, Request, BackgroundTasks, Query, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from dotenv import load_dotenv
from wp_api import WordPressAPI
from worker import process_optimization, optimization_history

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Initialize WordPress API
wp_api = WordPressAPI(
    base_url=os.getenv("WP_BASE_URL"),
    consumer_key=os.getenv("WC_CONSUMER_KEY"),
    consumer_secret=os.getenv("WC_CONSUMER_SECRET")
)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "results": optimization_history.get_results()
        }
    )

@app.get("/optimize-content/")
async def optimize_content(
    request: Request,
    dry_run: bool = Query(True),
    start_page: int = Query(1, ge=1),
    max_products: int = Query(10, ge=1, le=50),
    force_update: bool = Query(False),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Optimize product content with pagination support"""
    try:
        # Get total number of products
        total_products = wp_api.get_total_products()
        total_pages = (total_products + max_products - 1) // max_products
        
        # Convert string 'true'/'false' to boolean if needed
        dry_run = str(dry_run).lower() == 'true'
        force_update = str(force_update).lower() == 'true'
        
        print(f"Running optimization with dry_run={dry_run}")  # Debug log
        
        # Process optimization
        results = process_optimization(
            wp_api=wp_api,
            max_products=max_products,
            start_page=start_page,
            force_update=force_update,
            dry_run=dry_run
        )
        
        # Get updated results
        updated_results = optimization_history.get_results()
        
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "results": updated_results,
                "current_page": start_page,
                "products_per_page": max_products,
                "total_products": total_products,
                "total_pages": total_pages,
                "products_processed": len(updated_results),
                "dry_run": dry_run,
                "force_update": force_update,
                "background": True
            }
        )
    except Exception as e:
        print(f"Error in optimize_content: {str(e)}")  # Debug log
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/results/", response_class=HTMLResponse)
async def show_results(request: Request):
    """Show optimization results"""
    results = optimization_history.get_results()
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "results": results,
            "products_processed": len(results)
        }
    ) 