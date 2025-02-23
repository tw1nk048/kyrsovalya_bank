from sqlalchemy import (
    Column, Integer, String, Date, Numeric, ForeignKey, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.dialects.postgresql import MONEY
from dotenv import load_dotenv
import os

# Загрузите переменные окружения из файла .env
load_dotenv()

# Получите настройки подключения из переменных окружения
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

# Базовая модель
Base = declarative_base()

# Модель для таблицы `client`
class Client(Base):
    __tablename__ = 'client'
    id_client = Column(Integer, primary_key=True, autoincrement=True)
    clt_last_name = Column(String(32), nullable=False)
    clt_name = Column(String(32), nullable=False)
    clt_middle_name = Column(String(32))
    clt_date_birth = Column(Date, nullable=False)
    clt_residential_address = Column(String(64), nullable=False)
    clt_income = Column(MONEY, nullable=False)
    clt_passport_data = Column(String(10), nullable=False)
    clt_marital_status = Column(String(1), nullable=False)

    # Связи
    credits = relationship("Credit", back_populates="client")
    loan_repayments = relationship("LoanRepayment", back_populates="client")
    credit_histories = relationship("CreditHistory", back_populates="client")

# Модель для таблицы `credit`
class Credit(Base):
    __tablename__ = 'credit'
    id_credit = Column(Integer, primary_key=True, autoincrement=True)
    id_client = Column(Integer, ForeignKey('client.id_client'), nullable=False)
    id_credit_product = Column(Integer, ForeignKey('credit_products.id_credit_product'), nullable=False)
    crt_date_issue = Column(Date)
    crt_monthly_contributions = Column(MONEY, nullable=False)
    crt_maturity_date = Column(Date, nullable=False)
    crt_percent_on_credit = Column(Numeric(5, 2), nullable=False)
    crt_status_credit = Column(String(1), nullable=False)
    crt_sum_credit = Column(MONEY, nullable=False)

    # Связи
    client = relationship("Client", back_populates="credits")
    credit_product = relationship("CreditProduct", back_populates="credits")
    loan_repayments = relationship("LoanRepayment", back_populates="credit")
    credit_histories = relationship("CreditHistory", back_populates="credit")

# Модель для таблицы `credit_history`
class CreditHistory(Base):
    __tablename__ = 'credit_history'
    id_credit_history = Column(Integer, primary_key=True, autoincrement=True)
    id_client = Column(Integer, ForeignKey('client.id_client'), nullable=False)
    id_credit = Column(Integer, ForeignKey('credit.id_credit'), nullable=False)
    chs_amount_debt = Column(MONEY, nullable=False)
    chs_loan_status = Column(String(1), nullable=False)

    # Связи
    client = relationship("Client", back_populates="credit_histories")
    credit = relationship("Credit", back_populates="credit_histories")

# Модель для таблицы `credit_products`
class CreditProduct(Base):
    __tablename__ = 'credit_products'
    id_credit_product = Column(Integer, primary_key=True, autoincrement=True)
    cpr_name_product = Column(String(16), nullable=False)
    cpr_min_koef = Column(Numeric(5, 2), nullable=False)
    cpr_max_koef = Column(Numeric(5, 2))
    cpr_min_date_return = Column(Date, nullable=False)
    cpr_max_date_return = Column(Date)

    # Связи
    credits = relationship("Credit", back_populates="credit_product")

# Модель для таблицы `loan_repayments`
class LoanRepayment(Base):
    __tablename__ = 'loan_repayments'
    id_payout = Column(Integer, primary_key=True, autoincrement=True)
    id_client = Column(Integer, ForeignKey('client.id_client'), nullable=False)
    id_credit = Column(Integer, ForeignKey('credit.id_credit'), nullable=False)
    lnr_date_deposit = Column(Date, nullable=False)
    lnr_amount_payments = Column(MONEY, nullable=False)
    lnr_contribution_status = Column(String(1), nullable=False)

    # Связи
    client = relationship("Client", back_populates="loan_repayments")
    credit = relationship("Credit", back_populates="loan_repayments")

# Модель для таблицы `users`
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), default='user', nullable=False)

# Модель для таблицы `number`
class Number(Base):
    __tablename__ = 'number'
    numbers = Column(Integer, primary_key=True)

# Создание строки подключения
DATABASE_URI = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Создание движка и сессии
engine = create_engine(DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создание всех таблиц в базе данных (если их нет)
Base.metadata.create_all(bind=engine)