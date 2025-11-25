import streamlit as st
import requests
from bs4 import BeautifulSoup
import re

LOGIN_URL = "https://erp.psit.ac.in/Erp/Auth"
DASHBOARD_URL = "https://erp.psit.ac.in/Student/Dashboard"

st.set_page_config(page_title="PSIT ERP Attendance Tracker", layout="centered")

st.markdown("""
<style>
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stToolbar"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

st.title("📚 PSIT Attendance & Fine Checker")

st.write("Enter your ERP credentials below:")

# ---- User Inputs ----
user = st.text_input("User ID / Roll No")
password = st.text_input("Password", type="password")

if st.button("Login & Fetch Details"):
    if not user or not password:
        st.error("❌ Please enter both User ID and Password.")
    else:
        try:
            session = requests.Session()
            payload = {"username": user, "password": password}
            session.post(LOGIN_URL, data=payload)

            response = session.get(DASHBOARD_URL)
            soup = BeautifulSoup(response.text, "html.parser")

            # Attendance
            h5_tags = soup.find_all("h5")
            if len(h5_tags) < 2:
                st.error("❌ Login failed. Check credentials.")
                st.stop()

            summary = h5_tags[0].get_text(strip=True)
            percentages = h5_tags[1].get_text(strip=True)

            values = dict(re.findall(r"(\w+)-\s*([\d.]+)", summary))
            TL = int(values.get("TL", 0))  # Total lectures
            P = int(values.get("P", 0))    # Present
            Ab = int(values.get("Ab", 0))  # Absent
            with_pf, without_pf = map(float, re.findall(r"(\d+\.\d+)", percentages))

            st.success("🎉 Login Successful!")
            st.subheader("📌 Attendance Summary")
            st.write(f"**Total Lectures:** {TL}")
            st.write(f"**Present:** {P}")
            st.write(f"**Absent:** {Ab}")
            st.write(f"**Attendance (With PF):** {with_pf}%")
            st.write(f"**Attendance (Without PF):** {without_pf}%")

            # ---- Fine block extraction ----
            fine = None
            for block in soup.find_all("div"):
                span = block.find("span")
                h4 = block.find("h4")
                if span and h4 and "Attendance Security Deposit" in span.get_text(strip=True):
                    fine = h4.get_text(strip=True)
                    break

            if fine:
                st.subheader("💰 Current Fine from ERP")
                st.write(f"**₹ {fine}**")
            else:
                st.info("No fine applied at the moment.")

            # ---- Calculation to reach 90% ----
            current_att = without_pf
            target = 90.0

            if current_att >= target:
                st.success("🔥 Your attendance is already 90% or above.")
                st.info("No extra lectures required.")
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

                st.subheader("📌 Requirement to Reach 90% Attendance")
                st.write(f"**Extra lectures required:** {needed}")
                st.write(f"**Equivalent to:** {days} days and {extra_lectures} lectures")
                st.write(f"**Projected Attendance After Completion:** {np:.2f}%")

        except Exception as e:
            st.error(f"⚠ Unexpected error: {e}")
