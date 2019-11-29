# async-chat
Асинхронный клиент для прослушивания и записи чата.

## Требования
Python 3.7+

Установка зависимостей
```
pip install -r requirements.txt

```
## Использование
Запуск скрипта для прослушивания чата. Необходимые параметры адрес+порт чата, а также название файла для записи истории переписки.
```bash
  python3 listen_minechat.py --host %host% --port %port% --history %history file%

```
Запуск скрипта для отправления соообщений в чат.
```bash
  python3 write_minechat.py --host %host% --port %port% --token %token% --message %message% --username %username%

```
Хост и порт обязательные параметры для подключения к чату.<br>
Для авторизации используйте токен и укажите его при запуске.<br>
Если вы не зарегестрированы при запуске укажите имя через параметр --username, скрипт вернёт токен пользователя.<br>
Для отправки одного сообщения укажите его при запуске через параметр --message, для перехода в интерактивный режим оставьте его пустым.
