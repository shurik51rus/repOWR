# repOWR Protocol

**Decentralized reputation system on the TON blockchain**

[🇷🇺 Документация на русском](README.ru.md) | [Website](https://repowr.tech) | [Telegram Bot](https://t.me/RepOracle_bot)

---

## What is repOWR?

repOWR is an open protocol for building verifiable reputation on the TON blockchain. Reviews and profiles are stored in Jetton transaction comments, making them transparent, immutable, and owned by users — not platforms.

**Key features:**
- Reputation tied to wallet address, not usernames
- Two formats: simple (`repOWR:5:Great work:`) and JSON for detailed reviews
- Decentralized profiles (identity) stored on-chain
- Reviews cannot be deleted, faked, or manipulated
- Open API, embeddable widgets, Telegram bot

## How it works

1. **Send a review** — Transfer any amount of SPW tokens to the recipient with a review in the transaction comment
2. **Parser reads** — The system monitors all SPW transactions in real-time and extracts repOWR-formatted messages
3. **Reputation available** — Check any wallet's reputation via the bot, website, widget, or API

## Quick start

### Leave a review (simple format)
```
repOWR:5:Excellent service, fast delivery:
```

### Leave a review (JSON format)
```json
{
  "protocol": "repOWR",
  "rating": 5,
  "type": "deal",
  "comment": "Professional and reliable"
}
```

### Create a profile
Send SPW to the OMR address `UQCywBj5RIyKYf1SeLMkmt9gL13pMzCaqORZZ3iFeJyoRaqO` with comment:
```json
{
  "protocol": "repOWR",
  "type": "identity",
  "nickname": "YourName",
  "bio": "Your description",
  "skills": ["trading", "development"],
  "links": {"telegram": "@yourname"}
}
```

## SPW Token

| Parameter | Value |
|-----------|-------|
| Blockchain | TON |
| Standard | Jetton (TEP-74) |
| Total supply | 100,000,000 SPW |
| Jetton Master | `EQABi71g1y3BFnxA_qcY-giSbtRx9gArA9xXpfeZyTqP_Jwh` |
| DEX | [STON.fi](https://app.ston.fi) |

## Repository structure

```
repOWR/
├── docs/
│   └── protocol.md          # Full protocol specification
├── src/
│   ├── parser/
│   │   ├── validator.py      # Message validation (simple + JSON)
│   │   ├── ton_parser.py     # TON blockchain transaction parser
│   │   └── reputation.py     # Reputation calculation engine
│   ├── api/
│   │   └── index.php         # REST API (PHP)
│   └── widget/
│       └── embed.md          # Widget embedding instructions
├── examples/
│   ├── send-review.md        # How to send a review
│   └── create-profile.md     # How to create a profile
├── README.md                 # This file
├── README.ru.md              # Russian documentation
└── LICENSE                   # MIT License
```

## API

Base URL: `https://repowr.tech/api/`

| Endpoint | Description |
|----------|-------------|
| `?endpoint=health` | API status |
| `?endpoint=reputation&address=...` | Get wallet reputation |
| `?endpoint=reviews&address=...` | Get reviews for wallet |
| `?endpoint=top&limit=10` | Top users by reputation |
| `?endpoint=stats` | Overall system statistics |

## Widget

Embed reputation check on any website:
```html
<script src="https://repowr.tech/widget.js"></script>
<div class="repowr-widget" data-default-address="UQATKnig..."></div>
```

## Links

- **Website:** https://repowr.tech
- **Telegram Bot:** https://t.me/RepOracle_bot
- **Protocol Docs:** [docs/protocol.md](docs/protocol.md)

## License

MIT — free to use in any project.
