from pydantic import BaseModel
from typing import List, Optional, Set
from datetime import datetime
from pathlib import Path
import json

class OptimizationResult(BaseModel):
    product_id: int
    product_name: str
    old_description: str
    new_description: str
    old_meta_description: Optional[str] = None
    meta_description: str
    old_keywords: Optional[str] = None
    keywords: str
    status: str
    timestamp: datetime = datetime.now()

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
        self.save_history()

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