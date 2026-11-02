"""Descarga del calendario de LeetCode y estadísticas derivadas."""
import datetime as dt
import json
import random
import urllib.request

API = "https://leetcode.com/graphql"
QUERY = """
query userProfileCalendar($username: String!, $year: Int) {
  matchedUser(username: $username) {
    userCalendar(year: $year) { submissionCalendar }
  }
}
"""


def _calendar(user: str, year: int) -> dict:
    body = json.dumps({"query": QUERY, "variables": {"username": user, "year": year}}).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Content-Type": "application/json",
        "Referer": f"https://leetcode.com/u/{user}/",
        "User-Agent": "Mozilla/5.0 (leetcode-heatmap)",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    user_data = (data.get("data") or {}).get("matchedUser")
    if not user_data:
        raise SystemExit(f"LeetCode: usuario '{user}' no encontrado o perfil privado")
    return json.loads(user_data["userCalendar"]["submissionCalendar"] or "{}")


def fetch(user: str, today: dt.date) -> dict[dt.date, int]:
    """Envíos por día del año actual y el anterior (cubre 53 semanas y la racha)."""
    counts: dict[dt.date, int] = {}
    for year in (today.year - 1, today.year):
        for ts, n in _calendar(user, year).items():
            day = dt.datetime.fromtimestamp(int(ts), dt.timezone.utc).date()
            counts[day] = max(counts.get(day, 0), int(n))
    return counts


def sample(today: dt.date, seed: int = 7) -> dict[dt.date, int]:
    """Datos aleatorios para probar estilos sin conexión."""
    rnd = random.Random(seed)
    counts = {}
    for i in range(420):
        day = today - dt.timedelta(days=i)
        if i < 23 or rnd.random() < 0.5:
            counts[day] = rnd.choice([1, 1, 2, 2, 3, 4, 6, 9, 14])
    return counts


def current_streak(counts: dict, today: dt.date) -> list[dt.date]:
    """Días de la racha en curso. Si hoy aún no hay envíos, cuenta desde ayer."""
    day = today if counts.get(today) else today - dt.timedelta(days=1)
    days = []
    while counts.get(day):
        days.append(day)
        day -= dt.timedelta(days=1)
    return days


def longest_streak(counts: dict) -> int:
    best = run = 0
    prev = None
    for day in sorted(d for d, n in counts.items() if n):
        run = run + 1 if prev and (day - prev).days == 1 else 1
        best = max(best, run)
        prev = day
    return best


def stats(counts: dict, today: dt.date, start: dt.date) -> dict:
    window = [n for d, n in counts.items() if start <= d <= today]
    return {
        "streak": len(current_streak(counts, today)),
        "max_streak": longest_streak(counts),
        "active_days": sum(1 for n in window if n),
        "total": sum(window),
        "best_day": max(window, default=0),
        "today_count": counts.get(today, 0),
    }


def thresholds(mode: str, values: list, counts: list[int], levels: int) -> list[float]:
    if mode == "quantile":
        active = sorted(n for n in counts if n > 0)
        if not active:
            return [1] * levels
        return [active[min(len(active) - 1, len(active) * i // levels)] for i in range(levels)]
    out = list(values)[:levels]
    while len(out) < levels:
        out.append((out[-1] if out else 0) + 1)
    return out


def level(count: int, limits: list[float]) -> int:
    return sum(1 for v in limits if count >= v)
