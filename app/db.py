from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

# SQLite database (local file app.db in project root)
DATABASE_URL = "sqlite:///./app.db"

# Create engine and session
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# ==============================
# User model
# ==============================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)   # ✅ matches your auth_routes.py

    # Relationship: one user -> many uploads
    uploads = relationship("Upload", back_populates="user")


# ==============================
# Upload model
# ==============================
class Upload(Base):
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True)

    # Link to User
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="uploads")

    # Resume / JD storage
    resume_path = Column(String, nullable=True)
    resume_blob = Column(String, nullable=True)
    jd_path = Column(String, nullable=True)
    jd_blob = Column(String, nullable=True)

    # Interview-related
    questions = Column(Text, nullable=True)
    analysis_score = Column(Integer, nullable=True)
    analysis_summary = Column(Text, nullable=True)
    strengths = Column(Text, nullable=True)
    weaknesses = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


# ==============================
# Create all tables
# ==============================
Base.metadata.create_all(bind=engine)
