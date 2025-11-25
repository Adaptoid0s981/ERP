import requests
from bs4 import BeautifulSoup

# URLs
login_url = "https://erp.psit.ac.in/Erp/Auth"
dashboard_url = "https://erp.psit.ac.in/Erp"

# Start session
session = requests.session()

# Login credentials
payload = {
    "username": input("YOUR_USER_ID: "),
    "password": input("YOUR_PASSWORD: "),
}

# Send login request
session.post(login_url, data=payload)

# Load dashboard
dashboard_response = session.get(dashboard_url)
html = dashboard_response.text

# Parse HTML
soup = BeautifulSoup(html, "html.parser")

# Extract student name from h4.mb-0

name_tag = soup.find("h4", class_="mb-0")
name = name_tag.get_text(strip=True) if name_tag else None

# Check login success
if name:
    print(f"🔓 Login successful! Student name: {name}")
else:
    print("❌ Login failed — could not find student name")
