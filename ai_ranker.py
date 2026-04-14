def rank_events(events):
    ranked = []

    for e in events:
        score = 0

        # Heuristics (AI-like ranking)
        if "hackathon" in e["type"]:
            score += 30

        if "ctf" in e["name"].lower():
            score += 40

        if "ai" in e["name"].lower():
            score += 20

        if "web3" in e["name"].lower():
            score += 15

        if e["platform"] == "Devfolio":
            score += 25

        if e["platform"] == "Unstop":
            score += 20

        e["score"] = score
        ranked.append(e)

    return sorted(ranked, key=lambda x: x["score"], reverse=True)