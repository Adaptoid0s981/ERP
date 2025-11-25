import requests
from bs4 import BeautifulSoup
import re

# URLs
login_url = "https://erp.psit.ac.in/Erp/Auth"
dashboard_url = "https://erp.psit.ac.in/Student/Dashboard"

# Start session
session = requests.session()

# Login credentials
payload = {
    "username": input("Your User ID: "),
    "password": input("Your Password: "),
}

# Login
session.post(login_url, data=payload)

# Load dashboard page
dashboard_response = session.get(dashboard_url)
html = dashboard_response.text

# Parse HTML
soup = BeautifulSoup(html, "html.parser")

# Extract first and second h5 (attendance info)
h5_tags = soup.find_all("h5")

if len(h5_tags) < 2:
    print("⚠ Attendance not found — login may have failed.")
    exit()

first = h5_tags[0].get_text(strip=True)
second = h5_tags[1].get_text(strip=True)

attendance = {}

# Extract numbers from the first h5 → TL, P, PF, Ab
match1 = re.findall(r"(\w+)-\s*([\d.]+)", first)
for key, val in match1:
    attendance[key] = float(val) if "." in val else int(val)

# Extract percentages from the second h5 → With PF, Without PF
match2 = re.findall(r"(\d+\.\d+)", second)

if len(match2) >= 2:
    attendance["With_PF"] = float(match2[0])
    attendance["Without_PF"] = float(match2[1])

# Print in readable format
print("\n------ Attendance Summary ------")
print(f"Total Lectures : {attendance['TL']}")
print(f"Present        : {attendance['P']}")
print(f"Absent         : {attendance['Ab']}")
print(f"Attendance With PF    : {attendance['With_PF']}%")
print(f"Attendance Without PF : {attendance['Without_PF']}%")
print("--------------------------------\n")
