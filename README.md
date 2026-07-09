# channel-autopilot

An autonomous content pipeline that runs my Telegram channel, [@izzatullokhnotes](https://t.me/izzatullokhnotes).

I share my experience building things — and this repo is the first thing I'm building in public: the system that writes and publishes those posts for me, daily, on GitHub Actions, for free.

## Why

Consistency is the hardest part of writing in public. Instead of relying on discipline, I'm removing it from the equation: ideas go into a queue whenever I have them, and the pipeline turns them into polished Uzbek posts and publishes one every day at 13:00 Tashkent time.

## Architecture

```
idea inbox (Telegram bot) ──► content queue (this repo)
                                     │
              GitHub Actions cron (daily, 08:00 UTC)
                                     │
                       draft post (Claude API)
                                     │
                approval gate (approve / edit / skip)
                                     │
                       publish to @izzatullokhnotes
```

Built in stages, each independently shippable:

- [x] **1. Plumbing** — repo, bot, Actions cron, test post end-to-end
- [x] **2. Idea inbox** — forward raw notes/voice to the bot, they land in the queue (queue lives in a private repo)
- [ ] **3. Voice & generator** — Claude turns a queue item into a post in my voice
- [ ] **4. Daily engine + approval gate** — draft daily, approve with one tap, auto-publish on timeout
- [ ] **5. Full autonomy + work mining** — flip a flag; mine my commits for "what I built" posts
- [ ] **6. Feedback loop** — track reactions/views, weekly digest

## Stack

Python 3.11+, `httpx`, raw Telegram Bot API (no framework — sending messages is one POST), GitHub Actions for scheduling. Secrets live in GitHub Secrets / a local gitignored `.env`, never in code.

## Running locally

```bash
cp .env.example .env   # fill in your bot token
pip install httpx
python scripts/post_test.py            # dry run
python scripts/post_test.py --publish  # post to the channel
```
