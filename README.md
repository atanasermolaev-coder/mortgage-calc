# Калькулятор ипотеки: CI/CD на GitHub Actions

Учебный проект: автоматическая поставка кода на «продуктовый» сервер (виртуальная машина с Linux) после `git push`, с обязательными проверками линтером и тестами.

```
Локальный ПК ──git push──▶ GitHub ──▶ Actions:  lint ─▶ test ─▶ deploy
 (разработка)                         (облако)  (flake8) (pytest)   │
                                                                    ▼
                                         self-hosted runner на Ubuntu Server (прод-VM)
                                         копирует код в /opt/mortgage-app
                                         и перезапускает systemd-сервис
```

Раннер на VM сам подключается к GitHub (исходящее соединение), поэтому пробрасывать порты на VM для работы CI/CD не нужно.

**Что внутри**

| Файл | Назначение |
|---|---|
| `app/mortgage.py` | Логика: аннуитетный платёж, переплата, график платежей |
| `app/web.py` | Веб-интерфейс на Flask (работает на прод-VM) |
| `app/gui.py` | Окно на tkinter (только локально, для демонстрации) |
| `tests/` | Тесты pytest: 22 теста (логика и веб) |
| `.github/workflows/ci-cd.yml` | Pipeline: `lint → test → deploy` |
| `requirements.txt` | Зависимости для прода (flask, gunicorn) |
| `requirements-dev.txt` | Зависимости для разработки (+ pytest, flake8) |
| `.flake8` | Настройки линтера |

**Что закрывает из задания**

- Базовая часть: локальная разработка, GitHub вместо GitLab, раннер на прод-VM, автотесты в pipeline, автодеплой после push.
- Из «усложнённой версии» выполнен пункт про линтер (stage `lint`). Docker в проект не включён, потому что он не обязателен для базовой версии.

---

## Порядок работы (кратко)

1. Проверить проект локально.
2. Создать **пустой** репозиторий на GitHub.
3. Поднять VM с Ubuntu Server и подготовить её.
4. Зарегистрировать раннер на VM.
5. Сделать первый `git push` (после этого pipeline пройдёт целиком).
6. Показать демонстрацию.

Порядок важен: если запушить проект до появления раннера, job `deploy` будет висеть в очереди.

---

## Шаг 1. Локальная проверка (на вашем ПК)

Нужны: **Python 3.10+** и **Git**.
- Windows: https://www.python.org/downloads/ (при установке отметьте *Add python.exe to PATH*) и https://git-scm.com/download/win
- Linux: `sudo apt install python3 python3-venv python3-tk git`
- macOS: `brew install python git python-tk`

Откройте терминал в папке проекта (где лежит этот README).

**Linux / macOS**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```
Если PowerShell ругается на политику выполнения, один раз выполните `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, либо используйте `cmd` и `.venv\Scripts\activate.bat`.

Проверки:
```bash
flake8 .                # ничего не выведет, если всё хорошо
python -m pytest -v     # должно быть 22 passed
```

Запуск интерфейсов:
```bash
python -m app.web       # откройте http://localhost:8080
python -m app.gui       # окно tkinter
```

Если всё зелёное, переходим дальше.

---

## Шаг 2. Репозиторий на GitHub

1. https://github.com → **New repository**.
2. Название: `mortgage-calc`.
3. Видимость: лучше **Private** (см. раздел «Безопасность» ниже). Если преподавателю нужен доступ, добавьте его в *Settings → Collaborators*.
4. **Не** ставьте галочки *Add a README*, *.gitignore*, *license*: репозиторий должен быть пустым.
5. Нажмите **Create repository**. Страницу пока не закрывайте.

Настройте Git (один раз на ПК):
```bash
git config --global user.name "Ваше Имя"
git config --global user.email "ваша_почта@example.com"
```

Для `git push` понадобится авторизация. Вместо пароля GitHub требует токен:
**Settings (профиль) → Developer settings → Personal access tokens → Tokens (classic) → Generate new token**, права **`repo`** и **`workflow`**. Скопируйте токен сразу, потом он не покажется. Этот токен вводится вместо пароля при первом push. Альтернатива: настроить SSH-ключ (https://docs.github.com/ru/authentication).

Инициализируйте локальный репозиторий, **но пока не пушьте**:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<ВАШ_ЛОГИН>/mortgage-calc.git
```

---

## Шаг 3. Виртуальная машина (прод)

GUI на VM не нужен: используйте **Ubuntu Server 22.04 или 24.04 LTS**.

### 3.1. Создание VM в VirtualBox

1. Скачайте образ *Ubuntu Server* (файл `.iso`) с https://ubuntu.com/download/server и установите VirtualBox.
2. **Создать** → имя `prod-vm`, укажите ISO. Поставьте галочку **Skip Unattended Installation**, если она есть.
3. Ресурсы: 2 ГБ RAM (минимум 1 ГБ), 2 CPU, диск 15–20 ГБ.
4. **Настройки → Сеть → Адаптер 1:**
   - **Сетевой мост (Bridged Adapter)**: VM получит IP в вашей сети, сайт открывается с хоста по `http://<IP_VM>:8080`. Рекомендуемый вариант.
   - Если мост не работает (корпоративный Wi-Fi, ограничения сети): оставьте **NAT** и добавьте проброс портов (*Дополнительно → Проброс портов*): хост `2222` → гость `22` (SSH) и хост `8080` → гость `8080` (сайт). Тогда сайт открывается на `http://localhost:8080`, а SSH: `ssh -p 2222 user@127.0.0.1`.

### 3.2. Установка Ubuntu Server

Запустите VM и пройдите установщик с настройками по умолчанию. Важные моменты:
- Язык и раскладка: на ваш вкус.
- Сеть: DHCP по умолчанию.
- Зеркало: по умолчанию.
- Профиль: задайте имя пользователя (например `student`) и пароль. **Запомните их**, они понадобятся.
- На экране **SSH Setup** отметьте **Install OpenSSH server** (пробелом).
- Дополнительные пакеты (snaps) выбирать не нужно.

После установки перезагрузитесь и войдите под созданным пользователем.

### 3.3. Узнать IP и подключиться по SSH

На VM:
```bash
ip a
```
Ищите адрес вида `192.168.x.x` у интерфейса (`enp0s3` и т.п.).

С основного ПК (так удобнее копировать команды):
```bash
ssh student@192.168.x.x
```
Дальше **все команды из шагов 3.4 и 4 выполняются на VM** (по SSH или в окне VirtualBox).

### 3.4. Подготовка VM

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip rsync curl git
```

Папка приложения:
```bash
sudo mkdir -p /opt/mortgage-app
sudo chown $USER:$USER /opt/mortgage-app
```

Systemd-сервис (запускает приложение через gunicorn и поднимает его после перезагрузки VM). Команда подставит ваше имя пользователя автоматически:
```bash
sudo tee /etc/systemd/system/mortgage-app.service > /dev/null <<EOF
[Unit]
Description=Mortgage calculator
After=network.target

[Service]
User=$USER
WorkingDirectory=/opt/mortgage-app
ExecStart=/opt/mortgage-app/venv/bin/gunicorn --bind 0.0.0.0:8080 --workers 2 app.web:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF
```
```bash
sudo systemctl daemon-reload
sudo systemctl enable mortgage-app
```
Запускать сервис сейчас не нужно: `venv` и код появятся при первом деплое.

Разрешите пользователю перезапускать **только этот** сервис без пароля (раннер выполняет `sudo systemctl restart mortgage-app` в неинтерактивном режиме):
```bash
echo "$USER ALL=(root) NOPASSWD: /usr/bin/systemctl restart mortgage-app" | sudo tee /etc/sudoers.d/mortgage-app
sudo chmod 440 /etc/sudoers.d/mortgage-app
sudo visudo -cf /etc/sudoers.d/mortgage-app
```
Последняя команда должна ответить `parsed OK`. Проверка пути: `which systemctl` должен вернуть `/usr/bin/systemctl`.

Файрвол. На Ubuntu Server `ufw` по умолчанию выключен, и тогда ничего делать не нужно. Проверьте: `sudo ufw status`. Если он `active`, откройте порты:
```bash
sudo ufw allow 22/tcp
sudo ufw allow 8080/tcp
```

---

## Шаг 4. GitHub Actions Runner на VM

1. В репозитории на GitHub: **Settings → Actions → Runners → New self-hosted runner**.
2. Выберите **Linux** и архитектуру **x64** (если VM на Apple Silicon, то ARM64).
3. На странице будут блоки **Download** и **Configure** с актуальными командами и **одноразовым токеном** (действует около часа). Выполните команды из блока **Download** на VM (по SSH), как есть, под вашим обычным пользователем (не root). Выглядят они примерно так:
   ```bash
   mkdir actions-runner && cd actions-runner
   curl -o actions-runner-linux-x64-<версия>.tar.gz -L <ссылка>
   tar xzf ./actions-runner-linux-x64-<версия>.tar.gz
   ```
4. Регистрация. Возьмите команду `./config.sh --url ... --token ...` со страницы GitHub и **добавьте к ней** `--labels prod --unattended`:
   ```bash
   ./config.sh --url https://github.com/<ЛОГИН>/mortgage-calc --token <ТОКЕН> --labels prod --unattended
   ```
   Метка `prod` обязательна: workflow ищет раннер по ней (`runs-on: [self-hosted, prod]`).
5. Установка как сервиса, чтобы раннер работал в фоне и после перезагрузки VM:
   ```bash
   sudo ./svc.sh install $USER
   sudo ./svc.sh start
   sudo ./svc.sh status
   ```
   В статусе должно быть `active (running)`.
6. Вернитесь в **Settings → Actions → Runners**: раннер должен показываться со статусом **Idle** (зелёный). 📸 *Скриншот для отчёта.*

---

## Шаг 5. Первый push и запуск pipeline

На локальном ПК:
```bash
git push -u origin main
```
(логин GitHub и токен вместо пароля.)

Откройте вкладку **Actions** в репозитории. Должен запуститься workflow **CI/CD** с тремя job:

1. **Lint (flake8)**: проверка стиля.
2. **Tests (pytest)**: запускается только после успешного lint.
3. **Deploy to production VM**: запускается только после успешных тестов и только при push в `main`. Выполняется на вашей VM: копирует код в `/opt/mortgage-app`, ставит зависимости в `venv`, перезапускает сервис и проверяет, что `/health` отвечает.

Когда все три job зелёные, откройте в браузере на хосте:
```
http://<IP_VM>:8080
```
Должен появиться калькулятор (при NAT с пробросом: `http://localhost:8080`).

Проверка на самой VM:
```bash
systemctl status mortgage-app
curl http://127.0.0.1:8080/health      # ok
```

---

## Шаг 6. Демонстрация (для защиты)

### 6.1. Работа решения
- Покажите `http://<IP_VM>:8080`, введите значения (например 1 000 000 руб., 12 %, 1 год: платёж **88 848,79**).
- Покажите локальную tkinter-версию: `python -m app.gui`.

### 6.2. Работа тестов
- Локально: `python -m pytest -v`.
- В GitHub: **Actions → последний запуск → job «Tests (pytest)»**, раскройте шаг `python -m pytest -v` с логом.
- Объясните, что проверяют тесты: эталонный платёж, нулевая ставка, связь «платёж × месяцы = общая сумма», график платежей (остаток к концу срока равен нулю, сумма «тела» равна сумме кредита), отказ на некорректных данных (нулевая и отрицательная сумма, срок, ставка, NaN/inf), работа веб-страницы, показ ошибки и экранирование ввода.

### 6.3. Автоматическая поставка (главный пункт)
1. В `app/web.py` измените заголовок, например `<h2>Калькулятор ипотеки</h2>` → `<h2>Калькулятор ипотеки v2</h2>`.
2. Поправьте тест, если он зависит от текста (тест `test_page_opens` ищет «Калькулятор ипотеки», он останется зелёным).
3. Отправьте:
   ```bash
   git add .
   git commit -m "Change page title"
   git push
   ```
4. В **Actions** покажите, как последовательно проходят `lint → test → deploy`.
5. Обновите страницу в браузере (Ctrl+F5): заголовок изменился, а на VM вы ничего вручную не делали.

### 6.4. Бонус: сломанный код не попадает в прод
1. В `app/mortgage.py` сломайте формулу, например замените `principal * k` на `principal * k * 2`.
2. `git commit -am "Break formula"` и `git push`.
3. В Actions: `lint` зелёный, **`test` красный**, `deploy` не запускается (пропущен). Откройте сайт: на проде осталась прошлая рабочая версия.
4. Верните формулу, снова `commit` и `push`: pipeline снова зелёный.

### 6.5. Бонус: линтер
Добавьте в любой файл лишний пробел в конце строки или слишком длинную строку (больше 100 символов) и запушьте: упадёт job `lint`, до тестов и деплоя дело не дойдёт.

### Что приложить к отчёту (скриншоты)
- [ ] Раннер **Idle** в *Settings → Actions → Runners*
- [ ] Файл `.github/workflows/ci-cd.yml`
- [ ] Зелёный pipeline `lint → test → deploy`
- [ ] Лог pytest в Actions
- [ ] Сайт до и после изменения
- [ ] Красный pipeline со сломанным кодом
- [ ] `systemctl status mortgage-app` на VM

---

## Безопасность

- Self-hosted раннер выполняет код из репозитория на вашей VM. Поэтому лучше держать репозиторий **приватным**.
- Если репозиторий публичный: в *Settings → Actions → General → Fork pull request workflows* включите требование одобрения запусков от внешних участников. Job `deploy` в этом проекте всё равно запускается только при push в `main`, а не из pull request.
- Токен регистрации раннера и Personal Access Token не публикуйте и не коммитьте в репозиторий.
- Правило sudo ограничено одной командой (перезапуск сервиса), а не `NOPASSWD: ALL`.

---

## Частые проблемы

| Симптом | Причина и решение |
|---|---|
| Job `deploy` висит в **Queued** | Раннер офлайн или нет метки `prod`. На VM: `cd ~/actions-runner && sudo ./svc.sh status`, при необходимости `sudo ./svc.sh start`. В *Settings → Runners* у раннера должны быть метки `self-hosted` и `prod` |
| `sudo: a password is required` | Не сработало правило sudoers. Проверьте `sudo cat /etc/sudoers.d/mortgage-app`: там должен быть ваш логин и путь из `which systemctl` |
| `rsync: ... Permission denied` | Папка не принадлежит пользователю раннера: `sudo chown -R $USER:$USER /opt/mortgage-app` |
| `venv ... ensurepip is not available` | Не установлен `python3-venv`: `sudo apt install -y python3-venv` |
| Health check упал, сайт не открывается | Смотрите логи: `journalctl -u mortgage-app -n 50 --no-pager` и `systemctl status mortgage-app` |
| Сайт не открывается с хоста | Проверьте тип сети VM (Bridged или проброс портов), `ip a`, файрвол `sudo ufw status` |
| `flake8` ругается | Смотрите файл и номер строки в логе. Частые причины: строка длиннее 100 символов, нет двух пустых строк между функциями, пробелы в конце строки |
| Тесты падают в Actions, а локально проходят | Не закоммичены `app/__init__.py` или `tests/` (проверьте `git status`) |
| `git push` просит пароль и отказывает | Нужен Personal Access Token вместо пароля (шаг 2) |
| Токен раннера «истёк» | Токен на странице New self-hosted runner живёт около часа. Обновите страницу и возьмите новый |
| Предупреждения про Node.js в логах Actions | Это только предупреждения об устаревании версий `actions/*`. При желании поднимите версии в workflow до актуальных |

Полная переустановка раннера, если что-то пошло не так:
```bash
cd ~/actions-runner
sudo ./svc.sh stop && sudo ./svc.sh uninstall
./config.sh remove --token <НОВЫЙ_ТОКЕН_ИЗ_GITHUB>
```
после чего повторите шаг 4.

---

## Справка: полезные команды на VM

```bash
systemctl status mortgage-app              # состояние приложения
sudo systemctl restart mortgage-app        # перезапуск вручную
journalctl -u mortgage-app -f              # логи приложения в реальном времени
cd ~/actions-runner && sudo ./svc.sh status   # состояние раннера
ls /opt/mortgage-app                       # что сейчас задеплоено
```
