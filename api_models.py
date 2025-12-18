"""
Pydantic models for API request/response validation
Ensures strict schema compliance
"""

from pydantic import BaseModel, Field
from typing import List, Literal


class RecommendationRequest(BaseModel):
    """Request schema for recommendation endpoint"""
    query: str = Field(..., min_length=1, description="Natural language job description or requirements")
    top_k: int = Field(20, ge=1, le=50, description="Number of candidates to retrieve")
    final_count: int = Field(10, ge=5, le=10, description="Final recommendations to return")


class AssessmentResponse(BaseModel):
    """Single assessment in response"""
    name: str
    url: str
    adaptive_support: Literal["Yes", "No"]
    description: str
    duration: int  # in minutes
    remote_support: Literal["Yes", "No"]
    test_type: List[Literal["Knowledge & Skills", "Personality & Behavior"]]


class RecommendationResponse(BaseModel):
    """Response schema for recommendation endpoint"""
    recommended_assessments: List[AssessmentResponse]


class HealthResponse(BaseModel):
    """Health check response"""
    status: Literal["healthy", "unhealthy"]
    message: str = ""
