# tg-vc-streamer

A simple Telegram Voice Chat music bot built with `Pyrogram` ,`PyTgCalls` and `yt-dlp`.


## Requirements

1. A Telegram user account to act as the playback bot, since bots are not able to join voice chats.

> The user account must be an admin of the chat, with Manage Voice Chats and Delete Messages permissions.

2. A Linux Environment

Ensure you have the following installed:

- Python 3.10 or higher

- `uv`

## Installation

Clone the Repository

```bash
git clone https://github.com/zkittles101/tg-vc-streamer.git
cd tg-vc-streamer
```

Setup the environment using  `uv` to handle dependencies and the virtual environment automatically:

``` bash
uv sync
```

## Configuration

1. Copy the provided sample environment file:

``` bash
cp sample.env .env
```

2. Fill in the following variables in your `.env`:

| Key   | How to obtain    |
|--------------- | --------------- |
| `API_ID`       | Go to [my.telegram.org](my.telegram.org) , login with the Telegram account, and create an "App" to get your ID.   |
| `API_HASH`     | Obtained alongside your `API_ID` from [my.telegram.org](my.telegram.org).   |
| `SESSION_STRING`   | Run `uv run generate_string_session.py` and follow the login steps.   |
| `CHAT_ID`   | Add [@myidbot](https://t.me/myidbot) to your group and run /getgroupid in the chat.  |

## Usage

To start the bot, run:

```bash
uv run main.py
```

## Commands

| Commands   | Description    |
|--------------- | --------------- |
| `/play [query]`   |  Searches YouTube and plays the song in VC.  |
| `/skip`   | Skips the currently playing track.   |
| `/stop`   | Stops playback and clears the entire queue.   |
| `/queue`   | Shows the current song and remaining queue size.   |
| `/help`   | Displays the help menu with all available commands.  |

## Credits

- [TheHamkerCat/Telegram_VC_Bot](https://github.com/TheHamkerCat/Telegram_VC_Bot) : used as a template for most of this project
