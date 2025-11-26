import streamlit as st
import requests
from bs4 import BeautifulSoup
import re

LOGIN_URL = "https://erp.psit.ac.in/Erp/Auth"
DASHBOARD_URL = "https://erp.psit.ac.in/Student/Dashboard"

st.set_page_config(page_title="PSIT Attendance Tracker", layout="centered")

# --------- HIDE STREAMLIT HEADER, FOOTER & MENU ----------
st.markdown("""
<style>
header {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stToolbar"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

st.title("📚 PSIT Attendance & Fine Tracker")

# ---------------- INPUTS ----------------
user = st.text_input("User ID / Roll Number")
password = st.text_input("Password", type="password")

if st.button("🔓 Login & Fetch Data"):
    if not user or not password:
        st.error("⚠ Please enter both User ID and Password.")
        st.stop()

    try:
        session = requests.Session()
        payload = {"username": user, "password": password}
        session.post(LOGIN_URL, data=payload)

        response = session.get(DASHBOARD_URL)
        soup = BeautifulSoup(response.text, "html.parser")

        h5_tags = soup.find_all("h5")
        if len(h5_tags) < 2:
            st.error("❌ Login failed. Check your credentials.")
            st.stop()

        # Extract attendance
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
        st.write(f"**With PF:** {with_pf}%")
        st.write(f"**Without PF:** {without_pf}%")

        # -------- Fetch Fine (Attendance Security Deposit) --------
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
            st.info("No fine shown on dashboard.")

        # ============== BUTTON 1: Lectures needed to reach 90% ==============
        if st.button("📈 How many lectures needed to reach 90%?"):
            if without_pf >= 90:
                st.success("🔥 Your attendance is already 90% or more. No extra lectures needed.")
            else:
                present = P
                total = TL
                needed = 0
                projected = without_pf

                while projected < 90:
                    present += 1
                    total += 1
                    projected = (present / total) * 100
                    needed += 1

                days = needed // 8
                extra = needed % 8

                st.subheader("📌 Requirement to Reach 90%")
                st.write(f"➡ **Extra lectures required:** {needed}")
                st.write(f"➡ **Equivalent to:** {days} days and {extra} lectures")
                st.write(f"📌 **Projected attendance after completion:** {projected:.2f}%")

        # ============== BUTTON 2: Maximum lectures that can be bunked ==============
        if st.button("😎 How many lectures can I bunk & still remain 90%?"):
            target = 90
            bunkable = int((P - (target/100) * TL) / (target/100))

            if without_pf < 90:
                st.warning("⚠ Your attendance is below 90%. No bunks allowed.")
            elif bunkable <= 0:
                st.info("🚫 You cannot bunk any more lectures if you want to stay ≥ 90%.")
            else:
                days = bunkable // 8
                extra = bunkable % 8
                st.subheader("😎 Bunk Calculator")
                st.write(f"💤 You can bunk **{bunkable} more lectures** safely.")
                st.write(f"⏳ That means: **{days} days and {extra} lectures** can be missed.")
                st.write(f"📌 Attendance will remain **≥ 90%** after this.")

    except Exception as e:
        st.error(f"⚠ Unexpected error: {e}")


