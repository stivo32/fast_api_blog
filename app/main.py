from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth.router import router as router_auth
from app.api.router import router as router_api
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

app.mount('/static', StaticFiles(directory='app/static'), name='static')


@app.get("/")
def home_page():
    return {
        "message": "Welcome! Let this template be a convenient tool for your work and bring you benefits!"
    }


app.include_router(router_auth)
app.include_router(router_api)
