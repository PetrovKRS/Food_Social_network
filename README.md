#  -- > Социальная сеть для гурманов < --
***
### Общее описание
  Это социальная сеть для людей желающих например приготовить какое-нибудь изысканное 
блюдо! После прохождения регистрации пользователь получает доступ к общему списку заметок 
с рецептами размещенных в блоге, возможность разместить свою собственную заметку, 
подписаться на какого-нибудь автора, добавить понравившиеся заметки в избранные, 
добавить заметки с рецептами в покупки, и затем скачать список ингредиентов для 
понравившегося рецепта.

### Основные возможности проекта
  - регистрация пользователя
  - добавление новой заметки
  - добавление/удаление заметок в избранные
  - добавление/удаление заметок в покупки
  - возможность скачать список покупок в формате PDF 
      (дублирующиеся ингредиенты суммируются)

### Проект состоит из следующих страниц: 
  - главная,
  - страница заметки,
  - страница пользователя,
  - страница подписок,
  - избранное,
  - список заметок,
  - создание и редактирование заметки.

***
### Установка и запуск

#### Создание файла .env переменнх окружения
- Создайте в корне проекта .env файл и заполните его следующими данными 
  (см. env_example.txt):
  ```
  POSTGRES_USER — имя пользователя БД (необязательная переменная,
                  значение по умолчанию — postgres);
  POSTGRES_PASSWORD — пароль пользователя БД (обязательная переменная
                      для создания БД в контейнере);
  POSTGRES_DB — название базы данных (необязательная переменная, по
                умолчанию совпадает с POSTGRES_USER).
  DB_HOST — адрес, по которому Django будет соединяться с базой данных.
            При работе нескольких контейнеров в сети Docker network вместо
            адреса указывают имя контейнера, где запущен сервер БД, — в нашем
            случае это контейнер db.
  DB_PORT — порт, по которому Django будет обращаться к базе данных. 5432 —
            это порт по умолчанию для PostgreSQL.
  SECRET_KEY — секретный ключ для вашего проекта Django
  ALLOWED_HOSTS — доменные имена и ip-адреса, по которым будет доступен проект.
                  **Пример: ALLOWED_HOSTS=127.0.0.1,localhost,server_ip,domain_name**
  DEBUG - False, если хотите запустить сервис в контейнерах! True, если просто хотите 
            запустить API без фронтенда!

  Можно передать в окружение только переменную POSTGRES_PASSWORD —
  и будет создана БД с названием postgres и пользователем postgres
  ```

### Запуск проекта на удаленном сервере:

- Зайдите на удаленный сервер через ssh:
  ```
  ssh -i <путь к ssh ключу> <логин_на_сервере>@<IP_сервера>
  ```
- Установите на сервер docker и docker-compose:
  ```
  sudo apt update
  sudo apt install curl
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  sudo apt install docker-compose
  ```

- Скопируйте на сервер файлы docker-compose.yaml | default.conf | .env |
  ```
  scp -i <путь_к_ssh_ключу> docker-compose.yml nginx.conf .env \
  <логин_на_сервере>@<IP_сервера>:/home/<логин_на_сервере>/docker-compose.yml
  ```

- Добавьте в Secrets на Github следующие данные:

  ```
  DOCKER_USERNAME= Username в аккаунте на DockerHub
  DOCKER_PASSWORD= Пароль от аккаунта на DockerHub

  HOST= IP удалённого сервера
  USER= Логин на удалённом сервере
  SSH_KEY= SSH-ключ для доступа к удаленному серверу
  PASSPHRASE= Пароль от SSH-ключа

  TELEGRAM_TO= ID пользователя в Telegram
  TELEGRAM_TOKEN= ID Telegram бота
  ```

- Выполните команды:

  - git add .
  - git commit -m "Deploy"
  - git push

- Запустится workflow:

  - проверка кода на соответствие стандарту PEP8 (с помощью пакета flake8)
  - сборка и доставка докер-образа для контейнера backend на Docker Hub
  - Деплой на удаленном сервере
  - отправка уведомления пользователю в Telegram о том, что деплой проекта Foodgram успешно завершен

- В процессе деплоя на удаленном сервере должны быть выполнены следующие действия:

  ```
  sudo docker compose stop
  sudo docker compose rm -f backend frontend
  sudo docker pull ${{ secrets.DOCKER_USERNAME }}/foodgram_backend:latest
  sudo docker pull ${{ secrets.DOCKER_USERNAME }}/foodgram_frontend:latest
  sudo docker compose up -d
  sudo docker compose exec backend python3 manage.py makemigrations
  sudo docker compose exec backend python3 manage.py migrate
  sudo docker compose exec backend python3 manage.py collectstatic --no-input
  ```
- Создадим супер пользователя и загрузим в базу информацию об ингредиентах и теги:
  ```
  sudo docker compose exec backend python3 manage.py createsuperuser
  ```
  ```
  sudo docker compose exec web python manage.py load_tags
  sudo docker compose exec web python manage.py load_ingredients
  ```
- Затем прочитаем полезную статью ;=) выполнив следующую команду:
  ```
  sudo docker compose exec web python manage.py zen
  ```
- Откройте проект по адресу:
  ```
  http://<your_domain>
  ```
  Наслаждаемся проделанной работой !!!

***

### Для запуска проекта на локальном компьтере в контейнерах:

- Cклонируйте репозиторий в рабочую папку:
  ```
  git clone git@github.com:PetrovKRS/Food_Social_network.git
  ```
- В папку infra проекта поместите файл .env с переменными окружения:

- Установите docker compose
  ```
  sudo apt update
  sudo apt install curl
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  sudo apt install docker-compose
  ```
- Перейдите в папку infra в корневой папке склонированного репозитория:
  ```
  cd infra
  ```
- Запустите проект в docker контейнерах
  ```
  sudo docker compose up
  ```
- Выполните миграции
  ```
  sudo docker compose exec backend python3 manage.py migrate
  ```
- Соберите статику
  ```
  sudo docker compose exec backend python3 manage.py collectstatic --no-input
  ```
- Создайте пользователя:
  ```
  sudo docker compose exec backend python3 manage.py createsuperuser
  ```
- Откройте проект по адресу:
  ```
  http://localhost:9000
  ```



### Эндпоинты API сервиса:

* ```/api/users/```  Get-запрос – получение списка пользователей. POST-запрос – регистрация нового пользователя. Доступно без токена.

* ```/api/users/{id}``` GET-запрос – персональная страница пользователя с указанным id (доступно без токена).

* ```/api/users/me/``` GET-запрос – страница текущего пользователя. PATCH-запрос – редактирование собственной страницы. Доступно авторизированным пользователям. 

* ```/api/users/set_password``` POST-запрос – изменение собственного пароля. Доступно авторизированным пользователям. 

* ```/api/auth/token/login/``` POST-запрос – получение токена. Используется для авторизации по емейлу и паролю, чтобы далее использовать токен при запросах.

* ```/api/auth/token/logout/``` POST-запрос – удаление токена. 

* ```/api/tags/``` GET-запрос — получение списка всех тегов. Доступно без токена.

* ```/api/tags/{id}``` GET-запрос — получение информации о теге о его id. Доступно без токена. 

* ```/api/ingredients/``` GET-запрос – получение списка всех ингредиентов. Подключён поиск по частичному вхождению в начале названия ингредиента. Доступно без токена. 

* ```/api/ingredients/{id}/``` GET-запрос — получение информации об ингредиенте по его id. Доступно без токена. 

* ```/api/recipes/``` GET-запрос – получение списка всех рецептов. Возможен поиск рецептов по тегам и по id автора (доступно без токена). POST-запрос – добавление нового рецепта (доступно для авторизированных пользователей).

* ```/api/recipes/?is_favorited=1``` GET-запрос – получение списка всех рецептов, добавленных в избранное. Доступно для авторизированных пользователей. 

* ```/api/recipes/is_in_shopping_cart=1``` GET-запрос – получение списка всех рецептов, добавленных в список покупок. Доступно для авторизированных пользователей. 

* ```/api/recipes/{id}/``` GET-запрос – получение информации о рецепте по его id (доступно без токена). PATCH-запрос – изменение собственного рецепта (доступно для автора рецепта). DELETE-запрос – удаление собственного рецепта (доступно для автора рецепта).

* ```/api/recipes/{id}/favorite/``` POST-запрос – добавление нового рецепта в избранное. DELETE-запрос – удаление рецепта из избранного. Доступно для авторизированных пользователей. 

* ```/api/recipes/{id}/shopping_cart/``` POST-запрос – добавление нового рецепта в список покупок. DELETE-запрос – удаление рецепта из списка покупок. Доступно для авторизированных пользователей. 

* ```/api/recipes/download_shopping_cart/``` GET-запрос – получение текстового файла со списком покупок. Доступно для авторизированных пользователей. 

* ```/api/users/{id}/subscribe/``` GET-запрос – подписка на пользователя с указанным id. POST-запрос – отписка от пользователя с указанным id. Доступно для авторизированных пользователей

* ```/api/users/subscriptions/``` GET-запрос – получение списка всех пользователей, на которых подписан текущий пользователь Доступно для авторизированных пользователей.

***

### <b> Стек технологий: </b>

![Python](https://img.shields.io/badge/-Python_3.9-df?style=for-the-badge&logo=Python&labelColor=yellow&color=blue)
![Django](https://img.shields.io/badge/-Django-df?style=for-the-badge&logo=Django&labelColor=darkgreen&color=blue)
![REST](https://img.shields.io/badge/-REST-df?style=for-the-badge&logo=Django&labelColor=darkgreen&color=blue)
![Postman](https://img.shields.io/badge/-Postman-df?style=for-the-badge&logo=Postman&labelColor=black&color=blue)
![DOCKER](https://img.shields.io/badge/-DOCKER-df?style=for-the-badge&logo=DOCKER&labelColor=lightblue&color=blue)
![NGINX](https://img.shields.io/badge/-Nginx-df?style=for-the-badge&logo=NGINX&labelColor=green&color=blue)
![GUNICORN](https://img.shields.io/badge/-Gunicorn-df?style=for-the-badge&logo=Gunicorn&labelColor=lightgreen&color=blue)
![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-df?style=for-the-badge&logo=PostgreSQL&labelColor=darkgreen&color=blue)
![GitHub](https://img.shields.io/badge/-GitHub-df?style=for-the-badge&logo=GitHub&labelColor=black&color=blue)
![GitHubActions](https://img.shields.io/badge/-GitHubActions-df?style=for-the-badge&logo=GitHubActions&labelColor=black&color=blue)
***
### Автор проекта: 
[![GitHub](https://img.shields.io/badge/-Андрей_Петров-df?style=for-the-badge&logo=GitHub&labelColor=black&color=blue)](https://t.me/Petrov_KRS)
***