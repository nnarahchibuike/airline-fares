"""Telegram bot for flight scraper."""
import logging
import os
from datetime import datetime
from typing import List

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from core.models import FlightRequest, FlightResult
from core.orchestrator import FlightOrchestrator
from scrapers.emirates_scraper import EmiratesScraper
from scrapers.emiratesv2_scraper import EmiratesV2Scraper
from scrapers.ethiopian_scraper import EthiopianScraper
from scrapers.qatar_scraper import QatarScraper

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! 👋\n\n"
        "I can help you find the best flight prices.\n\n"
        "<b>Usage:</b>\n"
        "/search [ORIGIN] [DEST] [DEPART] [RETURN] [AIRLINE]\n\n"
        "<b>Examples:</b>\n"
        "1. Search all: /search LOS CAN 2025-12-03 2025-12-23\n"
        "2. Search specific: /search LOS CAN 2025-12-03 2025-12-23 emirates\n\n"
        "<i>Dates must be in YYYY-MM-DD format.</i>"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message when the command /help is issued."""
    await update.message.reply_text(
        "To search for flights, use the /search command:\n"
        "/search ORIGIN DESTINATION DEPART_DATE RETURN_DATE [AIRLINE]\n\n"
        "Optional [AIRLINE]: emirates, emiratesv2, ethiopian, qatar\n\n"
        "Example:\n"
        "/search LOS CAN 2025-12-03 2025-12-23 qatar"
    )

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /search command."""
    args = context.args
    if len(args) < 4 or len(args) > 5:
        await update.message.reply_text(
            "⚠️ Invalid format.\n\n"
            "Please use:\n"
            "/search ORIGIN DESTINATION DEPART_DATE RETURN_DATE [AIRLINE]\n\n"
            "Example:\n"
            "/search LOS CAN 2025-12-03 2025-12-23"
        )
        return

    origin, dest, dep_str, ret_str = args[:4]
    airline_filter = args[4].lower() if len(args) == 5 else None

    try:
        dep_date = datetime.strptime(dep_str, "%Y-%m-%d").date()
        ret_date = datetime.strptime(ret_str, "%Y-%m-%d").date()
    except ValueError:
        await update.message.reply_text(
            "⚠️ Invalid date format. Please use YYYY-MM-DD.\n"
            "Example: 2025-12-03"
        )
        return

    # Notify user that search is starting
    filter_msg = f" ({airline_filter.capitalize()})" if airline_filter else " (All Airlines)"
    status_msg = await update.message.reply_text(
        f"🔎 <b>Searching flights...</b>{filter_msg}\n"
        f"🛫 {origin} → {dest}\n"
        f"📅 {dep_str} to {ret_str}\n\n"
        "<i>This may take 2-3 minutes. Please wait...</i>",
        parse_mode="HTML"
    )

    try:
        # Create request
        request = FlightRequest(
            origin=origin,
            destination=dest,
            departure_date=dep_date,
            return_date=ret_date
        )

        # Setup orchestrator
        orchestrator = FlightOrchestrator()
        
        # Scraper mapping
        scraper_map = {
            "emirates": EmiratesScraper,
            "ek": EmiratesScraper,
            "emiratesv2": EmiratesV2Scraper,
            "ethiopian": EthiopianScraper,
            "et": EthiopianScraper,
            "qatar": QatarScraper,
            "qr": QatarScraper
        }

        if airline_filter:
            if airline_filter in scraper_map:
                orchestrator.register_scraper(scraper_map[airline_filter]())
            else:
                await status_msg.edit_text(
                    f"⚠️ Unknown airline: {airline_filter}\n"
                    "Supported: emirates, emiratesv2, ethiopian, qatar"
                )
                return
        else:
            # Register all
            orchestrator.register_scraper(EmiratesScraper())
            orchestrator.register_scraper(EthiopianScraper())
            orchestrator.register_scraper(QatarScraper())

        # Run search
        import asyncio
        loop = asyncio.get_running_loop()
        # asyncio.to_thread is only available in Python 3.9+
        # Using run_in_executor for Python 3.8 compatibility (Ubuntu 20.04 default)
        results_by_airline, errors = await loop.run_in_executor(None, orchestrator.scan_all, request)

        if not results_by_airline and not errors:
            await status_msg.edit_text("❌ No flights found for this route and dates.")
            return

        # Format results
        response = f"✈️ <b>Flight Results</b>\n" \
                   f"{origin} → {dest}\n" \
                   f"Requested: {dep_str} to {ret_str}\n\n"

        for airline, flights in results_by_airline.items():
            response += f"🔵 <b>{airline}</b>\n"
            
            # Show top 9 flights
            for i, flight in enumerate(flights[:9], 1):
                medal = "🥇" if i == 1 else ""
                best_tag = " (BEST)" if flight.is_lowest else ""
                response += f"{i}. {flight.departure_date} - {flight.return_date}: <b>{flight.price_display}</b>{medal}{best_tag}\n"
            
            response += "\n"
            
        # Report errors
        if errors:
            response += "\n⚠️ <b>Errors encountered:</b>\n"
            for error in errors:
                response += f"❌ {error['airline']}: {error['message']}\n"
                
        await status_msg.edit_text(response, parse_mode="HTML")
        
        # Send screenshots for errors
        for error in errors:
            # Send all progress screenshots if available
            if error.get('screenshot_paths'):
                for path in error['screenshot_paths']:
                    if os.path.exists(path):
                        try:
                            # Extract step name from filename for caption
                            filename = os.path.basename(path)
                            caption = f"📸 {error['airline']} Step: {filename}"
                            await update.message.reply_photo(
                                photo=open(path, 'rb'),
                                caption=caption
                            )
                        except Exception as e:
                            logger.error(f"Failed to send screenshot {path}: {e}")
            
            # Fallback to single screenshot path if no list or list empty
            elif error.get('screenshot_path') and os.path.exists(error['screenshot_path']):
                try:
                    await update.message.reply_photo(
                        photo=open(error['screenshot_path'], 'rb'),
                        caption=f"📸 Debug screenshot for {error['airline']}"
                    )
                except Exception as e:
                    logger.error(f"Failed to send screenshot: {e}")

    except Exception as e:
        logger.error(f"Search failed: {e}")
        await status_msg.edit_text(f"❌ An error occurred during search: {str(e)}")

def main() -> None:
    """Start the bot."""
    # Get token from environment variable
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set.")
        return

    # Create the Application
    builder = Application.builder().token(token)
    
    # Configure proxy if available
    proxy_url = os.environ.get("PROXY_URL")
    if proxy_url:
        print(f"Using proxy: {proxy_url}")
        builder.proxy(proxy_url)
        builder.get_updates_proxy(proxy_url)

    # Increase timeouts and pool size for slow proxies
    builder.connection_pool_size(8)
    builder.connect_timeout(60.0)
    builder.read_timeout(60.0)
    builder.write_timeout(60.0)
    builder.get_updates_connection_pool_size(8)
    builder.get_updates_connect_timeout(60.0)
    builder.get_updates_read_timeout(60.0)
    builder.get_updates_write_timeout(60.0)

    application = builder.build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("search", search))

    # Run the bot
    print("🤖 Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
