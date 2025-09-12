FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /RemoteServerMCP

COPY requirements.txt /RemoteServerMCP/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY serverZTR.py .
EXPOSE 8080

CMD ["python", "serverZTR.py"]
