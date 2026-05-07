CATEGORY_RULES = {
    "Food": ["swiggy", "zomato", "restaurant", "cafe", "food"],
    "Travel": ["uber", "ola", "metro", "fuel", "flight", "train"],
    "Shopping": ["amazon", "flipkart", "myntra", "store"],
    "Utilities": ["electricity", "water", "internet", "mobile", "recharge"],
    "Income": ["salary", "payroll", "interest", "refund"],
    "Rent": ["rent", "lease"],
}

DEFAULT_CATEGORY = "Uncategorized"


def categorize(text):
    lowered = (text or "").lower()
    for category, keywords in CATEGORY_RULES.items():
        if any(keyword in lowered for keyword in keywords):
            return category
    return DEFAULT_CATEGORY
