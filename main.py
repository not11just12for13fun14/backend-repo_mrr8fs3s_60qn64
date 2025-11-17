import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "E-commerce Admin Backend Running"}

# Schemas endpoint to expose defined collections (used by tooling/consumers)
@app.get("/schema")
def get_schema():
    from schemas import User, Product, Category, Blog, SaleConfig
    return {
        "collections": [
            "user", "product", "category", "blog", "saleconfig"
        ],
        "models": {
            "user": User.model_json_schema(),
            "product": Product.model_json_schema(),
            "category": Category.model_json_schema(),
            "blog": Blog.model_json_schema(),
            "saleconfig": SaleConfig.model_json_schema(),
        }
    }

# Utility to convert ObjectId

def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")

# Generic CRUD helpers using Mongo directly (simple and explicit)

def list_items(collection: str, query: dict | None = None):
    return list(db[collection].find(query or {}).sort("_id", -1))

def get_item(collection: str, item_id: str):
    item = db[collection].find_one({"_id": to_object_id(item_id)})
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item

def create_item(collection: str, data: dict):
    data['created_at'] = data.get('created_at') or __import__('datetime').datetime.utcnow()
    data['updated_at'] = data.get('updated_at') or __import__('datetime').datetime.utcnow()
    res = db[collection].insert_one(data)
    return str(res.inserted_id)

def update_item(collection: str, item_id: str, data: dict):
    data['updated_at'] = __import__('datetime').datetime.utcnow()
    res = db[collection].update_one({"_id": to_object_id(item_id)}, {"$set": data})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return True

def delete_item(collection: str, item_id: str):
    res = db[collection].delete_one({"_id": to_object_id(item_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return True

# Users - minimal create endpoint for the "new user" form
class UserIn(BaseModel):
    name: str
    email: str
    address: str
    age: Optional[int] = None
    is_active: bool = True

@app.post("/users")
def create_user(user: UserIn):
    user_id = create_item("user", user.model_dump())
    return {"id": user_id}

# Products
class ProductIn(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
    sku: Optional[str] = None
    image_url: Optional[str] = None

@app.get("/products")
def get_products():
    return [{**p, "_id": str(p["_id"]) } for p in list_items("product")]

@app.post("/products")
def create_product(product: ProductIn):
    pid = create_item("product", product.model_dump())
    return {"id": pid}

@app.get("/products/{product_id}")
def get_product(product_id: str):
    p = get_item("product", product_id)
    p["_id"] = str(p["_id"]) 
    return p

@app.put("/products/{product_id}")
def update_product(product_id: str, payload: dict):
    update_item("product", product_id, payload)
    return {"success": True}

@app.delete("/products/{product_id}")
def delete_product(product_id: str):
    delete_item("product", product_id)
    return {"success": True}

# Categories
class CategoryIn(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True

@app.get("/categories")
def get_categories():
    return [{**c, "_id": str(c["_id"]) } for c in list_items("category")]

@app.post("/categories")
def create_category(category: CategoryIn):
    cid = create_item("category", category.model_dump())
    return {"id": cid}

@app.put("/categories/{category_id}")
def update_category(category_id: str, payload: dict):
    update_item("category", category_id, payload)
    return {"success": True}

@app.delete("/categories/{category_id}")
def delete_category(category_id: str):
    delete_item("category", category_id)
    return {"success": True}

# Blogs
class BlogIn(BaseModel):
    title: str
    content: str
    author: str
    is_published: bool = False

@app.get("/blogs")
def get_blogs():
    return [{**b, "_id": str(b["_id"]) } for b in list_items("blog")]

@app.post("/blogs")
def create_blog(blog: BlogIn):
    bid = create_item("blog", blog.model_dump())
    return {"id": bid}

@app.get("/blogs/{blog_id}")
def get_blog(blog_id: str):
    b = get_item("blog", blog_id)
    b["_id"] = str(b["_id"]) 
    return b

@app.put("/blogs/{blog_id}")
def update_blog(blog_id: str, payload: dict):
    update_item("blog", blog_id, payload)
    return {"success": True}

@app.delete("/blogs/{blog_id}")
def delete_blog(blog_id: str):
    delete_item("blog", blog_id)
    return {"success": True}

# Sales
class SaleConfigIn(BaseModel):
    global_sale_active: bool = False
    global_discount_percent: float = 0
    product_sales: Dict[str, float] = {}

@app.get("/sale")
def get_sale_config():
    doc = db["saleconfig"].find_one({})
    if not doc:
        return {
            "global_sale_active": False,
            "global_discount_percent": 0,
            "product_sales": {}
        }
    doc["_id"] = str(doc["_id"])
    # convert product_sales keys to strings (ObjectIds may be stored)
    if "product_sales" in doc:
        doc["product_sales"] = {str(k): v for k, v in doc["product_sales"].items()}
    return doc

@app.put("/sale")
def update_sale_config(cfg: SaleConfigIn):
    data = cfg.model_dump()
    data['updated_at'] = __import__('datetime').datetime.utcnow()
    db["saleconfig"].update_one({}, {"$set": data}, upsert=True)
    return {"success": True}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
