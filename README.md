# Greedy Debt Settlement (Telegram Bot)

A simple Telegram bot that helps settle debts between players using a greedy cash-flow algorithm.

The bot lets you:
- add player final balances,
- edit player values,
- compute a minimal set of settlement transfers.

## How It Works

This project expects each player's final net result directly:

- losses as negative numbers,
- winnings as positive numbers.

Then it greedily settles debts by repeatedly matching:
- the player who owes the most, and
- the player who is owed the most.

Each transfer is the minimum of those two amounts, repeated until all balances are settled.

## Project Structure

- `app.py`: Flask entrypoint, webhook routes, and bot handlers
- `telegram_bot.py`: Telegram bot UI and conversation flow
- `min_cash_flow.py`: Greedy debt settlement algorithm
- `requirements.txt`: Python dependency list
- `Dockerfile`: Container setup to run the bot

## Requirements

- Python 3.11+
- A Telegram bot token from BotFather

## Setup (Local)

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
WEBHOOK_URL=https://your-public-domain-or-tunnel
WEBHOOK_SECRET_TOKEN=optional_shared_secret
```

4. Run the Flask app locally:

```bash
python app.py
```

5. Register the webhook once your public URL is available:

```bash
curl https://your-domain-or-vercel-app/api/set-webhook
```

The webhook endpoint is `POST /api/webhook` and the webhook registration endpoint is `GET /api/set-webhook`.

## Setup (Docker)

1. Build the image:

```bash
docker build -t greedy-debt-settlement .
```

2. Run the container with your bot token:

```bash
docker run --rm \
  -e TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here \
  -e WEBHOOK_URL=https://your-public-domain-or-tunnel \
  -e WEBHOOK_SECRET_TOKEN=optional_shared_secret \
  greedy-debt-settlement
```

## Setup (Vercel)

Vercel will use the top-level Flask `app` defined in [app.py](app.py).

Required environment variables:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
WEBHOOK_URL=https://your-vercel-project.vercel.app
WEBHOOK_SECRET_TOKEN=optional_shared_secret
```

After deployment, call:

```bash
curl https://your-vercel-project.vercel.app/api/set-webhook
```

That registers Telegram to send updates to:

```text
https://your-vercel-project.vercel.app/api/webhook
```

## Bot Usage

Start the bot in Telegram with `/start`.

Main menu options:
- `Add Players`
- `Edit Information`
- `Compute Debt`
- `Clear All Information`

### Add Players Format

When adding players, send one player per line:

```text
Alice -20
Ben 15.5
Cheryl 100
```

Important:
- Amount is the player's final net result.
- Use negative for losses and positive for winnings.

## Example Settlement Output

The bot returns:
- a totals consistency summary,
- total owed vs total owes,
- settlement transfers like:

```text
Alice -> Cheryl $20.00
Bob -> Cheryl $5.50
```

## Commands

- `/start`: Show main menu and current state
- `/cancel`: Cancel current operation and return to main flow

## Notes

- Data is stored in-memory per chat session (`context.user_data`) and is not persisted to a database.
- If total owed and total owes do not match, the algorithm returns a warning in the output.
