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
from typing import Optional, List, Dict

# Users
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

# Products
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
    sku: Optional[str] = Field(None, description="Stock keeping unit")
    image_url: Optional[str] = Field(None, description="Image URL")

# Categories
class Category(BaseModel):
    name: str = Field(..., description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    is_active: bool = Field(True, description="Category active status")

# Blogs
class Blog(BaseModel):
    title: str = Field(..., description="Blog title")
    content: str = Field(..., description="Blog content (markdown or HTML)")
    author: str = Field(..., description="Author name")
    is_published: bool = Field(False, description="Publish status")

# Sale configuration (single document collection)
class SaleConfig(BaseModel):
    global_sale_active: bool = Field(False, description="Whether global sale is active")
    global_discount_percent: float = Field(0, ge=0, le=100, description="Global discount percent")
    # Map of product_id -> discount percent
    product_sales: Dict[str, float] = Field(default_factory=dict, description="Per-product sale percentages")

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
