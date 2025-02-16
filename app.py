import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, session, redirect, url_for, send_file, flash
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import io
import re
import psycopg2

from dateutil.relativedelta import relativedelta
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secret_key'


def connect_db():
    dbname = os.getenv('DB_NAME')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')

    return psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )


@app.route('/')
def home():
    conn = connect_db()
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


@app.route('/admin')
def admin():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    return render_template('admin.html')


@app.route('/view_table/<table_name>')
def view_table(table_name):
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = connect_db()
    cursor = conn.cursor()

    table_mapping = {
        'credit': ('credit', ['id_credit', 'id_client', 'id_credit_product', 'crt_date_issue', 'crt_monthly_contributions', 'crt_maturity_date', 'crt_percent_on_credit', 'crt_status_credit', 'crt_sum_credit']),
        'loan_repayments': ('loan_repayments', ['id_payout', 'id_client', 'id_credit', 'lnr_date_deposit', 'lnr_amount_payments', 'lnr_contribution_status']),
        'client': ('client', ['id_client', 'clt_last_name', 'clt_name', 'clt_middle_name', 'clt_date_birth', 'clt_residential_address', 'clt_income', 'clt_passport_data', 'clt_marital_status']),
        'credit_history': ('credit_history', ['id_credit_history', 'id_client', 'id_credit', 'chs_amount_debt', 'chs_loan_status']),
        'credit_products': ('credit_products', ['id_credit_product', 'cpr_name_product', 'cpr_min_koef', 'cpr_max_koef', 'cpr_min_date_return', 'cpt_max_date_return']),
        'users': ('users', ['id', 'username', 'role']),
    }

    if table_name not in table_mapping:
        return redirect(url_for('admin'))

    table_title, columns = table_mapping[table_name]

    if table_title == 'users':
        cursor.execute(f"SELECT id, username, role FROM {table_title}")
        rows = cursor.fetchall()
        conn.close()
        return render_template('view_table.html', table_title=table_title, columns=columns, rows=rows)

    cursor.execute(f"SELECT * FROM {table_title}")
    rows = cursor.fetchall()
    conn.close()

    return render_template('view_table.html', table_title=table_title, columns=columns, rows=rows)


@app.route('/add_row/<table_name>', methods=['GET', 'POST'])
def add_row(table_name):
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    table_mapping = {
        'credit': ['id_client', 'id_credit_product', 'crt_date_issue', 'crt_monthly_contributions', 'crt_maturity_date', 'crt_percent_on_credit', 'crt_status_credit', 'crt_sum_credit'],
        'loan_repayments': ['id_client', 'id_credit', 'lnr_date_deposit', 'lnr_amount_payments', 'lnr_contribution_status'],
        'client': ['clt_last_name', 'clt_name', 'clt_middle_name', 'clt_date_birth', 'clt_residential_address', 'clt_income', 'clt_passport_data', 'clt_marital_status'],
        'credit_history': ['id_client', 'id_credit', 'chs_amount_debt', 'chs_loan_status'],
        'credit_products': ['cpr_name_product', 'cpr_min_koef', 'cpr_max_koef', 'cpr_min_date_return', 'cpr_max_date_return'],
        'users': ['id', 'username', 'password', 'role'],
    }
    table_mapping_print = {
        'credit': ['ID клиента', 'ID кредитного продукта', 'Дата взятия', 'Ежемесячный платеж', 'Дата выплачивания', 'Процент', 'Статус 0 - на рассмотрение. 1 - выдан 2 - отказано', 'Сумма кредита'],
        'loan_repayments': ['ID клиента', 'ID кредита', 'Дата внесения средств', 'Сумма выплаты', 'Статус 0 - заплачено 1 - просрочено 2 - на рассмотрение'],
        'client': ['Фамилия', 'Имя', 'Отчество', 'Дата рождения', 'Адрес проживания', 'Заработок', 'Паспорт', 'Статус 0 - холост 1 - женат/замужем 2 - разведен/а'],
        'credit_history': ['ID клиента', 'ID кредита', 'Сумма долга', 'Статус 0 - заплачено 1 - просрочено'],
        'credit_products': ['Названия продукта', 'Мин. коэф.', 'Макс. коэф.', 'Мин. дата возврата', 'Макс. дата возврата'],
        'users': ['ID', 'Логин', 'Пароль', 'Роль'],
    }

    if table_name not in table_mapping:
        return redirect(url_for('admin'))

    columns = table_mapping[table_name]
    columns_print = table_mapping_print[table_name]

    if request.method == 'POST':
        values = []
        for column in columns:
            value = request.form[column]
            if value == '':
                value = None
            values.append(value)

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))})",
            tuple(values)
        )
        conn.commit()
        conn.close()

        return redirect(url_for('view_table', table_name=table_name))

    return render_template('add_row.html', table_name=table_name, columns=columns)


@app.route('/delete_row/<table_name>/<int:row_id>', methods=['GET', 'POST'])
def delete_row(table_name, row_id):
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    table_mapping = {
        'credit': 'id_credit',
        'loan_repayments': 'id_payout',
        'client': 'id_client',
        'credit_history': 'id_credit_history',
        'credit_products': 'id_credit_product',
        'users': 'id',
    }

    if table_name not in table_mapping:
        return redirect(url_for('admin'))

    id_column = table_mapping[table_name]

    conn = connect_db()
    cursor = conn.cursor()

    if table_name == 'client':
        cursor.execute(f"SELECT id_credit FROM credit_history WHERE id_client = %s AND chs_amount_debt::numeric > 0", (row_id,))
        debt = cursor.fetchone()
        if debt:
            # Если задолженность существует, показать подтверждение
            return render_template('confirm_delete.html', row_id=row_id, table_name=table_name)

    cursor.execute(f"DELETE FROM {table_name} WHERE {id_column} = %s", (row_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('view_table', table_name=table_name))

@app.route('/confirm_delete/<table_name>/<int:row_id>', methods=['POST'])
def confirm_delete(table_name, row_id):
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    table_mapping = {
        'credit': 'id_credit',
        'loan_repayments': 'id_payout',
        'client': 'id_client',
        'credit_history': 'id_credit_history',
        'credit_products': 'id_credit_product',
        'users': 'id',
    }

    if table_name not in table_mapping:
        return redirect(url_for('admin'))

    id_column = table_mapping[table_name]

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table_name} WHERE {id_column} = %s", (row_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('view_table', table_name=table_name))



@app.route('/edit_row/<table_name>/<int:row_id>', methods=['GET', 'POST'])
def edit_row(table_name, row_id):
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    table_mapping = {
        'credit': ['id_client', 'id_credit_product', 'crt_date_issue', 'crt_monthly_contributions', 'crt_maturity_date', 'crt_percent_on_credit', 'crt_status_credit', 'crt_sum_credit'],
        'loan_repayments': ['id_client', 'id_credit', 'lnr_date_deposit', 'lnr_amount_payments', 'lnr_contribution_status'],
        'client': ['clt_last_name', 'clt_name', 'clt_middle_name', 'clt_date_birth', 'clt_residential_address', 'clt_income', 'clt_passport_data', 'clt_marital_status'],
        'credit_history': ['id_client', 'id_credit', 'chs_amount_debt', 'chs_loan_status'],
        'credit_products': ['cpr_name_product', 'cpr_min_koef', 'cpr_max_koef', 'cpr_min_date_return', 'cpr_max_date_return'],
        'users': ['id', 'username', 'password', 'role'],
    }

    id_mapping = {
        'credit': 'id_credit',
        'loan_repayments': 'id_payout',
        'client': 'id_client',
        'credit_history': 'id_credit_history',
        'credit_products': 'id_credit_product',
        'users': 'id',
    }

    if table_name not in table_mapping:
        return redirect(url_for('admin'))

    columns = table_mapping[table_name]
    id_column = id_mapping[table_name]

    conn = connect_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        values = [request.form[column] for column in columns]
        update_query = f"UPDATE {table_name} SET {', '.join([f'{col} = %s' for col in columns])} WHERE {id_column} = %s"
        cursor.execute(update_query, values + [row_id])
        conn.commit()
        conn.close()

        return redirect(url_for('view_table', table_name=table_name))

    cursor.execute(f"SELECT {', '.join(columns)} FROM {table_name} WHERE {id_column} = %s", (row_id,))
    row = cursor.fetchone()
    conn.close()

    return render_template('edit_row.html', table_name=table_name, columns=columns, row=row, zip=zip)


@app.route('/report1', methods=['GET', 'POST'])
def report1():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    data = None
    year_from = None
    year_to = None
    pdf_link = None

    if request.method == 'POST':
        year_from = request.form['year_from']
        year_to = request.form['year_to']

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT crt.id_credit, clt.clt_last_name, clt.clt_name, crp.cpr_name_product, 
                   crt.crt_date_issue, crt.crt_monthly_contributions, crt.crt_maturity_date, 
                   crt.crt_percent_on_credit, crt.crt_sum_credit
            FROM credit crt
            INNER JOIN client clt ON clt.id_client = crt.id_client
            INNER JOIN credit_products crp ON crp.id_credit_product = crt.id_credit_product
            WHERE crt.crt_date_issue >= %s AND crt.crt_date_issue < %s
            ORDER BY crt.id_credit
        """, (year_from, year_to))
        data = cursor.fetchall()
        cursor.close()
        conn.close()

        if data:
            pdf_buffer = generate_pdf(data)
            pdf_directory = 'reports'
            if not os.path.exists(pdf_directory):
                os.makedirs(pdf_directory)
            pdf_path = f"{pdf_directory}/report1_{year_from}_{year_to}.pdf"
            with open(pdf_path, 'wb') as f:
                f.write(pdf_buffer.getvalue())
            pdf_link = url_for('download_pdf', filename=pdf_path)

    return render_template('report1.html', data=data, year_from=year_from, year_to=year_to, pdf_link=pdf_link)


@app.route('/download/<path:filename>', methods=['GET'])
def download_pdf(filename):
    return send_file(filename, as_attachment=True)


def generate_pdf(data):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    font_path = "djsans/DejaVuSans.ttf"
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

    p.setFont("DejaVuSans", 8)
    p.drawString(50, height - 40, "Отчет по взятию кредитов по годам")

    headers = ["ID credit", "Фамилия", "Имя", "Продукт", "Дата взятия",
               "Платеж", "Дата выплаты", "Процент", "Сумма кредита"]

    x_offsets = [10, 50, 100, 150, 240, 300, 360, 440, 490]
    y_offset = height - 60
    line_height = 12

    for header, x_offset in zip(headers, x_offsets):
        p.drawString(x_offset, y_offset, header)

    y_offset -= line_height

    for row in data:
        x_offsets = [10, 50, 100, 150, 240, 300, 360, 440, 490]
        for item, x_offset in zip(row, x_offsets):
            p.drawString(x_offset, y_offset, str(item))
        y_offset -= line_height

    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer


@app.route('/report2', methods=['GET', 'POST'])
def report2():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    data = None

    if request.method == 'POST':

        onegod_value = request.form['onegod_tf']
        lastgod_value = request.form['lastgod_tf']

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT clt.clt_last_name, clt.clt_name, cpr.cpr_name_product, crt.crt_sum_credit
            FROM credit crt
            INNER JOIN client clt ON clt.id_client = crt.id_client
            INNER JOIN credit_products cpr ON crt.id_credit_product = cpr.id_credit_product
            WHERE crt.crt_sum_credit > %s AND cpr.cpr_name_product = %s
            ORDER BY crt.crt_sum_credit
        """, (onegod_value, lastgod_value))
        data = cursor.fetchall()
        cursor.close()

    return render_template('report2.html', data=data)


@app.route('/report3', methods=['GET', 'POST'])
def report3():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    data = None

    if request.method == 'POST':
        client_id = request.form['client_id']

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT clt.clt_last_name, clt.clt_name, crt.crt_sum_credit, lrp.lnr_date_deposit, lrp.lnr_amount_payments
            FROM loan_repayments lrp
            INNER JOIN credit crt ON lrp.id_credit = crt.id_credit
            INNER JOIN client clt ON crt.id_client = clt.id_client
            WHERE clt.id_client = %s
            ORDER BY lrp.lnr_date_deposit
        """, (client_id,))
        data = cursor.fetchall()
        cursor.close()

    return render_template('report3.html', data=data)


@app.route('/procedure.html', methods=['GET', 'POST'])
def procedure():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    data = None

    if request.method == 'POST':
        id_client = request.form['id_client_tf']
        credit_product = request.form['credit_product_tf']
        date = request.form['date_tf']
        monthly_contributions = request.form['sum_tf']
        maturity_date = request.form['sroc_tf']
        percent_on_credit = request.form['proc_tf']
        sum_credit = request.form['sumcred_tf']

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(f"""
            CALL create_credit_and_repayment(
                in_id_client := {id_client},
                in_id_credit_product := {credit_product},
                in_crt_date_issue := '{date}',
                in_crt_monthly_contributions := '{monthly_contributions}',
                in_crt_maturity_date := '{maturity_date}',
                in_crt_percent_on_credit := '{percent_on_credit}',
                in_crt_sum_credit := '{sum_credit}'
            )
        """)
        conn.commit()

        cursor.execute("SELECT * FROM public.credit ORDER BY id_credit ASC ")
        data = cursor.fetchall()
        cursor.close()

    return render_template('procedure.html', data=data)


@app.route('/apply_credit', methods=['GET', 'POST'])
def apply_credit():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = connect_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        credit_product = request.form['credit_product']
        requested_amount = request.form['sum']
        maturity_date = request.form['maturity_date']
        monthly_contributions = request.form['monthly_contributions']
        desired_interest = float(request.form['desired_interest']) / 100
        username = session['username']

        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        user_id = cursor.fetchone()[0]

        # Добавляем заявку в таблицу credit со статусом 0 (рассмотрение)
        cursor.execute("""
            INSERT INTO credit (id_client, id_credit_product, crt_date_issue, crt_sum_credit, crt_maturity_date, crt_status_credit, crt_monthly_contributions, crt_percent_on_credit)
            VALUES (%s, %s, CURRENT_DATE, %s, %s, 0, %s, %s)
        """, (user_id, credit_product, requested_amount, maturity_date if maturity_date else None, monthly_contributions, desired_interest))
        conn.commit()
        flash('Заявка на кредит успешно отправлена.')
        return redirect(url_for('profile'))

    cursor.execute("SELECT id_credit_product, cpr_name_product FROM credit_products")
    credit_products = cursor.fetchall()
    conn.close()

    return render_template('apply_credit.html', credit_products=credit_products)


@app.route('/status')
def view_applications():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cr.id_credit, c.clt_last_name, c.clt_name, c.clt_middle_name, cp.cpr_name_product, cr.crt_sum_credit, cr.crt_maturity_date, cr.crt_status_credit, cr.crt_date_issue
        FROM credit cr
        JOIN client c ON cr.id_client = c.id_client
        JOIN credit_products cp ON cr.id_credit_product = cp.id_credit_product
        WHERE cr.crt_status_credit = '0'
    """)
    applications = cursor.fetchall()
    conn.close()

    return render_template('admin_application.html', applications=applications)


@app.route('/status/<int:credit_id>/approve')
def approve_application(credit_id):
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = connect_db()
    cursor = conn.cursor()

    # Обновляем статус кредита на 1 (одобрено)
    cursor.execute("""
        UPDATE credit
        SET crt_status_credit = 1
        WHERE id_credit = %s
    """, (credit_id,))
    conn.commit()
    conn.close()

    flash('Заявка на кредит одобрена.')
    return redirect(url_for('view_applications'))


@app.route('/status/<int:credit_id>/reject')
def reject_application(credit_id):
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = connect_db()
    cursor = conn.cursor()

    # Обновляем статус кредита на 2 (отказано)
    cursor.execute("""
        UPDATE credit
        SET crt_status_credit = 2
        WHERE id_credit = %s
    """, (credit_id,))
    conn.commit()
    conn.close()

    flash('Заявка на кредит отклонена.')
    return redirect(url_for('view_applications'))


@app.route('/make_payment', methods=['GET', 'POST'])
def make_payment():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = connect_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        credit_id = request.form['credit_id']
        payment_amount = request.form['payment_amount']
        username = session['username']

        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        user_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO loan_repayments (id_client, id_credit, lnr_date_deposit, lnr_amount_payments, lnr_contribution_status)
            VALUES (%s, %s, CURRENT_DATE, %s, 2)
        """, (user_id, credit_id, payment_amount if payment_amount else None))
        conn.commit()
        flash('Выплата успешно добавлена.')
        return redirect(url_for('profile'))

    cursor.execute("""
        SELECT cr.id_credit, cp.cpr_name_product, cr.crt_sum_credit
        FROM credit cr
        JOIN credit_products cp ON cr.id_credit_product = cp.id_credit_product
        WHERE cr.id_client = (SELECT id FROM users WHERE username = %s)
    """, (session['username'],))
    credits = cursor.fetchall()
    conn.close()

    return render_template('make_payment.html', credits=credits)


@app.route('/payments')
def view_payments():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT lr.id_payout, c.clt_last_name, c.clt_name, c.clt_middle_name, lr.id_credit, lr.lnr_date_deposit, lr.lnr_amount_payments, lr.lnr_contribution_status
        FROM loan_repayments lr
        JOIN client c ON lr.id_client = c.id_client
        WHERE lr.lnr_contribution_status = '2'
    """)
    payments = cursor.fetchall()
    conn.close()

    return render_template('admin_payments.html', payments=payments)


@app.route('/payments/<int:payment_id>/mark_paid')
def mark_payment_paid(payment_id):
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE loan_repayments
        SET lnr_contribution_status = 0
        WHERE id_payout = %s
    """, (payment_id,))
    conn.commit()
    conn.close()

    flash('Выплата отмечена как оплаченная.')
    return redirect(url_for('view_payments'))


@app.route('/payments/<int:payment_id>/mark_overdue')
def mark_payment_overdue(payment_id):
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE loan_repayments
        SET lnr_contribution_status = 1
        WHERE id_payout = %s
    """, (payment_id,))
    conn.commit()
    conn.close()

    flash('Выплата отмечена как просроченная.')
    return redirect(url_for('view_payments'))


if __name__ == '__main__':
    app.run(debug=True)