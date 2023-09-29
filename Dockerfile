FROM python:3.11.5-slim-bullseye


COPY requirements.txt .
RUN pip install -r requirements.txt

WORKDIR /app
COPY . /app


CMD ["streamlit", "run", "visualizedProject.py"]
