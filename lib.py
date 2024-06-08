from pydantic import BaseModel
from typing import List
from mindee import Client, product  # type: ignore


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


def cv_to_json(resume_binary: bytes):
    mindee_client = Client()
    resume = mindee_client.source_from_bytes(resume_binary, "Resume.pdf")
    result = mindee_client.enqueue_and_parse(
        product.ResumeV1,  # type: ignore
        resume,
    )
    return result.document


def load_template(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def inject_variables(template, variables):
    for key, value in variables.items():
        template = template.replace(f"{{{key}}}", str(value))
    return template
