from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    type = Column(String)
    site_admin = Column(Boolean)
    name = Column(String)


class Repository(Base):
    __tablename__ = 'repositories'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    full_name = Column(String)
    owner_userfk = Column(Integer, ForeignKey('users.id'))
    description = Column(String)
    size = Column(Integer)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    owner = relationship("User", back_populates="repositories")


User.repositories = relationship("Repository", order_by=Repository.id, back_populates="owner")


class Commit(Base):
    __tablename__ = 'commits'
    id = Column(String, primary_key=True)
    user_fk = Column(Integer, ForeignKey('users.id'))
    repo_fk = Column(Integer, ForeignKey('repositories.id'))
    created_at = Column(TIMESTAMP)


class Issue(Base):
    __tablename__ = 'issues'
    id = Column(Integer, primary_key=True)
    number = Column(Integer)
    user_fk = Column(Integer, ForeignKey('users.id'))
    repo_fk = Column(Integer, ForeignKey('repositories.id'))
    state = Column(String)
    locked = Column(Boolean)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    author_association = Column(String)
    title = Column(String)
    comments = Column(Integer)
    body = Column(Text)


class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True)
    user_fk = Column(Integer, ForeignKey('users.id'))
    issue_fk = Column(Integer, ForeignKey('issues.id'))
    commit_id = Column(Integer, ForeignKey('commits.id'))
    created_at = Column(TIMESTAMP)
    author_association = Column(String)
    body = Column(Text)
    sentiment = Column(String)
    emotion = Column(String)


class Reaction(Base):
    __tablename__ = 'reactions'
    id = Column(Integer, primary_key=True)
    user_fk = Column(Integer, ForeignKey('users.id'))
    issue_fk = Column(Integer, ForeignKey('issues.id'))
    created_at = Column(TIMESTAMP)
    author_association = Column(String)
    content = Column(String)
    comment_id = Column(Integer, ForeignKey('comments.id'))
    total_count = Column(Integer)
    plus_one = Column(Integer)
    minus_one = Column(Integer)
    laugh = Column(Integer)
    hooray = Column(Integer)
    confused = Column(Integer)
    heart = Column(Integer)
    rocket = Column(Integer)
    eyes = Column(Integer)



class File(Base):
    __tablename__ = 'files'
    id = Column(String, primary_key=True)
    name = Column(String)
    repo_fk = Column(Integer, ForeignKey('repositories.id'))
    extension_type = Column(String)


class FileCommit(Base):
    __tablename__ = 'file_commits'
    id = Column(Integer, primary_key=True)
    commit_fk = Column(String, ForeignKey('commits.id'))
    user_fk = Column(Integer, ForeignKey('users.id'))
    file_fk = Column(String, ForeignKey('files.id'))
    raw = Column(Text)
    child_fk = Column(Integer)


class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    user_fk = Column(Integer, ForeignKey('users.id'))
    event_type = Column(String)
    commit_fk = Column(Text, ForeignKey('commits.id'))
    created_at = Column(TIMESTAMP)
    issue_fk = Column(Integer, ForeignKey('issues.id'))
    repo_fk = Column(Integer, ForeignKey('repositories.id'))
    total_count = Column(Integer)
