FROM python:3.8

RUN mkdir /quest

WORKDIR /quest

COPY . /quest/

RUN pip install -r requirements.txt

EXPOSE 8080

CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]