import base64
import os

import pandas as pd
import streamlit as st
import plotly.express as px
import textwrap
from wordcloud import WordCloud
import matplotlib.pyplot as plt

from streamlit_agraph import agraph, Node, Edge, Config

from dashboard.db_util.config import load_repositories, engine
from dashboard.home import setup_page

DIR_PATH = os.path.dirname(os.path.abspath(__file__))


def get_image_as_base64(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


def get_repo_index(repo_data):
    try:
        return repo_data['name'].tolist().index(st.session_state['repo_name'])
    except ValueError:
        # If the current repo is not in the list, default to the first item
        return 0


def get_delta_value(df, column_name):
    last_data = df.index.values[0]
    before_last_data = df.index.values[1]
    print(last_data, df.loc[last_data, column_name])
    return int(df.loc[last_data, column_name] - df.loc[before_last_data, column_name])


@st.cache_data
def load_issues(repo_id):
    # Assuming your repositories table is named 'repositories'
    # Query to count commits per day for a given repository
    query = f"""
        SELECT id
        FROM issues
        WHERE repo_fk = {repo_id}
        ORDER BY comments DESC 
        """
    with engine.connect() as conn:
        return pd.read_sql(query, conn)


@st.cache_data
def load_issue(issue_id):
    # Assuming your repositories table is named 'repositories'
    # Query to count commits per day for a given repository
    query = f"""
        SELECT *
        FROM issues
        WHERE id = {issue_id}
        """
    with engine.connect() as conn:
        return pd.read_sql(query, conn).iloc[0]


@st.cache_data
def get_comments_by_issue(issue_id):
    # Query to count commits per day for a given repository
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
def get_reactions_by_issue(issue_id):
    query = f"""
        SELECT  r.*
        FROM reactions AS r, comments AS c
        WHERE c.issue_fk = {issue_id} AND r.comment_id = c.id
        ORDER BY r.created_at DESC 
        """
    with engine.connect() as conn:
        # return pd.read_sql(query, conn).loc[0, 'comm_count']
        return pd.read_sql(query, conn)


@st.cache_data
def get_events_by_issue(issue_id):
    query = f"""
        SELECT *
        FROM events
        WHERE issue_fk = {issue_id}
        """
    with engine.connect() as conn:
        # return pd.read_sql(query, conn).loc[0, 'comm_count']
        return pd.read_sql(query, conn)


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

if repo_name:
    # Get repository ID based on selected name
    repo_id = repo_data[repo_data['name'] == repo_name]['id'].iloc[0]

    issues_data = load_issues(repo_id)
    issue_id = st.sidebar.selectbox('Select an Issue', issues_data['id'])

    if issue_id:
        issue_id = issues_data[issues_data['id'] == issue_id]['id'].iloc[0]

        issue = load_issue(issue_id)
        if not issue.empty:
            st.markdown(f"# Title: {issue.title}")
            with st.expander("## Description"):
                # st.markdown(f"## Description:")
                text = issue.body.replace("\\n", '')
                st.text(textwrap.fill(f"{text}", width=200))

            reactions = get_reactions_by_issue(issue_id)

            comments = get_comments_by_issue(issue_id)
            if not reactions.empty:
                one_sum = reactions.plus_one.sum()
                minus_one_sum = reactions.minus_one.sum()
                laugh_sum = reactions.laugh.sum()
                hooray_sum = reactions.hooray.sum()
                confused_sum = reactions.confused.sum()
                heart_sum = reactions.heart.sum()
                rocket_sum = reactions.rocket.sum()
                eyes_sum = reactions.eyes.sum()

                # Custom CSS to center the graph
                centering_css = """
                    <style>
                        .st-agraph {
                            display: flex;
                            justify-content: center;
                        }
                    </style>
                """

                # Inject custom CSS with st.markdown
                st.markdown(centering_css, unsafe_allow_html=True)

                tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Reactions", "Word Cloud",
                                                              "Sentiment", "Emotions",
                                                              "Network", "Events"])

                with tab1:
                    data = {
                        'Reaction': ['👍', '👎', '😄', '🎉', '😕', '❤️', '🚀', '👀'],
                        'Frequency': [one_sum, minus_one_sum, laugh_sum, hooray_sum,
                                      confused_sum, heart_sum, rocket_sum, eyes_sum]
                    }
                    df = pd.DataFrame(data)
                    df = df.sort_values('Frequency', ascending=False)
                    # Create a Plotly bar plot
                    fig = px.bar(df, x='Reaction', y='Frequency',
                                 title='Reactions', color='Frequency',
                                 color_continuous_scale='Viridis')

                    # Display the plot in Streamlit
                    st.plotly_chart(fig)

                    col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(9)
                    with col1:
                        st.metric("Total Reactions",
                                  reactions.total_count.sum(),
                                  delta=0,
                                  delta_color="normal")
                    with col2:
                        st.metric("👍", one_sum,
                                  delta=0, delta_color="normal")
                    with col3:
                        st.metric("👎", minus_one_sum,
                                  delta=0, delta_color="normal")
                    with col4:
                        st.metric("😄", laugh_sum,
                                  delta=0, delta_color="normal")
                    with col5:
                        st.metric("🎉", hooray_sum,
                                  delta=0, delta_color="normal")
                    with col6:
                        st.metric("😕", confused_sum,
                                  delta=0, delta_color="normal")
                    with col7:
                        st.metric("❤️", heart_sum,
                                  delta=0, delta_color="normal")
                    with col8:
                        st.metric("🚀", rocket_sum,
                                  delta=0, delta_color="normal")
                    with col9:
                        st.metric("👀", eyes_sum,
                                  delta=0, delta_color="normal")

                with tab2:
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
                    sentiment_df = comments['sentiment'].value_counts().reset_index()
                    sentiment_df.columns = ['Sentiment', 'Count']

                    # Sort the DataFrame by 'Count' in descending order
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
                    col1, col2 = st.columns(2)

                    emotion_df = comments['emotion'].value_counts().reset_index()
                    emotion_df.columns = ['Emotion', 'Count']
                    emotion_df.set_index('Emotion', inplace=True)
                    emotion_df = emotion_df.sort_values('Count', ascending=False)
                    if 'neutral' in emotion_df.index.values:
                        neutral_count = emotion_df[emotion_df.index.isin(['neutral'])].loc['neutral', 'Count']
                    else:
                        neutral_count = 0
                    emotion_df = emotion_df[~emotion_df.index.isin(['neutral'])]
                    with col1:
                        # Create the Plotly bar plot
                        sent_fig = px.bar(emotion_df, x=emotion_df.index,
                                          y='Count',
                                          color='Count',
                                          color_continuous_scale='Viridis',
                                          title='Emotion Levels')

                        st.plotly_chart(sent_fig)
                    with col2:
                        if neutral_count:
                            st.metric("Neutral", neutral_count,
                                      delta=0, delta_color="normal")

                with tab5:
                    dev_main_img = get_image_as_base64(f"{DIR_PATH}/../imgs/dev_main.png")
                    dev_img = get_image_as_base64(f"{DIR_PATH}/../imgs/dev.png")
                    if not comments.empty:
                        nodes = []
                        edges = []
                        comments_rows = comments.to_dict("records")
                        user_ids = set([c['user_fk'] for c in comments_rows])
                        nodes.append(Node(id=int(issue['user_fk']),
                                          label=int(issue['user_fk']),
                                          size=30,
                                          shape="circularImage",
                                          image=f"data:image/jpeg;base64,{dev_main_img}"
                                          ))
                        if int(issue['user_fk']) in user_ids:
                            user_ids.remove(int(issue['user_fk']))
                        for user_id in user_ids:
                            nodes.append(Node(id=user_id,
                                              label=user_id,
                                              size=20,
                                              shape="circularImage",
                                              image=f"data:image/jpeg;base64,{dev_img}"
                                              ))
                        if len(comments_rows) > 1:
                            for i, comment in enumerate(comments_rows[:len(comments_rows) - 1]):
                                edges.append(Edge(source=comment["user_fk"],
                                                  # label="contributed",
                                                  target=comments_rows[i + 1]["user_fk"],
                                                  # **kwargs
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
                with tab6:

                    col1, col2 = st.columns(2)

                    events = get_events_by_issue(issue_id)

                    with col1:
                        events_count = events[['event_type']][
                            ~events['event_type'].isin(['mentioned', 'subscribed'])
                        ].value_counts().reset_index()
                        events_count.columns = ['Type', 'Count']

                        events_count = events_count.sort_values('Count', ascending=False)

                        # Create the Plotly bar plot
                        events_count_fig = px.bar(events_count,
                                                  x='Type',
                                                  y='Count',
                                                  color='Count',
                                                  color_continuous_scale='Viridis',
                                                  title='Event Types')

                        # Show the plot
                        st.plotly_chart(events_count_fig)

                    with col2:
                        events_count = events[['event_type']][
                            events['event_type'].isin(['mentioned', 'subscribed'])
                        ].value_counts().reset_index()
                        events_count.columns = ['Type', 'Count']
                        events_count.set_index('Type', inplace=True)
                        st.metric("#Mentioned", events_count.loc['mentioned', 'Count'],
                                  delta=0, delta_color="normal")
                        st.metric("#Subscribed", events_count.loc['subscribed', 'Count'],
                                  delta=0, delta_color="normal")
