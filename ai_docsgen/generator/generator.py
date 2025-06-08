from ai_docsgen.schemas import Job, Project
from ai_docsgen.git.scm import Scm

def start_generation(project: Project, job: Job):
    gh_client = Scm(project.access_token)
    gh_client.get_repository_info