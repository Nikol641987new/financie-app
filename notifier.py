"""Odosielanie notifikácií cez Telegram bota."""

import os
import requests

from screener import Signal


def send_telegram_message(text: str, bot_token: str, chat_id: str) -> None:
    """Pošle textovú správu cez Telegram bota."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    response = requests.post(url, data={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    })
    response.raise_for_status()


def format_signal(signal: Signal) -> str:
    emoji = "🟢" if signal.signal_type == "BUY" else "🔴"
    return (
        f"{emoji} *{signal.ticker}*: {signal.signal_type}\n"
        f"Dôvod: {signal.reason}\n"
        f"Cena: {signal.price:.2f}"
    )


def notify_signals(signals: list[Signal]) -> None:
    """Odošle všetky signály. Ak Telegram nie je nastavený, len ich vypíše do konzoly."""
    if not signals:
        print("Žiadne signály dnes.")
        return

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    for signal in signals:
        message = format_signal(signal)
        print(message)
        print("---")

        if bot_token and chat_id:
            try:
                send_telegram_message(message, bot_token, chat_id)
            except Exception as e:
                print(f"Chyba pri odosielaní Telegram správy: {e}")
        else:
            print("(Telegram nie je nastavený - správa len vypísaná do konzoly. Pozri README.md)")
