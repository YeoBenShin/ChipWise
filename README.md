# Greedy Debt Settlement (Telegram Bot)

A simple Telegram bot that helps settle debts between players using a greedy cash-flow algorithm.

The bot lets you:
- add player final balances,
- set a shared initial buy-in,
- edit players or buy-in values,
- compute a minimal set of settlement transfers.

## How It Works

This project computes each player's net amount:

- `net = final_balance - initial_buy_in`

Then it greedily settles debts by repeatedly matching:
- the player who owes the most, and
- the player who is owed the most.

Each transfer is the minimum of those two amounts, repeated until all balances are settled.

## Project Structure

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
```

4. Run the bot:

```bash
python telegram_bot.py
```

## Setup (Docker)

1. Build the image:

```bash
docker build -t greedy-debt-settlement .
```

2. Run the container with your bot token:

```bash
docker run --rm \
  -e TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here \
  greedy-debt-settlement
```

## Bot Usage

Start the bot in Telegram with `/start`.

Main menu options:
- `Add Players`
- `Add Initial Buy In (Default = $0)`
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
- Amount is the final state balance relative to the initial buy-in.
- If initial buy-in is $10 and a player bought in for $20 total, subtract the initial $10 before entering amount.

## Example Settlement Output

The bot returns:
- a pot consistency summary,
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
