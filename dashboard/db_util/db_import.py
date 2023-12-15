import pandas as pd
import os
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dashboard.db_util.models import Comment, Commit, Event, FileCommit, File, Issue, Reaction, Base, Repository, User

# from .models import Comment, Commit, Event, FileCommit, File, Issue, Reaction, Base, Repository, User

DIR_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = f'{DIR_PATH}/ethereum_go'
DB_NAME = 'ethereum_tool.db'
DB_PATH = f'{DIR_PATH}/{DB_NAME}'

FILE_MODEL_MAP = {
    'users.csv': User,
    'repositories.csv': Repository,
    'issues.csv': Issue,
    'comments_with_sent_emo.csv': Comment,
    'commits.csv': Commit,
    'events.csv': Event,
    'file_commits.csv': FileCommit,
    'files.csv': File,
    'reactions.csv': Reaction
}


def import_csv_to_table(model, filename):
    df = pd.read_csv(f'{DATA_DIR}/{filename}')
    df = df.drop_duplicates(subset='id', keep='first')
    missing_columns = [column for column in ['created_at', 'updated_at'] if column not in df.columns]
    if not missing_columns:
        df['created_at'] = pd.to_datetime(df['created_at'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        df['updated_at'] = pd.to_datetime(df['updated_at'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    data = df.to_dict(orient='records')
    rows = []
    for record in data:
        if 'created_at' in record:
            record['created_at'] = datetime.strptime(str(record['created_at']), '%Y-%m-%d %H:%M:%S')
        if 'updated_at' in record:
            record['created_at'] = datetime.strptime(str(record['created_at']), '%Y-%m-%d %H:%M:%S')
        if 'user_fk' in record:
            if not np.isnan(record['user_fk']):
                record['user_fk'] = int(record['user_fk'])
        if 'repo_fk' in record:
            if not np.isnan(record['repo_fk']):
                record['repo_fk'] = int(record['repo_fk'])
        rows.append(model(**record))
    return rows


def import_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    engine = create_engine(f'sqlite:///{DB_PATH}')
    Base.metadata.create_all(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    for file_name, model in FILE_MODEL_MAP.items():
        session = Session()
        print(file_name)
        session.add_all(import_csv_to_table(model, file_name))
        session.commit()
    session.close()


if __name__ == '__main__':
    import_db()
    # comments_df = pd.read_csv(f'{DATA_DIR}/comments_with_sent_emo.csv', quotechar='"')
    # print(comments_df.head(10))