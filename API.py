from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

app = FastAPI()
Base = declarative_base()
engine = create_engine("sqlite:///likes.db")
SessionLocal = sessionmaker(bind=engine)

# Models
class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Like(Base):
    __tablename__ = "likes"
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    user_id = Column(String, nullable=False)
    liked_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint('post_id', 'user_id', name='unique_like'),)

# Schemas
class PostCreate(BaseModel):
    content: str

class LikeCreate(BaseModel):
    post_id: int
    user_id: str

# Create DB
Base.metadata.create_all(engine)

@app.post("/post")
def create_post(post: PostCreate):
    db = SessionLocal()
    new_post = Post(content=post.content)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return {"id": new_post.id, "message": "Post created successfully"}

@app.post("/like")
def like_post(like: LikeCreate):
    db = SessionLocal()
    if not db.query(Post).filter(Post.id == like.post_id).first():
        raise HTTPException(status_code=404, detail="Post not found")
    if db.query(Like).filter_by(post_id=like.post_id, user_id=like.user_id).first():
        raise HTTPException(status_code=400, detail="User has already liked this post")
    new_like = Like(post_id=like.post_id, user_id=like.user_id)
    db.add(new_like)
    db.commit()
    return {"message": "Post liked successfully"}

@app.get("/post/{post_id}/likes")
def get_likes(post_id: int):
    db = SessionLocal()
    count = db.query(Like).filter_by(post_id=post_id).count()
    return {"post_id": post_id, "like_count": count}

@app.get("/top-posts")
def get_top_posts():
    db = SessionLocal()
    result = db.query(Like.post_id, func.count().label("like_count"))\
               .group_by(Like.post_id)\
               .order_by(func.count().desc())\
               .limit(5).all()
    return [{"post_id": row.post_id, "like_count": row.like_count} for row in result]