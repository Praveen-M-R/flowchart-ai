import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="/home/praveen/polynomialai/flowchart_ai/.envvar.local")

GIT_ACCESS_KEY = os.getenv("GIT_ACCESS_KEY")
ORGANIZATION = os.getenv("ORGANIZATION")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GIT_USERNAME = os.getenv("GIT_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
