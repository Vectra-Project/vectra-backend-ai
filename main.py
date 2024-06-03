from datetime import datetime
import uuid
from fastapi.responses import JSONResponse
from openai import OpenAI
from dotenv import load_dotenv
import json
from lib import cv_to_json, Experiences, Resume
from fastapi import FastAPI, HTTPException, status, Request, Response, UploadFile
from orm import User, create_session, delete_session, get_session, db
from auth import UserInfo, UserLogin, generate_password_hash, check_password


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
    return json.loads(response.choices[0].message.content)


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
    return json.loads(response.choices[0].message.content)


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
    session_id = create_session(new_user.user_id)
    response.set_cookie("session_id", session_id, httponly=True, max_age=3600)
    db.commit()
    return {"message": "User registered successfully"}


@app.post("/login")
async def login(response: Response, login_body: UserLogin):
    user = User.get_by_email(login_body.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email or password is incorrect",
        )
    if not check_password(login_body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email or password is incorrect",
        )

    session_id = create_session(user.user_id)
    response.set_cookie("session_id", session_id, httponly=True, max_age=3600)
    return JSONResponse(content={"message": "Login successful"})


@app.post("/logout")
def logout(request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    if session_id:
        delete_session(session_id)
        response.delete_cookie("session_id")
    return JSONResponse(content={"message": "Logout successful"})


@app.get("/protected")
def protected_route(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    user = get_session(session_id) if session_id else None
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    print(user)
    return {"message": f"Hello {user['first_name']} {user['last_name']}"}
