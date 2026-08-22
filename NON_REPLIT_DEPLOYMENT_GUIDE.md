# Degen Dictionary — Railway Deployment Guide

**Prepared by Manus AI**

## Recommended Host

Use **Railway** for this project. The Degen Dictionary is a Python Telegram bot that uses long polling, so it needs a single process running continuously rather than a website host. Railway documents a background worker as an always-on service for continuous event processing, and it does not require a public domain unless you intentionally expose an HTTP endpoint.[1]

> This deployment does **not** need a domain name, port, web server, or webhook. The bot itself opens the outbound connection to Telegram using `run_polling()`.

| Option | Recommendation | Reason |
|---|---|---|
| **Railway** | **Use this** | Straightforward GitHub deployment for an always-on bot service. |
| Render Background Worker | Viable alternative | Its worker service is also continuous, but Render’s free plan is not available for background workers.[2] |
| Static hosting | Do not use | Static hosts cannot run a persistent Python process. |
| Vercel / Netlify serverless functions | Do not use for this version | The current long-polling process is not a request-driven serverless workload. |

## Files Prepared for Deployment

The project now includes a portable Docker-based deployment setup. It is ready to push to GitHub and import into Railway.

| File | Purpose |
|---|---|
| `pyproject.toml` | Corrected to install `python-telegram-bot`, which is the library that `main.py` actually imports. |
| `requirements.txt` | Pins the Python dependency required at deployment time. |
| `Dockerfile` | Builds a Python 3.11 container and starts the bot with `python main.py`. |
| `.dockerignore` | Excludes local metadata, caches, `.env`, and development-only files from the container build. |

## Deploy on Railway

First, commit and push the prepared files to the GitHub repository. Do **not** commit your Telegram bot token.

```bash
git add pyproject.toml requirements.txt Dockerfile .dockerignore
git commit -m "Add Railway-ready Telegram bot deployment"
git push origin main
```

Next, create a Railway account and select **New Project** → **Deploy from GitHub repo**. Authorize GitHub if prompted, then select the Degen Dictionary repository. Railway will recognize the included `Dockerfile`; leave the deployment command unset so the container’s default command is used.

After the project has been created, open the service’s **Variables** section and add the following value:

| Variable | Value |
|---|---|
| `BOT_TOKEN` | The token supplied by Telegram’s @BotFather for this exact bot. |

Redeploy after adding the variable. Keep a single running service/replica. A polling bot cannot use the same token in two active locations at once, so stop any local development copy after Railway becomes the live deployment.

## Configure the Telegram Bot

In Telegram, open **@BotFather** and create the bot with `/newbot` if you have not already done so. Copy the supplied API token directly into Railway’s `BOT_TOKEN` variable. Never paste it into code, GitHub, a `.env` file that is committed, or a public deployment log.

This project uses Telegram inline queries. Inline mode enables users to call the bot from the message field in any chat by typing a bot username followed by a query.[3] Enable it in **@BotFather**:

```text
/setinline
```

Choose your bot and use a placeholder such as:

```text
Search degen terms…
```

## Verify the Live Bot

Once the Railway deployment status is successful, open **Deploy Logs**. The expected successful startup line is:

```text
Degen bot is awake and ready to explain your terrible financial decisions...
```

Test direct suggestions with:

```text
/suggest REKT | Total financial wipeout | I went all in and got absolutely rekt
```

Then test inline lookup from any Telegram chat:

```text
@your_bot_username REKT
```

If inline results do not appear, check that inline mode is enabled in BotFather, the bot username is correct, and the Railway logs contain no `No BOT_TOKEN found` or Python import errors.

## Important Data Limitation

The `/suggest` command currently writes entries to `suggestions.json` inside the running container. That is suitable only for a test launch. Any redeploy or restart can discard those suggestions, and JSON-file writes do not offer reliable concurrent access.

For a real launch, move suggestions to persistent storage such as Railway Postgres, Supabase Postgres, or another managed database. Keep `dictionary.json` in Git because it is the curated, read-only source of terms.

| Data | Current state | Production recommendation |
|---|---|---|
| `dictionary.json` | Bundled static source | Keep under Git version control. |
| `suggestions.json` | Local file modified at runtime | Replace with a database table or backed-up persistent store. |
| `BOT_TOKEN` | Environment variable read at startup | Store only as a Railway variable. |

## Optional Render Alternative

If you prefer Render, deploy the same Dockerfile as a **Background Worker**, add `BOT_TOKEN` as a secret environment variable, and run one instance. Render’s Blueprint reference supports `type: worker` with `runtime: docker`, but background workers cannot use its free plan.[2] The service still does not need a public domain.

## References

[1]: https://docs.railway.com/guides/cron-workers-queues "Railway — Cron Jobs, Background Workers, and Queues"
[2]: https://render.com/docs/blueprint-spec "Render — Blueprint YAML Reference"
[3]: https://core.telegram.org/bots/features "Telegram — Bot Features"
