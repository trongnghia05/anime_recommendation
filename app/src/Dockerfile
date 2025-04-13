FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN mkdir -p /opt/airflow/cache
RUN mkdir -p /opt/airflow
RUN ln -s /app /opt/airflow/src

ENV PYTHONPATH="${PYTHONPATH}:/opt/airflow"


RUN pip install -r requirements.txt

CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug"]