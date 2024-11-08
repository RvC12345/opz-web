FROM python:3.10.8
WORKDIR /app
COPY ./ /app
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
CMD python3 app.py
