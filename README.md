# CryptoParser - Stock Monitoring Telegram Bot 📈

## Overview
**CryptoParser** is a Telegram bot designed to help users monitor stock prices, view price charts, set price alerts, and manage currency preferences. Built with Python, this bot integrates with the Telegram API, `yfinance` for stock data, and `plotly` for generating candlestick charts. It supports multiple currencies and provides a user-friendly interface with inline keyboards for seamless interaction.

The bot allows users to:
- Check real-time stock prices.
- View 1-month candlestick charts for stocks, indices, or cryptocurrencies.
- Set price alerts for specific symbols.
- Switch between multiple currencies (USD, EUR, UZS, RUB, GBP).
- Handle errors gracefully with improved timeout settings.

## Features
- **Real-Time Price Monitoring:** Fetch current stock prices for symbols like `AAPL`, `^GSPC`, or `BTC-USD`.
- **Candlestick Charts:** Generate and display 1-month price charts using `plotly`.
- **Price Alerts:** Set alerts for specific price targets (e.g., `AAPL 150`).
- **Currency Conversion:** Convert prices to supported currencies (USD, EUR, UZS, RUB, GBP) using real-time exchange rates.
- **Interactive Interface:** Navigate through options using inline keyboards.
- **Error Handling:** Graceful handling of errors, including connection timeouts, with user-friendly feedback.
- **Periodic Alert Checks:** Automatically checks price alerts every 5 minutes using Telegram's `JobQueue`.

## Supported Currencies
The bot supports the following currencies:
- **USD**: US Dollar ($)
- **EUR**: Euro (€)
- **UZS**: Uzbekistani Som (soʻm)
- **RUB**: Russian Ruble (₽)
- **GBP**: British Pound (£)

## Requirements
To run the bot, you need to install the required Python packages listed in `requirements.txt`. The bot also requires a Telegram Bot Token and an internet connection to fetch stock data and exchange rates.

### Dependencies
- `python-telegram-bot`: For interacting with the Telegram API.
- `yfinance`: To fetch stock and cryptocurrency data.
- `plotly`: For generating candlestick charts.
- `python-dotenv`: To load environment variables (e.g., bot token).
- `requests`: For fetching exchange rates.
- `logging`: For logging bot activities and errors.

Install the dependencies using:
```bash
pip install -r requirements.txt
```

## Setup
1. **Clone the Repository:**
   ```bash
   git clone https://github.com/usmanovabdulaziz/CryptoParser.git
   cd CryptoParser
   ```

2. **Create a Virtual Environment (Optional but Recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables:**
   - Create a `.env` file in the project root directory.
   - Add your Telegram Bot Token (obtained from [BotFather](https://t.me/BotFather)):
     ```
     BOT_TOKEN=your-telegram-bot-token
     ```
   - Example `.env` file:
     ```
     BOT_TOKEN=123456:ABC-GFF1234gxIcl-zyx57W2v1u123ew13
     ```

5. **Run the Bot:**
   ```bash
   python main.py
   ```

## Usage
1. **Start the Bot:**
   - Open Telegram and search for your bot.
   - Send the `/start` command to initialize the bot.

2. **Available Commands:**
   - `/start`: Restart the bot and display the main menu.
   - `/currency CODE`: Change the currency (e.g., `/currency USD`).
   - `/price SYMBOL`: Get the current price for a symbol (e.g., `/price AAPL`).
   - `/chart SYMBOL`: Get a 1-month candlestick chart for a symbol (e.g., `/chart BTC-USD`).
   - `/alert SYMBOL PRICE`: Set a price alert (e.g., `/alert ^GSPC 5000`).

3. **Main Menu Options:**
   - **📈 Price:** Check the current price of a stock or cryptocurrency.
   - **📊 Chart:** View a 1-month candlestick chart for a symbol.
   - **🔔 Set Alert:** Set a price alert for a specific symbol.
   - **💱 Change Currency:** Switch between supported currencies.
   - **ℹ️ Help:** View the help menu with command details and examples.

4. **Symbol Examples:**
   - `AAPL`: Apple Inc.
   - `^GSPC`: S&P 500 Index.
   - `BTC-USD`: Bitcoin in USD.
   - `EURUSD=X`: Euro to USD exchange rate.

5. **Alert Format:**
   - Use the format `SYMBOL PRICE` (e.g., `AAPL 150` or `BTC-USD 60000`).

## Code Structure
- **`main.py`:** The main script containing the bot's logic.
  - **Imports:** Libraries for Telegram API, stock data, charting, and environment variable management.
  - **Configuration:** Logging setup, Plotly configuration, and environment variable loading.
  - **Conversation States:** Manages the bot's conversation flow (`SELECT_ACTION`, `GET_SYMBOL`, `SET_ALERT`).
  - **Handlers:** Functions to handle commands, button callbacks, stock data fetching, alert setting, and error handling.
  - **Main Function:** Initializes the bot with custom request settings and starts polling.
- **`.env`:** Stores sensitive data like the bot token.
- **`requirements.txt`:** Lists all required Python packages.

## Error Handling
The bot includes robust error handling:
- **Timeouts:** Custom `HTTPXRequest` settings with increased timeouts (`connect_timeout=30`, `read_timeout=30`) to handle slow connections.
- **Invalid Inputs:** Validates symbols and price inputs with regex and error messages.
- **API Errors:** Catches and logs errors from `yfinance`, exchange rate APIs, and Telegram API.
- **User Feedback:** Provides clear error messages with options to return to the main menu.

## Logging
The bot uses Python's `logging` module to log activities and errors:
- Logs are formatted with timestamps, logger name, level, and message.
- Log level is set to `INFO` by default, but errors are logged with stack traces for debugging.

## Contributing
Contributions are welcome! If you'd like to contribute:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Make your changes and commit (`git commit -m "Add your feature"`).
4. Push to your branch (`git push origin feature/your-feature`).
5. Open a Pull Request on GitHub.

## Contact
For questions or support, feel free to reach out:
- GitHub: [usmanovabdulaziz](https://github.com/usmanovabdulaziz)
- Telegram: Contact via the bot or open an issue on GitHub.

---

Happy trading! 🚀
