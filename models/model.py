import enum
from sqlalchemy import Table, MetaData, Column, String, Integer, Text, Boolean, Date, ForeignKey, Float, DECIMAL, Enum, \
    TIMESTAMP, DATETIME
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, date

Base = declarative_base()
metadata = MetaData()


# User Table
user = Table(
    'users',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('password', String),
    Column('email', String, unique=True, index=True),
    Column('name', String),
    Column('phone_number', String),
    Column('is_admin',Boolean,default=False),
    Column('date_joined', Date, default=date.today),
)

# Book Table
book = Table(
    'books',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('special_book_id', Integer, index=True),
    Column('title', String, index=True),
    Column('author', String, index=True),
    Column('publication_date', Date),
    Column('category',String),
    Column('description', String, default='description is not available'),
    Column('price', Float, default=0),
    Column('quantity', Integer, default=0),
    Column('language', String, default="Russian"),
    Column('barcode', String, index=True)
)

# Wishlist Table
wishlist = Table(
    'wishlists',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('book_id', Integer, ForeignKey('books.id')),
    Column('number_of_books_left', Integer, default=0),
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
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('book_id', Integer, ForeignKey('books.id')),
    Column('quantity', Integer),
)

# Review Table
review = Table(
    'reviews',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('book_id', Integer, ForeignKey('books.id')),
    Column('rating', Integer, default=0),
    Column('comment', String,default='no comments yet'),
    Column('review_date', TIMESTAMP, default=datetime.utcnow)
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
age_categories = Table(
    'age_category',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('ages', String, unique=True, index=True)
)


categories = Table(
    'category',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('category_name', String, unique=True, index=True),
)

categories_in_ages = Table(
    'categories_in_ages',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('age_id', Integer, ForeignKey('age_category.id')),
    Column('category_id', Integer, ForeignKey('category.id'))
)



