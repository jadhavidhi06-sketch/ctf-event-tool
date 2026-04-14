from rich.prompt import Prompt

INDIAN_STATES = [
    "Maharashtra", "Delhi", "Karnataka", "Tamil Nadu",
    "Telangana", "Gujarat", "Rajasthan", "Uttar Pradesh"
]

def multi_select_states():
    print("\n📍 Select States (comma separated, or press enter for all):")

    for i, s in enumerate(INDIAN_STATES, 1):
        print(f"{i}. {s}")

    choice = Prompt.ask("Enter numbers (e.g. 1,3,5)")

    if not choice.strip():
        return []

    selected = []
    nums = choice.split(",")

    for n in nums:
        try:
            selected.append(INDIAN_STATES[int(n)-1])
        except:
            pass

    return selected