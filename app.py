import os
from sqlite3 import IntegrityError

from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, session, redirect, url_for, send_file, flash
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import io
from models import User, SessionLocal, CreditProduct, Client, LoanRepayment, Credit, CreditHistory

from utils.db import connect_db
import utils.db

app = Flask(__name__)
app.secret_key = 'secret_key'

@app.route('/')
def home():
    # Создаем сессию базы данных
    db = SessionLocal()

    # Получаем все кредитные продукты с помощью ORM
    credit_products = db.query(
        CreditProduct.cpr_name_product,
        CreditProduct.cpr_min_koef,
        CreditProduct.cpr_max_koef,
        CreditProduct.cpr_min_date_return,
        CreditProduct.cpr_max_date_return
    ).all()
    db.close()

    username = session.get('username')
    role = session.get('role')

    return render_template('home.html', username=username, role=role, credit_products=credit_products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = SessionLocal()
        user = db.query(User).filter(User.username == username).first()
        db.close()

        if user and check_password_hash(user.password, password):
            session['username'] = username
            session['role'] = user.role
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

        db = SessionLocal()
        try:
            new_client = Client(clt_last_name=clt_last_name, clt_name=clt_name, clt_middle_name=clt_middle_name, clt_date_birth=clt_date_birth,
                clt_residential_address=clt_residential_address, clt_income=clt_income, clt_passport_data=clt_passport_data, clt_marital_status=clt_marital_status
            )
            db.add(new_client)
            db.commit()

            new_user = User(id=new_client.id_client, username=username, password=password, role='user')
            db.add(new_user)
            db.commit()
            db.close()

            flash("Регистрация прошла успешно!", "success")
            return redirect(url_for('login'))
        except IntegrityError:
            db.rollback()
            db.close()
            flash("Пользователь с таким именем уже существует", "error")
            return redirect(url_for('register'))
        except Exception as e:
            db.rollback()
            db.close()
            flash(f"Ошибка при регистрации: {str(e)}", "error")
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
    db = SessionLocal()

    try:
        # Получаем информацию о пользователе и клиенте
        user = db.query(User).filter(User.username == username).first()
        if not user:
            flash("Пользователь не найден", "error")
            return redirect(url_for('home'))

        client = db.query(Client).filter(Client.id_client == user.id).first()
        if not client:
            flash("Клиент не найден", "error")
            return redirect(url_for('home'))

        # Преобразуем семейное положение в читаемый формат
        marital_status_map = {
            '0': 'Холост',
            '1': 'Женат/Замужем',
            '2': 'Разведен/а'
        }
        marital_status = marital_status_map.get(client.clt_marital_status, 'Неизвестно')

        # Формируем данные о клиенте
        user_data = {
            'id': client.id_client,
            'last_name': client.clt_last_name,
            'name': client.clt_name,
            'middle_name': client.clt_middle_name,
            'date_birth': client.clt_date_birth,
            'residential_address': client.clt_residential_address,
            'income': client.clt_income,
            'passport_data': client.clt_passport_data,
            'marital_status': marital_status
        }

        # Получаем кредиты клиента
        credits = db.query(Credit).filter(Credit.id_client == client.id_client).all()
        user_credits = []
        for credit in credits:
            # Преобразуем статус кредита в читаемый формат
            credit_status_map = {
                '0': 'На рассмотрение',
                '1': 'Выдан',
                '2': 'Отказано'
            }
            credit_status = credit_status_map.get(credit.crt_status_credit, 'Неизвестно')

            # Получаем информацию о кредитном продукте
            credit_product = db.query(CreditProduct).filter(CreditProduct.id_credit_product == credit.id_credit_product).first()

            credit_data = {
                'id': credit.id_credit,
                'product_id': credit.id_credit_product,
                'date_issue': credit.crt_date_issue,
                'monthly_contributions': credit.crt_monthly_contributions,
                'maturity_date': credit.crt_maturity_date,
                'percent_on_credit': int(credit.crt_percent_on_credit * 100),
                'status': credit_status,
                'sum': credit.crt_sum_credit,
                'product_name': credit_product.cpr_name_product,
                'min_koef': credit_product.cpr_min_koef,
                'max_koef': credit_product.cpr_max_koef,
                'min_date_return': credit_product.cpr_min_date_return,
                'max_date_return': credit_product.cpr_max_date_return
            }
            user_credits.append(credit_data)

        # Получаем выплаты клиента
        payouts = db.query(LoanRepayment).filter(LoanRepayment.id_client == client.id_client).all()
        user_payouts = []
        for payout in payouts:
            # Преобразуем статус выплаты в читаемый формат
            payout_status_map = {
                '0': 'Заплачено',
                '1': 'Просрочено'
            }
            payout_status = payout_status_map.get(payout.lnr_contribution_status, 'Неизвестно')

            payout_data = {
                'id': payout.id_payout,
                'credit_id': payout.id_credit,
                'date_deposit': payout.lnr_date_deposit,
                'amount_payments': payout.lnr_amount_payments,
                'contribution_status': payout_status
            }
            user_payouts.append(payout_data)

        return render_template('profile.html', user_data=user_data, user_credits=user_credits, user_payouts=user_payouts)

    except Exception as e:
        flash(f"Ошибка при загрузке профиля: {str(e)}", "error")
        return redirect(url_for('home'))
    finally:
        db.close()

@app.route('/admin')
def admin():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    return render_template('admin.html')



@app.route('/view_table/<table_name>')
def view_table(table_name):
    # Проверка прав доступа
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    # Создаем сессию базы данных
    db = SessionLocal()

    try:
        # Маппинг таблиц и их колонок
        table_mapping = {
            'credit': (Credit, ['id_credit', 'id_client', 'id_credit_product', 'crt_date_issue',
                                'crt_monthly_contributions', 'crt_maturity_date', 'crt_percent_on_credit',
                                'crt_status_credit', 'crt_sum_credit']),
            'loan_repayments': (LoanRepayment, ['id_payout', 'id_client', 'id_credit', 'lnr_date_deposit',
                                                'lnr_amount_payments', 'lnr_contribution_status']),
            'client': (Client, ['id_client', 'clt_last_name', 'clt_name', 'clt_middle_name', 'clt_date_birth', 'clt_residential_address', 'clt_income', 'clt_passport_data', 'clt_marital_status']),
            'credit_history': (CreditHistory, ['id_credit_history', 'id_client', 'id_credit', 'chs_amount_debt', 'chs_loan_status']),
            'credit_products': (CreditProduct, ['id_credit_product', 'cpr_name_product', 'cpr_min_koef', 'cpr_max_koef', 'cpr_min_date_return', 'cpr_max_date_return']),
            'users': (User, ['id', 'username', 'role']),
        }

        # Проверка, что таблица существует в маппинге
        if table_name not in table_mapping:
            flash(f"Таблица '{table_name}' не найдена.", "error")
            return redirect(url_for('admin'))

        # Получаем модель и колонки
        model, columns = table_mapping[table_name]

        # Получаем данные из таблицы
        rows = db.query(model).all()

        # Преобразуем объекты SQLAlchemy в словари
        rows_dicts = [model_to_dict(row, columns) for row in rows]

        return render_template('view_table.html', table_title=table_name, columns=columns, rows=rows_dicts)

    except Exception as e:
        # Обработка ошибок
        flash(f"Ошибка при загрузке таблицы '{table_name}': {str(e)}", "error")
        return redirect(url_for('admin'))
    finally:
        # Закрываем сессию
        db.close()

def model_to_dict(row, columns):
    return {column: getattr(row, column) for column in columns}

@app.route('/add_row/<table_name>', methods=['GET', 'POST'])
def add_row(table_name):
    # Проверка прав доступа
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    # Маппинг таблиц, колонок и их описаний
    table_mapping = {
        'credit': {
            'columns': ['id_client', 'id_credit_product', 'crt_date_issue', 'crt_monthly_contributions',
                        'crt_maturity_date', 'crt_percent_on_credit', 'crt_status_credit', 'crt_sum_credit'],
            'descriptions': ['ID клиента', 'ID кредитного продукта', 'Дата взятия', 'Ежемесячный платеж',
                             'Дата выплачивания', 'Процент', 'Статус (0 - на рассмотрение, 1 - выдан, 2 - отказано)',
                             'Сумма кредита']
        },
        'loan_repayments': {
            'columns': ['id_client', 'id_credit', 'lnr_date_deposit', 'lnr_amount_payments', 'lnr_contribution_status'],
            'descriptions': ['ID клиента', 'ID кредита', 'Дата внесения средств', 'Сумма выплаты',
                             'Статус (0 - заплачено, 1 - просрочено, 2 - на рассмотрение)']
        },
        'client': {
            'columns': ['clt_last_name', 'clt_name', 'clt_middle_name', 'clt_date_birth', 'clt_residential_address',
                        'clt_income', 'clt_passport_data', 'clt_marital_status'],
            'descriptions': ['Фамилия', 'Имя', 'Отчество', 'Дата рождения', 'Адрес проживания', 'Заработок',
                             'Паспорт', 'Статус (0 - холост, 1 - женат/замужем, 2 - разведен/а)']
        },
        'credit_history': {
            'columns': ['id_client', 'id_credit', 'chs_amount_debt', 'chs_loan_status'],
            'descriptions': ['ID клиента', 'ID кредита', 'Сумма долга', 'Статус (0 - заплачено, 1 - просрочено)']
        },
        'credit_products': {
            'columns': ['cpr_name_product', 'cpr_min_koef', 'cpr_max_koef', 'cpr_min_date_return', 'cpr_max_date_return'],
            'descriptions': ['Название продукта', 'Мин. коэф.', 'Макс. коэф.', 'Мин. дата возврата', 'Макс. дата возврата']
        },
        'users': {
            'columns': ['id', 'username', 'password', 'role'],
            'descriptions': ['ID', 'Логин', 'Пароль', 'Роль']
        }
    }

    # Проверка, что таблица существует в маппинге
    if table_name not in table_mapping:
        flash(f"Таблица '{table_name}' не найдена.", "error")
        return redirect(url_for('admin'))

    # Получаем колонки и их описания
    columns = table_mapping[table_name]['columns']
    columns_print = table_mapping[table_name]['descriptions']

    # Обработка POST-запроса (добавление новой строки)
    if request.method == 'POST':
        try:
            # Собираем данные из формы
            data = {}
            for column in columns:
                value = request.form.get(column)
                data[column] = value if value != '' else None  # Заменяем пустые строки на None

            # Создаем новую запись в базе данных
            db = SessionLocal()
            model = get_model_by_table_name(table_name)  # Функция для получения модели по имени таблицы
            new_row = model(**data)
            db.add(new_row)
            db.commit()
            db.close()

            flash("Запись успешно добавлена.", "success")
            return redirect(url_for('view_table', table_name=table_name))

        except Exception as e:
            db.rollback()
            flash(f"Ошибка при добавлении записи: {str(e)}", "error")
            return redirect(url_for('add_row', table_name=table_name))

    # Обработка GET-запроса (отображение формы)
    return render_template('add_row.html', table_name=table_name, columns=columns, columns_print=columns_print)

# Вспомогательная функция для получения модели по имени таблицы
def get_model_by_table_name(table_name):
    model_mapping = {
        'credit': Credit,
        'loan_repayments': LoanRepayment,
        'client': Client,
        'credit_history': CreditHistory,
        'credit_products': CreditProduct,
        'users': User
    }
    return model_mapping.get(table_name)

@app.route('/delete_row/<table_name>/<int:row_id>', methods=['GET', 'POST'])
def delete_row(table_name, row_id):
    # Проверка прав доступа
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    # Маппинг таблиц и их первичных ключей
    table_mapping = {
        'credit': 'id_credit',
        'loan_repayments': 'id_payout',
        'client': 'id_client',
        'credit_history': 'id_credit_history',
        'credit_products': 'id_credit_product',
        'users': 'id',
    }

    # Проверка, что таблица существует в маппинге
    if table_name not in table_mapping:
        flash(f"Таблица '{table_name}' не найдена.", "error")
        return redirect(url_for('admin'))

    # Получаем имя первичного ключа для таблицы
    id_column = table_mapping[table_name]

    # Создаем сессию базы данных
    db = SessionLocal()

    try:
        # Получаем модель таблицы
        model = get_model_by_table_name(table_name)

        # Для таблицы 'client' проверяем наличие задолженности
        if table_name == 'client':
            debt = db.query(CreditHistory).filter(
                CreditHistory.id_client == row_id,
                CreditHistory.chs_amount_debt > 0
            ).first()

            if debt:
                # Если задолженность существует, показываем подтверждение удаления
                return render_template('confirm_delete.html', row_id=row_id, table_name=table_name)

        # Удаляем строку из таблицы
        row_to_delete = db.query(model).filter(getattr(model, id_column) == row_id).first()
        if row_to_delete:
            db.delete(row_to_delete)
            db.commit()
            flash(f"Запись успешно удалена из таблицы '{table_name}'.", "success")
        else:
            flash(f"Запись с ID {row_id} не найдена в таблице '{table_name}'.", "error")

    except Exception as e:
        # Обработка ошибок
        db.rollback()
        flash(f"Ошибка при удалении записи: {str(e)}", "error")
    finally:
        # Закрываем сессию
        db.close()

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

    conn = utils.db.connect_db()
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

    conn = utils.db.connect_db()
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

        conn = utils.db.connect_db()
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

        conn = utils.db.connect_db()
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

        conn = utils.db.connect_db()
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

        conn = utils.db.connect_db()
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

    conn = utils.db.connect_db()
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

    conn = utils.db.connect_db()
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

    conn = utils.db.connect_db()
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

    conn = utils.db.connect_db()
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

    conn = utils.db.connect_db()
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

    conn = utils.db.connect_db()
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

    conn = utils.db.connect_db()
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

    conn = utils.db.connect_db()
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