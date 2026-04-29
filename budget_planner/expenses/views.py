import os
import uuid

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render

import numpy as np
import pandas as pd

from expenses.models import UserModel, RecordModel

# Instantiate models globally or per request
user_model = UserModel()
record_model = RecordModel()


def check_auth(request):
    return 'user_email' in request.session


def login_view(request):
    if check_auth(request):
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        success, msg, user = user_model.login(email, password)
        if success:
            request.session['user_email'] = user['email']
            request.session['user_name'] = user['name']
            messages.success(request, msg)
            return redirect('dashboard')

        messages.error(request, msg)

    return render(request, 'login.html')


def register_view(request):
    if check_auth(request):
        return redirect('dashboard')

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        success, msg = user_model.register(name, email, password)
        if success:
            messages.success(request, msg)
            return redirect('login')

        messages.error(request, msg)

    return render(request, 'register.html')


def logout_view(request):
    request.session.flush()
    return redirect('login')


def dashboard(request):
    if not check_auth(request):
        return redirect('login')

    records = record_model.get_all()

    if not records:
        messages.error(request, "Dataset not found.")
        return render(request, 'dashboard.html', {'has_data': False})

    df = pd.DataFrame(records)

    # Convert Dates
    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Date'].dt.year
    df['DateStr'] = df['Date'].dt.strftime('%Y-%m-%d')

    # Get distinct variables for filtering dropdowns
    unique_years = sorted(df['Year'].dropna().unique().tolist(), reverse=True)
    unique_dates = sorted(
        df['DateStr'].dropna().unique().tolist(),
        reverse=True)
    unique_types = sorted(df['Transaction_Type'].dropna().unique().tolist())
    unique_categories = sorted(df['Category'].dropna().unique().tolist())
    unique_methods = sorted(df['Payment_Method'].dropna().unique().tolist())
    unique_statuses = sorted(df['Status'].dropna().unique().tolist())
    unique_currencies = sorted(df['Currency'].dropna().unique().tolist())

    # Retrieve GET params
    selected_year = request.GET.get('year')
    selected_day = request.GET.get('day')
    selected_type = request.GET.get('type')
    selected_category = request.GET.get('category')
    selected_method = request.GET.get('method')
    selected_status = request.GET.get('status')
    selected_currency = request.GET.get('currency')
    amount_min = request.GET.get('amount_min')
    amount_max = request.GET.get('amount_max')

    # Apply Filters
    if selected_year and selected_year != 'all':
        df = df[df['Year'] == int(selected_year)]
    if selected_day and selected_day != 'all':
        df = df[df['DateStr'] == selected_day]
    if selected_type and selected_type != 'all':
        df = df[df['Transaction_Type'] == selected_type]
    if selected_category and selected_category != 'all':
        df = df[df['Category'] == selected_category]
    if selected_method and selected_method != 'all':
        df = df[df['Payment_Method'] == selected_method]
    if selected_status and selected_status != 'all':
        df = df[df['Status'] == selected_status]
    if selected_currency and selected_currency != 'all':
        df = df[df['Currency'] == selected_currency]

    if amount_min:
        try:
            df = df[df['Amount'] >= float(amount_min)]
        except ValueError:
            pass
    if amount_max:
        try:
            df = df[df['Amount'] <= float(amount_max)]
        except ValueError:
            pass

    # Map back to unified format
    df_mapped = pd.DataFrame()
    total_expense = 0.0
    total_income = 0.0
    savings = 0.0

    if len(df) > 0:
        df_mapped['id'] = df['Transaction_ID']
        df_mapped['date'] = df['DateStr']
        df_mapped['category'] = df['Category']
        df_mapped['description'] = df['Description']
        df_mapped['amount'] = pd.to_numeric(df['Amount'])
        df_mapped['type'] = df['Transaction_Type']
        df_mapped['currency'] = df['Currency']
        df_mapped['method'] = df['Payment_Method']
        df_mapped['status'] = df['Status']
        records = df_mapped.to_dict('records')

        # NumPy calculations for fast metric aggregation
        types_array = df_mapped['type'].to_numpy()
        amounts_array = df_mapped['amount'].to_numpy()

        expense_mask = types_array == 'Expense'
        income_mask = types_array == 'Income'

        if np.any(expense_mask):
            total_expense = float(np.sum(amounts_array[expense_mask]))
        if np.any(income_mask):
            total_income = float(np.sum(amounts_array[income_mask]))
        savings = total_income - total_expense
        savings_status = 'negative' if savings < 0 else 'positive'
    else:
        records = []
        savings_status = 'positive'

    has_data = len(records) > 0
    display_records = records  # Show all filtered records in front-end table

    bar_chart, pie_chart, line_chart, insights = None, None, None, {}
    if has_data:
        try:
            from expenses.analytics import generate_graphs
            # Generate plots based ONLY on exactly what was filtered above
            bar_chart, pie_chart, line_chart, insights = generate_graphs(records)
        except Exception as e:  # pylint: disable=broad-except
            print("Analytics error:", e)
            messages.error(request, "Failed to generate analytics graphs.")

    context = {
        'records': display_records,
        'total_count': len(records),
        'has_data': has_data,
        'bar_chart': bar_chart,
        'pie_chart': pie_chart,
        'line_chart': line_chart,
        'insights': insights,
        'total_expense': total_expense,
        'total_income': total_income,
        'savings': savings,
        'savings_status': savings_status,
        'name': request.session.get('user_name', ''),
        # Filter Lists
        'years': unique_years,
        'days': unique_dates,
        'types': unique_types,
        'categories': unique_categories,
        'methods': unique_methods,
        'statuses': unique_statuses,
        'currencies': unique_currencies,
        # Selected states
        'selected_year': selected_year,
        'selected_day': selected_day,
        'selected_type': selected_type,
        'selected_category': selected_category,
        'selected_method': selected_method,
        'selected_status': selected_status,
        'selected_currency': selected_currency,
        'amount_min': amount_min,
        'amount_max': amount_max,
    }
    return render(request, 'dashboard.html', context)
