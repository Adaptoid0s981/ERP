import streamlit as st
import requests
from bs4 import BeautifulSoup
import re

LOGIN_URL = "https://erp.psit.ac.in/Erp/Auth"
DASHBOARD_URL = "https://erp.psit.ac.in/Student/Dashboard"

st.set_page_config(page_title="PSIT Attendance Tracker", layout="centered")

# Hide Streamlit header, footer and toolbar
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


# ------------------------------------------------
# LOGIN BUTTON
# ------------------------------------------------
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
            st.error("❌ Login failed. Check credentials.")
            st.stop()

        summary = h5_tags[0].get_text(strip=True)
        percentages = h5_tags[1].get_text(strip=True)

        values = dict(re.findall(r"(\w+)-\s*([\d.]+)", summary))
        TL = int(values.get("TL", 0))
        P = int(values.get("P", 0))
        Ab = int(values.get("Ab", 0))
        with_pf, without_pf = map(float, re.findall(r"(\d+\.\d+)", percentages))

        # Save data permanently for other buttons
        st.session_state["TL"] = TL
        st.session_state["P"] = P
        st.session_state["Ab"] = Ab
        st.session_state["with_pf"] = with_pf
        st.session_state["without_pf"] = without_pf

        # Extract fine
        fine = None
        for block in soup.find_all("div"):
            span = block.find("span")
            h4 = block.find("h4")
            if span and h4 and "Attendance Security Deposit" in span.get_text(strip=True):
                fine = h4.get_text(strip=True)
                break
        st.session_state["fine"] = fine

        st.success("🎉 Login Successful! Data saved for other buttons.")
        st.subheader("📌 Attendance Summary")
        st.write(f"**Total Lectures:** {TL}")
        st.write(f"**Present:** {P}")
        st.write(f"**Absent:** {Ab}")
        st.write(f"**With PF:** {with_pf}%")
        st.write(f"**Without PF:** {without_pf}%")
        if fine:
            st.write(f"💰 **Fine:** ₹ {fine}")

    except Exception as e:
        st.error(f"⚠ Unexpected error: {e}")


# ------------------------------------------------
# BUTTON 1: Lectures needed to reach 90%
# ------------------------------------------------
if st.button("📈 How many lectures needed to reach 90%?"):
    if "without_pf" not in st.session_state:
        st.error("⚠ Please login first!")
        st.stop()

    TL = st.session_state["TL"]
    P = st.session_state["P"]
    without_pf = st.session_state["without_pf"]

    if without_pf >= 90:
        st.success("🔥 You already have 90% or more. No extra lectures needed.")
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


# ------------------------------------------------
# BUTTON 2: Lectures that can be bunked
# ------------------------------------------------
if st.button("😎 How many lectures can I bunk & stay 90%?"):
    if "without_pf" not in st.session_state:
        st.error("⚠ Please login first!")
        st.stop()

    TL = st.session_state["TL"]
    P = st.session_state["P"]
    without_pf = st.session_state["without_pf"]

    if without_pf < 90:
        st.warning("⚠ Your attendance is already below 90%. No bunks allowed.")
    else:
        bunkable = int((P - 0.90 * TL) / 0.90)

        if bunkable <= 0:
            st.info("🚫 You cannot bunk any lectures if you want to stay ≥ 90%.")
        else:
            days = bunkable // 8
            extra = bunkable % 8
            st.subheader("😎 Bunk Calculator")
            st.write(f"💤 You can bunk **{bunkable} more lectures** safely.")
            st.write(f"⏳ That is **{days} days and {extra} lectures**.")
            st.write("📌 Attendance will remain **≥ 90%** after this.")



