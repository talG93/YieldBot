import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ConversationHandler, CallbackContext
from telegram.error import BadRequest
import sys

TOKEN = "7256088213:AAGi4mQUR9ID-5ERBoUvk7FSciXvt4l3Uno"

# שלבים בשיחה
QUANTITY, PRICE, BUY_FEE, SELL_FEE, DESIRED_RETURN = range(5)
TAX_RATE = 0.25  # מס רווח הון 25%

def get_start_button():
    keyboard = [[InlineKeyboardButton("🔄 חישוב מחדש", callback_data="reset")]]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: CallbackContext) -> int:
    context.user_data.clear()  # איפוס כל הנתונים לפני התחלה מחדש
    if update.callback_query:
        await update.callback_query.answer()
    
    await update.effective_message.reply_text("ברוך הבא! כמה מניות קנית?")
    return QUANTITY

async def quantity(update: Update, context: CallbackContext) -> int:
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    context.user_data['quantity'] = float(update.message.text)
    await update.message.reply_text("כמה עלתה כל מניה?")
    return PRICE

async def price(update: Update, context: CallbackContext) -> int:
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    context.user_data['price'] = float(update.message.text)
    await update.message.reply_text("מהי עמלת הקניה?")
    return BUY_FEE

async def buy_fee(update: Update, context: CallbackContext) -> int:
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    context.user_data['buy_fee'] = float(update.message.text)
    await update.message.reply_text("מהי עמלת המכירה?")
    return SELL_FEE

async def sell_fee(update: Update, context: CallbackContext) -> int:
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    context.user_data['sell_fee'] = float(update.message.text)
    await update.message.reply_text("מהו אחוז התשואה הרצוי?")
    return DESIRED_RETURN

async def desired_return(update: Update, context: CallbackContext) -> int:
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    context.user_data['desired_return'] = float(update.message.text) / 100
    
    # חישוב אחוז העלייה הדרוש (בלי מס רווח הון)
    quantity = context.user_data['quantity']
    price_per_share = context.user_data['price']
    buy_fee = context.user_data['buy_fee']
    sell_fee = context.user_data['sell_fee']
    desired_return = context.user_data['desired_return']
    
    total_cost = (quantity * price_per_share) + buy_fee
    required_final_value = total_cost * (1 + desired_return)
    required_sell_price = (required_final_value + sell_fee) / quantity
    required_increase = ((required_sell_price - price_per_share) / price_per_share) * 100
    
    # חישוב אחוז העלייה הדרוש כולל מס רווח הון
    profit_before_tax = required_final_value - total_cost
    tax_amount = profit_before_tax * TAX_RATE
    required_final_value_with_tax = required_final_value + tax_amount
    required_sell_price_with_tax = (required_final_value_with_tax + sell_fee) / quantity
    required_increase_with_tax = ((required_sell_price_with_tax - price_per_share) / price_per_share) * 100
    
    result_text = (
        f"📈 תשואה נדרשת (ללא מס רווח הון): {required_increase:.2f}%\n"
        f"💰 מחיר יעד למניה: {required_sell_price:.2f}\n\n"
        f"📉 תשואה נדרשת (כולל מס רווח הון): {required_increase_with_tax:.2f}%\n"
        f"💵 מחיר יעד למניה: {required_sell_price_with_tax:.2f}"
    )
    
    await update.message.reply_text(result_text)
    await update.message.reply_text("😉 אחלה שרגא", reply_markup=get_start_button())
    return ConversationHandler.END

async def button(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    try:
        await query.answer()
        return await start(update, context)  # מתחיל שיחה חדשה בלי למחוק הודעות
    except BadRequest:
        print("⚠️ הכפתור פג תוקף, מתעלם מהבקשה.")
        return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> int:
    if update.message:
        await update.message.reply_text("בוטל בהצלחה.")
    return ConversationHandler.END

def main():
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    app = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CallbackQueryHandler(start, pattern="reset")],
        states={
            QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, quantity)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, price)],
            BUY_FEE: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_fee)],
            SELL_FEE: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_fee)],
            DESIRED_RETURN: [MessageHandler(filters.TEXT & ~filters.COMMAND, desired_return)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    app.add_handler(conv_handler)
    
    print("📢 הבוט פועל! שלח /start בטלגרם")
    app.run_polling()

if __name__ == "__main__":
    main()
