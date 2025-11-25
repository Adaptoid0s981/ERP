import requests
from bs4 import BeautifulSoup
import re

LOGIN_URL = "https://erp.psit.ac.in/Erp/Auth"
DASHBOARD_URL = "https://erp.psit.ac.in/Student/Dashboard"

session = requests.Session()
payload = {
    "username": input("Your User ID: "),
    "password": input("Your Password: "),
}

session.post(LOGIN_URL, data=payload)

response = session.get(DASHBOARD_URL)
soup = BeautifulSoup(response.text, "html.parser")

h5_tags = soup.find_all("h5")
if len(h5_tags) < 2:
    print("❌ Login failed — attendance details missing.")
    exit()

# Attendance values
summary = h5_tags[0].get_text(strip=True)
percentages = h5_tags[1].get_text(strip=True)

values = dict(re.findall(r"(\w+)-\s*([\d.]+)", summary))
TL = int(values.get("TL", 0))
P = int(values.get("P", 0))
Ab = int(values.get("Ab", 0))
with_pf, without_pf = map(float, re.findall(r"(\d+\.\d+)", percentages))

print("\n------ Attendance Summary ------")
print(f"Total Lectures : {TL}")
print(f"Present        : {P}")
print(f"Absent         : {Ab}")
print(f"With PF        : {with_pf}%")
print(f"Without PF     : {without_pf}%")

# ---------------- Fetch Fine Directly From Dashboard ----------------
# ---------------- Fetch Fine Directly From Dashboard ----------------
fine = None

for block in soup.find_all("div"):
    span = block.find("span")
    h4 = block.find("h4")

    if span and h4 and "Attendance Security Deposit" in span.get_text(strip=True):
        fine = h4.get_text(strip=True)
        break

if fine:
    print(f"\n💰 Current Fine (from ERP): ₹{fine}")
else:
    print("\n💰 Fine not found on dashboard (maybe not applicable).")


# ------------- Classes Required To Reach 90% -------------
current_att = without_pf
target = 90.0

if current_att >= 90:
    print("\n🎉 Attendance is already 90% or above.")
    print("🛑 No fine and no extra lectures needed.")
else:
    present = P
    total = TL
    needed = 0
    np = current_att

    while np < target:
        present += 1
        total += 1
        np = (present / total) * 100
        needed += 1

    days = needed // 8
    extra_lectures = needed % 8

    print("\n📌 To reach 90% attendance:")
    print(f"➡ Lectures needed: {needed}")
    print(f"➡ Equivalent to: {days} days and {extra_lectures} lectures")
    print(f"📌 Final projected attendance: {np:.2f}%")
    print("--------------------------------------\n")
