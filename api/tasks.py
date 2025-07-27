from celery import shared_task
from github import Github
from flowchart_ai.config import GIT_ACCESS_KEY, ORGANIZATION, GITHUB_TOKEN, GIT_USERNAME
from .models import Repository, Branch, RepositoryConfiguration
import redis
from django.conf import settings
import os
import shutil
from git import Repo
from flowchart_llm.llm_utils import generate_flowchart_from_code
import logging
from flowchart_ai.celery import app as celery_app

logger = logging.getLogger(__name__)

# Initialize Redis client
redis_url = settings.CELERY_BROKER_URL
redis_client = redis.from_url(redis_url)

LOCK_EXPIRE = 60 * 10  # Lock expires in 10 minutes

@shared_task
def fetch_and_save_repositories():
    lock_id = 'fetch_repositories_lock'
    
    # Acquire lock
    if redis_client.setnx(lock_id, 'locked'):
        redis_client.expire(lock_id, LOCK_EXPIRE)
        logger.info("Acquired lock for fetch_and_save_repositories task.")
        try:
            g = Github(GIT_ACCESS_KEY)
            org = g.get_organization(ORGANIZATION)
            repos = org.get_repos(type='all')
            logger.info(f"Fetching repositories for organization: {ORGANIZATION}")
            for repo_data in repos:
                logger.info(f"Processing repository: {repo_data.name}")
                repo, created = Repository.objects.update_or_create(
                    name=repo_data.name,
                    defaults={
                        'full_name': repo_data.full_name,
                        'private': repo_data.private,
                        'html_url': repo_data.html_url,
                        'description': repo_data.description,
                        'created_at': repo_data.created_at,
                        'updated_at': repo_data.updated_at,
                    }
                )
                logger.info(f"  Repository object used: {repo.name} (ID: {repo.id}), Created: {created}")

                # Fetch and save branches for the current repository
                logger.info(f"Fetching branches for {repo_data.name}")
                branches = repo_data.get_branches()
                if not branches:
                    logger.warning(f"No branches found for {repo_data.name}")
                for branch_data in branches:
                    branch, created_branch = Branch.objects.update_or_create(
                        repository=repo,
                        name=branch_data.name,
                    )
                    logger.info(f"  Saving branch: {branch.name} for repository: {repo.name} (ID: {repo.id}), Created/Updated: {created_branch}")
        finally:
            # Release lock
            redis_client.delete(lock_id)
            logger.info("Released lock for fetch_and_save_repositories task.")
    else:
        logger.info("Could not acquire lock for fetch_and_save_repositories task. Another instance is running.")


@shared_task(bind=True)
def start_flowchart_process(self, config_id):
    config = RepositoryConfiguration.objects.get(pk=config_id)
    repo_obj = config.repository
    main_branch = config.main_branch

    if not main_branch:
        config.status = 'FAILED'
        config.save()
        logger.error(f"Error: Main branch not configured for {repo_obj.name}")
        return f"Error: Main branch not configured for {repo_obj.name}"

    # Update status
    config.status = 'CLONING'
    config.process_id = self.request.id
    config.save()
    logger.info(f"Starting flowchart process for {repo_obj.name}. Task ID: {self.request.id}")

    clone_dir = f"/tmp/{repo_obj.name}_{self.request.id}"
    repo_url = f"https://{GIT_USERNAME}:{GITHUB_TOKEN}@github.com/{repo_obj.full_name}.git"

    try:
        # 1. Clone the repository
        logger.info(f"Cloning {repo_url} into {clone_dir}")
        if os.path.exists(clone_dir):
            shutil.rmtree(clone_dir)
            logger.info(f"Removed existing clone directory: {clone_dir}")
        repo = Repo.clone_from(repo_url, clone_dir, branch=main_branch.name)
        logger.info("Repository cloned successfully.")

        # 2. Process files and generate flowcharts
        config.status = 'PROCESSING'
        config.save()
        flowcharts_mermaid = {}
        logger.info("Processing files for flowchart generation.")
        for root, _, files in os.walk(clone_dir):
            for file in files:
                if file.endswith(('.py', '.js', '.java', '.c', '.cpp', '.go', '.ts')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        logger.info(f"Processing file: {file_path}")
                        mermaid_flowchart = generate_flowchart_from_code(content)
                        flowcharts_mermaid[file_path] = mermaid_flowchart
                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}")

        # 3. Generate README.md
        config.status = 'GENERATING_MD'
        config.save()
        logger.info("Generating README.md.")
        readme_content = "# Flowcharts for " + repo_obj.name + "\n\n"
        for file_path, mermaid_code in flowcharts_mermaid.items():
            relative_path = os.path.relpath(file_path, clone_dir)
            readme_content += f"## Flowchart for {relative_path}\n\n```mermaid\n{mermaid_code}\n```\n\n"

        readme_path = os.path.join(clone_dir, 'README.md')
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        logger.info("README.md generated.")

        # 4. Push to GitHub and create PR
        config.status = 'PUSHING'
        config.save()
        logger.info("Pushing to GitHub and creating PR.")

        repo.index.add(['README.md'])
        if repo.index.diff("HEAD"):
            new_branch_name = f"flowchart-ai-{main_branch.name}-{self.request.id[:8]}"
            repo.git.checkout(main_branch.name)
            repo.git.checkout('-b', new_branch_name)
            repo.index.commit("feat: Add flowcharts generated by Flowchart AI")
            repo.git.push('origin', new_branch_name, force=True) # Force push for simplicity in demo

            # Create PR using PyGithub
            g = Github(GITHUB_TOKEN)
            org = g.get_organization(ORGANIZATION)
            github_repo = org.get_repo(repo_obj.name)
            pr = github_repo.create_pull(title=f"feat: Flowcharts for {main_branch.name}",
                                         body="This PR adds auto-generated flowcharts for the main branch.",
                                         head=new_branch_name,
                                         base=main_branch.name)
            config.pr_url = pr.html_url
            config.status = 'PR_CREATED'
            logger.info(f"Pull Request created: {pr.html_url}")
        else:
            config.status = 'COMPLETED'
            logger.info("No changes to commit. README.md already up to date.")

        config.save()
        logger.info(f"Flowchart generation completed for {repo_obj.name}. PR: {config.pr_url}")
        return f"Flowchart generation completed for {repo_obj.name}. PR: {config.pr_url}"

    except Exception as e:
        config.status = 'FAILED'
        config.save()
        logger.error(f"Flowchart generation failed for {repo_obj.name}: {e}", exc_info=True)
        return f"Flowchart generation failed for {repo_obj.name}: {e}"
    finally:
        # Clean up cloned directory
        if os.path.exists(clone_dir):
            shutil.rmtree(clone_dir)
            logger.info(f"Cleaned up {clone_dir}")

@shared_task
def stop_flowchart_process(task_id):
    try:
        celery_app.control.revoke(task_id, terminate=True)
        logger.info(f"Revoked Celery task: {task_id}")
        return f"Task {task_id} revoked."
    except Exception as e:
        logger.error(f"Error revoking task {task_id}: {e}", exc_info=True)
        return f"Error revoking task {task_id}: {e}"