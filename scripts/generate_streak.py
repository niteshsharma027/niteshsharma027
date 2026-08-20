import datetime as dt
import html
import json
import os
import urllib.request

TOKEN = os.environ["GITHUB_TOKEN"]
QUERY = """
query {
  viewer {
    login
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { date contributionCount }
        }
      }
    }
  }
}
"""

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": QUERY}).encode(),
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "github-streak-card",
    },
    method="POST",
)

with urllib.request.urlopen(request) as response:
    payload = json.load(response)

if payload.get("errors"):
    raise RuntimeError(payload["errors"])

calendar = payload["data"]["viewer"]["contributionsCollection"]["contributionCalendar"]
days = [d for week in calendar["weeks"] for d in week["contributionDays"]]
counts = [d["contributionCount"] for d in days]

def streak(values):
    longest = current = 0
    for value in values:
        if value > 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    current = 0
    for value in reversed(values):
        if value > 0:
            current += 1
        else:
            break
    return current, longest

current, longest = streak(counts)
total = calendar["totalContributions"]
username = html.escape(payload["data"]["viewer"]["login"])

# Build a compact contribution heatmap from the most recent 52 weeks.
weeks = calendar["weeks"][-52:]
cell = 11
gap = 3
left = 28
top = 62
rows = 7
colors = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
rects = []
for x, week in enumerate(weeks):
    for y, day in enumerate(week["contributionDays"]):
        count = day["contributionCount"]
        level = 0 if count == 0 else min(4, 1 + (count >= 3) + (count >= 6) + (count >= 10))
        rects.append(
            f'<rect x="{left + x*(cell+gap)}" y="{top + y*(cell+gap)}" width="{cell}" height="{cell}" rx="2" fill="{colors[level]}"/>'
        )

width = 495
height = 195
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" rx="10" fill="#161b22"/>
<text x="24" y="32" fill="#58a6ff" font-family="Arial, sans-serif" font-size="20" font-weight="700">GitHub Streak</text>
<text x="24" y="52" fill="#8b949e" font-family="Arial, sans-serif" font-size="12">{username} • contribution activity</text>
<text x="375" y="29" fill="#8b949e" font-family="Arial, sans-serif" font-size="10">CURRENT</text>
<text x="375" y="47" fill="#f0f6fc" font-family="Arial, sans-serif" font-size="18" font-weight="700">{current} days</text>
<text x="375" y="68" fill="#8b949e" font-family="Arial, sans-serif" font-size="10">LONGEST</text>
<text x="375" y="86" fill="#f0f6fc" font-family="Arial, sans-serif" font-size="18" font-weight="700">{longest} days</text>
<text x="24" y="166" fill="#8b949e" font-family="Arial, sans-serif" font-size="11">{total} contributions</text>
{''.join(rects)}
</svg>'''

os.makedirs("assets", exist_ok=True)
with open("assets/streak.svg", "w", encoding="utf-8") as f:
    f.write(svg)
print(f"Generated streak card: current={current}, longest={longest}, total={total}")
