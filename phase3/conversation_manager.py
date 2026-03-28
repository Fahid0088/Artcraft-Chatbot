from __future__ import annotations

import difflib
import os
import random
import re
from typing import Dict, List, Optional, Tuple

try:
    import ollama
except ImportError:
    ollama = None

try:
    from .prompt_template import SYSTEM_PROMPT
except ImportError:
    from prompt_template import SYSTEM_PROMPT


PRODUCT_CATALOG: Dict[str, float] = {
    "Watercolor Set 12 colors": 12.99,
    "Watercolor Set 24 colors": 22.99,
    "Acrylic Paint Set 12 colors": 15.99,
    "Acrylic Paint Set 24 colors": 28.99,
    "Oil Paint Set 12 colors": 35.99,
    "Round Brush Set 6 pcs": 9.99,
    "Flat Brush Set 6 pcs": 9.99,
    "Complete Brush Set 12 pcs": 17.99,
    "Sketching Pencil Set 12 pcs": 8.99,
    "Charcoal Set": 6.99,
    "Watercolor Paper Pad": 11.99,
    "Sketchbook A4": 7.99,
    "Canvas Pack 3 pcs": 14.99,
    "Palette Knife Set": 8.99,
    "Clay 500g": 9.99,
    "Resin Kit": 24.99,
    "Craft Glue": 3.99,
    "Glitter Set": 5.99,
    "Beads Set": 6.99,
    "Easel wooden": 29.99,
}

ALIASES: Dict[str, str] = {
    "watercolor set 24": "Watercolor Set 24 colors",
    "watercolor 24": "Watercolor Set 24 colors",
    "watercolor set 12": "Watercolor Set 12 colors",
    "watercolor 12": "Watercolor Set 12 colors",
    "watercolor set": "Watercolor Set 12 colors",
    "water color set": "Watercolor Set 12 colors",
    "watercolor": "Watercolor Set 12 colors",
    "acrylic paint set 24": "Acrylic Paint Set 24 colors",
    "acrylic 24": "Acrylic Paint Set 24 colors",
    "acrylic paint set 12": "Acrylic Paint Set 12 colors",
    "acrylic 12": "Acrylic Paint Set 12 colors",
    "acrylic paint": "Acrylic Paint Set 12 colors",
    "acrylic paints": "Acrylic Paint Set 12 colors",
    "acrylic set": "Acrylic Paint Set 12 colors",
    "acrylic": "Acrylic Paint Set 12 colors",
    "oil paint": "Oil Paint Set 12 colors",
    "oil colors": "Oil Paint Set 12 colors",
    "oil set": "Oil Paint Set 12 colors",
    "round brushes": "Round Brush Set 6 pcs",
    "round brush": "Round Brush Set 6 pcs",
    "flat brushes": "Flat Brush Set 6 pcs",
    "flat brush": "Flat Brush Set 6 pcs",
    "complete brush set": "Complete Brush Set 12 pcs",
    "complete set": "Complete Brush Set 12 pcs",
    "brush set": "Complete Brush Set 12 pcs",
    "brushes": "Complete Brush Set 12 pcs",
    "brush": "Complete Brush Set 12 pcs",
    "sketching pencils": "Sketching Pencil Set 12 pcs",
    "sketching pencil": "Sketching Pencil Set 12 pcs",
    "pencils": "Sketching Pencil Set 12 pcs",
    "pencil": "Sketching Pencil Set 12 pcs",
    "charcoal set": "Charcoal Set",
    "charcoal": "Charcoal Set",
    "watercolor paper": "Watercolor Paper Pad",
    "paper pad": "Watercolor Paper Pad",
    "sketchbook": "Sketchbook A4",
    "canvas pack": "Canvas Pack 3 pcs",
    "canvas": "Canvas Pack 3 pcs",
    "palette knife": "Palette Knife Set",
    "clay": "Clay 500g",
    "resin": "Resin Kit",
    "craft glue": "Craft Glue",
    "glue": "Craft Glue",
    "glitter": "Glitter Set",
    "beads": "Beads Set",
    "easel": "Easel wooden",
}

ART_TERMS = [
    "art", "craft", "paint", "paints", "color", "colors", "brush", "brushes",
    "watercolor", "acrylic", "oil", "charcoal", "pencil", "canvas", "paper",
    "glue", "glitter", "beads", "clay", "resin", "sketch", "drawing", "doll house",
    "paper house", "cardboard", "model", "supplies", "materials", "tools", "equipment",
    "easel", "palette", "knife", "origami", "boat", "line", "lines", "painting",
    "paintings", "sketchbook", "school project", "poster", "craft project",
]

OFF_TOPIC_TERMS = [
    "coffee", "latte", "espresso", "cappuccino", "tea", "laptop", "laptops", "phone",
    "math", "equation", "algebra", "physics", "chemistry", "politics", "code",
    "programming", "football", "cricket", "recipe", "food", "restaurant",
]

UNSUPPORTED_PRODUCT_TERMS = [
    "hot glue gun", "glue gun", "laptop", "coffee", "tea",
]

GOODBYE_REPLY = "Thank you for visiting ArtCraft! Have a creative day!"
THANKS_REPLY = "You're welcome! Let me know if you need any art or craft help."
OFF_TOPIC_REPLY = (
    "I can help with art supplies, craft materials, store products, and simple "
    "art/craft guidance. Would you like help with that?"
)


class ConversationManager:
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or os.getenv("ARTCRAFT_OLLAMA_MODEL", "llama3.2:3b")
        self.use_llm = os.getenv("ARTCRAFT_USE_LLM", "1") == "1"
        self.history: List[Dict[str, str]] = []
        self.order_step = 0
        self.cancel_pending = False
        self.order_placed = False
        self.order_cancelled = False
        self.order_id: Optional[str] = None
        self.order_data = {
            "name": None,
            "phone": None,
            "email": None,
            "items": None,
        }

    def add_message(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})
        if len(self.history) > 12:
            self.history = self.history[-12:]

    def normalize_simple_text(self, text: str) -> str:
        return re.sub(r"[^a-z]", "", text.strip().lower())

    def normalize_name_input(self, text: str) -> str:
        value = text.strip().rstrip(".,!?:;")
        match = re.match(r"^(?:my name is|i am|i'm)\s+(.+)$", value, flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip()
        value = re.split(
            r"\b(?:and my phone number is|my phone number is|phone number is|phone is|number is|and my email is|my email is|email is)\b",
            value,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip()
        return value.rstrip(".,!?:;")

    def is_valid_full_name(self, text: str) -> bool:
        value = self.normalize_name_input(text)
        if not value:
            return False
        normalized = self.normalize_simple_text(value)
        if normalized in {"mynameis", "iam", "im", "name"}:
            return False
        parts = [part for part in re.split(r"\s+", value) if part]
        if len(parts) < 2:
            return False
        return all(re.search(r"[a-zA-Z]", part) for part in parts)

    def normalize_phone_input(self, text: str) -> str:
        value = text.lower()
        value = value.replace(",", " ").replace("-", " ").replace(".", " ")
        word_to_digit = {
            "zero": "0",
            "one": "1",
            "two": "2",
            "three": "3",
            "four": "4",
            "five": "5",
            "six": "6",
            "seven": "7",
            "eight": "8",
            "nine": "9",
            "oh": "0",
            "o": "0",
        }
        for word, digit in word_to_digit.items():
            value = re.sub(rf"\b{word}\b", digit, value)
        return re.sub(r"\D", "", value)

    def is_valid_email(self, text: str) -> bool:
        return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", text.strip()))

    def is_valid_phone(self, text: str) -> bool:
        return len(self.normalize_phone_input(text)) >= 10

    def extract_phone_if_present(self, text: str) -> Optional[str]:
        normalized = self.normalize_phone_input(text)
        return normalized if len(normalized) >= 10 else None

    def is_goodbye(self, text: str) -> bool:
        return bool(re.search(r"\b(bye|goodbye|good bye|see you)\b", text.lower()))

    def is_thanks(self, text: str) -> bool:
        return bool(re.search(r"\b(thanks|thank you|thx)\b", text.lower()))

    def is_greeting(self, text: str) -> bool:
        return bool(re.search(r"\b(hello|hi|hey)\b", text.lower()))

    def is_yes_no_reply(self, text: str) -> bool:
        return self.normalize_simple_text(text) in {"yes", "y", "yeah", "yep", "sure", "ok", "okay", "no", "n", "nope"}

    def is_acknowledgement(self, text: str) -> bool:
        return self.normalize_simple_text(text) in {"ok", "okay", "alright", "fine", "yeah", "yep", "sure"}

    def has_orderish_word(self, text: str) -> bool:
        tokens = re.findall(r"[a-z]+", text.lower())
        orderish_words = {"order", "orders", "ardor", "ardors", "mother", "office", "older", "hour"}
        for token in tokens:
            if token in orderish_words:
                return True
            if difflib.get_close_matches(token, ["order"], n=1, cutoff=0.72):
                return True
        return False

    def has_placeish_intent(self, text: str) -> bool:
        tokens = re.findall(r"[a-z]+", text.lower())
        intent_words = {"place", "please", "buy", "purchase", "purchasee", "purches", "purschase", "order"}
        for token in tokens:
            if token in intent_words:
                return True
            if difflib.get_close_matches(token, ["place", "purchase", "buy"], n=1, cutoff=0.72):
                return True
        return False

    def has_cancelish_intent(self, text: str) -> bool:
        tokens = re.findall(r"[a-z]+", text.lower())
        cancelish_words = {"cancel", "cansel", "cancelled", "canceled", "gents", "cant", "send", "sent", "tens"}
        for token in tokens:
            if token in cancelish_words:
                return True
            if difflib.get_close_matches(token, ["cancel"], n=1, cutoff=0.7):
                return True
        return False

    def is_likely_cancel_request(self, text: str) -> bool:
        lowered = text.lower().replace("/", " ")
        if self.is_cancel_request(lowered):
            return True

        tokens = re.findall(r"[a-z]+", lowered)
        if not tokens:
            return False

        has_order = self.has_orderish_word(lowered)
        has_cancel = self.has_cancelish_intent(lowered)

        # Let explicit order requests win unless there is a clear cancel signal too.
        if self.is_order_request(lowered) and not has_cancel:
            return False

        if has_order and has_cancel:
            return True

        if has_order and any(token in {"cant", "send", "sent", "tens", "gents"} for token in tokens):
            return True

        normalized = " ".join(tokens)
        likely_patterns = [
            "cant send my order",
            "can t send my order",
            "send my order",
            "gents in my order",
            "tens and my order",
        ]
        return any(difflib.SequenceMatcher(None, normalized, pattern).ratio() >= 0.72 for pattern in likely_patterns)

    def is_order_request(self, text: str) -> bool:
        text = text.lower()
        keywords = [
            "place an order",
            "place order",
            "place my order",
            "place my other",
            "place my mother",
            "place new order",
            "new order",
            "want to place an order",
            "i want to place an order",
            "i want to order",
            "i want to buy",
            "i want to purchase",
            "make an order",
            "order please",
        ]
        explicit_match = any(keyword in text for keyword in keywords)
        if explicit_match:
            return True
        if self.is_art_domain_query(text):
            return False
        return (
            ("place" in text and self.has_orderish_word(text))
            or (self.has_placeish_intent(text) and self.has_orderish_word(text))
        )

    def normalize_email_input(self, text: str) -> str:
        value = text.strip().lower()
        replacements = {
            " at the rate ": "@",
            " at rate ": "@",
            " at ": "@",
            " dot com": ".com",
            " dot pk": ".pk",
            " dot org": ".org",
            " dot net": ".net",
            " dot edu": ".edu",
            " dot ": ".",
            " underscore ": "_",
            " dash ": "-",
            " hyphen ": "-",
            " space ": "",
        }

        for source, target in replacements.items():
            value = value.replace(source, target)

        doubles = {
            "double zero": "00",
            "double one": "11",
            "double two": "22",
            "double three": "33",
            "double four": "44",
            "double five": "55",
            "double six": "66",
            "double seven": "77",
            "double eight": "88",
            "double nine": "99",
        }
        for source, target in doubles.items():
            value = value.replace(source, target)

        value = value.replace(",", "").replace(" ", "")
        value = re.sub(r"(?<=\w)-(?=\w)", "", value)
        value = value.rstrip(".")
        value = value.replace("@g.mail.com", "@gmail.com")
        if value.endswith("@gmail.c"):
            value = value[:-2] + ".com"
        if value.endswith(".c"):
            value = value[:-2] + ".com"
        return value

    def extract_email_if_present(self, text: str) -> Optional[str]:
        value = text.strip().lower()
        replacements = {
            " at the rate ": " @ ",
            " at rate ": " @ ",
            " at ": " @ ",
            " dot com": " .com",
            " dot pk": " .pk",
            " dot org": " .org",
            " dot net": " .net",
            " dot edu": " .edu",
            " dot ": " . ",
            " underscore ": "_",
            " dash ": "-",
            " hyphen ": "-",
        }
        for source, target in replacements.items():
            value = value.replace(source, target)

        doubles = {
            "double zero": "00",
            "double one": "11",
            "double two": "22",
            "double three": "33",
            "double four": "44",
            "double five": "55",
            "double six": "66",
            "double seven": "77",
            "double eight": "88",
            "double nine": "99",
        }
        for source, target in doubles.items():
            value = value.replace(source, target)

        value = re.sub(r"(?<=\w)-(?=\w)", "", value)
        value = value.replace(",", " ")
        value = re.sub(r"\s*@\s*", "@", value)
        value = re.sub(r"\s*\.\s*", ".", value)
        value = re.sub(r"\s+", " ", value)

        match = re.search(r"[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}", value)
        if match:
            candidate = self.normalize_email_input(match.group(0))
            if self.is_valid_email(candidate):
                return candidate

        compact = re.sub(r"[^a-z0-9@._+\-\s]", " ", value)
        compact = re.sub(r"\s+", " ", compact).strip()
        provider_match = re.search(
            r"\b([a-z0-9._+\-]+)\s+(?:and\s+)?(gmail|yahoo|outlook|hotmail)\.(com|net|org|pk|edu)\b",
            compact,
        )
        if provider_match:
            local, provider, suffix = provider_match.groups()
            candidate = f"{local}@{provider}.{suffix}"
            if self.is_valid_email(candidate):
                return candidate

        normalized = self.normalize_email_input(text)
        if " " not in text.strip() and self.is_valid_email(normalized):
            return normalized
        return None

    def is_cancel_request(self, text: str) -> bool:
        text = text.lower().replace("/", " ")
        keywords = ["cancel my order", "cancel mu order", "cancel order", "cancel the order", "cancel it"]
        return any(keyword in text for keyword in keywords) or (
            self.has_cancelish_intent(text) and self.has_orderish_word(text)
        )

    def is_art_domain_query(self, text: str) -> bool:
        text = text.lower()
        return any(term in text for term in ART_TERMS)

    def is_off_topic_query(self, text: str) -> bool:
        text = text.lower()
        return any(term in text for term in OFF_TOPIC_TERMS)

    def is_unclear_short_query(self, text: str) -> bool:
        tokens = re.findall(r"[a-z]+", text.lower())
        if not tokens or len(tokens) > 5:
            return False
        if self.is_order_request(text) or self.is_likely_cancel_request(text):
            return False
        if self.is_art_domain_query(text) or self.is_off_topic_query(text):
            return False
        if self.extract_email_if_present(text) or self.extract_phone_if_present(text):
            return False
        return True

    def should_use_llm(self, user_input: str) -> bool:
        if not self.use_llm or ollama is None:
            return False
        text = user_input.strip()
        if not text:
            return False
        if self.order_step > 0 or self.cancel_pending:
            return False
        if self.is_order_request(text) or self.is_cancel_request(text):
            return False
        if self.is_goodbye(text) or self.is_thanks(text) or self.is_greeting(text):
            return False
        if self.is_yes_no_reply(text) or self.is_acknowledgement(text):
            return False
        if self.is_unclear_short_query(text):
            return False
        return True

    def has_unsupported_product(self, text: str) -> bool:
        text = text.lower()
        return any(term in text for term in UNSUPPORTED_PRODUCT_TERMS)

    def parse_items(self, text: str) -> List[Tuple[str, int]]:
        text_lower = text.lower()
        quantity_match = re.search(r"\b(\d+)\b", text_lower)
        quantity = int(quantity_match.group(1)) if quantity_match else 1

        matches: List[Tuple[int, int, str]] = []
        for alias, product in sorted(ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
            start = text_lower.find(alias)
            if start >= 0:
                end = start + len(alias)
                matches.append((start, end, product))

        selected: List[Tuple[int, int, str]] = []
        for start, end, product in sorted(matches, key=lambda item: (item[0], -(item[1] - item[0]))):
            overlaps = any(not (end <= used_start or start >= used_end) for used_start, used_end, _ in selected)
            if not overlaps:
                selected.append((start, end, product))

        items: List[Tuple[str, int]] = []
        seen = set()
        for _, _, product in selected:
            if product not in seen:
                items.append((product, quantity))
                seen.add(product)
        return items

    def calculate_total(self, items: List[Tuple[str, int]]) -> float:
        return sum(PRODUCT_CATALOG[product] * quantity for product, quantity in items)

    def get_order_status(self) -> str:
        if self.order_cancelled:
            return f"ORDER STATUS: Order {self.order_id} is CANCELLED."
        if self.order_placed:
            return f"ORDER STATUS: Order {self.order_id} is ACTIVE."
        return "ORDER STATUS: No order placed."

    def build_messages(self, user_input: str) -> List[Dict[str, str]]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n\n" + self.get_order_status()}]
        messages.extend(self.history[-8:])
        messages.append({"role": "user", "content": user_input})
        return messages

    def fallback_reply(self, user_input: str) -> str:
        text = user_input.strip()

        if self.is_goodbye(text):
            return GOODBYE_REPLY

        if self.is_thanks(text):
            return THANKS_REPLY

        if self.is_greeting(text):
            return "Hello! I can help with art supplies, prices, store policies, and orders."

        if self.is_yes_no_reply(text):
            if self.order_placed and not self.order_cancelled:
                return f"You have active order {self.order_id}. If you want to cancel it, just say cancel my order."
            return "I can help with art supplies, craft materials, store products, and orders. What would you like to do next?"

        if self.is_acknowledgement(text):
            if self.order_placed and not self.order_cancelled:
                return f"Your order {self.order_id} is active. If you want to cancel it, just say cancel my order."
            return "Sure. What would you like help with next?"

        if self.is_unclear_short_query(text):
            return "I didn't catch that clearly. Please say it again in a short clear sentence."

        if self.is_off_topic_query(text):
            return OFF_TOPIC_REPLY

        if self.is_art_domain_query(text):
            return "I can help with art and craft questions, product recommendations, and store details. Please try again if my previous response was not clear."

        return OFF_TOPIC_REPLY

    def llm_reply(self, user_input: str) -> str:
        if not self.should_use_llm(user_input):
            return self.fallback_reply(user_input)

        try:
            response = ollama.chat(model=self.model_name, messages=self.build_messages(user_input))
            return response["message"]["content"].strip()
        except Exception as exc:
            print(f"Ollama reply failed, using fallback: {exc}")
            return self.fallback_reply(user_input)

    def handle_order(self, user_input: str) -> str:
        if self.order_step == 1:
            name = self.normalize_name_input(user_input)
            if not self.is_valid_full_name(user_input):
                return "Please enter your full name."
            self.order_data["name"] = name
            phone = self.extract_phone_if_present(user_input)
            email = self.extract_email_if_present(user_input)
            if phone:
                self.order_data["phone"] = phone
            if email:
                self.order_data["email"] = email

            if self.order_data["phone"] and self.order_data["email"]:
                self.order_step = 4
                return "Thank you! What would you like to order and how many?"
            if self.order_data["phone"]:
                self.order_step = 3
                return f"Thank you {name}! What is your email address?"

            self.order_step = 2
            return f"Thank you {name}! What is your phone number?"

        if self.order_step == 2:
            phone = self.extract_phone_if_present(user_input)
            email = self.extract_email_if_present(user_input)
            if not phone:
                return "Please enter a valid phone number with at least 10 digits."
            self.order_data["phone"] = phone
            if email:
                self.order_data["email"] = email
                self.order_step = 4
                return "What would you like to order and how many?"

            self.order_step = 3
            return "Great! What is your email address?"

        if self.order_step == 3:
            normalized_email = self.extract_email_if_present(user_input)
            if not normalized_email:
                return "Please enter a valid email like name@gmail.com"
            self.order_data["email"] = normalized_email
            self.order_step = 4
            return "What would you like to order and how many?"

        if self.order_step == 4:
            if self.is_yes_no_reply(user_input) or self.is_acknowledgement(user_input):
                return "Please tell me which ArtCraft item you want and the quantity."
            if any(phrase in user_input.lower() for phrase in ["what type", "what kinds", "tell me", "how to", "list", "steps", "can you", "which", "materials", "tools"]):
                info_reply = self.llm_reply(user_input) if self.is_art_domain_query(user_input) else self.fallback_reply(user_input)
                return f"{info_reply}\nWhen you're ready, tell me the item and quantity."
            if self.has_unsupported_product(user_input):
                return (
                    "Sorry, that item is not available at ArtCraft. Please choose a valid ArtCraft product "
                    "like watercolor set, brushes, canvas, glue, or sketchbook."
                )
            items = self.parse_items(user_input)
            if not items:
                return (
                    "Sorry, we only sell ArtCraft supplies. Please choose a valid ArtCraft product "
                    "like watercolor set, brushes, canvas, glue, or sketchbook."
                )

            self.order_data["items"] = ", ".join(f"{quantity} x {product}" for product, quantity in items)
            total = self.calculate_total(items)
            self.order_id = f"ART-{random.randint(1000, 9999)}"
            self.order_placed = True
            self.order_cancelled = False
            self.cancel_pending = False
            self.order_step = 0

            return (
                "Order Confirmed!\n"
                f"Name: {self.order_data['name']}\n"
                f"Phone: {self.order_data['phone']}\n"
                f"Email: {self.order_data['email']}\n"
                f"Items: {self.order_data['items']}\n"
                f"Total: ${total:.2f}\n"
                "Delivery: 3-5 business days\n"
                f"Order ID: {self.order_id}"
            )

        return "May I have your full name please?"

    def handle_cancel(self, user_input: str) -> str:
        if not self.order_placed:
            return "You have no active order to cancel in this session."

        if self.order_cancelled:
            return f"Your order {self.order_id} is already cancelled. No active order exists."

        if not self.cancel_pending:
            self.cancel_pending = True
            return f"Are you sure you want to cancel Order ID {self.order_id}? (yes/no)"

        answer = self.normalize_simple_text(user_input)
        if answer in {"yes", "y"}:
            self.order_cancelled = True
            self.cancel_pending = False
            return f"Order {self.order_id} cancelled successfully. Hope to see you again!"

        if answer in {"no", "n"}:
            self.cancel_pending = False
            return f"No problem! Your order {self.order_id} is still active. How can I help you?"

        return f"Please reply yes or no. Cancel Order {self.order_id}? (yes/no)"

    def chat(self, user_input: str) -> str:
        text = user_input.strip()
        lower = text.lower()

        if self.is_goodbye(lower):
            reply = GOODBYE_REPLY
        elif self.cancel_pending:
            reply = self.handle_cancel(user_input)
        elif self.is_likely_cancel_request(lower):
            reply = self.handle_cancel(user_input)
        elif self.order_step > 0:
            reply = self.handle_order(user_input)
        elif self.is_order_request(lower):
            if self.order_placed and not self.order_cancelled:
                reply = f"You already have active order {self.order_id}. If you want to cancel it, just say cancel my order."
            elif self.order_data["name"] and self.order_data["phone"] and self.order_data["email"]:
                self.order_step = 4
                reply = f"Welcome back {self.order_data['name']}! What would you like to order and how many?"
            else:
                self.order_step = 1
                reply = "May I have your full name please?"
        elif self.order_cancelled and self.is_yes_no_reply(lower):
            reply = "Your last order is already cancelled. If you want, I can help you place a new order."
        elif self.order_placed and not self.order_cancelled and self.is_yes_no_reply(lower):
            reply = f"You have active order {self.order_id}. If you want to cancel it, just say cancel my order."
        elif self.order_placed and not self.order_cancelled and self.is_acknowledgement(lower):
            reply = f"Your order {self.order_id} is active. If you want to cancel it, just say cancel my order."
        elif self.order_placed and not self.order_cancelled and self.is_likely_cancel_request(lower):
            reply = self.handle_cancel(user_input)
        elif (self.order_placed or self.order_cancelled) and self.has_orderish_word(lower) and not self.is_art_domain_query(lower):
            if self.order_placed and not self.order_cancelled:
                reply = (
                    f"I heard something about your order {self.order_id}. "
                    "If you want to cancel it, say cancel my order. "
                    "If you want a new order, say place my order."
                )
            else:
                reply = "Your last order is already cancelled. If you want, say place my order to start a new one."
        else:
            reply = self.llm_reply(user_input)

        self.add_message("user", user_input)
        self.add_message("assistant", reply)
        return reply

    def reset(self) -> None:
        self.history = []
        self.order_step = 0
        self.cancel_pending = False
        self.order_placed = False
        self.order_cancelled = False
        self.order_id = None
        self.order_data = {
            "name": None,
            "phone": None,
            "email": None,
            "items": None,
        }
