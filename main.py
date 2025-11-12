import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import create_document, get_documents, db
from schemas import Product

app = FastAPI(title="Karachi Couture API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Karachi Couture Backend is running"}

@app.get("/api/hello")
def hello():
    return {"message": "Welcome to Karachi Couture API"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
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
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
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

    # Final env check
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# Utility: expose schemas for tooling
@app.get("/schema")
def get_schema():
    return {
        "product": Product.model_json_schema(),
    }

# ------------------ Products Endpoints ------------------

class ProductCreate(Product):
    image: Optional[str] = None

@app.get("/api/products", response_model=List[dict])
def list_products(category: Optional[str] = None, limit: int = 50):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    filt = {"category": category} if category else {}
    docs = get_documents("product", filt, min(limit, 100))
    # Convert ObjectId to string for response
    for d in docs:
        if "_id" in d:
            d["id"] = str(d.pop("_id"))
    return docs

@app.post("/api/products")
def create_product(product: ProductCreate):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    data = product.model_dump()
    new_id = create_document("product", data)
    return {"id": new_id, "ok": True}

@app.post("/api/seed")
def seed_products():
    """Seed a curated set of Pakistani/Karachi outfits if collection is empty"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    existing = db["product"].count_documents({})
    if existing > 0:
        return {"ok": True, "message": "Products already exist", "count": existing}

    items = [
        {
            "title": "Embroidered Lawn Suit - Karachi Breeze",
            "description": "3-piece unstitched lawn with chiffon dupatta, floral threadwork inspired by Clifton sunsets.",
            "price": 39.99,
            "category": "Women",
            "in_stock": True,
            "image": "https://images.unsplash.com/photo-1593030253490-1540f48f5c3b?q=80&w=1200&auto=format&fit=crop"
        },
        {
            "title": "Men's Kurta - Old City Olive",
            "description": "Classic cotton kurta with band collar, comfortable for humid Karachi evenings.",
            "price": 24.99,
            "category": "Men",
            "in_stock": True,
            "image": "https://images.unsplash.com/photo-1542060748-10c28b62716a?q=80&w=1200&auto=format&fit=crop"
        },
        {
            "title": "Festive Shalwar Kameez - Eid Edition",
            "description": "Rich jacquard fabric with subtle zari, perfect for festive dinners at Burns Road.",
            "price": 59.0,
            "category": "Women",
            "in_stock": True,
            "image": "https://images.unsplash.com/photo-1596421250711-9ec0ef9a3e6a?q=80&w=1200&auto=format&fit=crop"
        },
        {
            "title": "Casual Kurti - Sea View Sky",
            "description": "Breathable cotton kurti with pastel palette inspired by Sea View mornings.",
            "price": 19.99,
            "category": "Women",
            "in_stock": True,
            "image": "https://images.unsplash.com/photo-1616596875243-8c7e89e1a3fd?q=80&w=1200&auto=format&fit=crop"
        },
        {
            "title": "Men's Waistcoat - Saddar Slate",
            "description": "Versatile waistcoat to elevate any kurta look.",
            "price": 34.5,
            "category": "Men",
            "in_stock": True,
            "image": "https://images.unsplash.com/photo-1544006659-f0b21884ce1d?q=80&w=1200&auto=format&fit=crop"
        },
        {
            "title": "Kids Shalwar Kameez - Mini Maroon",
            "description": "Soft cotton blend, easy-care for the little ones.",
            "price": 14.99,
            "category": "Kids",
            "in_stock": True,
            "image": "https://images.unsplash.com/photo-1621784563330-dfd31e50f58e?q=80&w=1200&auto=format&fit=crop"
        },
    ]

    for item in items:
        create_document("product", item)

    count = db["product"].count_documents({})
    return {"ok": True, "message": "Seeded sample Karachi styles", "count": count}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
