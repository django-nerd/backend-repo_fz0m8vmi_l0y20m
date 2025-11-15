"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Wedding guestbook/comment schema
class Comment(BaseModel):
    """
    Guest comments and RSVPs
    Collection name: "comment"
    """
    name: str = Field(..., min_length=1, max_length=100, description="Guest name")
    message: str = Field(..., min_length=1, max_length=1000, description="祝福/Message")
    attending: Optional[bool] = Field(None, description="Is attending the wedding")
    guests: Optional[int] = Field(1, ge=0, le=20, description="Number of guests including the submitter")
    phone: Optional[str] = Field(None, max_length=30, description="Contact phone (optional)")
