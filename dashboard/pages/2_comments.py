import os

import numpy as np
import pandas as pd
import sqlalchemy
import ydata_profiling
import plotly.express as px
import streamlit as st
from streamlit_pandas_profiling import st_profile_report
from dashboard.db_util.config import engine, load_repositories

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


def get_repo_index(repo_data):
    try:
        return repo_data['name'].tolist().index(st.session_state['repo_name'])
    except ValueError:
        # If the current repo is not in the list, default to the first item
        return 0


@st.cache_data
def get_number_of_comments(repo_id):
    # Query to count commits per day for a given repository
    query = f"""
        SELECT  DATE(c.created_at) as date, COUNT(*) as comm_count
        FROM issues AS s, comments AS c
        WHERE s.repo_fk = {repo_id} AND s.id = c.issue_fk
        GROUP BY DATE(c.created_at) 
        ORDER BY c.created_at DESC
        """
    with engine.connect() as conn:
        # return pd.read_sql(query, conn).loc[0, 'comm_count']
        return pd.read_sql(query, conn)


@st.cache_data
def get_number_of_commenters(repo_id):
    query = f"""
        SELECT  COUNT(DISTINCT c.user_fk)  as user_count
        FROM issues AS s, comments AS c
        WHERE s.repo_fk = {repo_id} AND s.id = c.issue_fk
        """
    with engine.connect() as conn:
        return pd.read_sql(query, conn).loc[0, 'user_count']


@st.cache_data
def get_comments_sentiment(repo_id):
    query = f"""
        SELECT     c.sentiment AS Sentiment,  COUNT(*) AS Frequency
        FROM  issues AS s, comments AS c
        WHERE s.repo_fk = {repo_id} AND s.id = c.issue_fk
        GROUP BY c.sentiment
        """
    with engine.connect() as conn:
        return pd.read_sql(query, conn)


@st.cache_data
def get_comments_emotions(repo_id):
    query = f"""
        SELECT     c.emotion AS Emotion,  COUNT(*) AS Frequency
        FROM  issues AS s, comments AS c
        WHERE s.repo_fk = {repo_id} AND s.id = c.issue_fk
        GROUP BY c.emotion
        """
    with engine.connect() as conn:
        return pd.read_sql(query, conn)


@st.cache_data
def commenters_scatter_plot_data(repo_id):
    query_comments = f"""
        SELECT  c.user_fk AS user_id, c.author_association, COUNT(*)  AS comments_count
        FROM issues AS s, comments AS c
        WHERE s.repo_fk = {repo_id} AND s.id = c.issue_fk
        GROUP BY c.user_fk
        ORDER BY comments_count DESC 
        """
    query_issues = f"""
            SELECT  s.user_fk AS user_id, COUNT(*)  AS issues_count
            FROM issues AS s
            WHERE s.repo_fk = {repo_id}
            GROUP BY s.user_fk
            ORDER BY issues_count DESC 
            """
    query_commits = f"""
                SELECT  c.user_fk AS user_id, COUNT(*)  AS commits_count
                FROM commits AS c
                WHERE c.repo_fk = {repo_id}
                GROUP BY c.user_fk
                ORDER BY commits_count DESC 
                """
    with engine.connect() as conn:
        df_comments = pd.read_sql(query_comments, conn)
        df_comments.set_index('user_id', inplace=True)
        df_issues = pd.read_sql(query_issues, conn)
        df_issues.set_index('user_id', inplace=True)
        df_commits = pd.read_sql(query_commits, conn)
        df_commits.set_index('user_id', inplace=True)
        df_merge = pd.merge(df_comments, df_issues, left_index=True, right_index=True, how='inner')
        df_merge = pd.merge(df_merge, df_commits, left_index=True, right_index=True, how='inner')
        conditions = [
            df_merge['commits_count'] > df_merge['comments_count'],  # Condition for 'commiter'
            df_merge['commits_count'] < df_merge['comments_count'],  # Condition for 'commenter'
            df_merge['commits_count'] == df_merge['comments_count']  # Condition for 'contributor'
        ]
        choices = ['commiter', 'commenter', 'contributor']
        df_merge['type'] = np.select(conditions, choices, default='Not Specified')
        return df_merge


setup_page()

if 'repo_name' not in st.session_state:
    st.session_state['repo_name'] = None

# Sidebar for repository selection
repo_data = load_repositories()
repo_name = st.sidebar.selectbox(
    'Select a Repository',
    repo_data['name'],
    index=get_repo_index(repo_data)
)

# Update the session state
st.session_state['repo_name'] = repo_name

st.title('Comments')

if repo_name:
    # Get repository ID based on selected name
    repo_id = repo_data[repo_data['name'] == repo_name]['id'].iloc[0]

    # Get commit data for the selected repository
    comments_data = get_number_of_comments(repo_id)

    if not comments_data.empty:
        comments_data.set_index('date', inplace=True)
        st.write(f"Number of Comments Per Day for Repository: {repo_name}")
        st.bar_chart(comments_data['comm_count'])
        if not comments_data.empty:
            # Subsequent rows with multiple columns
            col1, col2 = st.columns(2)

            with col1:
                last_data = comments_data.index.values[0]
                before_last_data = comments_data.index.values[1]
                total_commits = comments_data.comm_count.sum()
                delta_count = int(
                    comments_data.loc[last_data, 'comm_count'] - comments_data.loc[before_last_data, 'comm_count'])
                st.metric("Comments", total_commits,
                          delta=delta_count, delta_color="normal")

            with col2:
                number_of_committers = get_number_of_commenters(repo_id)
                st.metric("Commenters", number_of_committers,
                          delta=0, delta_color="normal")

            tab1, tab2, tab3, tab4 = st.tabs(["Plots", "Sentiment", "Emotion", "Statistics"])

            with tab1:
                df = px.data.gapminder()
                df_commenters = commenters_scatter_plot_data(repo_id)

                fig = px.scatter(
                    df_commenters,
                    x="issues_count",
                    y="comments_count",
                    size="commits_count",
                    color="author_association",
                    hover_name="type",
                    # log_x=True,
                    size_max=60,
                )
                st.plotly_chart(fig, theme="streamlit", use_container_width=True)

            with tab2:
                sentiment_count = get_comments_sentiment(repo_id)
                sentiment_count = sentiment_count.sort_values('Frequency', ascending=False)
                # Create the Plotly bar plot
                sentiment_count_fig = px.bar(sentiment_count,
                                             x='Sentiment',
                                             y='Frequency',
                                             color='Frequency',
                                             color_continuous_scale='Viridis',
                                             title='Sentiment Levels')
                # Show the plot
                st.plotly_chart(sentiment_count_fig)
            with tab3:
                col1, col2 = st.columns(2)

                with col1:
                    emotion_count = get_comments_emotions(repo_id)
                    emotion_count = emotion_count.sort_values('Frequency', ascending=False)
                    neutral_count = emotion_count[emotion_count['Emotion'] == 'neutral'].Frequency.values[0]
                    emotion_count = emotion_count[~emotion_count.Emotion.isin(['neutral'])]
                    # Create the Plotly bar plot
                    emotion_count_fig = px.bar(emotion_count,
                                               x='Emotion',
                                               y='Frequency',
                                               color='Frequency',
                                               color_continuous_scale='Viridis',
                                               title='Emotion Levels')
                    # Show the plot
                    st.plotly_chart(emotion_count_fig)
                with col2:
                    if neutral_count:
                        st.metric("Neutral", neutral_count,
                                  delta=0, delta_color="normal")

            with tab4:
                commit_pr = df_commenters.profile_report()
                st_profile_report(commit_pr)

else:
    st.write("No comments data available for the selected repository.")
