def rank_events(events):
    for e in events:
        score = 0

        name = e["name"].lower()

        if "ctf" in name:
            score += 50
        if "hackathon" in name:
            score += 40
        if "ai" in name:
            score += 25
        if "cyber" in name:
            score += 30

        if e["platform"] == "CTFtime":
            score += 40
        if e["platform"] == "Devfolio":
            score += 30

        e["score"] = score

    return sorted(events, key=lambda x: x["score"], reverse=True)