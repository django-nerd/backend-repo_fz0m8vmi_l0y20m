import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

from database import create_document, get_documents
from schemas import Comment as CommentSchema

app = FastAPI(title="Wedding Invitation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CommentIn(BaseModel):
    name: str
    message: str
    attending: Optional[bool] = None
    guests: Optional[int] = 1
    phone: Optional[str] = None

class CommentOut(CommentIn):
    id: Optional[str] = None

@app.get("/")
def read_root():
    return {"message": "Wedding Invitation Backend is running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

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
        from database import db
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
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    response["apps_script_url"] = "✅ Set" if os.getenv("GOOGLE_APPS_SCRIPT_URL") else "❌ Not Set"
    return response

@app.get("/api/comments", response_model=List[CommentOut])
def list_comments(limit: int = 50):
    try:
        docs = get_documents("comment", {}, limit)
        results: List[CommentOut] = []
        for d in docs:
            results.append(CommentOut(
                id=str(d.get("_id")),
                name=d.get("name", ""),
                message=d.get("message", ""),
                attending=d.get("attending"),
                guests=d.get("guests"),
                phone=d.get("phone")
            ))
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def forward_to_google_sheet(payload: dict):
    """
    Forward comment to Google Sheet via Apps Script Web App.
    Set env GOOGLE_APPS_SCRIPT_URL to the deployed Web App URL.
    The Apps Script should accept JSON POST and append to a Sheet.
    """
    url = os.getenv("GOOGLE_APPS_SCRIPT_URL")
    if not url:
        return {"forwarded": False, "reason": "No GOOGLE_APPS_SCRIPT_URL configured"}
    try:
        resp = requests.post(url, json=payload, timeout=8)
        ok = resp.status_code in (200, 201)
        return {"forwarded": ok, "status": resp.status_code, "response": resp.text[:200]}
    except Exception as e:
        return {"forwarded": False, "reason": str(e)[:200]}

@app.post("/api/comments", response_model=CommentOut)
def create_comment(comment: CommentIn):
    try:
        # Validate using schema and save to DB
        validated = CommentSchema(**comment.model_dump())
        new_id = create_document("comment", validated)

        # Forward to Google Sheet (best-effort)
        sheet_meta = forward_to_google_sheet({
            "name": validated.name,
            "message": validated.message,
            "attending": validated.attending,
            "guests": validated.guests,
            "phone": validated.phone,
        })

        return CommentOut(id=new_id, **validated.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
