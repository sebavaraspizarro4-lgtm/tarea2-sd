FROM python:3.12-slim
WORKDIR /app
RUN pip install kafka-python numpy
COPY main.py .
CMD ["python", "main.py"]
