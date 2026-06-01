FROM python:3.12-slim
WORKDIR /app
RUN pip install flask redis requests
COPY main.py .
CMD ["python", "main.py"]
