from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import dotenv_values
from database import engine
from src.users import models as model_user
from routes import users, auth

config = dotenv_values(".env")

app = FastAPI()

model_user.Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)
app.include_router(router=auth.router)
app.include_router(router=users.router)

@app.get('/', include_in_schema=False)
async def home():
    return {
        "description": "Communication API from store online",
        "framework":"FastAPI",
        "create_by":"Victor Apolinares"
    }

if __name__ == '__main__':
    uvicorn.run('main:app', host=config['HOST_APP'], port=int(config['PORT_APP']), log_level='info')
