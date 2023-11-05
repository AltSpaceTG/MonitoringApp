from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
from typing import Optional
from pyecharts.charts import Line
from pyecharts import options as opts
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Загрузка и предварительная обработка данных
df = pd.read_csv('weblog.csv')

# Извлечение и форматирование даты
df['Time'] = df['Time'].str.extract(r'\[(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})')[0]
df['Time'] = pd.to_datetime(df['Time'], format='%d/%b/%Y:%H:%M:%S')

# Сортировка и удаление лишних элементов
df = df.sort_values(by='Time')
df = df.dropna(subset=['Time'])

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, start_date: Optional[str] = None, end_date: Optional[str] = None):
    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Выбор элементов подходящих под запрос
        filtered_data = df[(df['Time'] >= start_date) & (df['Time'] <= end_date)]
    else:
        filtered_data = df

    table_data = filtered_data.to_dict(orient="records")

    # Группировка данных по дням и подсчет количества запросов
    daily_requests = filtered_data.groupby(filtered_data['Time'].dt.date)['URL'].count()

    # Создание графика
    chart = Line()

    chart.set_global_opts(title_opts=opts.TitleOpts(title="Requests per Day"))
    chart.set_global_opts(
        xaxis_opts=opts.AxisOpts(name="Date"),
        yaxis_opts=opts.AxisOpts(name="Number of Requests"),
    )

    chart.add_xaxis(daily_requests.index.tolist())  # Даты
    chart.add_yaxis("Requests", daily_requests.tolist())  # Количество запросов

    chart_html = chart.render_embed()

    return templates.TemplateResponse("index.html", {"request": request, "chart_html": chart_html, "table_data": table_data})