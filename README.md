# Fugitive Heist Referee Bot

The **Fugitive Heist Referee Bot** is a Discord bot that assists referees in running and scoring the custom game *Fugitive Heist*.  
It automates round management, scoring through emoji reactions, and provides simple slash commands for easy control.

---

## ✨ Features

- **Team Management**
  - Set custom names for two teams.
  - Flip attacker/defender roles between rounds.
- **Round Timer**
  - Start, pause, resume, extend, and stop rounds.
  - Automatically send score updates every 5 minutes.
- **Scoring System**
  - React with 💎 (extraction) for +10 attacker points.
  - React with 💲 (recovery) for +6 defender points.
  - React with ❌ to remove points from a photo.
  - Players' names are shown in extraction/recovery messages.
- **Manual Score Control**
  - Add or subtract points manually.
  - View scores at any time, even outside of rounds.
- **Slash Commands**
  - Full use of modern Discord slash commands for intuitive interaction.

---

## 🛠 Setup Instructions

1. **Clone this repository:**

   ```bash
   git clone https://github.com/your-username/fugitive-heist-referee-bot.git
   cd fugitive-heist-referee-bot
