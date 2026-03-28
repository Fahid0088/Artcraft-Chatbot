PRODUCT_KEYWORDS = [
    "brush", "paint", "watercolor", "acrylic", "oil paint", "gouache",
    "tempera", "spray paint", "fabric paint", "face paint",
    "pencil", "charcoal", "ink", "marker", "pen", "pastel", "crayon",
    "chalk", "graphite", "eraser", "sharpener",
    "canvas", "sketchbook", "paper", "cardboard", "wood panel",
    "watercolor paper", "drawing pad", "journal",
    "round brush", "flat brush", "fan brush", "palette knife",
    "sponge", "roller", "bristle",
    "craft", "glue", "scissors", "tape", "ribbon", "thread",
    "needle", "fabric", "clay", "resin", "beads", "wire",
    "foam", "glitter", "sequins", "sticker",
    "palette", "easel", "frame", "ruler", "compass", "stencil",
    "cutting mat", "craft knife", "hot glue", "mod podge"
]

ACTION_KEYWORDS = [
    "buy", "purchase", "order", "shop", "get", "want", "need",
    "looking for", "interested", "add to cart",
    "return", "refund", "exchange", "cancel", "complaint",
    "broken", "damaged", "missing", "wrong item",
    "price", "cost", "how much", "discount", "sale", "offer",
    "recommend", "suggest", "best", "compare", "difference",
    "which one", "what is", "how to use",
    "shipping", "delivery", "track", "arrive", "dispatch",
    "express", "standard", "free shipping",
    "available", "in stock", "out of stock", "when", "restock"
]

NOISE_KEYWORDS = [
    "ok", "okay", "k", "yes", "no", "nope", "yep", "yeah",
    "sure", "alright", "fine", "cool", "great", "nice",
    "hmm", "uh", "um", "ah", "oh", "wow", "haha", "lol",
    "thanks", "thank you", "thankyou", "ty", "thx",
    "bye", "goodbye", "see you", "later", "take care"
]

def score_message(message, index, total):
    score = 0
    content = message["content"].lower()

    for word in PRODUCT_KEYWORDS:
        if word in content:
            score += 3
            break

    for word in ACTION_KEYWORDS:
        if word in content:
            score += 2
            break

    if index >= total - 2:
        score += 2

    for word in NOISE_KEYWORDS:
        if content.strip() == word:
            score -= 2
            break

    return score

def filter_history(history, capacity=10):
    total = len(history)
    scored = [(score_message(msg, i, total), i, msg) for i, msg in enumerate(history)]
    scored.sort(key=lambda x: x[0], reverse=True)
    kept = sorted(scored[:capacity], key=lambda x: x[1])
    return [msg for score, index, msg in kept]
