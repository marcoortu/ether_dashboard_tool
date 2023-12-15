import sqlalchemy
import os
import streamlit as st
import pandas as pd

DIR_PATH = os.path.dirname(os.path.abspath(__file__))

# Create a connection to your SQLite database
engine = sqlalchemy.create_engine(f'sqlite:///{DIR_PATH}/ethereum_tool.db')


@st.cache_data
def load_repositories():
    # Assuming your repositories table is named 'repositories'
    with engine.connect() as conn:
        # Assuming your repositories table is named 'repositories'
        return pd.read_sql("SELECT id, name FROM repositories ORDER BY name", conn)
