# controllers.py
from flask import Flask, render_template, request, session, redirect, url_for, send_file, flash
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import io
import os
import psycopg2

import utils.db
from utils.db import connect_db
from werkzeug.security import generate_password_hash, check_password_hash

def setup_routes(app):
    @app.route('/')
    def home():
        conn = utils.db.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT cpr_name_product, cpr_min_koef, cpr_max_koef, cpr_min_date_return, cpr_max_date_return FROM credit_products")
        credit_products = cursor.fetchall()
        conn.close()

        username = session.get('username')
        role = session.get('role')
        return render_template('home.html', username=username, role=role, credit_products=credit_products)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            conn.close()
            if user and check_password_hash(user[2], password):
                session['username'] = username
                session['role'] = user[3]
                return redirect(url_for('home'))
            else:
                flash("Неправильное имя пользователя или пароль")
                return redirect(url_for('login'))
        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            password = generate_password_hash(request.form['password'])
            clt_last_name = request.form['clt_last_name']
            clt_name = request.form['clt_name']
            clt_middle_name = request.form['clt_middle_name']
            clt_date_birth = request.form['clt_date_birth']
            clt_residential_address = request.form['clt_residential_address']
            clt_income = request.form['clt_income']
            clt_passport_data = request.form['clt_passport_data']
            clt_marital_status = request.form['clt_marital_status']

            clt_passport_data = clt_passport_data.replace(" ", "")

            try:
                conn = connect_db()
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO client (clt_last_name, clt_name, clt_middle_name, clt_date_birth, 
                                       clt_residential_address, clt_income, clt_passport_data, clt_marital_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_client
                """, (clt_last_name, clt_name, clt_middle_name, clt_date_birth,
                      clt_residential_address, clt_income, clt_passport_data, clt_marital_status))

                client_id = cursor.fetchone()[0]
                cursor.execute("INSERT INTO users (id, username, password) VALUES (%s, %s, %s)",
                               (client_id, username, password))

                conn.commit()
                conn.close()
                return redirect(url_for('login'))
            except psycopg2.errors.UniqueViolation:
                flash("Пользователь с таким именем уже существует", "error")
                return redirect(url_for('register'))
        return render_template('register.html')

    @app.route('/logout')
    def logout():
        session.pop('username', None)
        session.pop('role', None)
        return redirect(url_for('home'))

    @app.route('/profile')
    def profile():
        if 'username' not in session:
            return redirect(url_for('login'))
        username = session['username']
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT u.id, c.clt_last_name, c.clt_name, c.clt_middle_name, c.clt_date_birth, c.clt_residential_address, c.clt_income, c.clt_passport_data, c.clt_marital_status
            FROM users u
            JOIN client c ON u.id = c.id_client
            WHERE u.username = %s
        """, (username,))
        client_info = cursor.fetchone()

        if not client_info:
            conn.close()
            flash("Не удалось загрузить информацию профиля")
            return redirect(url_for('home'))

        if client_info[8] == '0':
            marry = 'Холост'
        if client_info[8] == '1':
            marry = 'Женат/Замужем'
        if client_info[8] == '2':
            marry = 'Разведен/а'

        user_data = {
            'id': client_info[0],
            'last_name': client_info[1],
            'name': client_info[2],
            'middle_name': client_info[3],
            'date_birth': client_info[4],
            'residential_address': client_info[5],
            'income': client_info[6],
            'passport_data': client_info[7],
            'marital_status': marry
        }

        cursor.execute("""
            SELECT id_credit, id_credit_product, crt_date_issue, crt_monthly_contributions, crt_maturity_date, crt_percent_on_credit, crt_status_credit, crt_sum_credit
            FROM credit
            WHERE id_client = %s
        """, (user_data['id'],))
        credits = cursor.fetchall()

        user_credits = []
        for credit in credits:

            credit_stat = ''
            if credit[6] == '0':
                credit_stat = 'На рассмотрение'
            if credit[6] == '1':
                credit_stat = 'Выдан'
            if credit[6] == '2':
                credit_stat = 'Отказано'

            credit_data = {
                'id': credit[0],
                'product_id': credit[1],
                'date_issue': credit[2],
                'monthly_contributions': credit[3],
                'maturity_date': credit[4],
                'percent_on_credit': int(credit[5] * 100),
                'status': credit_stat,
                'sum': credit[7]
            }

            cursor.execute("""
                SELECT cpr_name_product, cpr_min_koef, cpr_max_koef, cpr_min_date_return, cpr_max_date_return
                FROM credit_products
                WHERE id_credit_product = %s
            """, (credit_data['product_id'],))
            product_info = cursor.fetchone()

            credit_data['product_name'] = product_info[0]
            credit_data['min_koef'] = product_info[1]
            credit_data['max_koef'] = product_info[2]
            credit_data['min_date_return'] = product_info[3]
            credit_data['max_date_return'] = product_info[4]

            user_credits.append(credit_data)

        cursor.execute("""
            SELECT id_payout, id_credit, lnr_date_deposit, lnr_amount_payments, lnr_contribution_status
            FROM loan_repayments
            WHERE id_client = %s
        """, (user_data['id'],))
        payouts = cursor.fetchall()

        user_payouts = []
        for payout in payouts:
            loan_stat = ''
            if payout[4] == '0':
                loan_stat = 'Заплачено'
            if payout[4] == '1':
                loan_stat = 'Просрочено'
            payout_data = {
                'id': payout[0],
                'credit_id': payout[1],
                'date_deposit': payout[2],
                'amount_payments': payout[3],
                'contribution_status': loan_stat
            }
            user_payouts.append(payout_data)

        conn.close()

        return render_template('profile.html', user_data=user_data, user_credits=user_credits, user_payouts=user_payouts)

