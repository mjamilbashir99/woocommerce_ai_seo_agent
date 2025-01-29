from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class OptimizationResult(BaseModel):
    product_id: int
    product_link: str
    product_name: str
    old_description: str
    new_description: str
    old_meta_description: Optional[str] = None
    meta_description: str
    old_keywords: Optional[str] = None
    keywords: str
    status: str
    timestamp: datetime

class OptimizationHistory:
    def __init__(self):
        self.results: List[OptimizationResult] = []

    def add_result(self, result: OptimizationResult):
        self.results.append(result)

    def get_results(self) -> List[OptimizationResult]:
        return self.results 