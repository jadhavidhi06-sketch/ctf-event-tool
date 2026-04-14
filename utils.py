from rich.prompt import Prompt

STATES = [
    "Maharashtra","Delhi","Karnataka","Tamil Nadu",
    "Telangana","Gujarat","Rajasthan","Uttar Pradesh"
]

def multi_select_states():
    print("\n📍 Select States (comma separated):")

    for i, s in enumerate(STATES, 1):
        print(f"{i}. {s}")

    choice = Prompt.ask("Enter numbers (or press enter for all)")

    if not choice.strip():
        return []

    selected = []
    for n in choice.split(","):
        try:
            selected.append(STATES[int(n)-1])
        except:
            pass

    return selected