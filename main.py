import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router


app = FastAPI(title="YM price parser")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=['GET', 'POST'],
    allow_headers=['*'],
)

app.include_router(router)


if __name__ == '__main__':
    uvicorn.run("main:app", host='127.0.0.1', port=5000, reload=True)