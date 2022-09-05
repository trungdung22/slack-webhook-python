FROM python:3.8-slim-buster
WORKDIR /usr/app
COPY /src/ .
RUN pip install -r requirements.txt
RUN chmod a+x run.sh
CMD ["./run.sh"]