import random, threading, time
from collections import deque
from flask import Flask, jsonify, request

app = Flask(__name__)
LOCK = threading.Lock()
HIST = deque(maxlen=300)
SAMPLE = 2  # seconds between readings
CFG = {"fla": 20.0, "temp_warn": 110.0, "temp_alarm": 130.0,
       "vib_warn": 4.5, "vib_alarm": 7.1}
STATE = {"fault": False, "n": 0, "temp": 72.0, "live": False}
NAMES = ["OK", "WARN", "ALARM"]


def level(v, warn, alarm):
    return 2 if v >= alarm else 1 if v >= warn else 0


def add(c, t, v):
    HIST.append({"ts": time.strftime("%H:%M:%S"),
                 "current": round(c, 2), "temp": round(t, 1), "vib": round(v, 2)})


def analyze():
    if not HIST:
        return {}
    last = HIST[-1]
    lv = {
        "current": level(last["current"], CFG["fla"] * 1.05, CFG["fla"] * 1.15),
        "temp": level(last["temp"], CFG["temp_warn"], CFG["temp_alarm"]),
        "vib": level(last["vib"], CFG["vib_warn"], CFG["vib_alarm"]),
    }
    eta = None
    pts = [h["temp"] for h in list(HIST)[-30:]]
    if len(pts) >= 10:
        n = len(pts)
        mx, my = (n - 1) / 2, sum(pts) / n
        slope = sum((x - mx) * (y - my) for x, y in enumerate(pts)) / sum((x - mx) ** 2 for x in range(n))
        if slope > 0.05:
            eta = round(max(0, (CFG["temp_alarm"] - last["temp"]) / slope * SAMPLE / 60), 1)
    return {"latest": last,
            "levels": {k: NAMES[v] for k, v in lv.items()},
            "status": NAMES[max(lv.values())],
            "eta_min": eta,
            "series": list(HIST)[-60:]}


def simulate():
    while True:
        time.sleep(SAMPLE)
        with LOCK:
            if STATE["live"]:
                continue
            f = STATE["fault"]
            STATE["n"] = STATE["n"] + 1 if f else 0
            n = STATE["n"]
            if f:
                STATE["temp"] += 0.8 + random.uniform(-0.2, 0.2)
            else:
                STATE["temp"] += (72 - STATE["temp"]) * 0.05 + random.uniform(-0.3, 0.3)
            add(CFG["fla"] * 0.8 + 0.1 * n + random.uniform(-0.4, 0.4),
                STATE["temp"],
                2.0 + 0.05 * n + random.uniform(-0.2, 0.2))


@app.route("/api/data")
def data():
    with LOCK:
        return jsonify(analyze())


@app.route("/api/reading", methods=["POST"])
def reading():
    j = request.get_json(force=True)
    with LOCK:
        STATE["live"] = True
        add(float(j["current"]), float(j["temp"]), float(j["vib"]))
    return jsonify(ok=True)


@app.route("/api/fault", methods=["POST"])
def fault():
    with LOCK:
        STATE["fault"] = not STATE["fault"]
        STATE["live"] = False
        return jsonify(fault=STATE["fault"])


PAGE = """<!doctype html><html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Motor Monitor</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1"></script>
<style>
body{font-family:sans-serif;background:#111;color:#eee;margin:0;padding:12px}
.row{display:flex;gap:8px;flex-wrap:wrap}
.card{flex:1;min-width:100px;background:#1e1e1e;border-radius:8px;padding:10px;text-align:center}
.v{font-size:1.6em;font-weight:bold}
.OK{color:#4caf50}.WARN{color:#ffb300}.ALARM{color:#f44336}
button{padding:10px;border:0;border-radius:6px;background:#333;color:#eee;margin:8px 0}
</style></head><body>
<h3>Motor Monitor <span id="st"></span></h3>
<div class="row">
<div class="card">Current (A)<div class="v" id="c"></div><small id="cs"></small></div>
<div class="card">Temp (C)<div class="v" id="t"></div><small id="ts"></small></div>
<div class="card">Vib (mm/s)<div class="v" id="v"></div><small id="vs"></small></div>
</div>
<p id="eta"></p>
<button onclick="fetch('/api/fault',{method:'POST'}).then(r=>r.json()).then(j=>this.textContent=j.fault?'Clear fault':'Inject fault')">Inject fault</button>
<canvas id="g1"></canvas><canvas id="g2"></canvas><canvas id="g3"></canvas>
<script>
function mk(id,label,color){return new Chart(document.getElementById(id),{type:'line',data:{labels:[],datasets:[{label:label,data:[],borderColor:color,pointRadius:0,tension:.3}]},options:{animation:false}})}
const ch={current:mk('g1','Current (A)','#42a5f5'),temp:mk('g2','Temp (C)','#ef5350'),vib:mk('g3','Vibration (mm/s)','#ab47bc')};
function setv(k,id,sid,d){const e=document.getElementById(id);e.textContent=d.latest[k];e.className='v '+d.levels[k];document.getElementById(sid).textContent=d.levels[k]}
async function tick(){
 const d=await (await fetch('/api/data')).json(); if(!d.latest)return;
 setv('current','c','cs',d);setv('temp','t','ts',d);setv('vib','v','vs',d);
 const s=document.getElementById('st');s.textContent=d.status;s.className=d.status;
 document.getElementById('eta').textContent=d.eta_min===null?'Trend: stable':'Temp rising: alarm in about '+d.eta_min+' min';
 for(const k in ch){ch[k].data.labels=d.series.map(x=>x.ts);ch[k].data.datasets[0].data=d.series.map(x=>x[k]);ch[k].update()}
}
setInterval(tick,2000);tick();
</script></body></html>"""


@app.route("/")
def index():
    return PAGE


if __name__ == "__main__":
    threading.Thread(target=simulate, daemon=True).start()
    app.run(host="0.0.0.0", port=5070)
