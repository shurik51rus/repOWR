# repOWR Protocol

**Decentralized reputation system on the TON blockchain**

[🇷🇺 Документация на русском](README.ru.md) | [Website](https://repowr.tech) | [Telegram bot](https://t.me/RepOracle_bot)

---

## What is repOWR?

repOWR is an open protocol for building verifiable reputation on the TON blockchain. Reviews and profiles are stored in Jetton transaction comments, making them transparent, immutable, and owned by users — not platforms.

## Key Features

- Reputation is tied to a wallet address, not a username
- Two formats: simplified (`repOWR:5:Great service:`) and JSON for detailed reviews
- Decentralized on-chain profiles (identity)
- **Social Power Score** — a composite influence metric (0–2000 SP) with 6 ranks
- **Dynamic NFTs** — reputation card updates in real time, no re-minting required
- Reviews cannot be deleted, faked, or inflated
- Open API, embeddable widgets, Telegram bot

## How It Works

1. **Send a review** — transfer any amount of SPW tokens to the recipient with a review in the transaction comment
2. **Parser reads it** — the system monitors all SPW transactions in real time and recognizes the repOWR format
3. **Reputation is available** — check any wallet's reputation via the bot, website, widget, or API

## Quick Start

### Leave a review (simplified format)
```
repOWR:5:Great service, fast delivery:
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
Send SPW to the repOWR address `UQCywBj5RIyKYf1SeLMkmt9gL13pMzCaqORZZ3iFeJyoRaqO` with the comment:
```json
{
  "protocol": "repOWR",
  "type": "identity",
  "nickname": "YourNick",
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
| DEX | [STON.fi](https://app.ston.fi/swap?ft=TON&tt=EQABi71g1y3BFnxA_qcY-giSbtRx9gArA9xXpfeZyTqP_Jwh&chartVisible=false) |

## Repository Structure

```
repOWR/
├── docs/
│   └── protocol.md           # Full protocol specification
├── src/
│   ├── parser/
│   │   ├── validator.py       # Message validation (simplified + JSON)
│   │   ├── ton_parser.py      # TON blockchain transaction parser
│   │   ├── reputation_counter.py  # Reputation calculation
│   │   ├── social_power.py    # Social Power Score and rank calculation
│   │   ├── database.py        # SQLite layer (transactions, ratings, profiles, balances)
│   │   └── config.py          # Parser and API settings
│   ├── api/
│   │   └── index.php          # REST API (PHP)
│   └── nft/
│       ├── nft_image.php      # Dynamic SVG NFT card
│       └── nft_metadata.php   # NFT metadata (TEP-64 standard)
├── widget/
│   ├── profile-widget.html    # Embeddable profile widget
│   └── embed.md               # Widget integration guide
├── examples/
│   ├── send-review.md         # How to send a review
│   └── create-profile.md      # How to create a profile
├── README.md                  # Documentation (English)
├── README.ru.md               # Documentation (Russian)
└── LICENSE                    # MIT License
```

## API

Base URL: `https://repowr.tech/api/`

| Endpoint | Description |
|----------|-------------|
| `?endpoint=health` | API status |
| `?endpoint=reputation&address=...` | Wallet reputation (includes Social Power and rank) |
| `?endpoint=reviews&address=...&limit=5` | Wallet reviews (received and given) |
| `?endpoint=top&limit=10` | Top users by Social Power |
| `?endpoint=stats` | Overall system statistics |

## Widget

Embed reputation lookup on any website:
```html
<script src="https://repowr.tech/widget.js"></script>
<div class="repowr-widget" data-default-address="UQATKnig..."></div>
```

## Dynamic NFTs

Every user can mint a reputation NFT card that displays live data: nickname, rank, Social Power, rating, review count, and SPW balance.

The card updates automatically when data changes — no re-minting required.

5 card styles available: Cyberpunk, Web3 Cosmos, P2P Exchange, Freelance, Meme.

NFT metadata follows the TEP-64 standard and is supported by the Getgems marketplace.

```
https://repowr.tech/nft_metadata.php?address=0:abc...&style=1
```

## Links

- **Website:** https://repowr.tech
- **Telegram bot:** https://t.me/RepOracle_bot
- **Telegram community:** https://t.me/repOWR_protocol
- **Protocol documentation:** [docs/protocol.md](docs/protocol.md)

## License

MIT — free to use in any project.
