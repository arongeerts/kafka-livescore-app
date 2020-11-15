FROM python:3.7

WORKDIR /code

ENV PYTHONPATH /code

COPY . ./producers

RUN pip install -r producers/requirements.txt

ENTRYPOINT [ "uvicorn", "producers.api:app", "--host", "0.0.0.0", "--port", "5000"]
