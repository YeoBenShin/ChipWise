import logging
import os
from typing import Dict, List, Tuple

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from min_cash_flow import compute


logging.basicConfig(
	format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
	level=logging.INFO,
)


MAIN_MENU = [
	["Compute Debt"],
	["Add Players"],
	["Edit Information", "Clear All Information"],
]

DONE_ADDING = "Done Adding Players"
BACK_MAIN = "Back to Main Menu"

EDIT_TYPE_MENU = [["Players"], [BACK_MAIN]]
EDIT_CONTINUE_MENU = [["Yes", "No"]]

MODE_ADD_MULTI = "add_multi"
MODE_EDIT_CHOOSE_TYPE = "edit_choose_type"
MODE_EDIT_CHOOSE_PLAYER = "edit_choose_player"
MODE_EDIT_PLAYER_VALUE = "edit_player_value"
MODE_EDIT_CONTINUE = "edit_continue"

ERROR_PREFIX = "Error: {detail}"
ERR_INVALID_PLAYER_FORMAT = "Invalid format.\nUse: person_name amount"
ERR_EMPTY_NAME = "Name cannot be empty."
ERR_EMPTY_PLAYER_BLOCK = "Please provide at least one non-empty line."
ERR_DUPLICATE_PLAYER_IN_INPUT = "Duplicate player name in the same input: {name}"
ERR_SIGN_SEPARATED_FROM_AMOUNT = "Invalid amount. Do not separate '+' or '-' from the number (example: -20, not - 20)."
ERR_NO_PLAYERS_TO_COMPUTE = "No players found. Add players first."
ERR_PLAYER_EXISTS = "Player already exists: {name}.\nUse Edit Information to change it."
ERR_NO_PLAYERS_TO_EDIT = "No players available to edit."
ERR_INVALID_EDIT_OPTION = "Invalid option.\nChoose 'Players'."
ERR_PLAYER_NOT_FOUND = "Player not found.\nPlease choose one of the listed names."
ERR_SELECTED_PLAYER_MISSING = "Selected player no longer exists.\nChoose edit option again."
ERR_PLAYER_NAME_EXISTS = "Player name already exists: {name}"
ERR_CHOOSE_YES_NO = "Please choose Yes or No."
ERR_UNKNOWN_OPTION = "Unknown option.\nUse the menu buttons or /start."
ERR_MISSING_BOT_TOKEN = "Missing TELEGRAM_BOT_TOKEN in environment or .env file"


def format_error(detail: str) -> str:
	return ERROR_PREFIX.format(detail=detail)


def load_dotenv_if_exists(dotenv_path: str = ".env") -> None:
	if not os.path.exists(dotenv_path):
		return

	with open(dotenv_path, "r", encoding="utf-8") as file:
		for raw_line in file:
			line = raw_line.strip()
			if not line or line.startswith("#") or "=" not in line:
				continue
			key, value = line.split("=", 1)
			key = key.strip()
			value = value.strip().strip('"').strip("'")
			if key and key not in os.environ:
				os.environ[key] = value


def get_players_store(context: ContextTypes.DEFAULT_TYPE) -> Dict[str, float]:
	players = context.user_data.setdefault("players", {})
	return players


def set_mode(context: ContextTypes.DEFAULT_TYPE, mode: str | None) -> None:
	if mode is None:
		context.user_data.pop("mode", None)
	else:
		context.user_data["mode"] = mode


def get_mode(context: ContextTypes.DEFAULT_TYPE) -> str | None:
	return context.user_data.get("mode")


def build_main_menu_markup() -> ReplyKeyboardMarkup:
	return ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)


def build_edit_player_picker_markup(players: Dict[str, float]) -> ReplyKeyboardMarkup:
	rows = [[name] for name in players.keys()]
	rows.append([BACK_MAIN])
	return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def parse_player_line(text: str) -> Tuple[str, float]:
	parts = text.strip().split()
	if len(parts) < 2:
		raise ValueError(ERR_INVALID_PLAYER_FORMAT)

	amount_token = parts[-1]
	if len(parts) >= 2 and parts[-2] in {"-", "+"}:
		raise ValueError(ERR_SIGN_SEPARATED_FROM_AMOUNT)

	name = " ".join(parts[:-1]).strip()
	if not name:
		raise ValueError(ERR_EMPTY_NAME)

	try:
		amount = float(amount_token)
	except ValueError as error:
		raise ValueError(ERR_INVALID_PLAYER_FORMAT) from error

	return name, amount


def parse_multiple_players_block(text: str) -> List[Tuple[str, float]]:
	lines = [line.strip() for line in text.splitlines() if line.strip()]
	if not lines:
		raise ValueError(ERR_EMPTY_PLAYER_BLOCK)

	parsed: List[Tuple[str, float]] = []
	seen_names = set()

	for line in lines:
		try:
			name, amount = parse_player_line(line)
		except ValueError as error:
			raise ValueError(f"{error}") from error

		lowered = name.lower()
		if lowered in seen_names:
			raise ValueError(f"{ERR_DUPLICATE_PLAYER_IN_INPUT.format(name=name)}")
		seen_names.add(lowered)
		parsed.append((name, amount))

	return parsed


def build_net_summary(players: Dict[str, float]) -> str:
	total_owes = sum(-amount for amount in players.values() if amount < 0)
	total_owed = sum(amount for amount in players.values() if amount > 0)
	difference = total_owed - total_owes

	if abs(difference) > 1e-9:
		return (
			f"Warning: Total owed does not match total owes. Please check the input data.\n\n"
			f"Total Owed: ${total_owed:.2f}, Total Owes: ${total_owes:.2f}\n"
			f"Difference: ${difference:.2f}"
		)

	return (
		f"Total Owed: ${total_owed:.2f}, Total Owes: ${total_owes:.2f}\n"
		f"Difference: ${difference:.2f}"
	)


def build_data_summary_from_values(players: Dict[str, float]) -> str:
	if not players:
		return "Players: (none)"

	lines = ["Players:"]
	for name, amount in players.items():
		lines.append(f"- {name}: ${amount:.2f}")
	lines.append("")
	lines.append(build_net_summary(players))
	return "\n".join(lines)


def build_data_summary(context: ContextTypes.DEFAULT_TYPE) -> str:
	players = get_players_store(context)
	return build_data_summary_from_values(players)


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, prefix: str | None = None) -> None:
	summary = build_data_summary(context)
	message = f"{prefix}\n\n{summary}" if prefix else summary
	await update.message.reply_text(message, reply_markup=build_main_menu_markup())


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	set_mode(context, None)
	await show_main_menu(update, context, "Welcome. Choose an option:")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	set_mode(context, None)
	context.user_data.pop("edit_target_player", None)
	await show_main_menu(update, context, "Operation canceled.")


async def handle_compute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	players = get_players_store(context)

	if not players:
		await update.message.reply_text(
			ERR_NO_PLAYERS_TO_COMPUTE,
			reply_markup=build_main_menu_markup(),
		)
		return

	final_state = [[name, amount] for name, amount in players.items()]
	transactions = compute(final_state)
	net_summary = build_net_summary(players)
	output = "\n".join(transactions)

	await update.message.reply_text(output, reply_markup=build_main_menu_markup())


async def enter_add_multi_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	set_mode(context, MODE_ADD_MULTI)
	await update.message.reply_text(
		"Send all players at once, one per line, in format: person_name amount\n\n"
		"The amount should be each player's FINAL net result. Use negative for losses and positive for winnings.\n\n"
		"Example:\nAlice -20\nBen 15.5\nCheryl 100",
		reply_markup=ReplyKeyboardMarkup([[BACK_MAIN]], resize_keyboard=True),
	)


async def handle_add_multi_mode(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
	if text == BACK_MAIN:
		set_mode(context, None)
		await show_main_menu(update, context, "Back to main menu.")
		return

	players = get_players_store(context)

	try:
		parsed_players = parse_multiple_players_block(text)
		for name, _ in parsed_players:
			if name in players:
				raise ValueError(ERR_PLAYER_EXISTS.format(name=name))
	except ValueError as error:
		await update.message.reply_text(
			format_error(str(error)),
			reply_markup=ReplyKeyboardMarkup([[BACK_MAIN]], resize_keyboard=True),
		)
		return

	for name, amount in parsed_players:
		players[name] = amount

	set_mode(context, None)
	await show_main_menu(update, context, f"Added {len(parsed_players)} players.")

async def enter_edit_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	set_mode(context, MODE_EDIT_CHOOSE_TYPE)
	current_state = build_data_summary(context)
	await update.message.reply_text(
		f"Current state:\n{current_state}\n\nWhat would you like to edit?",
		reply_markup=ReplyKeyboardMarkup(EDIT_TYPE_MENU, resize_keyboard=True),
	)


async def ask_edit_continue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	set_mode(context, MODE_EDIT_CONTINUE)
	await update.message.reply_text(
		"Do you still want to edit?",
		reply_markup=ReplyKeyboardMarkup(EDIT_CONTINUE_MENU, resize_keyboard=True),
	)


async def handle_edit_choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
	if text == BACK_MAIN:
		set_mode(context, None)
		await show_main_menu(update, context, "Back to main menu.")
		return

	if text == "Players":
		players = get_players_store(context)
		if not players:
			await update.message.reply_text(
				ERR_NO_PLAYERS_TO_EDIT,
				reply_markup=ReplyKeyboardMarkup(EDIT_TYPE_MENU, resize_keyboard=True),
			)
			return

		set_mode(context, MODE_EDIT_CHOOSE_PLAYER)
		current_state = build_data_summary(context)
		await update.message.reply_text(
			f"Current state:\n{current_state}\n\nChoose a player to edit by name.",
			reply_markup=build_edit_player_picker_markup(players),
		)
		return

	await update.message.reply_text(
		ERR_INVALID_EDIT_OPTION,
		reply_markup=ReplyKeyboardMarkup(EDIT_TYPE_MENU, resize_keyboard=True),
	)


async def handle_edit_choose_player(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
	if text == BACK_MAIN:
		set_mode(context, MODE_EDIT_CHOOSE_TYPE)
		await update.message.reply_text(
			"What would you like to edit?",
			reply_markup=ReplyKeyboardMarkup(EDIT_TYPE_MENU, resize_keyboard=True),
		)
		return

	players = get_players_store(context)
	if text not in players:
		await update.message.reply_text(
			ERR_PLAYER_NOT_FOUND,
			reply_markup=build_edit_player_picker_markup(players),
		)
		return

	context.user_data["edit_target_player"] = text
	set_mode(context, MODE_EDIT_PLAYER_VALUE)
	await update.message.reply_text(
		"Send the new player info in format: person_name amount\n\n"
		"The amount should be each player's FINAL net result. Use negative for losses and positive for winnings.",
		reply_markup=ReplyKeyboardMarkup([[BACK_MAIN]], resize_keyboard=True),
	)


async def handle_edit_player_value(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
	if text == BACK_MAIN:
		set_mode(context, MODE_EDIT_CHOOSE_TYPE)
		await update.message.reply_text(
			"What would you like to edit?",
			reply_markup=ReplyKeyboardMarkup(EDIT_TYPE_MENU, resize_keyboard=True),
		)
		return

	old_name = context.user_data.get("edit_target_player")
	players = get_players_store(context)

	if old_name not in players:
		set_mode(context, MODE_EDIT_CHOOSE_TYPE)
		await update.message.reply_text(
			ERR_SELECTED_PLAYER_MISSING,
			reply_markup=ReplyKeyboardMarkup(EDIT_TYPE_MENU, resize_keyboard=True),
		)
		return

	try:
		new_name, new_amount = parse_player_line(text)
		if new_name != old_name and new_name in players:
			raise ValueError(ERR_PLAYER_NAME_EXISTS.format(name=new_name))
	except ValueError as error:
		await update.message.reply_text(
			format_error(str(error)),
			reply_markup=ReplyKeyboardMarkup([[BACK_MAIN]], resize_keyboard=True),
		)
		return

	old_players = dict(players)

	del players[old_name]
	players[new_name] = new_amount
	context.user_data.pop("edit_target_player", None)

	new_state = build_data_summary_from_values(players)
	await update.message.reply_text(
		f"Player updated.\n"
		f"Old value: {old_name} ${old_players[old_name]:.2f}\n"
		f"New value: {new_name} ${new_amount:.2f}\n\n"
		f"New state:\n{new_state}"
	)
	await ask_edit_continue(update, context)

async def handle_edit_continue(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
	lowered = text.strip().lower()
	if lowered == "yes":
		set_mode(context, MODE_EDIT_CHOOSE_TYPE)
		await update.message.reply_text(
			"What would you like to edit?",
			reply_markup=ReplyKeyboardMarkup(EDIT_TYPE_MENU, resize_keyboard=True),
		)
		return

	if lowered == "no":
		set_mode(context, None)
		await show_main_menu(update, context, "Finished editing.")
		return

	await update.message.reply_text(
		ERR_CHOOSE_YES_NO,
		reply_markup=ReplyKeyboardMarkup(EDIT_CONTINUE_MENU, resize_keyboard=True),
	)


async def clear_all_information(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	context.user_data["players"] = {}
	context.user_data.pop("edit_target_player", None)
	set_mode(context, None)
	await show_main_menu(update, context, "All information has been cleared.")


async def route_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	text = (update.message.text or "").strip()
	mode = get_mode(context)

	if text == "/cancel":
		await cancel(update, context)
		return

	if mode == MODE_ADD_MULTI:
		await handle_add_multi_mode(update, context, text)
		return

	if mode == MODE_EDIT_CHOOSE_TYPE:
		await handle_edit_choose_type(update, context, text)
		return

	if mode == MODE_EDIT_CHOOSE_PLAYER:
		await handle_edit_choose_player(update, context, text)
		return

	if mode == MODE_EDIT_PLAYER_VALUE:
		await handle_edit_player_value(update, context, text)
		return

	if mode == MODE_EDIT_CONTINUE:
		await handle_edit_continue(update, context, text)
		return

	if text == "Compute Debt":
		await handle_compute(update, context)
		return

	if text == "Add Players":
		await enter_add_multi_mode(update, context)
		return

	if text == "Edit Information":
		await enter_edit_mode(update, context)
		return

	if text == "Clear All Information":
		await clear_all_information(update, context)
		return

	await update.message.reply_text(
		ERR_UNKNOWN_OPTION,
		reply_markup=build_main_menu_markup(),
	)


def get_bot_token() -> str:
	load_dotenv_if_exists()
	token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
	if not token:
		raise ValueError(ERR_MISSING_BOT_TOKEN)
	return token


def main() -> None:
	token = get_bot_token()
	app = Application.builder().token(token).build()

	app.add_handler(CommandHandler("start", start))
	app.add_handler(CommandHandler("help", start))
	app.add_handler(CommandHandler("cancel", cancel))
	app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, route_text))

	app.run_polling()


if __name__ == "__main__":
	main()
