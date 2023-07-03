# Fish shop bot

Bot for selling fish in telegram.

![demo](./images/bot_demo.gif)

## How to install

- Сlone this repository:
```bash
git clone git@github.com:MaxHC-vlop/fish_shop_bot.git
```
- You must have python3.9 (or higher) installed.

- Create a virtual environment on directory project:
```bash
python3 -m venv env
 ```
- Start the virtual environment:
```bash
. env/bin/activate
```
- Then use pip to install dependencies:
```bash
pip install -r requirements.txt
```
- Create `.env` file and then populate it:
  - start project [here](https://www.elasticpath.com/)
  - take tokens [here](https://telegram.me/BotFather)
  - start redis db [here](https://redis.io/)

```
REDIS_DATABASE_HOST=redis host
REDIS_DATABASE_PORT=redis port
REDIS_DATABASE_PASSWORD=redis password
CLIENT_TOKEN=client token
CLIENT_ID=client id
TG_TOKEN=bot token
TG_LOGGER_TOKEN=logger bot token
TG_ADMIN_CHAT_ID=id admin chat
```

## Run

```bash
python tg_bot.py
```
