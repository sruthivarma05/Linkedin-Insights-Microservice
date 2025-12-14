from fastapi import FastAPI
from app.routes.page_routes import router as page_router

app = FastAPI()

app.include_router(page_router)
