import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from datetime import date


LOGIN_URL = "https://erp.psit.ac.in/Erp/Auth"
DASHBOARD_URL = "https://erp.psit.ac.in/Student/Dashboard"
TIMETABLE_URL = "https://erp.psit.ac.in/Student/MyTimeTable"

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

user = st.text_input("User ID / Roll Number")
password = st.text_input("Password", type="password")


# ================= LOGIN =================
if st.button("🔓 Login & Fetch Data"):
    if not user or not password:
        st.error("⚠ Please enter both User ID and Password.")
        st.stop()

    try:
        # Login
        session = requests.Session()
        payload = {"username": user, "password": password}
        session.post(LOGIN_URL, data=payload)

        # Fetch attendance page
        dashboard = session.get(DASHBOARD_URL)
        soup = BeautifulSoup(dashboard.text, "html.parser")

        h5_tags = soup.find_all("h5")
        if len(h5_tags) < 2:
            st.error("❌ Login failed. Check credentials.")
            st.stop()

        # Attendance values extraction
        summary = h5_tags[0].get_text(strip=True)
        percentages = h5_tags[1].get_text(strip=True)
        values = dict(re.findall(r"(\w+)-\s*([\d.]+)", summary))
        TL = int(values.get("TL", 0))
        P = int(values.get("P", 0))
        Ab = int(values.get("Ab", 0))
        wpf, wopf = map(float, re.findall(r"(\d+\.\d+)", percentages))

        # Store session and attendance values
        st.session_state.update({
            "session": session,
            "TL": TL,
            "P": P,
            "Ab": Ab,
            "wpf": wpf,
            "wopf": wopf
        })

        # Fetch fine
        fine = None
        for block in soup.find_all("div"):
            span = block.find("span")
            h4 = block.find("h4")
            if span and h4 and "Attendance Security Deposit" in span.get_text(strip=True):
                fine = h4.get_text(strip=True)
                break
        st.session_state["fine"] = fine

        st.success("🎉 Login Successful! Data saved.")

    except Exception as e:
        st.error(f"⚠ Error: {e}")


# ================= SHOW TABS AFTER LOGIN =================
if "session" in st.session_state:

    tabs = st.tabs(["📈 Attendance", "📅 Today's Timetable", "ℹ About"])

    # ===== TAB 1 — ATTENDANCE =====
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
        if st.button("📈 How many extra lectures needed to reach 90%?"):
            if wopf >= 90:
                st.success("🔥 You already have 90% or more.")
            else:
                present, total, count, proj = P, TL, 0, wopf
                while proj < 90:
                    present += 1
                    total += 1
                    proj = (present / total) * 100
                    count += 1
                st.info(f"➡ You need **{count} more lectures** to reach 90% attendance.")

        # B) Bunk calculator
        if st.button("😎 How many lectures can I bunk & still remain 90%?"):
            if wopf < 90:
                st.warning("⚠ Attendance below 90%, no bunks allowed.")
            else:
                bunkable = int((P - 0.90 * TL) / 0.90)
                if bunkable <= 0:
                    st.info("🚫 Cannot bunk any more lectures.")
                else:
                    st.success(f"💤 You can bunk **{bunkable} lectures** safely while staying ≥ 90%.")


    # ===== TAB 2 — TODAY'S TIMETABLE =====
    with tabs[1]:
        st.subheader(f"📅 Today's Timetable — {date.today().strftime('%A, %d %B %Y')}")

        try:
            session = st.session_state["session"]
            tt_response = session.get(TIMETABLE_URL)
            soup = BeautifulSoup(tt_response.text, "html.parser")

            # Get only today's red highlighted row
            today_row = soup.find("tr", class_="odd gradeX bg-danger")

            if not today_row:
                st.warning("No classes scheduled for today.")
            else:
                lectures = []
                # Skip first column (day name)
                for cell in today_row.find_all("td")[1:]:
                    h5 = cell.find("h5")
                    lectures.append(h5.get_text("\n", strip=True) if h5 else "—")

                df = pd.DataFrame({"Lecture": list(range(1, 9)), "Details": lectures})
                df.index = df.index + 1

                st.table(df)

        except Exception as e:
            st.error(f"⚠ Error fetching timetable: {e}")


    # ===== TAB 3 — ABOUT =====
    with tabs[2]:
        st.info("This toolkit was created to help PSIT students check attendance, calculate bunks, and view today's timetable in one place.")
