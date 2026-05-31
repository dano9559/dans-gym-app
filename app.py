import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Dan's Gym App", page_icon="💪", layout="centered")

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect("fitness_notebook.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS gym_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT, split TEXT, muscle TEXT, exercise TEXT,
                        set_num INTEGER, weight REAL, reps INTEGER, effort TEXT,
                        start_time TEXT, stop_time TEXT, cals REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS cardio_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT, start_time TEXT, stop_time TEXT,
                        mins INTEGER, cals REAL, min_hr INTEGER, avg_hr INTEGER, 
                        max_hr INTEGER, notes TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- EXERCISE LIBRARY ---
LIBRARY = {
    "Upper Body Focus": {
        "Chest": ["Machine Chest Press", "Dumbbell Flat Bench", "Dumbbell Incline Press", "Pec Fly Machine"],
        "Back": ["Seated Row Machine", "Lat Pulldown Machine", "Machine Assisted Pull-Ups"],
        "Shoulders": ["Machine Shoulder Press", "Dumbbell Overhead Press", "Cable Face Pulls"],
        "Biceps": ["Dumbbell Curls", "Cable Bicep Curls", "Preacher Curl Machine"],
        "Triceps": ["Machine Dips", "Cable Tricep Pushdown", "Machine Tricep Extension"]
    },
    "Lower Body Focus": {
        "Quads": ["Machine Leg Press", "Machine Leg Extension", "Bodyweight Squats"],
        "Hamstrings": ["Machine Leg Curl", "Dumbbell Romanian Deadlift"],
        "Glutes/Hips": ["Seated Hip Abduction", "Seated Hip Adduction", "Glute Bridge"],
        "Calves": ["Calf Press (Leg Press)", "Standing Calf Raise", "Calf Extension Machine"]
    },
    "Core": {
        "Core": ["Machine Ab Crunches", "Dip Bar Leg Raises", "Plank Hold", "Back Extension"]
    }
}

# --- APP UI ---
st.title("💪 Dan's Gym App")

selected_date = st.date_input("Select Date", datetime.today(), format="MM/DD/YYYY")
display_date_str = selected_date.strftime("%d %b %Y")
st.write(f"### Log Date: {display_date_str}")

selected_split = st.selectbox("Workout Focus", ["Select Split", "Upper Body Focus", "Lower Body Focus", "Core", "Cardio Day Only"])

# --- LIFTING LOGIC ---
if selected_split in ["Upper Body Focus", "Lower Body Focus", "Core"]:
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    start = c1.text_input("Start", "06:30 AM")
    stop = c2.text_input("Stop", "07:15 AM")
    cals = c3.number_input("Cals", 0.0, 1000.0, 200.0)
    
    for muscle, exercises in LIBRARY[selected_split].items():
        st.subheader(muscle)
        ex = st.selectbox(f"Exercise", exercises, key=f"ex_{muscle}")
        
        style = st.radio("Set Structure", ["3 Sets (10-12 Reps)", "12-10-8-6-12-12 Pyramid"], key=f"rad_{muscle}", horizontal=True)
        num_sets = 6 if "Pyramid" in style else 3
        
        df = pd.DataFrame({"Weight": [100.0]*num_sets, "Reps": [12]*num_sets, "Effort": ["Good"]*num_sets})
        
        st.caption("💡 *Tip: Click the '+' at the bottom of the table to add extra sets!*")
        
        # The dynamic data editor
        edited = st.data_editor(
            df, 
            key=f"edit_{selected_split}_{muscle}_{ex}", 
            num_rows="dynamic", 
            column_config={"Effort": st.column_config.SelectboxColumn(options=["Good", "Easy", "Hard", "Fail"])}
        )
        
        if st.button(f"Log Entry for {ex}", key=f"btn_{selected_split}_{muscle}"):
            conn = sqlite3.connect("fitness_notebook.db")
            # Loop through however many rows exist and automatically number the sets sequentially!
            for idx, row in edited.iterrows():
                actual_set_number = idx + 1 
                conn.execute("INSERT INTO gym_logs VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                             (display_date_str, selected_split, muscle, ex, actual_set_number, row["Weight"], row["Reps"], row["Effort"], start, stop, cals))
            conn.commit()
            conn.close()
            st.success(f"Logged {ex}!")

# --- CARDIO LOGIC ---
elif selected_split == "Cardio Day Only":
    st.header("🏃 Cardio Log")
    col1, col2 = st.columns(2)
    start = col1.text_input("Start Time", "07:30 AM")
    stop = col2.text_input("Stop Time", "08:15 AM")
    mins = col1.number_input("Duration (min)", 0, 120, 30)
    cals = col2.number_input("Calories", 0.0, 1000.0, 300.0)
    min_hr = col1.number_input("Min HR", 0, 220, 90)
    avg_hr = col2.number_input("Avg HR", 0, 220, 135)
    max_hr = col1.number_input("Max HR", 0, 220, 150)
    notes = st.text_area("Notes")
    
    if st.button("Log Cardio Entry"):
        conn = sqlite3.connect("fitness_notebook.db")
        conn.execute("INSERT INTO cardio_logs VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                     (display_date_str, start, stop, mins, cals, min_hr, avg_hr, max_hr, notes))
        conn.commit()
        conn.close()
        st.success("Cardio Logged!")

# --- HISTORY VIEWER ---
st.markdown("---")
if st.checkbox("Expand History Viewer"):
    conn = sqlite3.connect("fitness_notebook.db")
    st.write("### Lifting History")
    try:
        st.dataframe(pd.read_sql("SELECT * FROM gym_logs ORDER BY id DESC", conn))
    except:
        st.info("No lifting data.")
    st.write("### Cardio History")
    try:
        st.dataframe(pd.read_sql("SELECT * FROM cardio_logs ORDER BY id DESC", conn))
    except:
        st.info("No cardio data.")
    conn.close()