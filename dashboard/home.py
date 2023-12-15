import os

import streamlit as st

from dashboard.db_util.db_import import import_db, DB_PATH

st.set_page_config(page_title="Ether Dash Tools", page_icon="🔥", layout="wide")

if not os.path.exists(DB_PATH):
    import_db()


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


setup_page()

st.write("# Ether Dash Tools 🔥")

st.markdown(
    """
        ## Architecture
    """
)

img_path = os.path.join(os.path.dirname(__file__), 'imgs', 'db_schema.png')

st.image(img_path, caption="", width=600)

st.markdown(
    """
        ## Commits
    """
)

img_path = os.path.join(os.path.dirname(__file__), 'imgs', 'commits_plot.png')

st.image(img_path, caption="")

st.markdown(
    """
        ## Comments
    """
)

img_path = os.path.join(os.path.dirname(__file__), 'imgs', 'sa-gauge.jpeg')

st.image(img_path, caption="", width=400)

st.markdown(
    """
        ## Issues
    """
)

img_path = os.path.join(os.path.dirname(__file__), 'imgs', 'issue_network.png')

st.image(img_path, caption="", width=400)
