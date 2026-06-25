# 💎 Diamond Premium Bot

> India's #1 Trusted Diamond Store — Telegram Bot

---

## Features

- 🥉 Starter / 🥈 Popular / 🥇 Premium plans
- Styled UPI QR code with branded canvas
- Auto TXN ID generation
- Admin approve / reject flow
- Card pool management (single + bulk)
- Balance command
- Inline "How to Use" guide

---

## Setup

```bash
# 1. Clone repo
git clone https://github.com/YOUR_USERNAME/diamond-bot.git
cd diamond-bot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Edit bot_config.py with your token / admin ID / UPI
nano bot_config.py

# 4. Run
python main_bot.py
```

---

## Admin Commands

| Command | Description |
|---|---|
| `/approve TXN-ID` | Approve payment & send card |
| `/reject TXN-ID` | Reject payment |
| `/cc_add <card>` | Add single card to pool |
| `/cc_add_bulk` | Bulk add cards (send lines, then `/done`) |
| `/cc_list` | View card pool status |

---

## Run on GitHub Actions (24/7)

Add a workflow in `.github/workflows/bot.yml`:

```yaml
name: Run Bot
on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: python main_bot.py
        env:
          BOT_TOKEN: ${{ secrets.BOT_TOKEN }}
```

> Set `BOT_TOKEN` in GitHub → Settings → Secrets → Actions.

---

_Premium Edition — Coded with ❤️_
