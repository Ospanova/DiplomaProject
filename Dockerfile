version: '3.7'
services:
  db:
    image: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data/
  django:
    build: .
    command: bash -c "sleep 5s && python manage.py migrate && python manage.py runserver 0.0.0.0:8888"
    volumes:
      - ./src:/src
    ports:
      - 8888:8888
    depends_on:
      - db
    environment:
        DJANGO_SETTINGS_MODULE: 'cinema.settings'
  rabbit:
    restart: always
    image: rabbitmq:alpine
    environment:
        - RABBITMQ_DEFAULT_USER=aida
        - RABBITMQ_DEFAULT_PASS=aida
    ports:
        - "5672:5672"
    celery:
    restart: always
    build: .
        context: .
    command:  celery -A cinema  worker -l info
    volumes:
        - ./src:/src
    environment:
        - C_FORCE_ROOT:true
        - DJANGO_SETTINGS_MODULE: 'cinema.settings'
    depends_on:
        - rabbit