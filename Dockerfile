FROM python:3-alpine

RUN addgroup -g 2000 app && adduser -u 2000 --disabled-password --gecos '' app --ingroup app
WORKDIR /usr/src/app

COPY src/ ./src
COPY entrypoint.sh .

RUN pip install --no-cache-dir -r src/requirements.txt

RUN chown -R app:app /home/app
USER app

EXPOSE 8080

CMD ["/bin/sh", "entrypoint.sh"]
