FROM python:3.10.7-alpine3.16

WORKDIR /bedev-bot

COPY . .

RUN pip3 install -r requirements.txt

CMD ["python", "main.py"]