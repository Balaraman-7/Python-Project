import base64
import io
import urllib.parse
import pandas as pd  # pylint: disable=import-error

import matplotlib  # pylint: disable=import-error
matplotlib.use('Agg')  # fix for non-gui environments

import matplotlib.pyplot as plt  # noqa: E402  # pylint: disable=import-error
import matplotlib.ticker as ticker  # noqa: E402  # pylint: disable=import-error


def generate_graphs(records):
    """
    Takes a list of MongoDB records, processes them with Pandas,
    and returns base64 encoded strings of Matplotlib charts.
    """
    if not records:
        return None, None, None

    df = pd.DataFrame(records)

    # Process Data
    df['amount'] = pd.to_numeric(df['amount'])

    # Increased font sizes for full-width layout readability
    plt.rcParams.update({
        'font.size': 16,
        'axes.titlesize': 20,
        'axes.labelsize': 16,
        'xtick.labelsize': 13,
        'ytick.labelsize': 13
    })

    # 1. Bar Chart: Category-wise Expense
    category_grouped = df.groupby('category')['amount'].sum().reset_index()

    plt.figure(figsize=(8, 6), dpi=200, facecolor='#ffffff')
    plt.bar(
        category_grouped['category'],
        category_grouped['amount'],
        color='#8b5cf6'
    )
    plt.title('Expenses by Category', color='black')
    plt.xlabel('Category', color='#555555')
    plt.ylabel('Amount', color='#555555')
    plt.xticks(rotation=45, ha='right', color='#555555')
    plt.yticks(color='#555555')
    ax = plt.gca()
    ax.set_facecolor('#ffffff')
    ax.spines['bottom'].set_color('#cccccc')
    ax.spines['top'].set_color('none')
    ax.spines['right'].set_color('none')
    ax.spines['left'].set_color('#cccccc')
    plt.tight_layout()
    bar_chart = get_base64_plot()

    # 2. Pie Chart: Expense Distribution (Interactive Plotly)
    try:
        import plotly.express as px
        import plotly.io as pio
        fig = px.pie(
            category_grouped, 
            values='amount', 
            names='category', 
            title='Expense Distribution',
            color_discrete_sequence=['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444']
        )
        fig.update_traces(
            textposition='inside', 
            textinfo='percent', 
            hoverinfo='label+percent+value',
            marker=dict(line=dict(color='#ffffff', width=2))
        )
        fig.update_layout(
            margin=dict(t=40, b=10, l=10, r=10),
            paper_bgcolor='#ffffff',
            plot_bgcolor='#ffffff',
            font=dict(color='#0f172a', size=16),
            legend=dict(font=dict(color='#0f172a')),
            showlegend=True
        )
        pie_chart = pio.to_html(fig, full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})
    except ImportError:
        # Fallback if Plotly fails to load
        plt.figure(figsize=(7, 5), dpi=150, facecolor='#ffffff')
        
        # Function to only show percent if slice is large enough
        def autopct_generator(pct):
            return ('%1.1f%%' % pct) if pct > 3 else ''

        wedges, texts, autotexts = plt.pie(
            category_grouped['amount'],
            autopct=autopct_generator,
            startangle=140,
            pctdistance=0.85,
            textprops={'color': 'black', 'fontsize': 11, 'weight': 'bold'},
            colors=['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#14b8a6', '#f43f5e']
        )
        
        # Calculate percentages for the legend labels
        total_amt = category_grouped['amount'].sum()
        legend_labels = [f"{cat} ({(amt/total_amt)*100:.1f}%)" for cat, amt in zip(category_grouped['category'], category_grouped['amount'])]
        
        # Use a legend instead of direct overlapping labels
        plt.legend(wedges, legend_labels,
                   title="Categories",
                   loc="center left",
                   bbox_to_anchor=(1, 0, 0.5, 1))

        plt.title('Expense Distribution', color='black', pad=20)
        plt.tight_layout()
        pie_chart = get_base64_plot()

    # 3. Line Chart: Expense Trend Over Time (Aggregated to Month)
    df['date_dt'] = pd.to_datetime(df['date'])
    df['month_period'] = df['date_dt'].dt.to_period('M')
    date_grouped = df.groupby('month_period')['amount'].sum()\
        .reset_index().sort_values('month_period')
    date_grouped['date_str'] = date_grouped['month_period'].dt.strftime(
        '%b %Y'
    )

    plt.figure(figsize=(14, 6), dpi=200, facecolor='#ffffff')
    plt.plot(
        date_grouped['date_str'],
        date_grouped['amount'],
        marker='o',
        color='#3b82f6',
        linestyle='-',
        linewidth=3,
        markersize=8
    )
    plt.title('Expense Trend', color='black')
    plt.xlabel('Date', color='#555555')
    plt.ylabel('Amount', color='#555555')
    plt.yticks(color='#555555')
    ax = plt.gca()
    ax.xaxis.set_major_locator(ticker.MaxNLocator(15))
    plt.xticks(rotation=45, ha='right', color='#555555')
    ax.set_facecolor('#ffffff')
    ax.spines['bottom'].set_color('#cccccc')
    ax.spines['top'].set_color('none')
    ax.spines['right'].set_color('none')
    ax.spines['left'].set_color('#cccccc')
    plt.grid(color='#cccccc', linestyle='--', linewidth=0.5, alpha=0.5)
    plt.tight_layout()
    plt.tight_layout()
    line_chart = get_base64_plot()

    # Generate Data-Driven Insights
    insights = {}
    
    if not category_grouped.empty:
        cat_sorted = category_grouped.sort_values('amount', ascending=False)
        top_cat = cat_sorted.iloc[0]
        total_amt = cat_sorted['amount'].sum()
        pct = (top_cat['amount'] / total_amt) * 100
        
        insights['pie'] = f"The largest portion of your transactions is '{top_cat['category']}', accounting for {pct:.1f}% ({top_cat['amount']:,.2f}) of the total shown."
        
        if len(cat_sorted) > 1:
            second_cat = cat_sorted.iloc[1]
            insights['bar'] = f"'{top_cat['category']}' is your top category ({top_cat['amount']:,.2f}), followed by '{second_cat['category']}' ({second_cat['amount']:,.2f})."
        else:
            insights['bar'] = f"All transactions currently fall under the '{top_cat['category']}' category."
    else:
        insights['pie'] = "No category data available."
        insights['bar'] = "No category data available."

    if not date_grouped.empty:
        max_month = date_grouped.loc[date_grouped['amount'].idxmax()]
        min_month = date_grouped.loc[date_grouped['amount'].idxmin()]
        if len(date_grouped) > 1:
            insights['line'] = f"Your highest recorded amount was {max_month['amount']:,.2f} in {max_month['date_str']}, and the lowest was {min_month['amount']:,.2f} in {min_month['date_str']}."
        else:
            insights['line'] = f"The total recorded amount for {max_month['date_str']} was {max_month['amount']:,.2f}."
    else:
        insights['line'] = "Not enough data to analyze trends."

    return bar_chart, pie_chart, line_chart, insights


def get_base64_plot():
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', facecolor='#ffffff')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = 'data:image/png;base64,' + urllib.parse.quote(string)
    plt.close()
    return uri
