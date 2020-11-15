FROM python:3.7

WORKDIR /code

ENV PYTHONPATH /code

COPY . ./api_service

RUN pip install -r api_service/requirements.txt

ENTRYPOINT [ "uvicorn", "api_service.api:app", "--host", "0.0.0.0", "--port", "5000"]
