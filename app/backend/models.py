from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Media(Base):
    __tablename__ = 'media'
    id = Column(String, primary_key=True)
    source = Column(String, nullable=False)  # 'upload' | 'youtube'
    original_name = Column(String, nullable=True)
    path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    transcripts = relationship('Transcript', back_populates='media', cascade='all, delete-orphan')
    renders = relationship('Render', back_populates='media', cascade='all, delete-orphan')

class Transcript(Base):
    __tablename__ = 'transcript'
    id = Column(Integer, primary_key=True, autoincrement=True)
    media_id = Column(String, ForeignKey('media.id'))
    language = Column(String, default='en')
    srt_path = Column(String, nullable=True)
    json_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    media = relationship('Media', back_populates='transcripts')
    segments = relationship('Segment', back_populates='transcript', cascade='all, delete-orphan')

class Segment(Base):
    __tablename__ = 'segment'
    id = Column(Integer, primary_key=True, autoincrement=True)
    transcript_id = Column(Integer, ForeignKey('transcript.id'))
    start = Column(Float, nullable=False)
    end = Column(Float, nullable=False)
    text = Column(Text, nullable=False)

    transcript = relationship('Transcript', back_populates='segments')
    words = relationship('Word', back_populates='segment', cascade='all, delete-orphan')

class Word(Base):
    __tablename__ = 'word'
    id = Column(Integer, primary_key=True, autoincrement=True)
    segment_id = Column(Integer, ForeignKey('segment.id'))
    start = Column(Float, nullable=False)
    end = Column(Float, nullable=False)
    text = Column(String, nullable=False)

    segment = relationship('Segment', back_populates='words')

class Render(Base):
    __tablename__ = 'render'
    id = Column(Integer, primary_key=True, autoincrement=True)
    media_id = Column(String, ForeignKey('media.id'))
    style_id = Column(String, nullable=False)
    resolution = Column(String, nullable=True)
    output_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=True)
    error = Column(Text, nullable=True)

    media = relationship('Media', back_populates='renders')