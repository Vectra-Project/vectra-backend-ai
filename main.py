from fastapi import FastAPI, UploadFile
from openai import OpenAI
from pydantic import BaseModel
from typing import BinaryIO, List
from dotenv import load_dotenv
import json
from mindee import Client, product

load_dotenv()

app = FastAPI()
client = OpenAI()


class ExperienceItem(BaseModel):
    job_title: str
    company: str
    description: List[str]


class Experiences(BaseModel):
    experience: List[ExperienceItem]


class Resume(BaseModel):
    skills: List[str]
    job_title: str
    company: str
    job_description: str


@app.post("/enhance_experience")
async def enhance_experience(experiences_input_json: Experiences):
    experiences_input = json.dumps(experiences_input_json.model_dump())

    file_path = "./Experience Section - System Prompt Vectra.txt"
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

    file_path = "./Skills Section - System Prompt Vectra.txt"
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


def cv_to_json(resume_binary: BinaryIO):
    mindee_client = Client()
    resume = mindee_client.source_from_bytes(resume_binary, "Resume.pdf")
    result = mindee_client.enqueue_and_parse(
        product.ResumeV1,
        resume,
    )
    return result.document
