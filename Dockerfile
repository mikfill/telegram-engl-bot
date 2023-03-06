FROM python:3.10.6-alpine3.16

WORKDIR /engl-tbot

COPY . .

RUN pip3 install -r requirements.txt

CMD ["python", "main.py"]