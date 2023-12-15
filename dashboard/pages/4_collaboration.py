import base64
import os

import pandas as pd
import plotly.express as px
import sqlalchemy
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import streamlit as st

from streamlit_agraph import agraph, Node, Edge, Config
import ydata_profiling
from streamlit_pandas_profiling import st_profile_report

IMG_DIR_PATH = os.path.dirname(os.path.abspath(__file__))

DIR_PATH = os.path.join(os.path.dirname(__file__), '..', 'db_util')

# Create a connection to your SQLite database
engine = sqlalchemy.create_engine(f'sqlite:///{DIR_PATH}/ethereum_tool.db')


@st.cache_data
def load_repositories():
    # Assuming your repositories table is named 'repositories'
    with engine.connect() as conn:
        # Assuming your repositories table is named 'repositories'
        return pd.read_sql("SELECT id, name FROM repositories ORDER BY name", conn)


def get_image_as_base64(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


def create_nx_graph(commiter_id):
    commits = load_commits(commiter_id)[:100]


@st.cache_data
def get_comments_by_issue(issue_id):
    query = f"""
        SELECT  *
        FROM comments AS c
        WHERE c.issue_fk = {issue_id}
        GROUP BY DATE(c.created_at) 
        ORDER BY c.created_at DESC
        """
    with engine.connect() as conn:
        # return pd.read_sql(query, conn).loc[0, 'comm_count']
        return pd.read_sql(query, conn)


@st.cache_data
def load_committers(repo_id):
    query = f"""
        SELECT user_fk, COUNT(*) as commits_count
        FROM commits
        WHERE repo_fk = {repo_id} AND user_fk IS NOT NULL
        GROUP BY user_fk
        ORDER BY commits_count DESC 
        """
    with engine.connect() as conn:
        return pd.read_sql(query, conn)


@st.cache_data
def load_commits(commiter_id):
    query = f"""
        SELECT *
        FROM commits
        WHERE user_fk = {commiter_id}
        """
    with engine.connect() as conn:
        return pd.read_sql(query, conn)


@st.cache_data
def load_files(committer_id):
    query = f"""
        SELECT fc.user_fk, f.name, f.id
        FROM file_commits AS fc, files AS f
        WHERE f.id = fc.file_fk AND fc.user_fk = {committer_id}
        GROUP BY fc.user_fk, fc.file_fk
        """
    with engine.connect() as conn:
        return pd.read_sql(query, conn)


@st.cache_data
def load_file_committers(file_id, committer_id):
    query = f"""
        SELECT DISTINCT fc.user_fk
        FROM file_commits AS fc
        WHERE fc.file_fk = '{file_id}' AND fc.user_fk <> {committer_id}
        GROUP BY fc.user_fk, fc.file_fk
        """
    with engine.connect() as conn:
        return pd.read_sql(query, conn)


@st.cache_data
def load_sentiment(committer_id):
    query = f"""
        SELECT body, sentiment, emotion
        FROM comments
        WHERE user_fk = {committer_id}
        """
    with engine.connect() as conn:
        return pd.read_sql(query, conn)


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

    if repo_id:
        commiters_data = load_committers(repo_id)
        committer_id = st.sidebar.selectbox('Select an Commiter', commiters_data['user_fk'])

        if committer_id:
            commits = load_commits(committer_id)[:100]
            files = load_files(committer_id)

            dev_img = get_image_as_base64(f"{IMG_DIR_PATH}/../imgs/dev.png")
            dev_main_img = get_image_as_base64(f"{IMG_DIR_PATH}/../imgs/dev_main.png")
            file_img = get_image_as_base64(f"{IMG_DIR_PATH}/../imgs/file.png")

            tab1, tab2, tab3, tab4, tab5 = st.tabs(["Files", "Word Cloud", "Sentiment",
                                                    "Emotion", "Statistics"])
            with tab1:
                if not commits.empty:
                    nodes = []
                    dev_nodes = set()
                    edges = []

                    nodes.append(
                        Node(id=committer_id,
                             label=committer_id,
                             size=30,
                             shape="circularImage",
                             image=f"data:image/jpeg;base64,{dev_main_img}")
                    )
                    for file in files.to_dict("records"):
                        if file['id'] not in dev_nodes:
                            dev_nodes.add(file['id'])
                            nodes.append(
                                Node(id=file["id"],
                                     title=file["name"],
                                     size=15,
                                     shape="circularImage",
                                     image=f"data:image/jpeg;base64,{file_img}")
                            )
                        edges.append(
                            Edge(source=committer_id,
                                 # label="committed",
                                 target=file["id"],
                                 )
                        )
                        for file_committer in load_file_committers(file['id'], committer_id).to_dict("records"):
                            if file_committer["user_fk"] not in dev_nodes:
                                dev_nodes.add(file_committer["user_fk"])
                                nodes.append(
                                    Node(id=file_committer["user_fk"],
                                         size=20,
                                         shape="circularImage",
                                         image=f"data:image/jpeg;base64,{dev_img}")
                                )
                            edges.append(
                                Edge(source=file_committer["user_fk"],
                                     # label="committed",
                                     target=file["id"],
                                     )
                            )

                    config = Config(
                        width=1000,
                        height=800,
                        directed=True,
                        # physics=True,
                        # hierarchical=True,
                        # **kwargs
                    )

                    return_value = agraph(nodes=nodes,
                                          edges=edges,
                                          config=config)

            with tab2:
                comments = load_sentiment(committer_id)
                text = " ".join(comments.body.values)
                wordcloud = WordCloud(width=800,
                                      height=400,
                                      min_word_length=3,
                                      normalize_plurals=True,
                                      background_color='white').generate(text)
                # Display the generated image using matplotlib
                fig, ax = plt.subplots()
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis('off')  # Remove axis

                # Display the plot in Streamlit
                st.image(wordcloud.to_array())

            with tab3:
                sentiment_df = comments[['sentiment']].value_counts().reset_index()
                sentiment_df.columns = ['Sentiment', 'Count']
                sentiment_df = sentiment_df.sort_values('Count', ascending=False)
                # Create the Plotly bar plot
                sent_fig = px.bar(sentiment_df, x='Sentiment',
                                  y='Count',
                                  color='Count',
                                  color_continuous_scale='Viridis',
                                  title='Sentiment Levels')

                # Show the plot
                st.plotly_chart(sent_fig)

            with tab4:
                emotion_df = comments[['emotion']].value_counts().reset_index()
                emotion_df.columns = ['Emotion', 'Count']

                emotion_df = emotion_df.sort_values('Count', ascending=False)

                col1, col2 = st.columns(2)

                with col1:
                    emotion_df = emotion_df.sort_values('Count', ascending=False)
                    neutral_count = emotion_df[emotion_df['Emotion'] == 'neutral'].Count.values[0]
                    emotion_df = emotion_df[~emotion_df.Emotion.isin(['neutral'])]
                    # Create the Plotly bar plot
                    emotion_count_fig = px.bar(emotion_df,
                                               x='Emotion',
                                               y='Count',
                                               color='Count',
                                               color_continuous_scale='Viridis',
                                               title='Emotion Levels')
                    # Show the plot
                    st.plotly_chart(emotion_count_fig)
                with col2:
                    if neutral_count:
                        st.metric("Neutral", neutral_count,
                                  delta=0, delta_color="normal")
            with tab5:
                comments_pr = comments[['body', 'sentiment', 'emotion']].profile_report()
                st_profile_report(comments_pr)
