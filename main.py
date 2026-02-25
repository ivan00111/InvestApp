import flet as ft
import sqlite3
from datetime import date, datetime, timedelta
import calendar

# --- ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ---
def init_db():
    conn = sqlite3.connect("investments.db")
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS deposits (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, name TEXT, bank TEXT, initial_sum REAL, rate REAL, term_months INTEGER, start_date TEXT, status TEXT, taxes REAL DEFAULT 0.0)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS stocks (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, name TEXT, quantity REAL, initial_price_per_unit REAL, current_price_per_unit REAL, dividends REAL DEFAULT 0.0, taxes REAL DEFAULT 0.0, status TEXT, sell_price_total REAL, sell_date TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS currency (id INTEGER PRIMARY KEY AUTOINCREMENT, currency_code TEXT, place TEXT, amount REAL, rub_rate REAL, date_added TEXT)''')
    conn.commit()
    conn.close()

# --- ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ---
def get_data(query, params=()):
    conn = sqlite3.connect("investments.db")
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows

def execute_query(query, params=()):
    conn = sqlite3.connect("investments.db")
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    conn.close()

def main(page: ft.Page):
    init_db()
    
    page.title = "Мои Инвестиции"
    page.window.width = 400
    page.window.height = 800
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.ADAPTIVE

    content_area = ft.Column(spacing=15)
    
    filters = {"deposit": "Активен", "stock": "Активен"}
    selected_year = date.today().year

    # --- ДИАЛОГ ДОБАВЛЕНИЯ НОВЫХ ЗАПИСЕЙ ---
    add_dialog = ft.AlertDialog()
    page.overlay.append(add_dialog)

    def show_add_dialog(e):
        idx = page.navigation_bar.selected_index
        
        if idx == 0:
            add_dialog.title = ft.Text("Новый вклад / ПИФ")
            f_type = ft.Dropdown(options=[ft.dropdown.Option("Вклад"), ft.dropdown.Option("ПИФ")], value="Вклад", label="Тип")
            f_name = ft.TextField(label="Название")
            f_bank = ft.TextField(label="Банк / Брокер")
            f_sum = ft.TextField(label="Сумма (₽)", keyboard_type=ft.KeyboardType.NUMBER)
            f_rate = ft.TextField(label="Ставка (%)", keyboard_type=ft.KeyboardType.NUMBER, value="0")
            f_term = ft.TextField(label="Срок (мес)", keyboard_type=ft.KeyboardType.NUMBER, value="12")
            
            def save_dep(e):
                try:
                    execute_query("INSERT INTO deposits (type, name, bank, initial_sum, rate, term_months, start_date, status) VALUES (?,?,?,?,?,?,?,'Активен')", 
                                  (f_type.value, f_name.value, f_bank.value, float(f_sum.value.replace(',','.')), float(f_rate.value.replace(',','.')), int(f_term.value), str(date.today())))
                    add_dialog.open = False
                    load_tab(0)
                except Exception: pass

            add_dialog.content = ft.Column([f_type, f_name, f_bank, f_sum, f_rate, f_term], tight=True, scroll=ft.ScrollMode.ADAPTIVE, height=350)
            add_dialog.actions = [ft.TextButton("Сохранить", on_click=save_dep)]

        elif idx == 1:
            add_dialog.title = ft.Text("Новый актив")
            f_type = ft.Dropdown(options=[ft.dropdown.Option("Акция"), ft.dropdown.Option("Металл")], value="Акция", label="Тип")
            f_name = ft.TextField(label="Тикер / Название")
            f_qty = ft.TextField(label="Количество", keyboard_type=ft.KeyboardType.NUMBER)
            f_buy_price = ft.TextField(label="Цена покупки (за шт)", keyboard_type=ft.KeyboardType.NUMBER)
            f_cur_price = ft.TextField(label="Текущая цена (за шт)", keyboard_type=ft.KeyboardType.NUMBER)
            
            def save_stock(e):
                try:
                    execute_query("INSERT INTO stocks (type, name, quantity, initial_price_per_unit, current_price_per_unit, status) VALUES (?,?,?,?,?,'Активен')", 
                                  (f_type.value, f_name.value, float(f_qty.value.replace(',','.')), float(f_buy_price.value.replace(',','.')), float(f_cur_price.value.replace(',','.'))))
                    add_dialog.open = False
                    load_tab(1)
                except Exception: pass

            add_dialog.content = ft.Column([f_type, f_name, f_qty, f_buy_price, f_cur_price], tight=True, scroll=ft.ScrollMode.ADAPTIVE, height=350)
            add_dialog.actions = [ft.TextButton("Сохранить", on_click=save_stock)]

        elif idx == 2:
            add_dialog.title = ft.Text("Новая валюта")
            f_code = ft.TextField(label="Код (USD, EUR, CNY)")
            f_place = ft.TextField(label="Где хранится?")
            f_amount = ft.TextField(label="Сумма", keyboard_type=ft.KeyboardType.NUMBER)
            f_rate = ft.TextField(label="Курс (₽)", keyboard_type=ft.KeyboardType.NUMBER)
            
            def save_cur(e):
                try:
                    execute_query("INSERT INTO currency (currency_code, place, amount, rub_rate, date_added) VALUES (?,?,?,?,?)", 
                                  (f_code.value.upper(), f_place.value, float(f_amount.value.replace(',','.')), float(f_rate.value.replace(',','.')), str(date.today())))
                    add_dialog.open = False
                    load_tab(2)
                except Exception: pass

            add_dialog.content = ft.Column([f_code, f_place, f_amount, f_rate], tight=True, scroll=ft.ScrollMode.ADAPTIVE, height=300)
            add_dialog.actions = [ft.TextButton("Сохранить", on_click=save_cur)]

        add_dialog.open = True
        page.update()

    # Круглая кнопка плюсика в нижнем углу
    page.floating_action_button = ft.FloatingActionButton(icon=ft.Icons.ADD, on_click=show_add_dialog, bgcolor=ft.Colors.BLUE_600)

    # --- УНИВЕРСАЛЬНЫЙ ДИАЛОГ ВВОДА ---
    input_dialog = ft.AlertDialog(title=ft.Text(""), content=ft.TextField(keyboard_type=ft.KeyboardType.NUMBER))
    page.overlay.append(input_dialog)

    def open_input_dialog(title, label, on_save):
        input_dialog.title.value = title
        input_dialog.content.label = label
        input_dialog.content.value = ""
        def save_and_close(e):
            if input_dialog.content.value:
                val = float(input_dialog.content.value.replace(',', '.'))
                on_save(val)
                input_dialog.open = False
                load_tab(page.navigation_bar.selected_index)
        input_dialog.actions = [ft.TextButton("Сохранить", on_click=save_and_close)]
        input_dialog.open = True
        page.update()

    # --- ШТОРКА ДЕЙСТВИЙ ---
    action_sheet = ft.BottomSheet(content=ft.Container(padding=20, content=ft.Column(tight=True)))
    page.overlay.append(action_sheet)

    def open_action_menu(db_id, item_type, status):
        actions = []
        def close_sheet(e):
            action_sheet.open = False
            page.update()

        if status == "Активен":
            if item_type == "deposit":
                actions.append(ft.ListTile(leading=ft.Icon(ft.Icons.PERCENT), title=ft.Text("Изменить ставку"), on_click=lambda e: (close_sheet(e), open_input_dialog("Ставка", "Новая ставка (%)", lambda v: execute_query("UPDATE deposits SET rate = ? WHERE id = ?", (v, db_id))))))
                actions.append(ft.ListTile(leading=ft.Icon(ft.Icons.RECEIPT_LONG), title=ft.Text("Учесть налог"), on_click=lambda e: (close_sheet(e), open_input_dialog("Налог", "Сумма налога (₽)", lambda v: execute_query("UPDATE deposits SET taxes = taxes + ? WHERE id = ?", (v, db_id))))))
                actions.append(ft.ListTile(leading=ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN), title=ft.Text("Закрыть вклад (в Архив)"), on_click=lambda e: (close_sheet(e), execute_query("UPDATE deposits SET status = 'Завершен' WHERE id = ?", (db_id,)), load_tab(0))))
                
            elif item_type == "stock":
                actions.append(ft.ListTile(leading=ft.Icon(ft.Icons.TRENDING_UP), title=ft.Text("Обновить цену"), on_click=lambda e: (close_sheet(e), open_input_dialog("Цена", "Текущая цена (за шт)", lambda v: execute_query("UPDATE stocks SET current_price_per_unit = ? WHERE id = ?", (v, db_id))))))
                actions.append(ft.ListTile(leading=ft.Icon(ft.Icons.ATTACH_MONEY), title=ft.Text("Добавить дивиденды"), on_click=lambda e: (close_sheet(e), open_input_dialog("Дивиденды", "Сумма (₽)", lambda v: execute_query("UPDATE stocks SET dividends = dividends + ? WHERE id = ?", (v, db_id))))))
                actions.append(ft.ListTile(leading=ft.Icon(ft.Icons.RECEIPT_LONG), title=ft.Text("Учесть налог"), on_click=lambda e: (close_sheet(e), open_input_dialog("Налог", "Сумма налога (₽)", lambda v: execute_query("UPDATE stocks SET taxes = taxes + ? WHERE id = ?", (v, db_id))))))
                actions.append(ft.ListTile(leading=ft.Icon(ft.Icons.SELL, color=ft.Colors.GREEN), title=ft.Text("Продать (в Архив)"), on_click=lambda e: (close_sheet(e), open_input_dialog("Продажа", "Цена продажи (за шт)", lambda v: execute_query("UPDATE stocks SET status = 'Продан', sell_price_total = quantity * ?, sell_date = ? WHERE id = ?", (v, str(date.today()), db_id))))))

            elif item_type == "currency":
                actions.append(ft.ListTile(leading=ft.Icon(ft.Icons.CURRENCY_EXCHANGE), title=ft.Text("Обновить курс"), on_click=lambda e: (close_sheet(e), open_input_dialog("Курс", "Новый курс (₽)", lambda v: execute_query("UPDATE currency SET rub_rate = ? WHERE id = ?", (v, db_id))))))

        table = "deposits" if item_type == "deposit" else "stocks" if item_type == "stock" else "currency"
        actions.append(ft.ListTile(leading=ft.Icon(ft.Icons.DELETE, color=ft.Colors.RED), title=ft.Text("Удалить запись", color=ft.Colors.RED), on_click=lambda e: (close_sheet(e), execute_query(f"DELETE FROM {table} WHERE id = ?", (db_id,)), load_tab(page.navigation_bar.selected_index))))

        action_sheet.content.content.controls = actions
        action_sheet.open = True
        page.update()

    # --- УМНАЯ КАРТОЧКА ---
    def create_card(db_id, item_type, title, subtitle, amount, profit="", profit_color=ft.Colors.GREEN_400, status="Активен"):
        is_archived = (status != "Активен")
        bg_color = ft.Colors.BLUE_GREY_900 if not is_archived else ft.Colors.GREY_900
        
        card_bg = ft.Container(
            padding=15, border_radius=15, bgcolor=bg_color,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.BLACK26),
            on_long_press=lambda e: open_action_menu(db_id, item_type, status)
        )
        card_bg.content = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.INVENTORY_2 if is_archived else ft.Icons.ACCOUNT_BALANCE_WALLET, size=30, color=ft.Colors.GREY_500 if is_archived else ft.Colors.BLUE_200),
                ft.Column([ft.Text(title, weight=ft.FontWeight.BOLD, size=16), ft.Text(subtitle, color=ft.Colors.WHITE70, size=12)], expand=True),
                ft.Icon(ft.Icons.MORE_VERT, color=ft.Colors.WHITE54)
            ]),
            ft.Divider(height=10, color=ft.Colors.WHITE24),
            ft.Row([
                ft.Text(f"{amount:,.0f} ₽".replace(",", " "), size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE54 if is_archived else ft.Colors.WHITE),
                ft.Text(profit, color=profit_color, weight=ft.FontWeight.BOLD)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ])
        return card_bg

    # --- ЛОГИКА АНАЛИТИКИ ---
    def build_analytics():
        nonlocal selected_year
        controls = []
        total = 0.0; passive_mo = 0.0
        by_type = {"Вклады": 0, "ПИФ": 0, "Акции": 0, "Металлы": 0, "Валюта": 0}
        
        for r in get_data("SELECT type, initial_sum, rate, start_date, taxes FROM deposits WHERE status='Активен'"):
            taxes = r[4] if r[4] else 0.0
            days = max(0, (date.today() - datetime.strptime(r[3], "%Y-%m-%d").date()).days)
            val = r[1] + (r[1] * r[2] / 100 / 365) * days - taxes
            total += val; by_type[r[0]] = by_type.get(r[0], 0) + val
            passive_mo += (r[1] * r[2] / 100) / 12

        for r in get_data("SELECT type, quantity, current_price_per_unit, dividends, taxes FROM stocks WHERE status='Активен'"):
            divs = r[3] if r[3] else 0.0; taxes = r[4] if r[4] else 0.0
            val = (r[1] * r[2]) + divs - taxes
            total += val; by_type["Акции" if "Акция" in r[0] else "Металлы"] += val

        for r in get_data("SELECT amount, rub_rate FROM currency"):
            val = r[0] * r[1]; total += val; by_type["Валюта"] += val

        controls.append(ft.Row([
            ft.Container(content=ft.Column([ft.Text("Общий Капитал", size=12, color=ft.Colors.WHITE70), ft.Text(f"{total:,.0f} ₽".replace(",", " "), size=20, weight=ft.FontWeight.BOLD)]), expand=True, padding=15, bgcolor=ft.Colors.BLUE_900, border_radius=10),
            ft.Container(content=ft.Column([ft.Text("Пассивный / Мес", size=12, color=ft.Colors.WHITE70), ft.Text(f"{passive_mo:,.0f} ₽".replace(",", " "), size=20, weight=ft.FontWeight.BOLD)]), expand=True, padding=15, bgcolor=ft.Colors.GREEN_900, border_radius=10),
        ]))

        controls.append(ft.Divider(height=20, color=ft.Colors.TRANSPARENT))
        controls.append(ft.Text("Структура портфеля", size=18, weight=ft.FontWeight.BOLD))

        segments = []; legend = []
        colors = [ft.Colors.BLUE_400, ft.Colors.GREEN_400, ft.Colors.AMBER_400, ft.Colors.RED_400, ft.Colors.PURPLE_400]
        color_idx = 0
        for k, v in by_type.items():
            if v > 0:
                pct = (v / total * 100) if total > 0 else 0
                c = colors[color_idx % len(colors)]
                segments.append(ft.Container(expand=max(1, int(v)), bgcolor=c)) 
                legend.append(ft.Row([ft.Container(width=12, height=12, bgcolor=c, border_radius=6), ft.Text(f"{k} - {pct:.1f}%", size=12)], tight=True))
                color_idx += 1

        controls.append(ft.Container(content=ft.Row(segments, spacing=0), height=15, border_radius=7, clip_behavior=ft.ClipBehavior.ANTI_ALIAS))
        controls.append(ft.Container(height=5))
        controls.append(ft.Row(legend, wrap=True, spacing=15))

        controls.append(ft.Divider(height=20, color=ft.Colors.TRANSPARENT))
        controls.append(ft.Text("История доходов", size=18, weight=ft.FontWeight.BOLD))

        inf_input = ft.TextField(label="Инфляция (%)", value="0", keyboard_type=ft.KeyboardType.NUMBER, expand=True)
        years = [str(y) for y in range(2020, date.today().year + 5)]
        
        year_dropdown = ft.Dropdown(options=[ft.dropdown.Option(y) for y in years], value=str(selected_year), width=150)

        chart_container = ft.Container(height=200)
        chart_info_text = ft.Text("Нажми на столбец", size=12, color=ft.Colors.WHITE54)

        def show_bar_info(m_name, nom, real):
            chart_info_text.value = f"{m_name} {selected_year} г.\nНоминал: {nom:,.0f} ₽ | Реал: {real:,.0f} ₽"
            chart_info_text.color = ft.Colors.AMBER_400
            page.update()

        def update_bar_chart(e=None):
            nonlocal selected_year
            selected_year = int(year_dropdown.value)
            inf_val = float(inf_input.value.replace(',', '.')) if inf_input.value else 0.0
            nom_vals = []

            for m in range(1, 13):
                m_tot = 0
                t_start = date(selected_year, m, 1); last_day = calendar.monthrange(selected_year, m)[1]; t_end = date(selected_year, m, last_day)
                for r in get_data("SELECT initial_sum, rate, start_date, term_months FROM deposits WHERE status='Активен'"):
                    d_start = datetime.strptime(r[2], "%Y-%m-%d").date()
                    d_end = (d_start.replace(day=1) + timedelta(days=32*r[3])).replace(day=d_start.day)
                    if d_start <= t_end and d_end >= t_start: m_tot += (r[0] * r[1] / 100) / 12
                nom_vals.append(m_tot)

            max_val = max(nom_vals + [1])
            bars = []
            month_names = ["Янв","Фев","Мар","Апр","Май","Июн","Июл","Авг","Сен","Окт","Ноя","Дек"]
            
            for i, nom in enumerate(nom_vals):
                real = nom * (1 - (inf_val / 100))
                nom_h = max(0, (nom / max_val) * 150)
                real_h = max(0, (real / max_val) * 150)

                bars.append(
                    ft.GestureDetector(
                        on_tap=lambda e, m=month_names[i], n=nom, r=real: show_bar_info(m, n, r),
                        content=ft.Column([
                            ft.Stack([
                                ft.Container(height=nom_h, width=16, bgcolor=ft.Colors.GREEN_700, border_radius=4, bottom=0),
                                ft.Container(height=real_h, width=16, bgcolor=ft.Colors.AMBER_400, border_radius=4, bottom=0),
                            ], height=150, width=16),
                            ft.Text(month_names[i][:1], size=10, color=ft.Colors.WHITE70)
                        ], alignment=ft.MainAxisAlignment.END, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                    )
                )

            chart_container.content = ft.Row(bars, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.END)
            page.update()

        inf_input.on_change = update_bar_chart
        year_dropdown.on_change = update_bar_chart
        update_bar_chart()

        controls.append(ft.Row([inf_input, year_dropdown]))
        controls.append(ft.Row([chart_info_text], alignment=ft.MainAxisAlignment.END)) 
        controls.append(chart_container)

        content_area.controls = controls

    # --- ЛОГИКА ПЕРЕКЛЮЧЕНИЯ ВЛАДОК И АРХИВОВ ---
    def load_tab(index):
        content_area.controls.clear()
        
        # Скрываем кнопку "+" на вкладке Аналитики (индекс 3)
        page.floating_action_button.visible = (index != 3)
        
        if index == 0:
            def set_dep_filter(status):
                filters["deposit"] = status
                load_tab(0)

            btn_row = ft.Row([
                ft.Button("Активные", style=ft.ButtonStyle(color=ft.Colors.WHITE if filters["deposit"] == "Активен" else ft.Colors.WHITE54, bgcolor=ft.Colors.BLUE_700 if filters["deposit"] == "Активен" else ft.Colors.TRANSPARENT), on_click=lambda e: set_dep_filter("Активен")),
                ft.Button("Архив", style=ft.ButtonStyle(color=ft.Colors.WHITE if filters["deposit"] == "Завершен" else ft.Colors.WHITE54, bgcolor=ft.Colors.BLUE_700 if filters["deposit"] == "Завершен" else ft.Colors.TRANSPARENT), on_click=lambda e: set_dep_filter("Завершен")),
            ], alignment=ft.MainAxisAlignment.CENTER)
            
            page.appbar = ft.AppBar(title=ft.Text("Вклады и ПИФы", weight=ft.FontWeight.BOLD), bgcolor=ft.Colors.BLUE_GREY_900)
            content_area.controls.append(btn_row)
            
            for r in get_data("SELECT id, name, bank, initial_sum, rate, start_date, taxes, status, term_months FROM deposits WHERE status=?", (filters["deposit"],)):
                tax = r[6] if r[6] else 0.0
                if r[7] == "Активен":
                    days = max(0, (date.today() - datetime.strptime(r[5], "%Y-%m-%d").date()).days)
                    gross = (r[3] * r[4] / 100 / 365) * days
                else:
                    gross = (r[3] * r[4] / 100 / 12) * r[8] 
                    
                net = gross - tax
                content_area.controls.append(create_card(r[0], "deposit", f"{r[1]}", f"Банк: {r[2]} | Ставка: {r[4]}% | Налог: {tax}₽", r[3] + net, f"+{net:,.0f} ₽", status=r[7]))
                
        elif index == 1:
            def set_stk_filter(status):
                filters["stock"] = status
                load_tab(1)

            btn_row = ft.Row([
                ft.Button("Активные", style=ft.ButtonStyle(color=ft.Colors.WHITE if filters["stock"] == "Активен" else ft.Colors.WHITE54, bgcolor=ft.Colors.BLUE_700 if filters["stock"] == "Активен" else ft.Colors.TRANSPARENT), on_click=lambda e: set_stk_filter("Активен")),
                ft.Button("Архив", style=ft.ButtonStyle(color=ft.Colors.WHITE if filters["stock"] == "Продан" else ft.Colors.WHITE54, bgcolor=ft.Colors.BLUE_700 if filters["stock"] == "Продан" else ft.Colors.TRANSPARENT), on_click=lambda e: set_stk_filter("Продан")),
            ], alignment=ft.MainAxisAlignment.CENTER)

            page.appbar = ft.AppBar(title=ft.Text("Акции и Металлы", weight=ft.FontWeight.BOLD), bgcolor=ft.Colors.BLUE_GREY_900)
            content_area.controls.append(btn_row)

            for r in get_data("SELECT id, name, type, quantity, initial_price_per_unit, current_price_per_unit, dividends, taxes, status, sell_price_total FROM stocks WHERE status=?", (filters["stock"],)):
                divs = r[6] if r[6] else 0.0; tax = r[7] if r[7] else 0.0
                init_tot = r[3] * r[4]
                
                if r[8] == "Активен":
                    cur_tot = r[3] * r[5]
                else: 
                    cur_tot = r[9] if r[9] else 0.0

                net = cur_tot - init_tot + divs - tax
                content_area.controls.append(create_card(r[0], "stock", f"{r[1]}", f"Тип: {r[2]} | Кол-во: {r[3]} | Див: {divs}₽", cur_tot, f"{'+' if net>0 else ''}{net:,.0f} ₽", ft.Colors.GREEN_400 if net>0 else ft.Colors.RED_400, status=r[8]))
                
        elif index == 2:
            page.appbar = ft.AppBar(title=ft.Text("Валюта", weight=ft.FontWeight.BOLD), bgcolor=ft.Colors.BLUE_GREY_900)
            for r in get_data("SELECT id, currency_code, place, amount, rub_rate FROM currency"):
                content_area.controls.append(create_card(r[0], "currency", f"{r[1]}", f"Где: {r[2]} | Курс: {r[4]}", r[3] * r[4], f"{r[3]:,.0f} {r[1]}"))
                
        elif index == 3:
            page.appbar = ft.AppBar(title=ft.Text("Аналитика", weight=ft.FontWeight.BOLD), bgcolor=ft.Colors.BLUE_GREY_900)
            build_analytics()

        page.update()

    # --- НИЖНЕЕ МЕНЮ НАВИГАЦИИ ---
    page.navigation_bar = ft.NavigationBar(
        selected_index=0,
        on_change=lambda e: load_tab(e.control.selected_index),
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.SAVINGS_OUTLINED, selected_icon=ft.Icons.SAVINGS, label="Вклады"),
            ft.NavigationBarDestination(icon=ft.Icons.SHOW_CHART_OUTLINED, selected_icon=ft.Icons.SHOW_CHART, label="Активы"),
            ft.NavigationBarDestination(icon=ft.Icons.CURRENCY_EXCHANGE_OUTLINED, selected_icon=ft.Icons.CURRENCY_EXCHANGE, label="Валюта"),
            ft.NavigationBarDestination(icon=ft.Icons.PIE_CHART_OUTLINE, selected_icon=ft.Icons.PIE_CHART, label="Сводка"),
        ]
    )

    page.add(content_area)
    load_tab(0)

ft.run(main)
