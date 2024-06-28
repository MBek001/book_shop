import enum
from sqlalchemy import Table, MetaData, Column, String, Integer, Text, Boolean, Date, ForeignKey, Float, DECIMAL, Enum, \
    TIMESTAMP, DATETIME
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()
metadata = MetaData()


# User Table
user = Table(
    'users',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('username', String, unique=True, index=True),
    Column('password', String),
    Column('email', String, unique=True, index=True),
    Column('first_name', String),
    Column('last_name', String),
    Column('address', String),
    Column('phone_number', String),
    Column('is_admin',Boolean),
    Column('date_joined', TIMESTAMP, default=datetime.utcnow),
    Column('last_login', TIMESTAMP),
)

# Book Table
book = Table(
    'books',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('title', String, index=True),
    Column('author', String, index=True),
    Column('publication_date', TIMESTAMP),
    Column('genre', String),
    Column('description', String),
    Column('price', Float),
    Column('quantity', Integer),
    Column('language', String),
    Column('average_rating', Float),
    Column('number_of_reviews', Integer)
)

# Wishlist Table
wishlist = Table(
    'wishlists',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('book_id', Integer, ForeignKey('books.id')),
    Column('number_of_books_left', Integer),
    Column('date_created', TIMESTAMP, default=datetime.utcnow)
)

# Order Table
order = Table(
    'orders',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('order_date', TIMESTAMP, default=datetime.utcnow),
    Column('address', String),
    Column('order_status', String),
    Column('total_price', Float),
    Column('phone_number', String)
)

# OrderItem Table
shopping_cart = Table(
    'shopping_cart',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('book_id', Integer, ForeignKey('books.id')),
    Column('quantity', Integer),
    Column('price_per_unit', Float),
    Column('total_price', Float)
)

# Review Table
review = Table(
    'reviews',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('book_id', Integer, ForeignKey('books.id')),
    Column('rating', Integer),
    Column('comment', String),
    Column('review_date', TIMESTAMP, default=datetime.utcnow)
)

# Category Table
category = Table(
    'categories',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('category_name', String, index=True),
    Column('description', String),
)


# Payment Table
payment = Table(
    'payments',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('order_id', Integer, ForeignKey('orders.id')),
    Column('payment_date', TIMESTAMP, default=datetime.utcnow),
    Column('amount', Float),
    Column('payment_method', String),
    Column('payment_status', String)
)

# Promotion Table
promotion = Table(
    'promotions',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('promotion_name', String, unique=True, index=True),
    Column('description', String),
    Column('discount_percentage', Float),
    Column('start_date', TIMESTAMP),
    Column('end_date', TIMESTAMP)
)

# Images Table
images = Table(
    'images',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('photo_url', String)
)

image_items = Table(
    'image_item',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('book_id', Integer, ForeignKey('books.id')),
    Column('photo_id', Integer, ForeignKey('images.id'))
)

#Age categories
categories = Table(
    'category',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('ages', String, unique=True, index=True),
    Column('number_of_books', Integer)
)

#genres
Genres = Table(
    'genre',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('category_id', Integer, ForeignKey('category.id')),
    Column('genres', String, unique=True, index=True),
    Column('number_of_books', Integer)
)

books_genres = Table(
    'books_genre',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('book_id', Integer, ForeignKey('books.id')),
    Column('genre_id', Integer, ForeignKey('genre.id'))
)



