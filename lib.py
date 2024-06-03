from pydantic import BaseModel
from typing import BinaryIO, List
from mindee import Client, product


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


def cv_to_json(resume_binary: BinaryIO):
    mindee_client = Client()
    resume = mindee_client.source_from_bytes(resume_binary, "Resume.pdf")
    result = mindee_client.enqueue_and_parse(
        product.ResumeV1,
        resume,
    )
    return result.document
