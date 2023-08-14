import streamlit as st
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import pytz
import base64
from matplotlib.ticker import MaxNLocator
import streamlit.components.v1 as components

def create_connection():
    conn = sqlite3.connect('data.db')
    return conn
def create_table(conn):
    query = """
    CREATE TABLE IF NOT EXISTS form_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME,
        phone TEXT,
        state TEXT,
        zip TEXT,
        team TEXT,
        line TEXT,
        sip TEXT,
        age INTEGER
    );
    """
    conn.execute(query)
def insert_form_data1(conn, phone, state, zip, team, line, sip, age):
    timestamp = datetime.now()
    query = """
    INSERT INTO form_data (timestamp, phone, state, zip, team, line, sip, age)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    conn.execute(query, (timestamp, phone, state, zip, team, line, sip, age))
    conn.commit()
def insert_form_data(conn, phone, state, zip, team, line, sip, age):
    # Get the PKT time zone
    pkt_tz = pytz.timezone('Asia/Karachi')

    # Get the current time in PKT
    pkt_timestamp = datetime.now(pkt_tz)

    query = """
    INSERT INTO form_data (timestamp, phone, state, zip, team, line, sip, age)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    conn.execute(query, (pkt_timestamp, phone, state, zip, team, line, sip, age))
    conn.commit()

users_data = [
    ("admin@JV", "Kpleads@01129"),("admin@kp.com","help@123"),
]

def create_users_table(conn):
    query = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    );
    """
    conn.execute(query)

    # Insert hardcoded user data
    for user in users_data:
        insert_user(conn, user[0], user[1])
#user_authenticated = False

def insert_user(conn, username, password):
    query = """
    INSERT INTO users (username, password)
    VALUES (?, ?)
    """
    conn.execute(query, (username, password))
    conn.commit()
def authenticate_user(conn, username, password):
    query = """
    SELECT * FROM users WHERE username = ? AND password = ?
    """
    cursor = conn.execute(query, (username, password))
    user = cursor.fetchone()
    return user is not None
def get_team_counts(conn):
    query = """
    SELECT team, COUNT(*) as count
    FROM form_data
    GROUP BY team
    """
    cursor = conn.execute(query)
    team_counts = {row[0]: row[1] for row in cursor.fetchall()}
    return team_counts


def show_visualization(team_counts):
    if team_counts:
        st.write("Form Submission Counts by Team:")
        colors = {
            'BLUE': 'cornflowerblue',
            'YELLOW': 'gold',
            'GREEN': 'olivedrab'
        }
        team_names = list(team_counts.keys())
        submission_counts = list(team_counts.values())
        team_colors = [colors[team] for team in team_names]

        fig, ax = plt.subplots()
        ax.set_facecolor('#0e1117')  # Set background color
        patches, texts, autotexts = ax.pie(
            submission_counts,
            labels=[f'{team} ({count})' for team, count in zip(team_names, submission_counts)],  # Display team names
            colors=team_colors,
            autopct="",  # Display submission counts
            startangle=140,
            textprops={'color': 'white'}
        )

        # Increase font size of labels and percentages
        for text in texts + autotexts:
            text.set_fontsize(14)

        plt.axis('equal')
        # Equal aspect ratio ensures that pie is drawn as a circle.
        fig.patch.set_facecolor('#0e1117')
        st.pyplot(fig)
    else:
        st.write("No form submissions yet.")


# ... (existing code)

def get_line_sip_data(conn):
    query = """
    SELECT sip, COUNT(*) as count
    FROM form_data
    GROUP BY sip
    """
    cursor = conn.execute(query)
    line_sip_data = [(row[0], row[1]) for row in cursor.fetchall()]
    return line_sip_data


def show_line_graph_visualization(line_sip_data):
    if line_sip_data:
        st.write("Bar Graph Visualization:")
        df = pd.DataFrame(line_sip_data, columns=["SIP", "Form Count"])
        df = df.sort_values(by="Form Count", ascending=False)

        # Assign different colors for each SIP value
        colors = plt.cm.get_cmap("tab20", len(df["SIP"]))
        color_dict = {sip: colors(i) for i, sip in enumerate(df["SIP"])}

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(df["SIP"], df["Form Count"], color=[color_dict[sip] for sip in df["SIP"]])

        plt.xlabel("SIP")
        plt.ylabel("Form Count")
        plt.title("Form Count Based on SIP")
        plt.xticks(rotation=45, ha="right")

        # Create a legend with custom labels based on SIP values
        legend_labels = [plt.Line2D([0], [0], color=color_dict[sip], lw=4, label=sip) for sip in df["SIP"]]
        ax.legend(handles=legend_labels, title="SIP")

        # Annotate bars with their counts
        for bar in bars:
            yval = bar.get_height()
            #ax.text(bar.get_x() + bar.get_width()/2, yval + 5, round(yval), ha="center", va="bottom")
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        st.pyplot(fig)
    else:
        st.write("No data available for bar graph visualization.")



# ... (existing code)

def export_to_csv(file_name):
    conn = create_connection()  # Open a new connection
    query = "SELECT * FROM form_data"
    df = pd.read_sql_query(query, conn)
    conn.close()  # Close the connection
    df.to_csv(file_name, index=False)

def download_csv1():
    conn = sqlite3.connect("data.db")  # Replace with your database name
    query = """
        SELECT timestamp, phone, state, zip, team, line, sip, age 
        FROM form_data
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
def download_csv():
    conn = sqlite3.connect("data.db")
    query = """
        SELECT timestamp, phone, state, zip, team, line, sip, age 
        FROM form_data
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Convert timestamps to PKT
    pkt_tz = pytz.timezone('Asia/Karachi')
    df['timestamp'] = df['timestamp'].apply(lambda x: x.astimezone(pkt_tz))

    return df
def fetch_sip_data(conn, selected_sip):
    query = """
    SELECT timestamp, phone, state, zip, team, line, sip, age 
    FROM form_data
    WHERE sip = ?
    """
    cursor = conn.execute(query, (selected_sip,))
    sip_data = cursor.fetchall()
    return sip_data
def fetch_team_data(conn, selected_team):
    query = """
    SELECT timestamp, phone, state, zip, team, line, sip, age 
    FROM form_data
    WHERE team = ?
    """
    cursor = conn.execute(query, (selected_team,))
    sip_data = cursor.fetchall()
    return sip_data

def fetch_dataframe(conn):
    query = """
    SELECT timestamp, phone, state, zip, team, line, sip, age 
    FROM form_data
    """
    df = pd.read_sql_query(query, conn)
    return df
def clear_database(conn):
    query = "DELETE FROM form_data"
    conn.execute(query)
    conn.commit()

def logout():
    global user_authenticated
    user_authenticated = False
    #components.html("<script>window.location.reload();</script>", height=0)

def show_visualization1(team_counts):
    if team_counts:
        st.write("Form Submission Counts by Team:")
        colors = {
            'BLUE': 'cornflowerblue',
            'YELLOW': 'gold',
            'GREEN': 'olivedrab'
        }

        # Extract teams and lines for each submission count
        team_lines = [(team, line) for team, line in team_counts.keys()]
        unique_teams = list(set([team for team, _ in team_lines]))
        unique_lines = list(set([line for _, line in team_lines]))

        # Initialize a data dictionary for plotting
        data = {team: {line: 0 for line in unique_lines} for team in unique_teams}

        # Fill in the data dictionary with submission counts
        for (team, line), count in team_counts.items():
            data[team][line] = count

        # Convert data dictionary into a DataFrame for plotting
        df_team_lines = pd.DataFrame(data)

        # Plot the data
        df_team_lines.plot(kind='bar', stacked=True, color=[colors[team] for team in unique_teams])
        plt.xlabel("Line")
        plt.ylabel("Form Count")
        plt.title("Form Count by Team and Line Transfer")
        plt.legend(title="Team")
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        st.pyplot(plt.gcf())
    else:
        st.write("No form submissions yet.")
def get_team_line_counts(conn):
    query = """
    SELECT team, line, COUNT(*) as count
    FROM form_data
    GROUP BY team, line
    """
    cursor = conn.execute(query)
    team_line_counts = {(row[0], row[1]): row[2] for row in cursor.fetchall()}
    return team_line_counts
def main():
    #global user_authenticated
    st.title("Medicare Form Submission")
    phone = st.text_input("Phone")
    state = st.text_input("State")
    zip = st.text_input("Zip")
    teams = ['BLUE', 'YELLOW', 'GREEN']
    team = st.selectbox("Team", teams)
    line = st.text_input("Line")
    sip = st.text_input("Sip")
    age = st.number_input("Age", min_value=0, max_value=150)
    if st.button("Submit"):
        conn = create_connection()
        create_table(conn)
        insert_form_data(conn, phone, state, zip, team, line, sip, age)
        st.success("Form submitted successfully!")
        conn.close()

    conn = create_connection()
    team_counts = get_team_counts(conn)
    conn.close()
    if st.button("Show Team-based Visualization"):
        if team_counts:
            show_visualization(team_counts)
        else:
            st.write("No form submissions yet.")

    if st.button("Show Line Graph Visualization"):
        conn = create_connection()
        line_sip_data = get_line_sip_data(conn)
        conn.close()

        if line_sip_data:
            show_line_graph_visualization(line_sip_data)
        else:
            st.write("No form submissions yet.")
    if st.button("Line Transfer Visualizaion"):
        conn = create_connection()
        data=get_team_line_counts(conn)
        conn.close()
        if data:
            show_visualization1(data)
        else:
            st.write("Nthing to show")
    conn=create_connection()
    create_users_table(conn)
    conn.close()
    entered_username = st.sidebar.text_input("Username")
    entered_password = st.sidebar.text_input("Password", type="password")
    login_button = st.sidebar.button("Login")
    conn = create_connection()
    user_authenticated = authenticate_user(conn, entered_username, entered_password)
    conn.close()

    if user_authenticated:
        st.sidebar.success("Authenticated")

        selected_action = st.sidebar.radio("Select Action", ("Download CSV", "Delete Database", "Logout"))

        if selected_action == "Download CSV":
            if st.sidebar.button("Download"):
                df = download_csv()
                csv = df.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="form_data_{datetime.now().date()}.csv">Download CSV</a>'
                st.sidebar.markdown(href, unsafe_allow_html=True)

        if selected_action == "Delete Database":
            if st.sidebar.button("Delete"):
                conn = create_connection()
                clear_database(conn)
                conn.close()
                st.sidebar.success("Database cleared successfully!")
        conn1 = create_connection()
        df = fetch_dataframe(conn1)  # Fetch the DataFrame
        conn.close()
        selected_sip = st.sidebar.selectbox("Select SIP", df["sip"].unique())
        selected_team = st.sidebar.selectbox("Select Team", df["team"].unique())
        # Replace 'df' with your DataFrame

        if st.sidebar.button("Fetch Data"):
            conn = create_connection()
            df = fetch_dataframe(conn)
            conn.close()

            if df is not None and not df.empty:
                selected_sip_data = df[df["sip"] == selected_sip]
                selected_team_data = df[df["team"] == selected_team]
                if not selected_sip_data.empty:
                    st.write("Filtering Based on SIP Data:")
                    st.dataframe(selected_sip_data)
                    st.write("Filtering based on Teams")
                    st.dataframe(selected_team_data)
                else:
                    st.write("No data available for the selected.")
            else:
                st.write("No data available.")


        if selected_action == "Logout":
            if st.sidebar.button("Logout"):
                logout()
                st.sidebar.warning("Logged out")

    else:
        st.sidebar.error("Authentication failed")




if __name__ == "__main__":
    main()
