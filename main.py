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
from magic_link import confirm_user, generate_magic_number, verify_magic_number
from orm import MagicLink, User, db
from auth import (
    MagicNumberBody,
    UserInfo,
    create_access_token,
    get_current_user,
)
from send_magic_email import send_email_with_magic_code

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
async def sign_up(user_info: UserInfo):
    if db.query(User).filter_by(email=user_info.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )

    new_user = User(
        id=str(uuid.uuid4()),
        first_name=user_info.first_name,
        last_name=user_info.last_name,
        email=user_info.email,
        verified=False,
        created_at=datetime.now(),
    )
    magic_number = generate_magic_number()
    new_magic_number = MagicLink(
        code=magic_number,
        user_id=new_user.id,
        consumed=False,
    )
    db.add(new_user)
    db.add(new_magic_number)
    db.commit()
    send_email_with_magic_code(new_user, magic_number)
    return status.HTTP_200_OK


@app.post("/verify")
async def magic_number(response: Response, magic_number: MagicNumberBody):
    if not await verify_magic_number(magic_number.magic_number):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The code you entered is incorrect or has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email = await confirm_user(magic_number.magic_number)
    access_token = create_access_token(data={"sub": email})
    response.headers["Authorization"] = f"Bearer {access_token}"
    return status.HTTP_200_OK


@app.get("/protected")
def protected_route(json_user: str = Depends(get_current_user)):
    current_user = json.loads(json_user)
    return {
        "message": f"Hello {current_user['first_name']} {current_user['last_name']}"
    }
