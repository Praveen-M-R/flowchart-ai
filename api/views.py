from django.http import JsonResponse
from github import Github
from flowchart_ai.config import GIT_ACCESS_KEY, ORGANIZATION

def list_repositories(request):
    g = Github(GIT_ACCESS_KEY)
    org = g.get_organization(ORGANIZATION)
    repos = org.get_repos(type='all')
    repo_list = [repo.name for repo in repos]
    return JsonResponse({'repositories': repo_list})