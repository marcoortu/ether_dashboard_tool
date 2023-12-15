import os

import pandas as pd
import sqlalchemy
import ydata_profiling
import streamlit as st
from streamlit_pandas_profiling import st_profile_report

DIR_PATH = os.path.join(os.path.dirname(__file__), '..', 'db_util')

# Create a connection to your SQLite database
engine = sqlalchemy.create_engine(f'sqlite:///{DIR_PATH}/ethereum_tool.db')


@st.cache_data
def load_repositories():
    # Assuming your repositories table is named 'repositories'
    with engine.connect() as conn:
        # Assuming your repositories table is named 'repositories'
        return pd.read_sql("SELECT id, name FROM repositories ORDER BY name", conn)


def setup_page():
    # Hide the 'Made with Streamlit' footer by injecting custom CSS
    hide_streamlit_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                </style>
                """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    # CSS to hide the Streamlit "Deploy" button
    hide_deploy_button = """
                <style>
                #MainMenu {visibility: hidden;}
                .stDeployButton {visibility: hidden;}
                </style>
                """
    st.markdown(hide_deploy_button, unsafe_allow_html=True)

    # Styling for the tiles
    tile_style = """
    <style>
    .tile {
        padding: 10px;
        font-size: 30px;
        text-align: center;
        color: white;
        border-radius: 10px;
    }
    .tile-1 {
        background-color: #0078D4;
    }
    .tile-2 {
        background-color: #28A745;
    }
    .tile-3 {
        background-color: #FFC107;
    }
    </style>
    """
    st.markdown(tile_style, unsafe_allow_html=True)


@st.cache_data
def get_commits_by_repo(repo_id):
    # Query to count commits per day for a given repository
    query = f"""
        SELECT DATE(created_at) as date, COUNT(*) as commit_count
        FROM commits
        WHERE repo_fk = {repo_id}
        GROUP BY DATE(created_at) 
        ORDER BY created_at DESC 
        """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
        return df


@st.cache_data
def get_number_of_committers(repo_id):
    # Query to count commits per day for a given repository
    query = f"""
        SELECT  COUNT(DISTINCT user_fk) as dev_count
        FROM commits
        WHERE repo_fk = {repo_id}
        """
    with engine.connect() as conn:
        return pd.read_sql(query, conn).loc[0, 'dev_count']


def get_repo_index(repo_data):
    try:
        return repo_data['name'].tolist().index(st.session_state['repo_name'])
    except ValueError:
        # If the current repo is not in the list, default to the first item
        return 0


repo_data = load_repositories()

# Initialize the session state for 'repo_name' if it does not exist
if 'repo_name' not in st.session_state:
    st.session_state['repo_name'] = repo_data['name'][0]

repo_name = st.sidebar.selectbox(
    'Select a Repository',
    repo_data['name'],
    index=get_repo_index(repo_data)
)

# Update the session state
st.session_state['repo_name'] = repo_name

# Main content
if repo_name:
    # Get repository ID based on selected name
    repo_id = repo_data[repo_data['name'] == repo_name]['id'].iloc[0]

    # Get commit data for the selected repository
    commit_data = get_commits_by_repo(repo_id)

    # First row, spanning all columns for the plot
    if not commit_data.empty:
        commit_data.set_index('date', inplace=True)
        st.write(f"Number of Commits Per Day for Repository: {repo_name}")
        st.bar_chart(commit_data['commit_count'])
    else:
        st.write("No commit data available for the selected repository.")

    if not commit_data.empty:
        # Subsequent rows with multiple columns
        col1, col2 = st.columns(2)

        with col1:
            last_data = commit_data.index.values[0]
            before_last_data = commit_data.index.values[1]
            total_commits = commit_data.commit_count.sum()
            delta_count = int(
                commit_data.loc[last_data, 'commit_count'] - commit_data.loc[before_last_data, 'commit_count'])
            st.metric("Commits", total_commits,
                      delta=delta_count, delta_color="normal")
            # st.markdown(f"<div class='tile tile-1'>Commits: {total_commits}</div>", unsafe_allow_html=True)

        with col2:
            number_of_committers = get_number_of_committers(repo_id)
            st.metric("Committers", number_of_committers,
                      delta=0, delta_color="normal")
            # st.markdown(f"<div class='tile tile-2'>Committers: {number_of_committers}</div>",
            #             unsafe_allow_html=True)

        # with col3:
        #     number_of_comments = get_number_of_comments(repo_id)
        #     st.markdown(f"<div class='tile tile-3'>Comments: {number_of_comments}</div>", unsafe_allow_html=True)

        commit_pr = commit_data.profile_report()
        st_profile_report(commit_pr)
