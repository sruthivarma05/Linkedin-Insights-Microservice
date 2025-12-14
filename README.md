# Linkedin-Insights-Microservice
This project scrapes LinkedIn company pages, stores the data in MongoDB, and exposes it through a FastAPI backend.
It uses Playwright with a saved login session to access LinkedIn’s protected company information.

Features

Scrape LinkedIn company details:

Name, URL, description, industry, website

Followers, company size, founded year

Headquarters, specialties

Employees on LinkedIn

Profile & banner images

Save all details to MongoDB

API endpoints for:

Fetching company data

Listing posts

Listing employees

Searching by name, followers, or industry

Pagination support

Tech Stack

Python 3

FastAPI

Playwright (Chromium)

MongoDB Community Server

Project Structure (Simplified)
app/
  main.py
  models/
  routes/
  services/
  utils/
linkedin_session/
  storage.json

Setup
1. Create virtual environment
python -m venv venv
venv\Scripts\activate

2. Install dependencies
pip install fastapi uvicorn pymongo playwright pydantic
playwright install

Save LinkedIn Login Session (Required)

Run:

playwright codegen --save-storage=linkedin_session/storage.json https://www.linkedin.com


Log in manually → close browser → session saved.

Run the API Server
uvicorn app.main:app --reload


API docs:

http://127.0.0.1:8000/docs

Example Usage
Get company:
GET /page/deepsolv

Search:
GET /page/search?industry=IT&min_followers=1000

Common Issues

Fields returning null
→ Your LinkedIn session expired.
Fix by re-running:

playwright codegen --save-storage=linkedin_session/storage.json


ModuleNotFoundError: playwright
→ Install:

pip install playwright
playwright install
