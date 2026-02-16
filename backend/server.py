from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, Request, Response, UploadFile, File, Form
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import PyPDF2
import httpx
import base64
import io

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]


# Create the main app
app = FastAPI(title="GoGarvis API")
api_router = APIRouter(prefix="/api")

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# LLM Integration
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
chat_sessions = {}

# Secure LLM Proxy Endpoint
@api_router.post("/llm/proxy")
@limiter.limit("20/minute")
async def llm_proxy(request: Request, payload: dict = Body(...)):
    """Proxy LLM requests to Emergent/OpenAI using backend-only key."""
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="LLM API key not configured")
    prompt = payload.get("prompt")
    context = payload.get("context")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt required")
    # Forward to Emergent/OpenAI (example endpoint, adjust as needed)
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": "gpt-5.2", "messages": [{"role": "user", "content": prompt}], "context": context},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    data = resp.json()
    # Strip any keys/metadata
    return {"response": data.get("choices", [{}])[0].get("message", {}).get("content", "")}

# File upload storage
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

DOCS_PATH = Path("/app/docs/specs")

# ============== Auth Models ==============

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    role: str = "viewer"  # admin, editor, viewer
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserSession(BaseModel):
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============== Content Models ==============

class ContentVersion(BaseModel):
    version_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content_id: str
    content_type: str  # document, glossary, component, pigpen, brand
    data: Dict[str, Any]
    changed_by: str  # user_id
    changed_by_name: str
    change_type: str  # create, update, delete, rollback
    change_summary: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AuditLogEntry(BaseModel):
    log_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: str
    user_email: str
    action: str  # create, update, delete, rollback, login, logout
    content_type: str
    content_id: str
    content_title: str
    details: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Document(BaseModel):
    model_config = ConfigDict(extra="ignore")
    doc_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    title: str
    category: str
    description: str
    content: str = ""
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GlossaryTerm(BaseModel):
    model_config = ConfigDict(extra="ignore")
    term_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    term: str
    definition: str
    category: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SystemComponent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    component_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    status: str = "active"
    layer: int
    key_functions: List[str]
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PigPenOperator(BaseModel):
    model_config = ConfigDict(extra="ignore")
    operator_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tai_d: str  # TAI-D identifier
    name: str
    capabilities: str
    role: str
    authority: str
    status: str = "LOCKED"
    category: str  # Core Resolution, Business, Creative, Systems, Quality, Optional
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BrandProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    brand_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    primary_color: str = "#FF4500"
    secondary_color: str = "#1A1A1A"
    font_heading: str = "JetBrains Mono"
    font_body: str = "Manrope"
    logo_url: Optional[str] = None
    style_guidelines: str = ""
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============== Request Models ==============

class DocumentCreate(BaseModel):
    filename: str
    title: str
    category: str
    description: str
    content: str = ""

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None

class GlossaryTermCreate(BaseModel):
    term: str
    definition: str
    category: str

class GlossaryTermUpdate(BaseModel):
    term: Optional[str] = None
    definition: Optional[str] = None
    category: Optional[str] = None

class ComponentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    key_functions: Optional[List[str]] = None

class PigPenOperatorCreate(BaseModel):
    tai_d: str
    name: str
    capabilities: str
    role: str
    authority: str
    status: str = "LOCKED"
    category: str

class PigPenOperatorUpdate(BaseModel):
    name: Optional[str] = None
    capabilities: Optional[str] = None
    role: Optional[str] = None
    authority: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None

class BrandProfileCreate(BaseModel):
    name: str
    description: str
    primary_color: str = "#FF4500"
    secondary_color: str = "#1A1A1A"
    font_heading: str = "JetBrains Mono"
    font_body: str = "Manrope"
    logo_url: Optional[str] = None
    style_guidelines: str = ""

class BrandProfileUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    font_heading: Optional[str] = None
    font_body: Optional[str] = None
    logo_url: Optional[str] = None
    style_guidelines: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    file_ids: Optional[List[str]] = None  # List of uploaded file IDs to include

class ChatResponse(BaseModel):
    response: str
    session_id: str

class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    file_type: str
    size: int
    extracted_text: Optional[str] = None

class RoleUpdate(BaseModel):
    role: str

# ============== Auth Helpers ==============

async def get_current_user(request: Request) -> Optional[User]:
    """Get current user from session token in cookie or Authorization header"""
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    
    if not session_token:
        return None
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        return None
    
    expires_at = session["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        return None
    
    return User(**user)

async def require_auth(request: Request) -> User:
    """Require authenticated user"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

async def require_editor(request: Request) -> User:
    """Require editor or admin role"""
    user = await require_auth(request)
    if user.role not in ["admin", "editor"]:
        raise HTTPException(status_code=403, detail="Editor or admin role required")
    return user

async def require_admin(request: Request) -> User:
    """Require admin role"""
    user = await require_auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return user

# ============== Audit & Version Helpers ==============

async def log_audit(user: User, action: str, content_type: str, content_id: str, content_title: str, details: dict = {}):
    """Log an audit entry"""
    entry = AuditLogEntry(
        user_id=user.user_id,
        user_name=user.name,
        user_email=user.email,
        action=action,
        content_type=content_type,
        content_id=content_id,
        content_title=content_title,
        details=details
    )
    doc = entry.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    await db.audit_log.insert_one(doc)

async def save_version(user: User, content_type: str, content_id: str, data: dict, change_type: str, change_summary: str):
    """Save a version snapshot"""
    version = ContentVersion(
        content_id=content_id,
        content_type=content_type,
        data=data,
        changed_by=user.user_id,
        changed_by_name=user.name,
        change_type=change_type,
        change_summary=change_summary
    )
    doc = version.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    await db.content_versions.insert_one(doc)

# ============== Auth Routes ==============

@api_router.post("/auth/session")
async def create_session(request: Request, response: Response):
    """Exchange session_id for session_token"""
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    # Call Emergent Auth to get user data
    async with httpx.AsyncClient() as client:
        auth_response = await client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
    
    if auth_response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session_id")
    
    user_data = auth_response.json()
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data["email"]}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        # Update user data
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": user_data["name"], "picture": user_data.get("picture")}}
        )
        role = existing_user.get("role", "viewer")
    else:
        # Create new user
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        # First user becomes admin
        user_count = await db.users.count_documents({})
        role = "admin" if user_count == 0 else "viewer"
        
        new_user = {
            "user_id": user_id,
            "email": user_data["email"],
            "name": user_data["name"],
            "picture": user_data.get("picture"),
            "role": role,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(new_user)
    
    # Create session
    session_token = user_data.get("session_token") or f"session_{uuid.uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    await db.user_sessions.delete_many({"user_id": user_id})
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    
    # Log audit
    user = User(user_id=user_id, email=user_data["email"], name=user_data["name"], role=role)
    await log_audit(user, "login", "auth", user_id, user_data["name"])
    
    return {
        "user_id": user_id,
        "email": user_data["email"],
        "name": user_data["name"],
        "picture": user_data.get("picture"),
        "role": role
    }

@api_router.get("/auth/me")
async def get_me(request: Request):
    """Get current user"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "user_id": user.user_id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "role": user.role
    }

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout user"""
    user = await get_current_user(request)
    if user:
        await db.user_sessions.delete_many({"user_id": user.user_id})
        await log_audit(user, "logout", "auth", user.user_id, user.name)
    
    response.delete_cookie(key="session_token", path="/")
    return {"message": "Logged out"}

# ============== User Management Routes (Admin) ==============

@api_router.get("/admin/users")
async def list_users(request: Request):
    """List all users (admin only)"""
    await require_admin(request)
    users = await db.users.find({}, {"_id": 0}).to_list(1000)
    return {"users": users}

@api_router.put("/admin/users/{user_id}/role")
async def update_user_role(user_id: str, role_update: RoleUpdate, request: Request):
    """Update user role (admin only)"""
    admin = await require_admin(request)
    
    if role_update.role not in ["admin", "editor", "viewer"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_role = user.get("role", "viewer")
    await db.users.update_one({"user_id": user_id}, {"$set": {"role": role_update.role}})
    
    await log_audit(admin, "update", "user", user_id, user["name"], {"old_role": old_role, "new_role": role_update.role})
    
    return {"message": "Role updated", "user_id": user_id, "role": role_update.role}

# ============== Audit Log Routes ==============

@api_router.get("/audit-log")
async def get_audit_log(
    request: Request,
    content_type: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 100
):
    """Get audit log entries"""
    await require_auth(request)
    
    query = {}
    if content_type:
        query["content_type"] = content_type
    if user_id:
        query["user_id"] = user_id
    
    entries = await db.audit_log.find(query, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    return {"entries": entries, "total": len(entries)}

# ============== Version History Routes ==============

@api_router.get("/versions/{content_type}/{content_id}")
async def get_versions(content_type: str, content_id: str, request: Request):
    """Get version history for content"""
    await require_auth(request)
    
    versions = await db.content_versions.find(
        {"content_type": content_type, "content_id": content_id},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(100)
    
    return {"versions": versions}

@api_router.post("/versions/{content_type}/{content_id}/rollback/{version_id}")
async def rollback_version(content_type: str, content_id: str, version_id: str, request: Request):
    """Rollback to a specific version"""
    user = await require_editor(request)
    
    version = await db.content_versions.find_one(
        {"version_id": version_id, "content_type": content_type, "content_id": content_id},
        {"_id": 0}
    )
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Get collection name
    collection_map = {
        "document": "documents",
        "glossary": "glossary_terms",
        "component": "components",
        "pigpen": "pigpen_operators",
        "brand": "brand_profiles"
    }
    
    collection_name = collection_map.get(content_type)
    if not collection_name:
        raise HTTPException(status_code=400, detail="Invalid content type")
    
    # Get current state before rollback
    id_field = f"{content_type}_id" if content_type != "document" else "doc_id"
    current = await db[collection_name].find_one({id_field: content_id}, {"_id": 0})
    
    # Save current state as a version
    if current:
        await save_version(user, content_type, content_id, current, "rollback", f"State before rollback to {version_id[:8]}")
    
    # Apply rollback
    rollback_data = version["data"].copy()
    rollback_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db[collection_name].update_one({id_field: content_id}, {"$set": rollback_data})
    
    # Save rollback version
    await save_version(user, content_type, content_id, rollback_data, "rollback", f"Rolled back to version {version_id[:8]}")
    
    # Log audit
    await log_audit(user, "rollback", content_type, content_id, rollback_data.get("title") or rollback_data.get("name") or rollback_data.get("term", "Unknown"), {"version_id": version_id})
    
    return {"message": "Rollback successful", "version_id": version_id}

# ============== Document Routes ==============

@api_router.get("/documents")
async def get_documents(category: Optional[str] = None, search: Optional[str] = None):
    documents = await db.documents.find({"is_active": True}, {"_id": 0}).to_list(1000)
    
    if category and category != "all":
        documents = [d for d in documents if d.get("category", "").lower() == category.lower()]
    
    if search:
        search_lower = search.lower()
        documents = [d for d in documents if search_lower in d.get("title", "").lower() or search_lower in d.get("description", "").lower()]
    
    return {"documents": documents, "total": len(documents)}

@api_router.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    doc = await db.documents.find_one({"doc_id": doc_id, "is_active": True}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@api_router.post("/documents")
async def create_document(doc: DocumentCreate, request: Request):
    user = await require_editor(request)
    
    new_doc = Document(**doc.model_dump())
    doc_dict = new_doc.model_dump()
    doc_dict["created_at"] = doc_dict["created_at"].isoformat()
    doc_dict["updated_at"] = doc_dict["updated_at"].isoformat()
    
    await db.documents.insert_one(doc_dict)
    await save_version(user, "document", new_doc.doc_id, doc_dict, "create", f"Created document: {doc.title}")
    await log_audit(user, "create", "document", new_doc.doc_id, doc.title)
    
    return {"message": "Document created", "doc_id": new_doc.doc_id}

@api_router.put("/documents/{doc_id}")
async def update_document(doc_id: str, update: DocumentUpdate, request: Request):
    user = await require_editor(request)
    
    doc = await db.documents.find_one({"doc_id": doc_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Save current version
    await save_version(user, "document", doc_id, doc, "update", f"Before update: {doc.get('title')}")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.documents.update_one({"doc_id": doc_id}, {"$set": update_data})
    
    # Get updated doc for version
    updated_doc = await db.documents.find_one({"doc_id": doc_id}, {"_id": 0})
    await save_version(user, "document", doc_id, updated_doc, "update", f"Updated document: {updated_doc.get('title')}")
    await log_audit(user, "update", "document", doc_id, updated_doc.get("title"), {"changes": list(update_data.keys())})
    
    return {"message": "Document updated", "doc_id": doc_id}

@api_router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, request: Request):
    user = await require_editor(request)
    
    doc = await db.documents.find_one({"doc_id": doc_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    await save_version(user, "document", doc_id, doc, "delete", f"Deleted document: {doc.get('title')}")
    await db.documents.update_one({"doc_id": doc_id}, {"$set": {"is_active": False}})
    await log_audit(user, "delete", "document", doc_id, doc.get("title"))
    
    return {"message": "Document deleted", "doc_id": doc_id}

@api_router.get("/documents/categories/list")
async def get_document_categories():
    documents = await db.documents.find({"is_active": True}, {"_id": 0, "category": 1}).to_list(1000)
    categories = list(set(d.get("category") for d in documents if d.get("category")))
    return {"categories": sorted(categories)}

# ============== Glossary Routes ==============

@api_router.get("/glossary")
async def get_glossary(category: Optional[str] = None, search: Optional[str] = None):
    terms = await db.glossary_terms.find({"is_active": True}, {"_id": 0}).to_list(1000)
    
    if category and category != "all":
        terms = [t for t in terms if t.get("category", "").lower() == category.lower()]
    
    if search:
        search_lower = search.lower()
        terms = [t for t in terms if search_lower in t.get("term", "").lower() or search_lower in t.get("definition", "").lower()]
    
    return {"terms": terms, "total": len(terms)}

@api_router.post("/glossary")
async def create_glossary_term(term: GlossaryTermCreate, request: Request):
    user = await require_editor(request)
    
    new_term = GlossaryTerm(**term.model_dump())
    term_dict = new_term.model_dump()
    term_dict["created_at"] = term_dict["created_at"].isoformat()
    term_dict["updated_at"] = term_dict["updated_at"].isoformat()
    
    await db.glossary_terms.insert_one(term_dict)
    await save_version(user, "glossary", new_term.term_id, term_dict, "create", f"Created term: {term.term}")
    await log_audit(user, "create", "glossary", new_term.term_id, term.term)
    
    return {"message": "Term created", "term_id": new_term.term_id}

@api_router.put("/glossary/{term_id}")
async def update_glossary_term(term_id: str, update: GlossaryTermUpdate, request: Request):
    user = await require_editor(request)
    
    term = await db.glossary_terms.find_one({"term_id": term_id}, {"_id": 0})
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    
    await save_version(user, "glossary", term_id, term, "update", f"Before update: {term.get('term')}")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.glossary_terms.update_one({"term_id": term_id}, {"$set": update_data})
    
    updated_term = await db.glossary_terms.find_one({"term_id": term_id}, {"_id": 0})
    await save_version(user, "glossary", term_id, updated_term, "update", f"Updated term: {updated_term.get('term')}")
    await log_audit(user, "update", "glossary", term_id, updated_term.get("term"), {"changes": list(update_data.keys())})
    
    return {"message": "Term updated", "term_id": term_id}

@api_router.delete("/glossary/{term_id}")
async def delete_glossary_term(term_id: str, request: Request):
    user = await require_editor(request)
    
    term = await db.glossary_terms.find_one({"term_id": term_id}, {"_id": 0})
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    
    await save_version(user, "glossary", term_id, term, "delete", f"Deleted term: {term.get('term')}")
    await db.glossary_terms.update_one({"term_id": term_id}, {"$set": {"is_active": False}})
    await log_audit(user, "delete", "glossary", term_id, term.get("term"))
    
    return {"message": "Term deleted", "term_id": term_id}

@api_router.get("/glossary/categories")
async def get_glossary_categories():
    terms = await db.glossary_terms.find({"is_active": True}, {"_id": 0, "category": 1}).to_list(1000)
    categories = list(set(t.get("category") for t in terms if t.get("category")))
    return {"categories": sorted(categories)}

# ============== Architecture Components Routes ==============

@api_router.get("/architecture/components")
async def get_components():
    components = await db.components.find({"is_active": True}, {"_id": 0}).sort("layer", 1).to_list(100)
    return {"components": components}

@api_router.put("/architecture/components/{component_id}")
async def update_component(component_id: str, update: ComponentUpdate, request: Request):
    user = await require_editor(request)
    
    component = await db.components.find_one({"component_id": component_id}, {"_id": 0})
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    
    await save_version(user, "component", component_id, component, "update", f"Before update: {component.get('name')}")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.components.update_one({"component_id": component_id}, {"$set": update_data})
    
    updated_component = await db.components.find_one({"component_id": component_id}, {"_id": 0})
    await save_version(user, "component", component_id, updated_component, "update", f"Updated component: {updated_component.get('name')}")
    await log_audit(user, "update", "component", component_id, updated_component.get("name"), {"changes": list(update_data.keys())})
    
    return {"message": "Component updated", "component_id": component_id}

# ============== Pig Pen Operators Routes ==============
# CANONICAL PROTECTION: Operators with is_canonical=True can ONLY be modified by sovereign (TSID-0001)
# Users can ADD new operators, but cannot edit/delete canonical ones

SOVEREIGN_EMAIL = "jonpearlandpig@gmail.com"  # Founder email for sovereign access

async def check_canonical_access(user: User, operator: dict, action: str):
    """Check if user can modify a canonical operator"""
    if operator.get("is_canonical", False):
        # Only sovereign can modify canonical operators
        if user.email != SOVEREIGN_EMAIL:
            raise HTTPException(
                status_code=403, 
                detail=f"CANONICAL PROTECTION: Cannot {action} canonical operator '{operator.get('name')}'. Only sovereign authority (TSID-0001) can modify canonical operators."
            )

@api_router.get("/pigpen")
async def get_pigpen_operators(category: Optional[str] = None):
    query = {"is_active": True}
    if category and category != "all":
        query["category"] = category
    
    operators = await db.pigpen_operators.find(query, {"_id": 0}).sort([("decision_weight", -1), ("tai_d", 1)]).to_list(200)
    
    # Count canonical vs user-added
    canonical_count = sum(1 for o in operators if o.get("is_canonical", False))
    user_count = len(operators) - canonical_count
    
    return {
        "operators": operators, 
        "total": len(operators),
        "canonical_count": canonical_count,
        "user_count": user_count
    }

@api_router.get("/pigpen/{operator_id}")
async def get_pigpen_operator(operator_id: str):
    operator = await db.pigpen_operators.find_one({"operator_id": operator_id, "is_active": True}, {"_id": 0})
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")
    return operator

@api_router.post("/pigpen")
async def create_pigpen_operator(operator: PigPenOperatorCreate, request: Request):
    user = await require_editor(request)
    
    # Check if TAI-D already exists
    existing = await db.pigpen_operators.find_one({"tai_d": operator.tai_d})
    if existing:
        raise HTTPException(status_code=400, detail=f"Operator with TAI-D '{operator.tai_d}' already exists")
    
    new_operator = PigPenOperator(**operator.model_dump())
    op_dict = new_operator.model_dump()
    op_dict["is_canonical"] = False  # User-created operators are NEVER canonical
    op_dict["decision_weight"] = op_dict.get("decision_weight", 1)  # Default low weight
    op_dict["created_at"] = op_dict["created_at"].isoformat()
    op_dict["updated_at"] = op_dict["updated_at"].isoformat()
    
    await db.pigpen_operators.insert_one(op_dict)
    await save_version(user, "pigpen", new_operator.operator_id, op_dict, "create", f"Created operator: {operator.name}")
    await log_audit(user, "create", "pigpen", new_operator.operator_id, operator.name, {"is_canonical": False})
    
    return {"message": "Operator created", "operator_id": new_operator.operator_id, "is_canonical": False}

@api_router.put("/pigpen/{operator_id}")
async def update_pigpen_operator(operator_id: str, update: PigPenOperatorUpdate, request: Request):
    user = await require_editor(request)
    
    operator = await db.pigpen_operators.find_one({"operator_id": operator_id}, {"_id": 0})
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")
    
    # CANONICAL PROTECTION CHECK
    await check_canonical_access(user, operator, "edit")
    
    await save_version(user, "pigpen", operator_id, operator, "update", f"Before update: {operator.get('name')}")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.pigpen_operators.update_one({"operator_id": operator_id}, {"$set": update_data})
    
    updated_op = await db.pigpen_operators.find_one({"operator_id": operator_id}, {"_id": 0})
    await save_version(user, "pigpen", operator_id, updated_op, "update", f"Updated operator: {updated_op.get('name')}")
    await log_audit(user, "update", "pigpen", operator_id, updated_op.get("name"), {"changes": list(update_data.keys())})
    
    return {"message": "Operator updated", "operator_id": operator_id}

@api_router.delete("/pigpen/{operator_id}")
async def delete_pigpen_operator(operator_id: str, request: Request):
    user = await require_editor(request)
    
    operator = await db.pigpen_operators.find_one({"operator_id": operator_id}, {"_id": 0})
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")
    
    # CANONICAL PROTECTION CHECK
    await check_canonical_access(user, operator, "delete")
    
    await save_version(user, "pigpen", operator_id, operator, "delete", f"Deleted operator: {operator.get('name')}")
    await db.pigpen_operators.update_one({"operator_id": operator_id}, {"$set": {"is_active": False}})
    await log_audit(user, "delete", "pigpen", operator_id, operator.get("name"))
    
    return {"message": "Operator deleted", "operator_id": operator_id}

@api_router.get("/pigpen/categories/list")
async def get_pigpen_categories():
    operators = await db.pigpen_operators.find({"is_active": True}, {"_id": 0, "category": 1}).to_list(100)
    categories = list(set(o.get("category") for o in operators if o.get("category")))
    return {"categories": sorted(categories)}

# ============== Brand Profiles Routes ==============

@api_router.get("/brands")
async def get_brand_profiles():
    brands = await db.brand_profiles.find({"is_active": True}, {"_id": 0}).to_list(100)
    return {"brands": brands, "total": len(brands)}

@api_router.get("/brands/{brand_id}")
async def get_brand_profile(brand_id: str):
    brand = await db.brand_profiles.find_one({"brand_id": brand_id, "is_active": True}, {"_id": 0})
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand

@api_router.post("/brands")
async def create_brand_profile(brand: BrandProfileCreate, request: Request):
    user = await require_editor(request)
    
    new_brand = BrandProfile(**brand.model_dump())
    brand_dict = new_brand.model_dump()
    brand_dict["created_at"] = brand_dict["created_at"].isoformat()
    brand_dict["updated_at"] = brand_dict["updated_at"].isoformat()
    
    await db.brand_profiles.insert_one(brand_dict)
    await save_version(user, "brand", new_brand.brand_id, brand_dict, "create", f"Created brand: {brand.name}")
    await log_audit(user, "create", "brand", new_brand.brand_id, brand.name)
    
    return {"message": "Brand created", "brand_id": new_brand.brand_id}

@api_router.put("/brands/{brand_id}")
async def update_brand_profile(brand_id: str, update: BrandProfileUpdate, request: Request):
    user = await require_editor(request)
    
    brand = await db.brand_profiles.find_one({"brand_id": brand_id}, {"_id": 0})
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    await save_version(user, "brand", brand_id, brand, "update", f"Before update: {brand.get('name')}")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.brand_profiles.update_one({"brand_id": brand_id}, {"$set": update_data})
    
    updated_brand = await db.brand_profiles.find_one({"brand_id": brand_id}, {"_id": 0})
    await save_version(user, "brand", brand_id, updated_brand, "update", f"Updated brand: {updated_brand.get('name')}")
    await log_audit(user, "update", "brand", brand_id, updated_brand.get("name"), {"changes": list(update_data.keys())})
    
    return {"message": "Brand updated", "brand_id": brand_id}

@api_router.delete("/brands/{brand_id}")
async def delete_brand_profile(brand_id: str, request: Request):
    user = await require_editor(request)
    
    brand = await db.brand_profiles.find_one({"brand_id": brand_id}, {"_id": 0})
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    await save_version(user, "brand", brand_id, brand, "delete", f"Deleted brand: {brand.get('name')}")
    await db.brand_profiles.update_one({"brand_id": brand_id}, {"$set": {"is_active": False}})
    await log_audit(user, "delete", "brand", brand_id, brand.get("name"))
    
    return {"message": "Brand deleted", "brand_id": brand_id}

# ============== Chat Routes ==============

SYSTEM_MESSAGE = """You are GARVIS AI, the sovereign intelligence assistant for the GoGarvis Full Stack architecture. You are knowledgeable about:

**Core Systems:**
- GARVIS: Sovereign intelligence and enforcement layer
- Telauthorium: Authorship, provenance, and rights registry
- Flightpath COS: Creative law and phase discipline (SPARK → BUILD → LAUNCH → EXPAND → EVERGREEN → SUNSET)
- MOSE: Multi-Operator Systems Engine for routing and orchestration
- Pig Pen: Registry of non-human cognition operators (TAI-D)
- TELA: Trusted Efficiency Liaison Assistant for execution
- ECOS: Enterprise Creative Operating System for tenant deployments

**Authority Flow:**
Authority flows from top to bottom: SOVEREIGN AUTHORITY → TELAUTHORIUM → GARVIS → FLIGHTPATH COS → MOSE → PIG PEN → TELA
No component below can override one above. Execution only happens at TELA.

**Identity Types:**
- TID: Telauthorium ID for objects
- TAID: Telauthorium Authority ID for humans
- TAI-D: Telauthorium AI-D for AI operators
- TSID: Telauthorium Sovereign ID for the founder

You provide authoritative answers about the system architecture, help users understand concepts, and guide them through the documentation. Respond in a professional, precise manner befitting a sovereign intelligence system."""

# ============== File Upload Helpers ==============

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return ""

def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """Extract text from text-based files"""
    try:
        if filename.lower().endswith('.pdf'):
            return extract_text_from_pdf(file_content)
        elif filename.lower().endswith(('.txt', '.md')):
            return file_content.decode('utf-8', errors='ignore')
        return ""
    except Exception as e:
        logger.error(f"Text extraction error: {e}")
        return ""

def get_mime_type(filename: str) -> str:
    """Get MIME type from filename"""
    ext = filename.lower().split('.')[-1]
    mime_types = {
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'webp': 'image/webp',
        'pdf': 'application/pdf',
        'txt': 'text/plain',
        'md': 'text/markdown'
    }
    return mime_types.get(ext, 'application/octet-stream')

def is_image_file(filename: str) -> bool:
    """Check if file is an image"""
    return filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))

# ============== File Upload Routes ==============

@api_router.post("/chat/upload", response_model=List[FileUploadResponse])
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload multiple files for chat context"""
    results = []
    
    for file in files:
        # Validate file extension
        allowed_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.pdf', '.txt', '.md')
        if not file.filename.lower().endswith(allowed_extensions):
            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed: {file.filename}. Allowed: {allowed_extensions}"
            )
        
        # Read file content
        content = await file.read()
        
        # Validate file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large: {file.filename}. Max size: 50MB"
            )
        
        # Generate file ID and save
        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Extract text for documents
        extracted_text = None
        if not is_image_file(file.filename):
            extracted_text = extract_text_from_file(content, file.filename)
            if extracted_text and len(extracted_text) > 10000:
                extracted_text = extracted_text[:10000] + "... [truncated]"
        
        # Store file metadata in DB
        file_doc = {
            "file_id": file_id,
            "filename": file.filename,
            "file_type": get_mime_type(file.filename),
            "size": len(content),
            "path": str(file_path),
            "is_image": is_image_file(file.filename),
            "extracted_text": extracted_text,
            "uploaded_at": datetime.now(timezone.utc).isoformat()
        }
        await db.chat_files.insert_one(file_doc)
        
        results.append(FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            file_type=get_mime_type(file.filename),
            size=len(content),
            extracted_text=extracted_text[:500] + "..." if extracted_text and len(extracted_text) > 500 else extracted_text
        ))
    
    return results

@api_router.get("/chat/files/{file_id}")
async def get_file_info(file_id: str):
    """Get file metadata"""
    file_doc = await db.chat_files.find_one({"file_id": file_id}, {"_id": 0})
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found")
    return file_doc

@api_router.delete("/chat/files/{file_id}")
async def delete_file(file_id: str):
    """Delete uploaded file"""
    file_doc = await db.chat_files.find_one({"file_id": file_id})
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete file from disk
    file_path = Path(file_doc["path"])
    if file_path.exists():
        file_path.unlink()
    
    # Delete from DB
    await db.chat_files.delete_one({"file_id": file_id})
    return {"message": "File deleted", "file_id": file_id}

# ============== Chat Routes ==============

@api_router.post("/chat", response_model=ChatResponse)
async def chat_with_garvis(request_body: ChatRequest):
    session_id = request_body.session_id or str(uuid.uuid4())
    
    if session_id not in chat_sessions:
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="LLM API key not configured")
        
        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message=SYSTEM_MESSAGE
        ).with_model("openai", "gpt-5.2")
        
        chat_sessions[session_id] = chat
    
    chat = chat_sessions[session_id]
    
    try:
        # Build message with file attachments
        message_text = request_body.message
        image_contents = []
        
        if request_body.file_ids:
            document_context = []
            
            for file_id in request_body.file_ids:
                file_doc = await db.chat_files.find_one({"file_id": file_id})
                if not file_doc:
                    continue
                
                if file_doc.get("is_image"):
                    # Load image and convert to base64
                    file_path = Path(file_doc["path"])
                    if file_path.exists():
                        with open(file_path, 'rb') as f:
                            image_data = f.read()
                        image_base64 = base64.b64encode(image_data).decode('utf-8')
                        image_contents.append(ImageContent(image_base64=image_base64))
                else:
                    # Add document text to context
                    if file_doc.get("extracted_text"):
                        document_context.append(f"[Document: {file_doc['filename']}]\n{file_doc['extracted_text']}")
            
            # Prepend document context to message
            if document_context:
                context_text = "\n\n".join(document_context)
                message_text = f"Context from uploaded documents:\n{context_text}\n\nUser question: {request_body.message}"
        
        # Create user message with optional images
        if image_contents:
            user_message = UserMessage(text=message_text, images=image_contents)
        else:
            user_message = UserMessage(text=message_text)
        
        response = await chat.send_message(user_message)
        
        # Store chat history with file references
        await db.chat_history.insert_one({
            "session_id": session_id,
            "role": "user",
            "content": request_body.message,
            "file_ids": request_body.file_ids or [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        await db.chat_history.insert_one({
            "session_id": session_id,
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return ChatResponse(response=response, session_id=session_id)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@api_router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    messages = await db.chat_history.find({"session_id": session_id}, {"_id": 0}).sort("timestamp", 1).to_list(100)
    return {"messages": messages, "session_id": session_id}

@api_router.delete("/chat/session/{session_id}")
async def clear_chat_session(session_id: str):
    if session_id in chat_sessions:
        del chat_sessions[session_id]
    await db.chat_history.delete_many({"session_id": session_id})
    return {"message": "Session cleared", "session_id": session_id}

# ============== Dashboard Stats ==============

@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    doc_count = await db.documents.count_documents({"is_active": True})
    term_count = await db.glossary_terms.count_documents({"is_active": True})
    component_count = await db.components.count_documents({"is_active": True})
    operator_count = await db.pigpen_operators.count_documents({"is_active": True})
    brand_count = await db.brand_profiles.count_documents({"is_active": True})
    
    return {
        "total_documents": doc_count,
        "total_glossary_terms": term_count,
        "total_components": component_count,
        "total_pigpen_operators": operator_count,
        "total_brand_profiles": brand_count,
        "active_components": component_count,
        "system_status": "OPERATIONAL",
        "authority_chain": "INTACT"
    }

# ============== Health & Root ==============

@api_router.get("/")
async def root():
    return {"message": "GoGarvis API", "version": "2.0.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
