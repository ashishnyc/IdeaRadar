from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime,
    ForeignKey, ARRAY, BigInteger
)
from sqlalchemy.orm import declarative_base, relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class RawPost(Base):
    __tablename__ = "raw_posts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    platform = Column(String(50), nullable=False)
    source_url = Column(String(2048), nullable=False)
    author_hash = Column(String(64))
    title = Column(String(512))
    body = Column(Text)
    upvotes = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    created_at = Column(DateTime, nullable=False)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    processed_post = relationship("ProcessedPost", back_populates="raw_post", uselist=False)


class ProcessedPost(Base):
    __tablename__ = "processed_posts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    raw_post_id = Column(BigInteger, ForeignKey("raw_posts.id"), nullable=False)
    clean_text = Column(Text)
    category = Column(String(100))
    confidence = Column(Float)
    niche = Column(String(100))
    severity = Column(Integer)
    sentiment = Column(Float)
    summary = Column(Text)
    embedding = Column(Vector(384))

    raw_post = relationship("RawPost", back_populates="processed_post")
    cluster_memberships = relationship("ClusterMember", back_populates="processed_post")


class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    label = Column(String(256))
    ai_summary = Column(Text)
    post_count = Column(Integer, default=0)
    avg_sentiment = Column(Float)
    platform_count = Column(Integer, default=0)
    first_seen = Column(DateTime)
    last_seen = Column(DateTime)
    opportunity_score = Column(Float)

    members = relationship("ClusterMember", back_populates="cluster")
    opportunity = relationship("Opportunity", back_populates="cluster", uselist=False)


class ClusterMember(Base):
    __tablename__ = "cluster_members"

    cluster_id = Column(BigInteger, ForeignKey("clusters.id"), primary_key=True)
    processed_post_id = Column(BigInteger, ForeignKey("processed_posts.id"), primary_key=True)
    similarity_score = Column(Float)

    cluster = relationship("Cluster", back_populates="members")
    processed_post = relationship("ProcessedPost", back_populates="cluster_memberships")


class ScrapeCheckpoint(Base):
    __tablename__ = "scrape_checkpoints"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    platform = Column(String(50), nullable=False)
    source_key = Column(String(256), nullable=False)
    last_id = Column(String(256))
    last_timestamp = Column(DateTime)


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    cluster_id = Column(BigInteger, ForeignKey("clusters.id"), nullable=False)
    title = Column(String(512))
    description = Column(Text)
    score = Column(Float)
    status = Column(String(50), default="new")
    idea_brief = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cluster = relationship("Cluster", back_populates="opportunity")
    alerts = relationship("Alert", back_populates="opportunity")


class Niche(Base):
    __tablename__ = "niches"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False)
    parent_id = Column(BigInteger, ForeignKey("niches.id"), nullable=True)
    keywords = Column(ARRAY(String))
    post_count = Column(Integer, default=0)

    children = relationship("Niche", backref="parent", remote_side=[id])


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    opportunity_id = Column(BigInteger, ForeignKey("opportunities.id"), nullable=False)
    channel = Column(String(100))
    sent_at = Column(DateTime, default=datetime.utcnow)
    payload = Column(Text)

    opportunity = relationship("Opportunity", back_populates="alerts")
