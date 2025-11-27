import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from datetime import date

LOGIN_URL = "https://erp.psit.ac.in/Erp/Auth"
DASHBOARD_URL = "https://erp.psit.ac.in/Student/Dashboard"
TIMETABLE_URL = "https://erp.psit.ac.in/Student/TimeTable"

st.set_page_config(page_title="PSIT Student Toolkit", layout="centered")

# Hide Streamlit header, footer, menu
st.markdown("""
<style>
header {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stToolbar"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

st.title("🎓 PSIT Student Toolkit")

# ---------------- LOGIN ----------------
user = st.text_input("User ID / Roll Number")
password = st.text_input("Password", type="password")

if st.button("🔓 Login & Fetch Data"):
    if not user or not password:
        st.error("⚠ Enter both User ID and Password.")
        st.stop()

    try:
        session = requests.Session()
        payload = {"username": user, "password": password}
        session.post(LOGIN_URL, data=payload)

        dashboard = session.get(DASHBOARD_URL)
        soup = BeautifulSoup(dashboard.text, "html.parser")

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
        wpf, wopf = map(float, re.findall(r"(\d+\.\d+)", percentages))

        # Save attendance state for other tabs
        st.session_state.update({
            "session": session,
            "TL": TL,
            "P": P,
            "Ab": Ab,
            "wpf": wpf,
            "wopf": wopf
        })

        # Extract fine
        fine = None
        for block in soup.find_all("div"):
            span = block.find("span")
            h4 = block.find("h4")
            if span and h4 and "Attendance Security Deposit" in span.get_text(strip=True):
                fine = h4.get_text(strip=True)
                break
        st.session_state["fine"] = fine

        st.success("🎉 Login Successful! Data loaded.")
    except Exception as e:
        st.error(f"⚠ Error: {e}")


# ===== SHOW TABS ONLY AFTER LOGIN SUCCESS =====
if "session" in st.session_state:

    tabs = st.tabs(["📈 Attendance", "📅 Today's Timetable", "ℹ About"])

    # ------------ TAB 1: ATTENDANCE FEATURES ------------
    with tabs[0]:
        TL = st.session_state["TL"]
        P = st.session_state["P"]
        Ab = st.session_state["Ab"]
        wpf = st.session_state["wpf"]
        wopf = st.session_state["wopf"]
        fine = st.session_state["fine"]

        st.subheader("📌 Attendance Summary")
        st.write(f"Total Lectures: **{TL}**")
        st.write(f"Present: **{P}**")
        st.write(f"Absent: **{Ab}**")
        st.write(f"Without PF Attendance: **{wopf}%**")
        if fine:
            st.write(f"💰 Fine: **₹ {fine}**")

        # A) Reach 90%
        if st.button("📈 How many lectures needed to reach 90%?"):
            if wopf >= 90:
                st.success("🔥 Already 90% or above.")
            else:
                present, total, count, proj = P, TL, 0, wopf
                while proj < 90:
                    present += 1
                    total += 1
                    proj = (present / total) * 100
                    count += 1
                st.info(f"➡ Need **{count} lectures** to reach 90%.")

        # B) Bunk calculator
        if st.button("😎 How many lectures can I bunk & stay 90%?"):
            if wopf < 90:
                st.warning("⚠ Attendance below 90%, no bunks allowed.")
            else:
                bunkable = int((P - 0.90 * TL) / 0.90)
                if bunkable <= 0:
                    st.info("🚫 Cannot bunk any more lectures.")
                else:
                    st.success(f"💤 You can bunk **{bunkable} lectures** safely.")

    # ------------ TAB 2: TIMETABLE ------------
    with tabs[1]:
        st.subheader("📅 Today's Timetable")

        try:
            session = st.session_state["session"]
            tt_res = session.get(TIMETABLE_URL)
            soup = BeautifulSoup(tt_res.text, "html.parser")

            table_div = soup.find("div", class_="table-responsive")
            h5_tags = table_div.find_all("h5")
            raw = [[t.strip() for t in h5.stripped_strings] for h5 in h5_tags]
            raw = raw[8:]  # drop top portion

            day_index = date.today().weekday()  # Monday=0
            start, end = 8 * day_index, 8 * (day_index + 1)
            today = raw[start:end]

            if today:
                df = pd.DataFrame(today, columns=["Faculty", "Subject/Room", "Batch"])
                df.index = df.index + 1
                st.table(df)
            else:
                st.warning("No timetable found for today.")
        except:
            st.error("⚠ Could not fetch timetable.")

    # ------------ TAB 3: ABOUT ------------
    with tabs[2]:
        st.info("Built for PSIT students — Attendance + Timetable Dashboard.")




