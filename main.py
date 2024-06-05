from datetime import datetime
import uuid
from openai import OpenAI
from dotenv import load_dotenv
import json
from lib import cv_to_json, Experiences, Resume
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    status,
    Response,
    UploadFile,
)
from orm import User, db
from auth import (
    UserInfo,
    UserLogin,
    authenticate_user,
    create_access_token,
    generate_password_hash,
    get_current_user,
)

load_dotenv()

app = FastAPI()
client = OpenAI()


@app.post("/enhance_experience")
async def enhance_experience(experiences_input_json: Experiences):
    experiences_input = json.dumps(experiences_input_json.model_dump())

    file_path = "./system_prompts/Experience Section - System Prompt Vectra.txt"
    with open(file_path, "r") as file:
        experience_system_prompt_json = file.read()
    experience_system_prompt = json.dumps(experience_system_prompt_json)

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.7,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": experience_system_prompt},
            {"role": "user", "content": experiences_input},
        ],
    )
    content = response.choices[0].message.content
    if content is None:
        content = ""
    return json.loads(content)


@app.post("/suggest_skills")
async def suggest_skills(resume_json: Resume):
    resume = json.dumps(resume_json.model_dump())

    file_path = "./system_prompts/Skills Section - System Prompt Vectra.txt"
    with open(file_path, "r") as file:
        skills_system_prompt_json = file.read()
    skills_system_prompt = json.dumps(skills_system_prompt_json)

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": skills_system_prompt},
            {"role": "user", "content": resume},
        ],
    )
    content = response.choices[0].message.content
    if content is None:
        content = ""
    return json.loads(content)


@app.post("/resume_to_json")
async def test_resume_upload(resume_file: UploadFile):
    resume_binary = await resume_file.read()
    resume_json = cv_to_json(resume_binary)
    return resume_json


@app.post("/signup")
async def sign_up(response: Response, user_info: UserInfo):
    if User.get_by_email(user_info.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )

    user_info.password = generate_password_hash(user_info.password)

    new_user = User(
        user_id=str(uuid.uuid4()),
        first_name=user_info.first_name,
        last_name=user_info.last_name,
        email=user_info.email,
        password=user_info.password,
        created_at=datetime.now(),
    )
    db.add(new_user)
    db.commit()
    access_token = create_access_token(data={"sub": new_user.email})
    response.headers["Authorization"] = f"Bearer {access_token}"
    return status.HTTP_200_OK


@app.post("/token")
async def login(response: Response, login_body: UserLogin):
    user = await authenticate_user(login_body.email, login_body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    response.headers["Authorization"] = f"Bearer {access_token}"
    return status.HTTP_200_OK


@app.get("/protected")
def protected_route(json_user: str = Depends(get_current_user)):
    current_user = json.loads(json_user)
    return {
        "message": f"Hello {current_user['first_name']} {current_user['last_name']}"
    }
